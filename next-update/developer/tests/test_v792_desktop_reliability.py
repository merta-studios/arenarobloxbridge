#!/usr/bin/env python3
"""Offline-Regressionsgate für 7.9.2 (Nachfolger von test_v791).

Prüft die vom Nutzer beauftragten 7.9.2-Punkte auf Quellebene:
  * Stichpunkt-Regel für die Nutzer-Notizen (dauerhaft in version.json und Doku),
  * neues Update-Fenster mit Zeitstrahl und Stichpunkten, "Später" OHNE Restzahl,
  * echte Umlaute in deutschen Texten (UTF-8 mit BOM),
  * weiches Ziehen (ohne DragMove) und gedämpftes Scrollen,
  * Einstellungen mit genau einem Ordner-Knopf (Bridge-Datenordner),
  * unangetasteter Veröffentlichungskanal (release/latest.json).

Nur Quellstruktur und Verträge: Windows-PowerShell, WPF und Explorer sind hier
nicht ausführbar und bleiben ein Windows-Test.
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app" / "ArenaBridge.ps1"
VERSION = ROOT / "app" / "version.json"
LATEST = ROOT / "release" / "latest.json"
DOC = ROOT / "developer" / "docs" / "GANZ WICHTIG LESEN VOR JEDER BEARBEITUNG"
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


def as_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def main() -> int:
    print("7.9.2 offline regression checks")
    version = json.loads(VERSION.read_text(encoding="utf-8"))
    app_version = str(version.get("version", ""))
    check(re.fullmatch(r"\d+\.\d+\.\d+", app_version) is not None,
          "app/version.json nennt eine gültige Version")
    note = str(version.get("notes", [""])[0])
    check(note.startswith("• " + app_version + " "),
          "Die Notiz der aktuellen Version beginnt mit der Versionszeile")
    check(note.count("•") >= 5,
          "Die Notiz ist eine kurze Stichpunktliste (mindestens fünf Stichpunkte)")
    check(len(" ".join(note.split())) <= 600,
          "Die Notiz passt ins Manifest (höchstens 600 Zeichen nach Leerraum-Zusammenziehen)")
    check(any(letter in note for letter in "äöüÄÖÜß") and "Spaeter" not in note,
          "Die Notiz benutzt echte Umlaute statt ae/oe/ue")

    doc = DOC.read_text(encoding="utf-8")
    check("STICHPUNKT-REGEL FÜR NUTZER-NOTIZEN" in doc and "notes[0]" in doc,
          "Die Stichpunkt-Regel steht dauerhaft in GANZ WICHTIG LESEN VOR JEDER BEARBEITUNG")
    check("Stichpunkt-Regel" in (ROOT / "README.md").read_text(encoding="utf-8")
          and "Stichpunkte" in (ROOT / "START-HIER.txt").read_text(encoding="utf-8")
          and "KURZE STICHPUNKTE" in (ROOT / "app" / "README.txt").read_text(encoding="utf-8")
          and "Stichpunkt-Regel" in (ROOT / "developer" / "README.md").read_text(encoding="utf-8"),
          "Die READ-Dateien nennen die Stichpunkt-Regel für künftige Updates")

    latest = json.loads(LATEST.read_text(encoding="utf-8"))
    check(re.fullmatch(r"\d+\.\d+\.\d+", str(latest.get("version", ""))) is not None
          and as_tuple(str(latest["version"])) <= as_tuple(app_version),
          "release/latest.json bleibt das gültige veröffentlichte Manifest (nicht angehoben)")
    check(len(str(latest.get("sha256", ""))) == 64
          and str(latest.get("url", "")).startswith(
              "https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/"),
          "Das veröffentlichte Manifest trägt Prüfsumme und Repository-Adresse")

    # --- Update-Fenster (Punkt 1 und 4) ---
    window = region("function Show-ArenaUpdateWindow {", "function Invoke-ArenaUpdateGate {")
    check(window != "", "Das Update-Fenster ist als eigener Block vorhanden")
    check("StaticResource" not in window and "DynamicResource" not in window,
          "Das Update-Fenster nutzt keine geteilten Ressourcen (kein XAML-Absturz)")
    check('x:Name="UpdateCurrentVersionText"' in window and 'x:Name="UpdateNewVersionText"' in window
          and 'x:Name="UpdateHeadlineText"' in window,
          "Der Zeitstrahl zeigt laufende und neue Version plus Überschrift")
    check('x:Name="UpdateBulletsPanel"' in window and 'x:Name="UpdateNotesScroll"' in window,
          "Das Fenster hat eine eigene Stichpunktliste in einem Scrollbereich")
    later_lines = [line for line in window.splitlines() if "UpdatePromptLater.Content" in line]
    check(bool(later_lines) and all(not re.search(r"\d", line.split("=", 1)[-1]) for line in later_lines),
          'Der "Später"-Knopf zeigt keine Restzahl')
    check("$script:UpdateLaterLimit" not in window and "$script:UpdateLaterLimit" in SOURCE,
          'Das Später-Limit bleibt im Programm und ist kein Thema für die Nutzer')
    check("Get-ArenaUpdateBullets -Notes $notes" in window
          and "Add-ArenaUpdateBulletRow -Panel $bulletsPanel" in window,
          "Das Fenster zeichnet die Neuigkeiten als einzelne Stichpunkte")
    # Version 7.9.4: Der Knopf merkt sich die alte EXE und öffnet die Download-Seite.
    check("Save-ArenaUpdateState" in window and "Start-Process -FilePath $script:UpdateDownloadPageUrl" in window
          and "https://arena-rblx-bridge.netlify.app/" in SOURCE,
          "Der Installieren-Knopf merkt sich die alte EXE und öffnet die Download-Seite")
    xaml_start = window.find('$xaml = @"\n')
    xaml_end = window.find('\n"@', xaml_start + 1) if xaml_start >= 0 else -1
    xaml = window[xaml_start + len('$xaml = @"\n'):xaml_end] if xaml_start >= 0 and xaml_end >= 0 else ""
    try:
        ET.fromstring(xaml)
        window_xml_valid = True
    except ET.ParseError:
        window_xml_valid = False
    check(window_xml_valid, "Das XAML des Update-Fensters ist wohlgeformtes XML")

    bullets = region("function Get-ArenaUpdateBullets {", "function Add-ArenaUpdateBulletRow {")
    check("return ,$bullets" in bullets,
          "Die Stichpunktliste wird entpackbar zurückgegeben (kein Binder-Fehler)")
    check("[char]0x2022" in bullets and "$bullets.Count -ge 8" in bullets,
          "Auch das einzeilige Manifest trennt die Stichpunkte (höchstens acht Zeilen)")
    check("^\\d+\\.\\d+\\.\\d+" in bullets,
          "Die reine Versionszeile ist Überschrift und kein Stichpunkt")
    notice = region("function Show-UpdateNotice {", "function ConvertTo-XmlSafeText {")
    check("NoticeBulletsPanel" in notice and "Add-ArenaUpdateBulletRow -Panel $noticeBulletsEl" in notice
          and "Get-ArenaUpdateBullets -Notes" in notice,
          "Auch der Hinweis \"Update installiert\" zeigt die Stichpunkte")

    # --- Weiches Ziehen und Scrollen (Punkt 7) ---
    drag = region("function Enable-BridgeWindowDrag {", "function Enable-BridgeSmoothScroll {")
    check("PointToScreen" in drag and "CaptureMouse" in drag and "LostMouseCapture" in drag
          and ".DragMove()" not in SOURCE,
          "Fenster ziehen läuft ohne blockierendes DragMove (Mausposition + Capture)")
    scroll = region("function Start-BridgeScrollClock {", "function Get-ProgramBrandBitmap {")
    check("DispatcherTimer" in scroll and "FromMilliseconds(15)" in scroll
          and "PreviewMouseWheel" in scroll and "$e.Handled = $true" in scroll,
          "Scrollen läuft gedämpft über einen eigenen 15-ms-Timer statt in Stufen")
    check(SOURCE.count("Enable-BridgeSmoothScroll -Scroller") >= 8
          and SOURCE.count("Enable-BridgeWindowDrag -Window") >= 8,
          "Ziehen und Scrollen sind in allen Nebenfenstern und im Hauptfenster verdrahtet")
    check("Enable-BridgeWindowDrag -Window $win -Handle ($win.FindName('UpdateHead'))" in window
          and "Enable-BridgeSmoothScroll -Scroller $notesScroll" in window,
          "Das neue Update-Fenster ist ziehbar und scrollt weich")

    # --- Einstellungen (Punkt 6) ---
    settings = region("function Open-SettingsWindow {", "# Version 3.8: Die Update-Infos")
    xaml_start = settings.find("$settingsXaml = @'\n")
    xaml_end = settings.find("\n'@", xaml_start + 1) if xaml_start >= 0 else -1
    settings_xaml = settings[xaml_start:xaml_end] if xaml_start >= 0 and xaml_end >= 0 else ""
    if settings_xaml:
        settings_xaml = settings_xaml.split("\n", 1)[-1]
    try:
        ET.fromstring(settings_xaml)
        settings_xml_valid = True
    except ET.ParseError:
        settings_xml_valid = False
    check(settings_xml_valid, "Das XAML der Einstellungen bleibt wohlgeformt")
    about_start = settings_xaml.find('<Border x:Name="AboutCard"')
    about_end = settings_xaml.find("</Border>", about_start) if about_start >= 0 else -1
    about_card = settings_xaml[about_start:about_end] if about_start >= 0 and about_end >= 0 else ""
    check('Content="Programmdateien öffnen"' in about_card
          and "Entwickelt von MertaStudios mit dem Arena Agenten." in about_card,
          "Die Entwicklerkarte hat genau den Knopf \"Programmdateien öffnen\"")
    # Der Wortlaut darf nur noch in Kommentaren stehen - nie in XAML oder Code.
    no_button_label = all("Content=" not in line and ".Content" not in line
                          for line in SOURCE.splitlines() if "Laufzeitprotokolle öffnen" in line)
    check("OpenRuntimeFilesButton" not in SOURCE and no_button_label,
          "Der Knopf \"Laufzeitprotokolle öffnen\" ist restlos entfernt")
    check("$openProgramFilesButton.ToolTip = [string]$script:AppDataRoot" in settings
          and "$openProgramFilesButton.Add_Click" in settings
          and "Start-Process -FilePath 'explorer.exe'" in settings
          and "$script:AppFolder" not in settings,
          "Der Knopf öffnet den Bridge-Datenordner (Laufzeitprotokolle, Diagnose, Einstellungen)")
    check("Öffnet den Bridge-Ordner mit Laufzeitprotokollen, Diagnosedateien und Einstellungen."
          in about_card,
          "Der Hinweistext unter dem Knopf nennt den Inhalt des Ordners")

    # --- Umlaute (Punkt 5) ---
    check(APP.read_bytes().startswith(b"\xef\xbb\xbf"),
          "ArenaBridge.ps1 bleibt UTF-8 mit BOM (Windows PowerShell liest die Umlaute)")
    old_spellings = ("Programmdateien oeffnen", "Laufzeitprotokolle oeffnen", "Spaeter",
                     "Groesse", "Pruefung", "Schluessel", "verschluesselt", "moeglich")
    check("Programmdateien öffnen" in SOURCE
          and all(word not in SOURCE for word in old_spellings),
          "Deutsche Texte benutzen echte Umlaute statt ae/oe/ue")

    # --- 7.9.1-Verhalten, das bleiben muss ---
    background = region("function Set-BackgroundShellBrush {", "# Version 7.7.1: Das Programmlogo")
    check("FromArgb(112, 0, 0, 0)" in background and "BitmapScalingMode]::HighQuality" in background
          and "Set-BackgroundArtwork -ImageControl" in SOURCE,
          "Der Nutzer-Hintergrund der Nebenschalen bleibt abgedunkelt, die Place-Liste klar")
    progress = region("function Update-ArenaProgressState {", "# Version 7.0.0: ÜBERGABE (HANDOFF)")
    modes = region("function Get-ProgressMode($node)", "function Get-ShortSid")
    check("Monitor]::Enter($Shared.ProgressStateLock)" in progress
          and "'not_applicable'" in modes and "if ($node -is [bool] -and -not $node)" in modes,
          "Fortschritt bleibt gesperrt-synchronisiert und ohne erfundene Prozentwerte")
    notify_ui = region("function Show-ArenaDoneDesktopPopup {", "function Show-ArenaDoneNotification {")
    check("Topmost = $true" in notify_ui and "Add_ContentRendered" in notify_ui
          and "'DISPLAYED'" in notify_ui,
          "Das Fertig-Popup bestätigt weiter erst nach dem WPF-Rendern")

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} check(s).")
        return 1
    print("\nOK: 7.9.2 Update-Fenster, Stichpunkte, Umlaute, Ziehen/Scrollen und Einstellungen sind in Ordnung.")
    print("Windows-Verhalten (WPF, Explorer, Papierkorb) ist hier NICHT geprüft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
