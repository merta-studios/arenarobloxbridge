#!/usr/bin/env python3
"""Offline regression checks for the current Bridge plus the 7.6.2 Open Cloud key UX."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = ROOT / "app"
PS1 = APP_ROOT / "ArenaBridge.ps1"
VERSION = "7.7.0"
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("[OK]   " if condition else "[FAIL] ") + message)
    if not condition:
        FAILURES.append(message)


def region(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    stop = source.index(end, begin)
    return source[begin:stop]


def main() -> int:
    raw = PS1.read_bytes()
    check(raw.startswith(b"\xef\xbb\xbf"), "ArenaBridge.ps1 retains the required UTF-8 BOM")
    check(b"\r\n" not in raw, "ArenaBridge.ps1 retains LF-only line endings")
    source = raw.decode("utf-8-sig")
    metadata = json.loads((APP_ROOT / "version.json").read_text(encoding="utf-8"))
    notes = [str(note) for note in metadata.get("notes", [])]
    latest = notes[0] if notes else ""
    check(metadata.get("version") == VERSION, "version.json is 7.7.0")
    check(latest.startswith("• 7.7.0") and "PROJEKT ZUERST" in latest,
          "latest release note identifies the current project-first update")
    check(any(note.startswith("• 7.6.2") and "600 Zeichen" in note for note in notes),
          "the exact 7.6.2 Open Cloud key validation release note remains in history")

    gate = region(source, "function Assert-OpenCloudToolAccess {", "function Get-OpenCloudAssetSpec {")
    check("OPENCLOUD_KEY_MISSING" in gate and "OPENCLOUD_KEY_HAS_EXPIRATION" in gate
          and "OPENCLOUD_SCOPE_INCOMPLETE" in gate,
          "the shared gate has the three fail-closed codes")
    check("Test-OpenCloudKeyHasExpiration" in gate and "Test-OpenCloudPermission" in gate,
          "expiration and exact per-operation scopes are checked before Open Cloud calls")
    check("userMessage" in gate and "WORTLICH" in gate,
          "every gate failure tells Arena exactly what to say to the user")

    upload = region(source, "function Invoke-OpenCloudUpload {", "function Get-OpenCloudOperation {")
    check("Assert-OpenCloudToolAccess -Shared $Shared -RequiredScopes @('asset:read','asset:write')" in upload,
          "upload_asset goes through the asset-specific gate")
    dashboard = region(source, "function Invoke-CreatorDashboardTool {", "function Invoke-DatastoreHttp {")
    check("Assert-OpenCloudToolAccess -Shared $Shared -What" in dashboard,
          "creator_dashboard goes through the per-action scope gate")
    datastore = region(source, "function Invoke-DatastoreTool {", "function Get-DatastoreValueBody {")
    check("Assert-OpenCloudToolAccess -Shared $Shared -What 'datastore'" in datastore,
          "datastore goes through the key validity gate; exact scopes checked by HTTP helper")

    catalog = region(source, "function Get-CloudPermissionCatalog {", "function New-CloudPermissionRow {")
    check("(Get-OpenCloudCatalog).permissions.PSObject.Properties" in catalog,
          "tutorial displays the complete shared per-permission catalog")
    permissions = json.loads((APP_ROOT / "opencloud/permissions.json").read_text(encoding="utf-8"))
    check(len(permissions) == 41 and "asset:read" in permissions and "asset:write" in permissions,
          "read and write appear as separate permissions")
    check("thumbnail:read" not in permissions and "universe.user-restriction:write" not in permissions,
          "explicitly forbidden permissions are not advertised")
    row = region(source, "function New-CloudPermissionRow {",
                 "# Tutorial-Schritt 4: die komplette Berechtigungs-Uebersicht fuellen.")
    check("Scope: " not in row, "permission rows do not repeat the scope under the title")

    window = region(source, "function Show-CloudPermissionsWindow {",
                    "# --- Tutorial: ANIMIERT auf- und zuklappen")
    check('x:Name="PermSpinnerRotation"' in window and "Show-PermLoading" in window,
          "the permission window shows a spinner first")
    check("Show-CloudPermissionsWindow -PendingKey $keyText" in source
          and "Start-CloudIntrospectRun { param($verdict) Show-CloudPermissionsWindow" not in source,
          "save opens the window immediately instead of waiting for Introspect")
    check("fehlenden Kern-Rechten" in source or "Kern-Rechte-Warnung" in window,
          "the old core-rights warning is only mentioned as removed")
    check("Roblox nimmt den Key an – aber es fehlen Kern-Rechte." not in window,
          "the user-facing core-rights warning text is gone")

    save_click = region(source, "$cloudSaveButton.Add_Click({",
                        "# --- Berechtigungen des gespeicherten Schluessels ansehen")
    check("Show-CloudPermissionsWindow -PendingKey $keyText" in save_click
          and "Set-OpenCloudKey" not in save_click,
          "save still does not persist the key until the yes-button")

    if FAILURES:
        print(f"\n{len(FAILURES)} 7.6.2 regression check(s) failed.")
        return 1
    print("\nOK: 7.6.2 Open Cloud key tutorial, spinner window, expiration refuse and tool gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
