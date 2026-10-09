#!/usr/bin/env python3
"""Offline regression checks for the 7.5.9 Creator Dashboard Open Cloud tool.

The test is deliberately network-free: it verifies the exact integration,
security gates, action inventory, scopes, metadata fields, and multipart icon
path from the PowerShell source. Roblox Studio/Creator Dashboard live calls
still require a Windows machine, a published test experience, and a suitable
Open Cloud key.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "ArenaBridge.ps1"
VERSION = "7.5.9"
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("[OK]   " if condition else "[FAIL] ") + message)
    if not condition:
        FAILURES.append(message)


def region(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    stop = source.index(end, begin)
    return source[begin:stop]


def quoted_array(source: str, variable: str) -> list[str]:
    match = re.search(r"\$" + re.escape(variable) + r"\s*=\s*@\(([^)]*)\)", source)
    if not match:
        return []
    return re.findall(r"'([^']+)'", match.group(1))


def main() -> int:
    raw = PS1.read_bytes()
    check(raw.startswith(b"\xef\xbb\xbf"), "ArenaBridge.ps1 retains the required UTF-8 BOM")
    check(b"\r\n" not in raw, "ArenaBridge.ps1 retains LF-only line endings")
    source = raw.decode("utf-8-sig")
    metadata = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    latest = str(metadata.get("notes", [""])[0])
    check(metadata.get("version") == VERSION, "version.json is 7.5.9")
    check(latest.startswith("• 7.5.9") and "creator_dashboard" in latest
          and "standardmäßig ausgeschaltet" in latest and "imageFile" in latest,
          "release note documents the default-off opt-in and supported icon upload")
    check(any("7.5.8" in str(note) and "ask_user" in str(note)
              for note in metadata.get("notes", [])[1:]),
          "the prior 7.5.8 release note remains historical")

    # Persistent opt-in: missing/legacy settings must resolve to disabled.
    settings = region(source, "function Get-BridgeSettingsFile {", "function Save-BridgeSettingsFile {")
    save = region(source, "function Save-BridgeSettingsFile {", "function Write-RuntimeLog {")
    check(re.search(r"creatorDashboardEnabled\s*=\s*\$false", settings) is not None,
          "a fresh or legacy settings file defaults the management switch to false")
    check("-contains 'creatorDashboardEnabled'" in settings
          and "$settings.creatorDashboardEnabled = [bool]$loaded.creatorDashboardEnabled" in settings,
          "the opt-in is loaded only when an explicit saved value exists")
    check("creatorDashboardEnabled = [bool]$script:SettingsCache.creatorDashboardEnabled" in save,
          "the opt-in is persisted in settings.json")
    shared_settings = region(source, "function Sync-CloudSharedSettings {", "$creatorDashboardSwitch.Add_Click")
    check("creatorDashboardEnabled = [bool]$script:SettingsCache.creatorDashboardEnabled" in shared_settings,
          "the saved opt-in is synchronized to the HTTP server's shared settings")

    # UI placement and durable toggle behavior.
    settings_xaml = region(source, "$settingsXaml = @'", "\n'@")
    cloud_card = region(settings_xaml, 'TextBlock Text="ROBLOX OPEN CLOUD API-KEY"', 'TextBlock Text="UPDATES"')
    tutorial_xaml = region(settings_xaml, 'x:Name="CloudTutorialWrap"', 'TextBlock Text="UPDATES"')
    check('x:Name="CreatorDashboardSwitch"' in cloud_card
          and "Arena darf den aktuellen Place im Creator Dashboard verwalten" in cloud_card,
          "the switch is placed inside the Open Cloud API-key settings card")
    check("standardmäßig ausgeschaltet" in cloud_card and "bereits veröffentlichte" in cloud_card,
          "settings UI states default-off and published-place-only behavior")
    click = region(source, "$creatorDashboardSwitch.Add_Click({", "# --- Startzustand: steht schon ein Schluessel bereit?")
    check("Save-BridgeSettingsFile" in click and "Sync-CloudSharedSettings" not in click,
          "click handler saves the toggle immediately; the event synchronizes the shared value")
    check("$script:Shared.BridgeSettings.creatorDashboardEnabled = $enabled" in click
          and "Standard: aus" in click,
          "the clicked value reaches the active runtime immediately and is logged")

    # Tutorial names all and only the additional rights.
    check('for ($stepIndex = 1; $stepIndex -le 10;' in source,
          "the animated key tutorial enumerates all ten steps")
    tutorial_steps = [int(value) for value in re.findall(r'x:Name="CloudStep(\d+)"', tutorial_xaml)]
    check(tutorial_steps == list(range(1, 11)), "all ten XAML tutorial cards are present in order")
    tutorial_text = "\n".join(re.findall(r'<TextBlock Text="([^"]*)"', tutorial_xaml))
    for scope in ("universe:write", "universe.place:write", "game-pass:read", "developer-product:read"):
        check(scope in tutorial_xaml, f"the setup tutorial names the additional scope {scope}")
    check("game-pass:write" in tutorial_xaml and "developer-product:write" in tutorial_xaml,
          "the tutorial includes write scopes for both monetization APIs")
    check("read UND write" in tutorial_xaml and "Creator-Dashboard-Rechte" in tutorial_xaml,
          "the tutorial distinguishes the read/write monetization permissions from asset-upload scopes")
    check("creatorDashboardRules" in source and "universe.place:write" in source
          and "developer-product:read" in source and "game-pass:write" in source,
          "agent-facing Creator Dashboard guide documents the exact required scopes")

    # Official API scope introspection and user-facing diagnosis.
    introspect = region(source, "function Invoke-OpenCloudIntrospect {", "function Get-OpenCloudArgumentValue {")
    for marker in ("$universeWrite = $false", "$universePlaceWrite = $false",
                   "$gamePassRead = $false", "$gamePassWrite = $false",
                   "$developerProductRead = $false", "$developerProductWrite = $false",
                   "scopeBase -eq 'universe'", "scopeBase -eq 'universe.place'",
                   "'game-pass','game-passes'", "'developer-product','developer-products'"):
        check(marker in introspect, f"Open Cloud introspection recognizes {marker}")
    check("universeWrite = $universeWrite" in introspect
          and "developerProductWrite = $developerProductWrite" in introspect,
          "scope results are returned for settings feedback")
    verdict = region(source, "function Apply-CloudIntrospectVerdict {", "# --- Tutorial: ANIMIERT")
    check("missingPermissions" in verdict and "game-pass:read" in verdict
          and "developer-product:write" in verdict and "universe.place:write" in verdict,
          "settings feedback warns about each missing scope only when dashboard opt-in is on")

    # One inventory is shared by docs, preflight, and the server-side handler.
    docs = region(source, "function Get-ToolDocs {", "function Get-BridgeAskUserProtocol {")
    helper = region(source, "function Invoke-CreatorDashboardTool {", "function Resolve-OpenCloudCreatorFromKey {")
    preflight = region(source, "function Test-CommandArguments(", "function Invoke-PluginTool(")
    tool_docs = region(docs, "$t.Add(@{ name = 'creator_dashboard'", "# ---------------- JOBS ----------------")
    helper_actions = quoted_array(helper, "actions")
    preflight_actions = quoted_array(preflight, "dashboardActions")
    check(len(helper_actions) == 12 and len(set(helper_actions)) == 12,
          "server handler accepts exactly twelve unique documented actions")
    check(set(helper_actions) == set(preflight_actions),
          "argument preflight and server handler have the same action allowlist")
    check(all(action in tool_docs for action in helper_actions),
          "the user-facing tool documentation lists every accepted action")
    form_builder = region(source, "function Get-CreatorDashboardFormFields {", "function Invoke-CreatorDashboardHttp {")
    check("isManagedPricingEnabled" not in tool_docs and "isManagedPricingEnabled" not in form_builder
          and "code = 'UNSUPPORTED_FIELD'" in helper,
          "fields absent from the official request schemas are neither advertised nor silently accepted")
    check("price muss eine nichtnegative int64-Ganzzahl sein." in form_builder
          and "Standardpreis als nichtnegative int64-Robux-Zahl" in tool_docs,
          "price validation and documentation match the official int64 request field")
    check("name = 'creator_dashboard'" in tool_docs and "category = 'cloud'" in tool_docs
          and "action = @{ type = 'string'; required = $true" in tool_docs,
          "creator_dashboard appears as a fully documented cloud tool with required action")
    for not_supported in ("kein Erstellen/Löschen/Veröffentlichen von Places oder Universes",
                          "Keine Creator-Hub-Cookies"):
        check(not_supported in tool_docs,
              f"documentation clearly restricts unsupported Creator Dashboard features: {not_supported}")

    # Settings gate, active Studio identity, target-id rejection, and read-only.
    gate = helper.index("if (-not $dashboardEnabled)")
    net = helper.index("return (Invoke-CreatorDashboardHttp")
    readonly = helper.index("if ($action -in $writeActions")
    active_session = helper.index("Get-SessionEntry ([string]$SessionId)")
    check(gate < active_session < net, "opt-in and active-session checks precede every outbound request")
    check("$dashboardEnabled = [bool]$Shared.BridgeSettings.creatorDashboardEnabled" in helper
          and "CREATOR_DASHBOARD_DISABLED" in helper
          and "Es wurde keine Anfrage an Roblox gesendet" in helper,
          "disabled-by-default gate fails closed before network I/O")
    check("$writeActions = @(" in helper and readonly < net
          and "[string]$accessMode -eq 'readonly'" in helper
          and "READONLY_TOKEN" in helper,
          "all mutating dashboard actions honor the active session's read-only lock")
    check("foreach ($targetField in @('universeId','placeId','gameId','targetPlace'))" in helper
          and "darf nicht angegeben werden" in helper,
          "caller-supplied target IDs are rejected")
    check("$entry.gameId" in helper and "$entry.placeId" in helper
          and "PUBLISHED_PLACE_REQUIRED" in helper,
          "only real Universe/Place IDs from the connected, published Studio session are used")
    check("OPENCLOUD_KEY_MISSING" in helper and "Get-OpenCloudConfig $Shared" in helper,
          "API-key absence returns a typed error and setup instructions")

    # Exact official endpoints, supported operations, and least-privilege scopes.
    expected_endpoints = (
        "/cloud/v2/universes/",
        "/game-passes/v1/universes/",
        "/developer-products/v2/universes/",
        "'/places/' + $placeId",
        "'/creator?pageSize='",
    )
    for endpoint in expected_endpoints:
        check(endpoint in helper, f"the implementation uses the documented endpoint fragment {endpoint}")
    for scope in ("universe:write", "universe.place:write", "game-pass:read",
                  "game-pass:write", "developer-product:read", "developer-product:write"):
        check(scope in helper, f"the request declares required scope {scope}")
    check("/game-passes/v1/universes/' + $universeId + '/game-passes'" in helper
          and "'/creator'" in helper,
          "gamepass listing/details use the documented v1 creator routes")
    check("/developer-products/v2/universes/' + $universeId + '/developer-products'" in helper,
          "developer products use the documented v2 routes")
    check("updateMask=" in helper and "$fields.Keys -join ','" in helper,
          "Universe and Place metadata updates send explicit update masks")
    check("foreach ($fieldName in @('displayName','description'))" in helper
          and "'universe_update'" in helper and "'place_update'" in helper,
          "metadata mutations are limited to documented displayName/description fields")
    check("game-pass:read" in source and "developer-product:write" in source,
          "the extra permissions are described in the settings tutorial and tool guide")
    check("cookie" in tool_docs.lower() and "kein Erstellen/Löschen/Veröffentlichen" in tool_docs,
          "the tool explicitly rejects Creator-Hub cookies and unpublished/unsupported management claims")
    check("return (Invoke-CreatorDashboardHttp" in helper
          and "-RequiredScopes $requiredScopes" in helper
          and "CREATOR_DASHBOARD_CONFLICT" in source
          and "OPENCLOUD_RATE_LIMITED" in source,
          "API scope, 409 and 429 responses stay typed and are not retried automatically")

    # Multipart icon handling is strict and compatible with both HTTP transports.
    image = region(source, "function Get-CreatorDashboardImage {", "function Get-CreatorDashboardFormFields {")
    multipart = region(source, "function New-OpenCloudMultipartBytes {", "function Send-OpenCloudRequestFallback {")
    sender = region(source, "function Send-OpenCloudHttp {", "function Get-OpenCloudTransportError {")
    check("FromBase64String" in image and "10485760" in image
          and "ICON_TOO_LARGE" in image,
          "icon bytes are decoded and capped at 10 MiB")
    check("image/png" in image and "image/jpeg" in image
          and "ICON_FORMAT_MISMATCH" in image and "UNSUPPORTED_ICON_FORMAT" in image,
          "icons must be actual PNG/JPEG bytes matching their filename")
    check("fileName.Length -gt 128" in image and "iconFileName" in image,
          "icon filename length/path/header injection is guarded")
    check("-FileFieldName 'imageFile'" in helper and "-FormFields $formFields" in helper,
          "gamepass/product icons and scalar fields are sent as the official multipart imageFile/form fields")
    check("[string]$FieldName" in multipart and "imageFile" in helper,
          "multipart file part uses the documented imageFile name")
    check("$IncludeRequestPart" in multipart and "name=\"request\"" in multipart
          and "if ($null -ne $FormFields)" in multipart,
          "asset uploads keep request+fileContent while creator forms need no extra request part")
    check("$hasFormFields = ($null -ne $FormFields)" in sender
          and "FormFields $FormFields" in sender,
          "multipart transport detects direct form fields without confusing file-only forms")
    creator_http = region(source, "function Invoke-CreatorDashboardHttp {", "function Invoke-CreatorDashboardTool {")
    check("-MaxResponseChars 2000000" in creator_http,
          "large product listings receive a bounded two-megabyte JSON response buffer")

    # Correct catalog/activity/dispatch integration.
    labels = region(source, "ActivityToolLabels = @{", "\n    }\n")
    activity = region(source, "function Get-ArenaActivityText", "function Get-ArenaActivityKind")
    sets = region(source, "function Get-ActivityToolSets {", "function Get-ArenaActivityText")
    server_dispatch = region(source, "function Invoke-ServerTool($sessionId", "function Test-PolygonBuildWithoutRequest(")
    check("creator_dashboard = 'Creator-Dashboard-Verwaltung'" in labels,
          "activity timeline has a readable Creator Dashboard label")
    check("creator_dashboard = 'Hat die angeforderte Creator-Dashboard-Aktion" in activity,
          "activity history reports a clear German operation summary")
    check("'creator_dashboard' {" in source and "Creator-Dashboard-Aktion:" in source,
          "activity detail adds the requested action and product id")
    check("'upload_asset','creator_dashboard','force_fail'" in sets,
          "creator_dashboard is classified as a server-side write-capable activity")
    check("'creator_dashboard'  { return (Invoke-OpenCloudServerTool" in server_dispatch,
          "the HTTP tool dispatcher routes creator_dashboard through the Open Cloud helper")
    check("creator_dashboard" in source[source.index("$writeTools = @("):source.index("$persistentEditTools = @(")],
          "creator_dashboard is protected by the write-tool dispatch path")
    check("# Arena Roblox Bridge  -  Version 7.5.9" in source
          and "DocsVersion     = '7.5.9'" in source
          and "RuntimeInfo.Version = '7.5.9'" in source,
          "runtime, docs and plugin version metadata are synchronized to 7.5.9")

    if FAILURES:
        print(f"\n{len(FAILURES)} Creator Dashboard regression check(s) failed.")
        return 1
    print("\nOK: 7.5.9 Creator Dashboard opt-in, security gates, Open Cloud routes/scopes, multipart icons, docs and activity checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
