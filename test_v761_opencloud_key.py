#!/usr/bin/env python3
"""Offline regression checks for Arena Roblox Bridge 7.6.1 Open Cloud key UX."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "ArenaBridge.ps1"
VERSION = "7.6.1"
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
    metadata = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    latest = str(metadata.get("notes", [""])[0])
    check(metadata.get("version") == VERSION, "version.json is 7.6.1")
    check(latest.startswith("• 7.6.1") and "OPENCLOUD_KEY_HAS_EXPIRATION" in latest
          and "Ladekreis" in latest,
          "release note documents spinner, expiration refuse and the tool gate")

    gate = region(source, "function Assert-OpenCloudToolAccess {", "function Get-OpenCloudAssetSpec {")
    check("OPENCLOUD_KEY_MISSING" in gate and "OPENCLOUD_KEY_HAS_EXPIRATION" in gate
          and "OPENCLOUD_SCOPE_INCOMPLETE" in gate,
          "the shared gate has the three fail-closed codes")
    check("Test-OpenCloudKeyHasExpiration" in gate and "Get-OpenCloudFamilyCoverage" in gate,
          "expiration and read+write coverage are checked before any Open Cloud call")
    check("userMessage" in gate and "WORTLICH" in gate,
          "every gate failure tells Arena exactly what to say to the user")

    upload = region(source, "function Invoke-OpenCloudUpload {", "function Get-OpenCloudOperation {")
    check("Assert-OpenCloudToolAccess -Shared $Shared -Family 'asset'" in upload,
          "upload_asset goes through the asset read+write gate")
    dashboard = region(source, "function Invoke-CreatorDashboardTool {", "function Invoke-DatastoreHttp {")
    check("Assert-OpenCloudToolAccess -Shared $Shared -Family $family" in dashboard,
          "creator_dashboard goes through the per-action scope gate")
    datastore = region(source, "function Invoke-DatastoreTool {", "function Get-DatastoreValueBody {")
    check("Assert-OpenCloudToolAccess -Shared $Shared -Family 'universe-datastores'" in datastore,
          "datastore goes through the universe-datastores read+write gate")

    catalog = region(source, "function Get-CloudPermissionCatalog {", "function New-CloudPermissionRow {")
    for scope in ("creator-store-product", "universe.user-restriction", "universe.thumbnail",
                  "universe.places", "universe.event", "universe.analytics", "thumbnails",
                  "universe.ordered-data-store.scope.entry", "universe-places", "localization-table"):
        check(f"title = '{scope}'" in catalog, f"tutorial names the scope {scope} as the bullet title")
    for gone in ("memory-store", "universe-messaging-service", "user.user-notification"):
        check(gone not in catalog, f"{gone} is not in the tutorial catalog")
    check("Pflicht" not in catalog, "tutorial catalog does not say Pflicht")

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
        print(f"\n{len(FAILURES)} 7.6.1 regression check(s) failed.")
        return 1
    print("\nOK: 7.6.1 Open Cloud key tutorial, spinner window, expiration refuse and tool gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
