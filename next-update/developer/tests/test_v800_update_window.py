#!/usr/bin/env python3
"""Prueft das Pflicht-Update-Fenster (Gate) in app/ArenaBridge.ps1 (Updater 3.0.0).

Anforderungen des Nutzers (2026-10-11), die hier als Struktur geprueft werden:

  1. Das Update startet bei JEDEM Programmstart automatisch, vor allen Diensten.
  2. Es gibt keinen Knopf "Später", "Diese Version überspringen" oder "Abbrechen".
  3. Das Fenster laesst sich nicht schliessen (kein Schliessen-Knopf, Closing wird
     abgebrochen, solange die Bridge nicht freigegeben ist).
  4. Waehrend des Updates ist die Bridge nicht bedienbar (modales Fenster).
  5. Im Einstellungsfenster gibt es KEINEN Updates-Bereich mehr.
  6. Der Integrationsblock beendet nie einen Prozess und enthaelt keine Rueckfall-
     Pfade mit Ueberspringen-Logik.

Die Pruefung ist bewusst strukturell (Quelltext), weil PowerShell-Fenster nur unter
Windows laufen. Das Verhalten selbst prueft der Windows-Smoke-Test.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "app" / "ArenaBridge.ps1"
BLOCK_START = "# >>> ARENA-UPDATE-INTEGRATION >>>"
BLOCK_END = "# <<< ARENA-UPDATE-INTEGRATION <<<"
XAML_NS = "{http://schemas.microsoft.com/winfx/2006/xaml}Name"
FORBIDDEN_LABELS = (
    "Später", "Spaeter", "überspringen", "Überspringen", "Diese Version",
    "Abbrechen", "Protokoll öffnen", "Jetzt aktualisieren", "Jetzt nach Updates suchen",
    "Update-Diagnose", "Update verfügbar",
)

FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("  ok   " if condition else "  FAIL ") + message)
    if not condition:
        FAILURES.append(message)


def app_source() -> str:
    return APP.read_bytes().decode("utf-8-sig")


def marker_slice(text: str, start: str, end: str) -> str:
    begin = text.find(start)
    if begin < 0:
        return ""
    stop = text.find(end, begin)
    if stop < 0:
        return ""
    return text[begin:stop + len(end)]


def function_body(text: str, name: str) -> str:
    """Rumpf einer PowerShell-Funktion (bis zur naechsten Funktion auf Spaltenposition 0)."""
    match = re.search(r"^function " + re.escape(name) + r"\b[^\n]*\{", text, re.MULTILINE)
    if not match:
        return ""
    following = re.search(r"^function ", text[match.end():], re.MULTILINE)
    end = match.end() + following.start() if following else len(text)
    return text[match.start():end]


def main() -> int:
    source = app_source().replace("\r\n", "\n")
    block = marker_slice(source, BLOCK_START, BLOCK_END)
    check(bool(block), "Integrationsblock gefunden")
    if not block:
        return 1

    # 1) Genau ein Gate-Fenster, wohlgeformtes XML.
    windows = re.findall(r"@'\n(<Window[\s\S]*?\n</Window>)\n'@", block)
    check(len(windows) == 1, f"genau ein Pflicht-Fenster im Block (gefunden: {len(windows)})")
    if len(windows) != 1:
        print(f"\nFAILED: {len(FAILURES)} Pruefung(en).")
        return 1
    xaml = windows[0]
    try:
        root = ET.fromstring(xaml)
        check(True, "Pflicht-Fenster ist wohlgeformtes XML")
    except ET.ParseError as exc:
        check(False, f"Pflicht-Fenster ist wohlgeformtes XML ({exc})")
        print(f"\nFAILED: {len(FAILURES)} Pruefung(en).")
        return 1

    # 2) Kein Bedienelement: keine Buttons, keine Schliessen-Knoepfe, kein Fenster-Rahmen.
    check("<Button" not in xaml, "das Pflicht-Fenster hat keinen Knopf (kein Später, kein Abbrechen, kein X)")
    check('WindowStyle="None"' in xaml, "das Fenster hat keine Titelleiste mit Schliessen-Symbol")
    check('ResizeMode="NoResize"' in xaml, "das Fenster ist nicht in der Groesse veraenderbar")
    code_only = "\n".join(line for line in block.splitlines() if not line.lstrip().startswith("#"))
    for label in FORBIDDEN_LABELS:
        check(label not in code_only, f"Text '{label}' kommt im Update-Code nicht mehr vor")

    names = {element.get(XAML_NS) for element in root.iter() if element.get(XAML_NS)}
    required = {"GateTitle", "GateSubtitle", "GateNotes", "GateProgress", "GateStatus"}
    missing = sorted(required - names)
    check(not missing, "die Anzeigeelemente existieren: " + (", ".join(missing) if missing else "ok"))

    # 3) Keine geteilten Fensterressourcen (StaticResource-Absturz vermeiden).
    check("StaticResource" not in xaml, "das Pflicht-Fenster nutzt keine geteilten Ressourcen")

    # Deutsche Beschriftungen korrekt kodiert.
    check("Arena Roblox Bridge - Update" in xaml, "Fenstertitel steht im Fenster")
    check("verpflichtend" in xaml, "Hinweis auf die Pflicht steht im Fenster (mit Umlaut-Kodierung)")

    # 4) Schliessen wird abgebrochen, solange das Gate nicht freigegeben ist.
    gate_code = block
    check("Add_Closing" in gate_code and "$eventArgs.Cancel = $true" in gate_code
          and "if (-not $script:UpdateGateMayClose)" in gate_code,
          "Schliessen (Alt+F4, Taskleiste) wird abgebrochen, solange die Bridge gesperrt ist")
    check("$window.Owner" in gate_code or "Owner = $script:MainWindow" in gate_code,
          "das Gate ist dem Hauptfenster als Eigentuemer zugeordnet (Hauptfenster ist gesperrt)")
    check("[void]$window.ShowDialog()" in gate_code, "das Gate ist ein modaler Dialog (Bridge nicht bedienbar)")

    # 5) Start-Reihenfolge: Gate VOR den Diensten.
    start_body = function_body(source, "Start-BridgeRuntime")
    gate_call = start_body.find("Invoke-ArenaUpdateGate")
    studio_call = start_body.find("Find-RobloxStudio")
    check(start_body and gate_call > 0 and (studio_call < 0 or gate_call < studio_call),
          "das Pflicht-Gate laeuft in Start-BridgeRuntime VOR Roblox-Studio, Plugin, Server und Tunnel")
    check("Start-ArenaUpdateCheck" not in source, "die alte Hintergrundpruefung ist vollstaendig entfernt")

    # 6) Nur Freigabe-Pfade: Gate endet nur ueber Complete (weiterlaufen) oder Exit (Installation).
    check("function Complete-ArenaUpdateGate" in block and "function Exit-ArenaForUpdate" in block,
          "es gibt genau zwei Ausgaenge: Complete-ArenaUpdateGate und Exit-ArenaForUpdate")
    check("Environment]::Exit(0)" in function_body(block, "Exit-ArenaForUpdate"),
          "Exit-ArenaForUpdate beendet nur die eigene Bridge (kein fremder Prozess)")

    # 7) Der Block beendet nie einen Prozess und hat keinen Sprung ins Ueberspringen.
    check(not any(token in block for token in ("Stop-Process", "taskkill", ".Kill(")),
          "der Update-Block kann keinen Prozess beenden")
    for removed in ("Add-ArenaSkippedVersion", "Get-ArenaUpdatePreferences", "Start-ArenaManualUpdateCheck",
                    "Show-ArenaUpdateDiagnose", "Open-ArenaUpdateLog", "Show-ArenaUpdatePrompt",
                    "Start-ArenaUpdaterTask", "Schedule-ArenaUpdateRecheck"):
        check(removed not in block, f"{removed} ist entfernt")
    check("Show-ArenaUpdateFallbackPrompt" not in block, "keine MessageBox-Ja/Nein-Rueckfrage mehr (Pflicht statt Auswahl)")

    # 8) Einstellungen: kein Updates-Bereich mehr, kein Knopf, kein Text.
    settings_part = source[:source.find(BLOCK_START)] + source[source.find(BLOCK_END) + len(BLOCK_END):]
    check("ARENA-UPDATE-SETTINGS" not in source, "keine Update-Marker mehr in den Einstellungen")
    check("UpdateCheckButton" not in settings_part and "UpdateInfoText" not in settings_part
          and "UpdateCheckResultText" not in settings_part,
          "das Einstellungsfenster hat keine Update-Elemente mehr")
    check("Start-ArenaManualUpdateCheck" not in settings_part and "Show-ArenaUpdateDiagnose" not in settings_part,
          "das Einstellungsfenster verdrahtet keine Update-Funktion mehr")
    check('Text="UPDATES"' not in source, "die Ueberschrift UPDATES ist aus den Einstellungen entfernt")

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} Oberflaechen-Pruefung(en).")
        return 1
    print("\nOK: Pflicht-Update-Fenster, Einstellungen und Start-Reihenfolge sind geprueft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
