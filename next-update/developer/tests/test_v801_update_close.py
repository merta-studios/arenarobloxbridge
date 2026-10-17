#!/usr/bin/env python3
"""Offline-Regressionsgate für 8.0.1: Pflicht-Update ohne Schlupfloch.

Gemeldeter Fehler: Nach 5x "Später" ist das Update Pflicht - aber das X oben
rechts im Update-Fenster wurde als "Später" gewertet, also konnte man das
Fenster wegklicken und die Bridge bequem weiter nutzen.

Geprüft wird auf Quellebene:
  * Das X (UpdateCloseButton) setzt die Auswahl 'exit', niemals 'later'.
  * Jedes andere Schließen ohne Auswahl (Add_Closing, z. B. Alt+F4) wird
    ebenfalls 'exit'; eine getroffene Installations-Auswahl bleibt erhalten.
  * Das Update-Gate beendet bei 'exit' immer (Rückgabe $false), ohne den
    Später-Zähler zu erhöhen, und ein "Später" startet bei fälligem
    Pflicht-Update ($forced) grundsätzlich nicht mehr.
  * Der Aufrufer schließt bei $false das Hauptfenster, bevor die Dienste
    starten - die komplette Bridge beendet sich also.
  * app/version.json ist 8.0.1 mit Stichpunkt-Notiz; release/latest.json
    (veröffentlichtes Manifest) bleibt unangetastet dahinter.

Windows-Verhalten (WPF, ShowDialog, Prozessende) ist hier nicht ausführbar
und bleibt ein Windows-Test (Checkliste in docs/UPDATE-SYSTEM.md).
"""
from __future__ import annotations

import json
import re
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
    return SOURCE[a:b] if a >= 0 and b > a else ""


def as_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def main() -> int:
    print("8.0.1 offline regression checks: X im Update-Fenster beendet die Bridge")

    # --- Version + unveröffentlichtes Manifest bleibt zurück ---
    data = json.loads(VERSION.read_text(encoding="utf-8"))
    check(str(data.get("version")) >= "8.0.1", "app/version.json enthält mindestens die 8.0.1-Korrektur")
    note = next((str(n) for n in data.get("notes", []) if str(n).startswith("• 8.0.1 — ")), "")
    check(note.startswith("• 8.0.1 — ") and note.count("•") >= 5
          and len(" ".join(note.split())) <= 600,
          "notes[0] ist die 8.0.1-Stichpunkt-Notiz (Titel + >=5 Punkte, <600 Zeichen)")
    check("Hauptfenster" in note and "Später" in note,
          "Die 8.0.1-Notiz sagt dem Nutzer: X schließt auch das Hauptfenster")
    notes = [str(n) for n in data.get("notes", [])]
    check(any(n.startswith("• 8.0.0 — ") for n in notes),
          "Die 8.0.0-Notiz bleibt als Historie an zweiter Stelle")
    latest = json.loads(LATEST.read_text(encoding="utf-8"))
    check(as_tuple(str(latest["version"])) <= as_tuple("8.0.3"),
          "release/latest.json bleibt das veröffentlichte Manifest (nicht angehoben)")

    # --- Update-Fenster: X ist 'exit', nie 'later' ---
    window = region("function Show-ArenaUpdateWindow {", "function Invoke-ArenaUpdateGate {")
    check(window != "", "Das Update-Fenster ist als eigener Block vorhanden")
    check('x:Name="UpdateCloseButton"' in window,
          "Das X oben rechts (UpdateCloseButton) ist weiter im Fenster")
    close_handler = region("            $closeButton.Add_Click({", "        })")
    check(close_handler != "" and "$script:UpdateWindowChoice = 'exit'" in close_handler,
          "Das X setzt die Auswahl 'exit'")
    check("'later'" not in close_handler,
          "Das X setzt NIRGENDS mehr 'later' (das war das Schlupfloch)")
    check("$win.Add_Closing({" in window
          and window.count("$script:UpdateWindowChoice = 'exit'") >= 2,
          "Auch Schließen ohne Auswahl (Add_Closing, z. B. Alt+F4) wird 'exit'")
    check(window.count("[string]::IsNullOrEmpty($script:UpdateWindowChoice)") >= 2,
          "Eine getroffene Auswahl (Installieren/Später) wird beim Schließen nicht überschrieben")
    check("$closeButton.ToolTip = 'Bridge beenden'" in window,
          "Das X sagt per Tooltip ehrlich, dass es die Bridge beendet")

    # --- Update-Gate: 'exit' beendet immer, Pflicht-'Später' startet nie ---
    gate = region("function Invoke-ArenaUpdateGate {", "# <<< ARENA-UPDATE-INTEGRATION <<<")
    check(gate != "", "Das Update-Gate ist vorhanden")
    exit_pos = gate.find("if ($choice -eq 'exit')")
    later_pos = gate.find("if ($choice -eq 'later' -or $choice -eq '')")
    check(exit_pos >= 0 and "return $false" in gate[exit_pos:exit_pos + 400],
          "Das Gate beendet die Bridge bei 'exit' (Rückgabe $false)")
    check(0 <= exit_pos < later_pos,
          "'exit' wird VOR der 'later'-Auswertung behandelt (kein Weiter-Start, kein Zähler)")
    check("if ($forced) { return $false }" in gate
          and gate.find("if ($forced) { return $false }") < later_pos,
          "Pflicht-Sperre: Ein 'Später' startet bei fälligem Pflicht-Update nie mehr")
    check("$state.laterClicks = $clicks + 1" in gate[later_pos:],
          "Nur ein echtes 'Später' vor der Pflicht erhöht weiter den Zähler")
    check("$script:UpdateLaterLimit = 5" in SOURCE,
          "Das Später-Limit bleibt 5")

    # --- Aufrufer: $false schließt das Hauptfenster, Dienste starten nicht ---
    startup = region("$script:StartupLaunchTimer.Add_Tick({", "$script:StartupLaunchTimer.Start()")
    gate_pos = startup.find("Invoke-ArenaUpdateGate $window")
    close_pos = startup.find("$window.Close()", gate_pos)
    runtime_pos = startup.find("Start-BridgeRuntime", gate_pos)
    check(0 <= gate_pos < close_pos < runtime_pos,
          "Bei $false schließt der Aufrufer das Hauptfenster, bevor Start-BridgeRuntime läuft")
    check("[System.Environment]::Exit(0)" in SOURCE,
          "Das geschlossene Hauptfenster beendet den Prozess vollständig (Exit im Closed-Pfad)")

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} check(s).")
        return 1
    print("\nOK: 8.0.1 - das X beendet die komplette Bridge, die Pflicht lässt sich nicht wegklicken.")
    print("Windows-Verhalten (WPF/ShowDialog/Prozessende) ist hier NICHT geprüft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
