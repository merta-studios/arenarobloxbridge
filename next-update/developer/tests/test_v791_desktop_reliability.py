#!/usr/bin/env python3
"""Offline regression gate for the 7.9.1 desktop/progress/notification changes.

This checks source structure and contracts only. It cannot execute Windows PowerShell,
WPF, Explorer, or Windows notification behavior; those still require a Windows test.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app" / "ArenaBridge.ps1"
VERSION = ROOT / "app" / "version.json"
LATEST = ROOT / "release" / "latest.json"
SOURCE = APP.read_text(encoding="utf-8-sig")
FAILURES: list[str] = []


def check(condition: bool, label: str) -> None:
    print(("[OK]   " if condition else "[FAIL] ") + label)
    if not condition:
        FAILURES.append(label)


def region(start: str, end: str) -> str:
    a = SOURCE.find(start)
    b = SOURCE.find(end, a + len(start)) if a >= 0 else -1
    if a < 0 or b < 0:
        return ""
    return SOURCE[a:b]


def main() -> int:
    print("7.9.1 offline regression checks")
    version = json.loads(VERSION.read_text(encoding="utf-8"))
    latest = json.loads(LATEST.read_text(encoding="utf-8"))
    check(version.get("version") == "7.9.1", "app/version.json prepares version 7.9.1")
    check(str(version.get("notes", [""])[0]).startswith("• 7.9.1 "), "7.9.1 is the leading release note")
    check(latest.get("version") == "7.9.0", "published release manifest remains untouched until Windows approval")

    background = region("function Set-BackgroundShellBrush {", "# Version 7.7.1: Das Programmlogo")
    check("DrawingGroup" in background and "ImageDrawing" in background,
          "secondary-window background composites the supplied artwork")
    check("FromArgb(112, 0, 0, 0)" in background and "DrawingBrush" in background
          and "BitmapScalingMode]::HighQuality" in background,
          "secondary artwork has a dark glass layer and keeps high-quality scaling")
    check("Set-BackgroundArtwork" not in background and "Set-BackgroundArtwork -ImageControl" in SOURCE,
          "the main Place-list artwork path stays separate and undimmed")

    progress = region("function Update-ArenaProgressState {", "# Version 7.0.0: UEBERGABE (HANDOFF)")
    modes = region("function Get-ProgressMode($node)", "function Get-ShortSid")
    snapshot = region("function Get-ProgressStateSnapshot {", "function Get-ArenaActivityDisplayLabel")
    place_row = region("function Update-PlaceProgressVisual", "function Get-ProgressDiagnoseLines")
    history = region("function Update-ArenaHistoryProgressCard {", "function Update-ArenaHistoryProgress {")
    check("Monitor]::Enter($Shared.ProgressStateLock)" in progress
          and "Monitor]::Exit($Shared.ProgressStateLock)" in progress,
          "progress read-modify-write is protected by one shared lock")
    check("$Shared.ProgressRevision" in progress and "Revision =" in SOURCE and "$bestRevision" in snapshot,
          "global revisions disambiguate fast parallel/reconnect snapshots")
    check("'off'" in modes and "'disabled'" in modes and "'not_applicable'" in modes
          and "if ($node -is [bool] -and -not $node)" in modes,
          "progress can be explicitly disabled with false/off/hidden/not_applicable")
    check("reason = 'no_percent_reported'" in progress and "Set-ProgressField $state 'mode' 'hidden'" in progress,
          "completion without a genuine percentage becomes not applicable, not synthetic 100%")
    check("$showNumericProgress = ($percentKnown -and $progressMode -ne 'hidden')" in place_row
          and "$Row.ProgressBar.Visibility = 'Collapsed'" in place_row,
          "Place row paints a numeric bar only for an explicitly reported percentage")
    check("$showNumericProgress = ($percentKnown -and $progressMode -ne 'hidden')" in history
          and "if ($state -eq 'done' -and -not $percentKnown)" not in history,
          "history card does not turn a no-progress completion into 100%")
    check("Progress is optional" in SOURCE and "progress=false" in SOURCE,
          "Arena instructions allow chat/read-only work to omit progress entirely")

    notify_ui = region("function Show-ArenaDoneDesktopPopup {", "function Show-ArenaDoneNotification {")
    notify = region("function Show-ArenaDoneNotification {", "function Get-NotifyDiagnoseLines {")
    sweep = region("function Invoke-NotifySweep {", "function Clear-NotifyQueue {")
    timer = region("$script:NotifyTimer = [System.Windows.Threading.DispatcherTimer]::new()", "Refresh-Ui\n    Set-StartupStage")
    done_start = SOURCE.find("                $notifyFlowId = 'n-' + [string]$notifyFlowSeq")
    done_end = SOURCE.find("                return @{ ok = $true; result = $notifyResult }", done_start)
    done = SOURCE[done_start:done_end] if done_start >= 0 and done_end >= 0 else ""
    check("Topmost = $true" in notify_ui and "Add_ContentRendered" in notify_ui
          and "'DISPLAYED'" in notify_ui,
          "primary Bridge popup is topmost and acknowledges only after WPF renders it")
    check("Show-ArenaDoneDesktopPopup $record" in notify
          and notify.index("Show-ArenaDoneDesktopPopup $record") < notify.index("ToastNotificationManager")
          and "Update-NotifyPlatformCache -Force" not in notify,
          "Bridge popup is attempted before native fallback without a blocking forced platform probe")
    check("AddSeconds(3)" in done and "TryUpdate" in done and "WPF_ContentRendered" in done,
          "report_done waits briefly for an atomic rendered-window acknowledgement")
    check("delivered = [bool]$notifyVerified" in done and "NOTIFICATION_UNVERIFIED" in done
          and "delivered = $true" not in done,
          "report_done never claims delivery solely because Windows accepted a toast call")
    check("'DISPLAY_UNVERIFIED'" in sweep and "SHOWN_UNVERIFIED" in sweep
          and "if ([string]$platform.verdict -eq 'READY')" not in sweep,
          "sweep never upgrades native toast-call success to a verified display")
    check("popupOpenedAt" in sweep and "Set-UiMessageField $record 'popupOpenedAt'" in notify,
          "render timeout starts when WPF opens the popup, not when a busy queue enqueued it")
    check("$notifyBatchCount -lt 2" in timer,
          "bounded UI queue draining leaves time for popup render events")

    settings = region("function Open-SettingsWindow {", "# Version 3.8: Die Update-Infos")
    xaml_start = settings.find("$settingsXaml = @'\n")
    xaml_end = settings.find("\n'@", xaml_start + 1) if xaml_start >= 0 else -1
    xaml = settings[xaml_start:xaml_end] if xaml_start >= 0 and xaml_end >= 0 else ""
    if xaml:
        xaml = xaml.split("\n", 1)[-1]
    try:
        ET.fromstring(xaml)
        settings_xml_valid = True
    except ET.ParseError:
        settings_xml_valid = False
    check(settings_xml_valid, "settings-window XAML remains well-formed after adding the two cards")
    update_start = xaml.find('<Border x:Name="UpdateInfoCard"')
    update_end = xaml.find("</Border>", update_start) if update_start >= 0 else -1
    update_card = xaml[update_start:update_end] if update_start >= 0 and update_end >= 0 else ""
    about_start = xaml.find('<Border x:Name="AboutCard"')
    about_end = xaml.find("</Border>", about_start) if about_start >= 0 else -1
    about_card = xaml[about_start:about_end] if about_start >= 0 and about_end >= 0 else ""
    check('Text="UPDATES"' in update_card and 'x:Name="UpdateInfoText"' in update_card
          and 'Version __ARENA_BUILD_VERSION__' in update_card,
          "update title, automatic-check description, and version are grouped in one card")
    check("Entwickelt von MertaStudios mit dem Arena Agenten." in about_card
          and 'Content="Programmdateien öffnen"' in about_card,
          "separate developer card has the requested wording and program-folder button")
    check('Content="Laufzeitprotokolle öffnen"' in about_card
          and "$script:AppFolder" in settings and "$script:AppDataRoot" in settings
          and "Start-Process -FilePath 'explorer.exe'" in settings,
          "program folder and the actual runtime-log folder each open in Explorer")

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} check(s).")
        return 1
    print("\nOK: 7.9.1 desktop, progress, notification, settings, and release-preparation checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
