#!/usr/bin/env python3
"""Offline regression checks for Arena Roblox Bridge 7.6.0.

Covers the two owner-requested areas without Windows/Roblox:

1. USER MESSAGES CANNOT BE IGNORED ANY MORE: the message text sits at the top
   AND the bottom of every envelope, unacknowledged messages repeat up to ten
   times, every envelope carries an open-message counter, and report_done is
   blocked with UNACKED_USER_MESSAGE until every message is acknowledged.
2. THE OPEN CLOUD KEY IS THE PERMISSION SYSTEM: the local creator-dashboard
   switch is gone, the save flow verifies the key via the official Introspect
   endpoint BEFORE storing it and shows a dedicated permission window with
   clear "Oh, das ändere ich nochmal!" / "Ja, alles richtig! Key speichern!"
   decisions, the tutorial lists the full permission catalog, and the new
   datastore tool exposes the stable /cloud/v2 data-store APIs for the
   connected session only.

The test is deliberately network-free; it verifies the exact integration,
gates, action inventories and scope mapping from the PowerShell source. A
Windows/Roblox Studio live acceptance run is still required.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "ArenaBridge.ps1"
VERSION = "7.6.0"
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
    check(metadata.get("version") == VERSION, "version.json is 7.6.0")
    check(latest.startswith("• 7.6.0") and "UNACKED_USER_MESSAGE" in latest
          and "introspect" in latest.lower() and "datastore" in latest,
          "release note documents the message gate, the Introspect save flow and the datastore tool")

    # ------------------------------------------------------------------
    # 1) User messages: repeat ten times, banner top and bottom, gate.
    # ------------------------------------------------------------------
    delivery = region(source, "function Get-PendingUserMessageViews {",
                      "function Get-PendingUserMessageViewsForDelivery {")
    check("$attempts -lt 10" in delivery,
          "an unacknowledged message repeats in up to ten responses (was three)")
    check("$repeatWait = 20 + (20 * $attempts)" in delivery and "$repeatWait -gt 120" in delivery,
          "repetition pauses grow from 20s up to a 120s cap instead of spamming")

    unacked = region(source, "function Get-UnackedUserMessageViews {",
                     "function Mark-UserMessagesDelivered {")
    check("'acked' -or $messageState -eq 'withdrawn'" in unacked,
          "the unacked view skips acknowledged and withdrawn messages only")
    check("$Shared.UserMessages.Keys" in unacked,
          "the unacked view scans every session (reconnects cannot hide a message)")

    envelope = region(source, "$pendingUserMessages = Get-PendingUserMessageViewsForDelivery",
                      "$late = Take-LateResults $sessionId")
    check("!!! USER MESSAGE - STOP AND READ THIS FIRST !!!" in envelope,
          "the attention banner is loud and sits at the TOP of every envelope")
    check("userMessageReminder" in envelope,
          "the exact message text is repeated at the BOTTOM of the envelope")
    check("openUserMessageCount" in envelope and "Get-UnackedUserMessageViews" in envelope,
          "every envelope carries the count of still-unacknowledged user messages")
    check("TEN responses" in envelope and "UNACKED_USER_MESSAGE" in envelope,
          "the user-message contract explains the ten repeats and the report_done gate")

    done_gate = region(source, "'report_done' {\n                # Version 7.6.0: USER-MESSAGE-GATE.",
                       "# Version 7.0.0: report_done setzt fehlende 100 selbst")
    check("Get-UnackedUserMessageViews" in done_gate and "UNACKED_USER_MESSAGE" in done_gate,
          "report_done checks open user messages BEFORE any other gate")
    check("MESH_UPLOAD_PENDING" not in done_gate,
          "the message gate really precedes the mesh/quality gates (separate block)")
    check("ack_user_message" in done_gate,
          "the gate tells the agent exactly how to unlock (ack_user_message)")
    done_docs = region(source, "$t.Add(@{ name = 'report_done'", "$t.Add(@{ name = 'set_context'")
    check("UNACKED_USER_MESSAGE" in done_docs,
          "report_done documentation lists the new error code")
    check("USER CHANNEL (7.2.0, HARDENED 7.6.0)" in source,
          "the session rules describe the hardened user channel")

    # ------------------------------------------------------------------
    # 2) The switch is gone - the key is the permission system.
    # ------------------------------------------------------------------
    check("creatorDashboardEnabled" not in source,
          "the removed setting creatorDashboardEnabled appears nowhere in the script")
    check("CreatorDashboardSwitch" not in source,
          "the removed XAML switch appears nowhere in the script")
    check("CREATOR_DASHBOARD_DISABLED" not in source,
          "the local fail-closed gate code is gone (Roblox 403 is the only gate)")
    check("OPEN-CLOUD-FULL-POWER (7.6.0)" in source,
          "the session rules explain that the key's scopes are the only permission system")

    # ------------------------------------------------------------------
    # 3) Save flow: Introspect first, permission window, then save.
    # ------------------------------------------------------------------
    save_click = region(source, "$cloudSaveButton.Add_Click({",
                        "# --- Berechtigungen des gespeicherten Schluessels ansehen")
    check("Set-OpenCloudKey" not in save_click and "Save-BridgeSettingsFile" not in save_click,
          "the save button stores nothing by itself")
    check("Start-CloudIntrospectRun" in save_click and "-Key $keyText" in save_click,
          "the save button verifies the typed key via Introspect in the background")
    check("Show-CloudPermissionsWindow" in save_click,
          "the verification result opens the dedicated permission window")

    introspect_run = region(source, "function Start-CloudIntrospectRun {",
                            "function Apply-CloudIntrospectVerdict {")
    check("[string]$Key = ''" in introspect_run and "AddArgument([string]$Key)" in introspect_run,
          "the background run can verify a not-yet-saved key")
    check("Invoke-OpenCloudIntrospect -Shared $SharedObject -Key ([string]$PendingKey)" in introspect_run,
          "the verification calls the official Introspect function with the pending key")

    window = region(source, "function Show-CloudPermissionsWindow {",
                    "# --- Tutorial: ANIMIERT auf- und zuklappen")
    check("Oh, das ändere ich nochmal!" in window,
          "the window offers the 'Oh, das ändere ich nochmal!' decision")
    check("Ja, alles richtig! Key speichern!" in window,
          "the window offers the 'Ja, alles richtig! Key speichern!' decision")
    check("Save-OpenCloudKeyFromText" in window,
          "only the yes-button persists the key (Save-OpenCloudKeyFromText)")
    check("nichts wurde gespeichert" in window and "PermRetryButton" in window,
          "a failed verification honestly reports that nothing was saved and offers a retry")
    check("api-keys/v1/introspect" in window,
          "the window names the official Introspect endpoint as its source")
    saver = region(source, "function Save-OpenCloudKeyFromText {",
                   "function Show-CloudPermissionsWindow {")
    check("Set-OpenCloudKey" in saver and "Save-BridgeSettingsFile" in saver
          and "Sync-CloudSharedSettings" in saver,
          "the real save path encrypts the key, persists metadata and syncs $Shared")

    # The permission window XAML is a real Window here-string using the shared
    # dialog resources (already XML-validated by test_v398_structure.py).
    check('<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"' in window
          and "<!--ARENA_DIALOG_STYLES-->" in window
          and 'x:Name="PermList"' in window,
          "the permission window is a styled WPF dialog with a generated permission list")

    # ------------------------------------------------------------------
    # 4) The permission catalog covers the official Open Cloud systems.
    # ------------------------------------------------------------------
    catalog = region(source, "function Get-CloudPermissionCatalog {",
                     "function New-CloudPermissionRow {")
    expected_scopes = ("asset", "universe", "universe.place", "game-pass", "developer-product",
                       "universe-datastores.control / .objects / .versions",
                       "universe.ordered-data-store.scope.entry", "memory-store",
                       "universe-messaging-service", "universe.place.instance",
                       "universe-places", "localization-table", "user.user-notification")
    for scope in expected_scopes:
        check(scope in catalog, f"the permission catalog documents the scope {scope}")
    check(catalog.count("core = $true") == 6,
          "exactly the six permissions Arena actively uses are marked core")
    check("Von Arena noch nicht genutzt" in catalog,
          "permissions Arena does not use yet are honestly marked")
    row = region(source, "function New-CloudPermissionRow {",
                 "# Tutorial-Schritt 4: die komplette Berechtigungs-Uebersicht fuellen.")
    check("0x2714" in row and "0x2716" in row,
          "granted/missing permissions render as green check / red cross glyphs")
    tutorial_xaml = region(source, "$settingsXaml = @'", "\n'@")
    check('x:Name="CloudPermissionList"' in tutorial_xaml,
          "tutorial step four hosts the generated catalog")
    check('for ($stepIndex = 1; $stepIndex -le 7;' in source,
          "the tutorial animation walks the seven remaining steps")

    # ------------------------------------------------------------------
    # 5) Introspect parses the full modern scope catalog.
    # ------------------------------------------------------------------
    introspect = region(source, "function Invoke-OpenCloudIntrospect {",
                        "function Get-OpenCloudArgumentValue {")
    for marker in ("$universeRead = $false", "$placePublishWrite = $false",
                   "$placeInstanceRead = $false", "$datastoreControlList = $false",
                   "$datastoreObjectsList = $false", "$datastoreObjectsRead = $false",
                   "$datastoreObjectsCreate = $false", "$datastoreObjectsUpdate = $false",
                   "$datastoreObjectsDelete = $false", "$datastoreVersionsList = $false",
                   "$orderedDatastoreRead = $false", "$orderedDatastoreWrite = $false",
                   "$memoryStoreAny = $false", "$messagingPublish = $false",
                   "$localizationRead = $false", "$localizationWrite = $false",
                   "$userNotificationWrite = $false"):
        check(marker in introspect, f"Introspect detects {marker.split('=')[0].strip()}")
    check("scopeBase -eq 'universe-datastores.objects'" in introspect
          and "scopeBase -eq 'universe-datastores.control'" in introspect
          and "scopeBase -eq 'universe-datastores.versions'" in introspect,
          "the stable v2 data-store scopes are recognized")
    check("scopeBase -in @('universe-places','universe.places')" in introspect,
          "the place-publishing scope is recognized")
    check("universeDatastores = $(try { @($scope.universeDatastores)" in introspect,
          "data-store resource bindings (universeId/datastoreName) are kept per scope")

    # ------------------------------------------------------------------
    # 6) The new datastore tool.
    # ------------------------------------------------------------------
    helper = region(source, "function Invoke-DatastoreTool {", "function Get-DatastoreValueBody {")
    http = region(source, "function Invoke-DatastoreHttp {", "function Invoke-DatastoreTool {")
    helper_actions = quoted_array(helper, "actions")
    expected_actions = ["list_datastores", "list_entries", "get_entry", "create_entry",
                        "update_entry", "increment_entry", "delete_entry", "list_versions"]
    check(helper_actions == expected_actions,
          f"the datastore tool accepts exactly the eight documented actions: {helper_actions}")
    preflight = region(source, "'datastore' {\n                $actionArg = Get-CommandArgumentValue",
                       "'ground_height' {")
    check(set(quoted_array(preflight, "datastoreActions")) == set(expected_actions),
          "argument preflight and server handler share the same datastore action allowlist")
    check("/cloud/v2/universes/' + $universeId" in helper
          and "'/data-stores" in helper and "':increment'" in helper
          and "':listRevisions?'" in helper,
          "the tool uses the documented stable /cloud/v2 data-store endpoints")
    check("$scopeName = 'global'" in helper,
          "the default data-store scope matches the engine default (global)")
    check("[Uri]::EscapeDataString($datastoreName)" in helper
          and "[Uri]::EscapeDataString($entryKey)" in helper,
          "store names, scopes and entry keys are URL-escaped path segments")
    check("$entryKey.Length -gt 50" in helper,
          "entry keys respect the documented 50-character limit")
    check("READONLY_TOKEN" in helper and "[string]$accessMode -eq 'readonly'" in helper,
          "mutating data-store actions honor the session read-only lock")
    check("foreach ($targetField in @('universeId','placeId','gameId','targetPlace'))" in helper,
          "caller-supplied target IDs are rejected (connected session only)")
    check("PUBLISHED_PLACE_REQUIRED" in helper and "OPENCLOUD_KEY_MISSING" in helper,
          "missing publish IDs or a missing key fail closed with typed errors")
    check("'universe-datastores.objects:create'" in helper
          and "'universe-datastores.objects:update'" in helper
          and "'universe-datastores.objects:delete'" in helper
          and "'universe-datastores.control:list'" in helper
          and "'universe-datastores.versions:list'" in helper,
          "every action declares its exact required scope for honest 403 diagnosis")
    check("OPENCLOUD_SCOPE_MISSING" in http and "DATASTORE_NOT_FOUND" in http,
          "missing scopes and unknown stores/entries produce typed, honest errors")
    value_body = region(source, "function Get-DatastoreValueBody {",
                        "function Resolve-OpenCloudCreatorFromKey {")
    check("valueJson" in value_body and "ConvertFrom-Json" in value_body,
          "values are accepted as JSON objects or raw JSON text and validated")

    docs = region(source, "$t.Add(@{ name = 'datastore'", "# ---------------- JOBS ----------------")
    check("category = 'cloud'" in docs and "universe-datastores.objects" in docs,
          "the datastore tool is fully documented in the cloud category")
    check("Anlegen und Ändern" in docs,
          "the documentation explains the create/update split of the Open Cloud API")

    dispatch = region(source, "function Invoke-OpenCloudServerTool($sessionId",
                      "$operationId = ''")
    check("if ($tool -eq 'datastore')" in dispatch and "Invoke-DatastoreTool" in dispatch,
          "the Open Cloud server helper routes the datastore tool")
    server_dispatch = region(source, "'upload_asset'       { return (Invoke-OpenCloudServerTool",
                             "'get_docs' {")
    check("'datastore'          { return (Invoke-OpenCloudServerTool" in server_dispatch,
          "the HTTP tool dispatcher routes datastore through the Open Cloud helper")
    check("'datastore'" in source[source.index("$writeTools = @("):source.index("$persistentEditTools = @(")],
          "datastore is protected by the write-tool dispatch path")
    sets = region(source, "function Get-ActivityToolSets {", "function Get-ArenaActivityText")
    check("'creator_dashboard','datastore','force_fail'" in sets,
          "the activity system classifies datastore as a write-capable tool")
    labels = region(source, "ActivityToolLabels = @{", "\n    }\n")
    check("datastore = 'DataStore über Open Cloud verwalten'" in labels,
          "the activity timeline has a readable datastore label")
    activity = region(source, "function Get-ArenaActivityText", "function Get-ArenaActivityKind")
    check("datastore = 'Hat den DataStore des verbundenen Spiels" in activity,
          "the activity history reports a clear German datastore summary")

    if FAILURES:
        print(f"\n{len(FAILURES)} 7.6.0 regression check(s) failed.")
        return 1
    print("\nOK: 7.6.0 user-message hardening, Introspect-first save flow, permission "
          "catalog/window and the datastore tool checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
