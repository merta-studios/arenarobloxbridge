#!/usr/bin/env python3
"""Offline regression checks for the 7.6.0 Creator Dashboard / Open Cloud key tool.

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

ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = ROOT / "app"
PS1 = APP_ROOT / "ArenaBridge.ps1"
VERSION = "7.8.0"
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
    metadata = json.loads((APP_ROOT / "version.json").read_text(encoding="utf-8"))
    latest = str(metadata.get("notes", [""])[0])
    check(metadata.get("version") == VERSION, "version.json is 7.8.0")
    check(latest.startswith("• 7.8.0") and "PROJEKT ZUERST" in latest,
          "current release note documents the project-first update")
    check(any(str(note).startswith("• 7.6.2") and "open_cloud" in str(note)
              for note in metadata.get("notes", [])),
          "historical Open Cloud release note remains available")
    check(any(str(note).startswith("• 7.6.0") and "SCHALTER ENTFERNT" in str(note)
              for note in metadata.get("notes", [])),
          "historical 7.6.0 note still documents the removed switch")
    check(any("7.5.9" in str(note) and "creator_dashboard" in str(note)
              for note in metadata.get("notes", [])[1:]),
          "the prior 7.5.9 Creator Dashboard release note remains historical")

    # 7.6.0: the local opt-in is GONE - the key's scopes are the only gate.
    settings = region(source, "function Get-BridgeSettingsFile {", "function Save-BridgeSettingsFile {")
    save = region(source, "function Save-BridgeSettingsFile {", "function Write-RuntimeLog {")
    check("creatorDashboardEnabled" not in settings,
          "a fresh or legacy settings file no longer carries the management switch")
    check("creatorDashboardEnabled" not in save,
          "settings.json no longer persists the removed opt-in")
    check("creatorDashboardEnabled" not in source,
          "creatorDashboardEnabled is removed from the whole script")
    settings_xaml = region(source, "$settingsXaml = @'", "\n'@")
    cloud_card = region(settings_xaml, 'TextBlock Text="ROBLOX OPEN CLOUD API-KEY"', '<Border Height="1" Background="{StaticResource SwLine}" Margin="0,18,0,12"/>')
    tutorial_xaml = region(settings_xaml, 'x:Name="CloudTutorialWrap"', '<Border Height="1" Background="{StaticResource SwLine}" Margin="0,18,0,12"/>')
    check('x:Name="CreatorDashboardSwitch"' not in cloud_card
          and "Arena darf den aktuellen Place im Creator Dashboard verwalten" not in cloud_card,
          "the opt-in switch is removed from the Open Cloud API-key settings card")
    check("kein Ablaufdatum" in cloud_card and "Grün = vorhanden, rot = fehlt" in cloud_card,
          "settings UI explains the immediate permission window and that expiration is refused")

    # Tutorial: seven steps plus the full permission catalog in step four.
    check('for ($stepIndex = 1; $stepIndex -le 7;' in source,
          "the animated key tutorial enumerates all seven steps")
    tutorial_steps = [int(value) for value in re.findall(r'x:Name="CloudStep(\d+)"', tutorial_xaml)]
    check(tutorial_steps == list(range(1, 8)), "all seven XAML tutorial cards are present in order")
    check('x:Name="CloudPermissionList"' in tutorial_xaml,
          "tutorial step four hosts the generated permission catalog list")
    catalog = region(source, "function Get-CloudPermissionCatalog {", "function New-CloudPermissionRow {")
    permissions = json.loads((APP_ROOT / "opencloud/permissions.json").read_text(encoding="utf-8"))
    check("(Get-OpenCloudCatalog).permissions.PSObject.Properties" in catalog,
          "permission UI uses the shared exact-permission catalog")
    check(len(permissions) == 41 and "asset:read" in permissions and "asset:write" in permissions,
          "all 41 individual permissions are documented, read/write separately")
    for gone in ("memory-store", "universe-messaging-service", "universe.place.instance",
                 "user.user-notification"):
        check(gone not in catalog, f"unused scope {gone} is gone from the tutorial catalog")
    check("core = $true" not in catalog and "Pflicht" not in catalog,
          "the catalog has no required/core ranking")
    check("creatorDashboardRules" in source and "universe.place:write" in source
          and "developer-product:read" in source and "game-pass:write" in source,
          "agent-facing Creator Dashboard guide documents the exact required scopes")

    # Official API scope introspection and user-facing diagnosis.
    introspect = region(source, "function Invoke-OpenCloudIntrospect {", "function Get-OpenCloudArgumentValue {")
    for marker in ("$universeWrite = $false", "$universePlaceWrite = $false",
                   "$gamePassRead = $false", "$gamePassWrite = $false",
                   "$developerProductRead = $false", "$developerProductWrite = $false",
                   "scopeBase -eq 'universe'", "scopeBase -eq 'universe.place'",
                   "'game-pass','game-passes'", "'developer-product','developer-products'",
                   "$datastoreObjectsRead = $false", "$datastoreObjectsCreate = $false",
                   "$datastoreObjectsUpdate = $false", "$datastoreObjectsDelete = $false",
                   "$datastoreControlList = $false", "$datastoreVersionsList = $false",
                   "$orderedDatastoreRead = $false", "$memoryStoreAny = $false",
                   "$messagingPublish = $false", "$placePublishWrite = $false",
                   "$placeInstanceRead = $false", "$localizationRead = $false",
                   "$userNotificationWrite = $false",
                   "scopeBase -eq 'universe-datastores.control'",
                   "scopeBase -eq 'universe-datastores.objects'",
                   "scopeBase -eq 'universe-datastores.versions'",
                   "scopeBase -eq 'universe.ordered-data-store.scope.entry'",
                   "scopeBase -like 'memory-store*'",
                   "scopeBase -eq 'universe-messaging-service'",
                   "scopeBase -eq 'universe.place.instance'",
                   "scopeBase -like 'localization*'",
                   "scopeBase -eq 'user.user-notification'"):
        check(marker in introspect, f"Open Cloud introspection recognizes {marker}")
    check("universeWrite = $universeWrite" in introspect
          and "developerProductWrite = $developerProductWrite" in introspect
          and "datastoreObjectsUpdate = $datastoreObjectsUpdate" in introspect
          and "placePublishWrite = $placePublishWrite" in introspect,
          "scope results are returned for the permission window and settings feedback")
    check("universeDatastores = $(try { @($scope.universeDatastores)" in introspect,
          "introspection keeps the universe-datastore resource bindings of each scope")
    verdict = region(source, "function Apply-CloudIntrospectVerdict {", "function Save-OpenCloudKeyFromText {")
    check("Test-OpenCloudKeyHasExpiration" in verdict
          and "weigert sich komplett" in verdict,
          "settings feedback refuses keys with an expiration date instead of ranking core rights")

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

    # No local gate any more; active Studio identity, target-id rejection and
    # read-only stay, and a missing key still fails closed before network I/O.
    net = helper.index("return (Invoke-CreatorDashboardHttp")
    readonly = helper.index("if ($action -in $writeActions")
    active_session = helper.index("Get-SessionEntry ([string]$SessionId)")
    check("CREATOR_DASHBOARD_DISABLED" not in helper
          and "dashboardEnabled" not in helper,
          "the local opt-in gate is removed - only the key's scopes decide")
    check(readonly < active_session < net,
          "read-only and active-session checks precede every outbound request")
    check("$writeActions = @(" in helper and readonly < net
          and "[string]$accessMode -ne 'readwrite'" in helper
          and "READONLY_TOKEN" in helper,
          "all mutating dashboard actions honor the active session's read-only lock")
    check("foreach ($targetField in @('universeId','placeId','gameId','targetPlace'))" in helper
          and "darf nicht angegeben werden" in helper,
          "caller-supplied target IDs are rejected")
    check("$entry.gameId" in helper and "$entry.placeId" in helper
          and "PUBLISHED_PLACE_REQUIRED" in helper,
          "only real Universe/Place IDs from the connected, published Studio session are used")
    check("Assert-OpenCloudToolAccess" in helper and "Get-OpenCloudConfig $Shared" in helper,
          "API-key absence and expiration/scope checks run before any dashboard request")

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
    server_dispatch = region(source, "function Invoke-ServerTool($sessionId", "function Get-OrganicBuildGuardResult(")
    check("creator_dashboard = 'Creator-Dashboard-Verwaltung'" in labels,
          "activity timeline has a readable Creator Dashboard label")
    check("creator_dashboard = 'Hat die angeforderte Creator-Dashboard-Aktion" in activity,
          "activity history reports a clear German operation summary")
    check("'creator_dashboard' {" in source and "Creator-Dashboard-Aktion:" in source,
          "activity detail adds the requested action and product id")
    activity_read_tools = sets[sets.index("$read = @("):sets.index("$write = @(")]
    activity_write_tools = sets[sets.index("$write = @("):]
    check("'creator_dashboard','datastore','force_fail'" in activity_write_tools
          and "'creator_dashboard'" not in activity_read_tools
          and "'datastore'" not in activity_read_tools,
          "creator_dashboard and datastore are classified as server-side write-capable activities")
    check("'creator_dashboard'  { return (Invoke-OpenCloudServerTool" in server_dispatch,
          "the HTTP tool dispatcher routes creator_dashboard through the Open Cloud helper")
    check("creator_dashboard" in source[source.index("$writeTools = @("):source.index("$persistentEditTools = @(")],
          "creator_dashboard is protected by the write-tool dispatch path")
    check("# Arena Roblox Bridge  -  Version 7.8.0" in source
          and "DocsVersion     = '7.8.0'" in source
          and "RuntimeInfo.Version = '7.8.0'" in source,
          "runtime, docs and plugin version metadata are synchronized to 7.8.0")

    if FAILURES:
        print(f"\n{len(FAILURES)} Creator Dashboard regression check(s) failed.")
        return 1
    print("\nOK: 7.6.0 key-scope-only gating, removed opt-in, permission catalog, Introspect save flow, Open Cloud routes/scopes, multipart icons, docs and activity checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
