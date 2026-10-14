#!/usr/bin/env python3
"""Offline-Regressionsgate für 7.9.4 (genau eine EXE + Installation über die Download-Seite).

Der Nutzer hat zwei Dinge verlangt:
  1. Der Builder erzeugt nur noch EINE Datei: ArenaRobloxBridge.exe. Die frühere
     zweite Programmdatei (ArenaBridge-Diagnose.exe) und Start-Diagnostic.bat
     sollen weg sein.
  2. Die Bridge prüft Updates weiter über das Repository (latest.json), aber der
     Knopf "Jetzt installieren" öffnet die neue Download-Seite
     https://arena-rblx-bridge.netlify.app/.

Nur Quellstruktur und Verträge: Windows-PowerShell, WPF, Explorer, Papierkorb und
der echte ps2exe-Build sind hier nicht ausführbar und bleiben ein Windows-Test.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # next-update/
APP = ROOT / "app" / "ArenaBridge.ps1"
BUILDER = ROOT / "builder" / "Build-EXE.ps1"
BAT = ROOT / "Build-EXE.bat"
VERSION = ROOT / "app" / "version.json"
RELEASE = ROOT / "release"
WEBSITE = ROOT / "website"
DOCS = ROOT / "developer" / "docs"
DOWNLOAD_PAGE = "https://arena-rblx-bridge.netlify.app/"

SOURCE = APP.read_text(encoding="utf-8-sig")
BUILD_TEXT = BUILDER.read_text(encoding="utf-8")
FAILURES: list[str] = []


def check(condition: bool, label: str) -> None:
    print(("  ok   " if condition else "  FAIL ") + label)
    if not condition:
        FAILURES.append(label)


def block_text(text: str) -> str:
    start = text.find("# >>> ARENA-UPDATE-INTEGRATION >>>")
    end = text.find("# <<< ARENA-UPDATE-INTEGRATION <<<")
    if start < 0 or end < 0 or end < start:
        return ""
    return text[start:end]


def test_builder_one_exe() -> None:
    print("\n-- Builder: genau eine EXE")
    check("$exePath = Join-Path $buildOutputDirectory 'ArenaRobloxBridge.exe'" in BUILD_TEXT,
          "Der Builder hat genau einen Ausgabepfad (ArenaRobloxBridge.exe)")
    check("$diagnosticExePath" not in BUILD_TEXT and "$stagingDiagnosticExePath" not in BUILD_TEXT
          and "$diagnosticBatPath" not in BUILD_TEXT,
          "Keine Variablen für eine zweite (Diagnose-)EXE oder einen Starter mehr")
    check("Write-DiagnosticLauncher" not in BUILD_TEXT and "Write-DiagnosticLauncher -Path" not in BUILD_TEXT,
          "Der Diagnose-Starter (Start-Diagnostic.bat) wird nicht mehr erzeugt")
    check(BUILD_TEXT.count("Invoke-BridgeCompiler -InputPath") == 1
          and "-NoConsole $true" in BUILD_TEXT,
          "Es wird nur noch genau eine EXE kompiliert (normaler Start ohne Konsolenfenster)")
    check("Remove-LegacyReleaseArtifacts" in BUILD_TEXT
          and "'ArenaBridge-Diagnose.exe'" in BUILD_TEXT
          and "'Start-Diagnostic.bat'" in BUILD_TEXT
          and "'*.previous-*.exe'" in BUILD_TEXT,
          "Alte Diagnose-Dateien und Backup-Kopien werden aus dem Ausgabeordner entfernt")
    check("schemaVersion = 4" in BUILD_TEXT and "outputFileCount = 1" in BUILD_TEXT
          and re.search(r"diagnosticSha256\s*=", BUILD_TEXT) is None
          and re.search(r"diagnostic(FileName|SizeBytes)\s*=", BUILD_TEXT) is None,
          "Die lokalen Metadaten beschreiben genau eine Datei (Schema 4)")
    check(BUILD_TEXT.count(".sha256')") == 1
          and "Write-Utf8NoBom (Join-Path $buildOutputDirectory 'ArenaBridge-Diagnose.exe.sha256')" not in BUILD_TEXT,
          "Es wird nur noch eine Prüfsummendatei geschrieben")
    check("*.previous-*.exe" in BUILD_TEXT and "Preserved at" not in BUILD_TEXT,
          "Der Builder legt keine Sicherungskopie (*.previous-*.exe) mehr ab")
    check("noConsole = $NoConsole" in BUILD_TEXT and "-NoConsole $true" in BUILD_TEXT
          and "Arena Roblox Bridge - Diagnose" not in BUILD_TEXT,
          "Der normale unsichtbare EXE-Start bleibt unverändert")


def test_bat_and_folder() -> None:
    print("\n-- Build-EXE.bat und release/")
    bat = BAT.read_text(encoding="ascii")
    check("release\\ArenaRobloxBridge.exe" in bat and "kein zweites Programm" in bat,
          "Die BAT nennt genau eine Ergebnisdatei und kein zweites Programm")
    check("Start-Diagnostic" not in bat and "ArenaBridge-Diagnose" not in bat,
          "Die BAT verweist nicht mehr auf eine Diagnose-Datei")
    check("START-CHECK.txt" in bat and "startup-diagnose.txt" in bat,
          "Die BAT nennt die Startdiagnose-Dateien für den Fall 'kein Fenster'")
    check(not (RELEASE / "ArenaBridge-Diagnose.exe").exists()
          and not (RELEASE / "Start-Diagnostic.bat").exists()
          and not list(RELEASE.glob("*.previous-*.exe")),
          "release/ enthält keine zweite EXE, keinen Starter und keine Backup-Kopie")


def test_update_window_opens_download_page() -> None:
    print("\n-- Update: Repository-Prüfung bleibt, Installation über die Download-Seite")
    block = block_text(SOURCE)
    check(block != "", "Der Update-Block ist vorhanden")
    check(f"$script:UpdateDownloadPageUrl = '{DOWNLOAD_PAGE}'" in block,
          "Der Update-Block führt die Download-Seite als feste Adresse")
    check("Start-Process -FilePath $script:UpdateDownloadPageUrl" in block,
          "\"Jetzt installieren\" öffnet die Download-Seite im Standard-Browser")
    check("$script:UpdateManifestUrl = 'https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/next-update/release/latest.json'"
          in block,
          "Geprüft wird weiter das Repository-Manifest (latest.json)")
    check("$script:UpdateRepoUrlPrefix" in block
          and "*/next-update/release/ArenaRobloxBridge.exe" in block
          and "'^[0-9a-f]{64}$'" in block,
          "Adresse, Prüfsumme und Dateiname des Manifests werden weiter geprüft")
    check("Save-ArenaUpdateState $state" in block and "SendToRecycleBin" in block,
          "Die alte EXE wird weiter als pendingCleanup gemerkt und in den Papierkorb verschoben")
    window = block[block.find("function Show-ArenaUpdateWindow {"):block.find("function Invoke-ArenaUpdateGate {")]
    check("Download-Seite" in window
          and "Start-Process -FilePath $script:UpdatePendingUrl" not in window,
          "Das Fenster nennt die Download-Seite und öffnet nicht mehr die rohe EXE-Adresse")
    check("arena-rblx-bridge.netlify.app" in SOURCE
          and SOURCE.count("arena-rblx-bridge.netlify.app") >= 2,
          "Die Download-Seite steht als feste Adresse im Update-Weg der Bridge")


def test_website_and_docs() -> None:
    print("\n-- Download-Seite und Doku")
    index = (WEBSITE / "index.html").read_text(encoding="utf-8")
    check(DOWNLOAD_PAGE.strip("/").split("//")[-1] in (WEBSITE / "README.md").read_text(encoding="utf-8"),
          "website/README.md nennt die Live-Adresse der Download-Seite")
    check("next-update/release/latest.json" in index and "ArenaRobloxBridge.exe" in index,
          "Die Download-Seite liest latest.json und liefert ArenaRobloxBridge.exe")
    handoff = (DOCS / "GANZ WICHTIG LESEN VOR JEDER BEARBEITUNG").read_text(encoding="utf-8")
    check("NACHTRAG 7.9.4" in handoff and "GENAU EINE PROGRAMMDATEI" in handoff
          and DOWNLOAD_PAGE in handoff,
          "Das Übergabedokument hat den Nachtrag 7.9.4 (genau eine EXE, Download-Seite)")
    update_system = (DOCS / "UPDATE-SYSTEM.md").read_text(encoding="utf-8")
    check(DOWNLOAD_PAGE in update_system and "ArenaBridge-Diagnose.exe" in update_system,
          "UPDATE-SYSTEM.md beschreibt Download-Seite und das Ende der zweiten EXE")
    for rel in ("README.md", "START-HIER.txt"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        check("ArenaRobloxBridge.exe" in text and "genau eine" in text.lower(),
              f"{rel} erklärt die eine Programmdatei")
    check(DOWNLOAD_PAGE in (ROOT / "README.md").read_text(encoding="utf-8")
          and DOWNLOAD_PAGE in (ROOT / "START-HIER.txt").read_text(encoding="utf-8"),
          "README.md und START-HIER.txt nennen die Download-Seite")


def test_version_note() -> None:
    print("\n-- Vorbereitete Testversion")
    data = json.loads(VERSION.read_text(encoding="utf-8"))
    version = str(data.get("version", ""))
    check(re.fullmatch(r"\d+\.\d+\.\d+", version) is not None,
          "app/version.json nennt eine gültige dreiteilige Version")
    note = str(data.get("notes", [""])[0])
    check(note.startswith(f"• {version} — "),
          "Die neueste Notiz beginnt mit der vorbereiteten Version")
    check(note.count("•") >= 5 and len(" ".join(note.split())) <= 600,
          "Die Notiz folgt der Stichpunkt-Regel (mindestens fünf Stichpunkte, unter 600 Zeichen)")
    check("Billboard" in note and any(letter in note for letter in "äöüÄÖÜß"),
          "Die Notiz nennt das 8.0.0-Thema (Billboards) und benutzt echte Umlaute")
    check("8.0.0" in note and "Englisch" in note and "Fortschritt" in note,
          "Die Notiz kennzeichnet Version 8.0.0 mit Sprache und Fortschritts-Reset")


def main() -> int:
    print("7.9.4 offline regression checks")
    test_builder_one_exe()
    test_bat_and_folder()
    test_update_window_opens_download_page()
    test_website_and_docs()
    test_version_note()
    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s).")
        return 1
    print("OK: Genau eine EXE und die Installation über die Download-Seite sind auf dieser Prüfebene in Ordnung.")
    print("Windows-Verhalten (ps2exe-Build, WPF-Browserstart, Papierkorb) ist hier NICHT geprüft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
