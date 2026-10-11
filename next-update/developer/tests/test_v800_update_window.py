#!/usr/bin/env python3
"""Prüft die Update-Oberfläche in app/ArenaBridge.ps1 (7.8.0, Updater 2.0.0).

Warum dieser Test existiert: Das erste Update-Fenster ist beim Öffnen abgestürzt,
weil der XAML-Block mit StaticResource auf Fensterressourcen zeigte, die es in
diesem Fenster nicht gab (XamlReader wirft dann eine Ausnahme → Fenster sofort zu).
Damit das nie wieder passiert, prüft dieser Test die Oberfläche als echte Struktur:

  1. Der Integrationsblock enthält genau ein Update-Fenster, und der XAML-Block ist
     wohlgeformtes XML (wird mit xml.etree geparst).
  2. Jede StaticResource-Verwendung im Fenster löst sich in eine Ressource auf, die
     dasselbe Fenster selbst definiert (keine geteilten Fensterressourcen).
  3. Alle erwarteten Bedienelemente existieren: Fortschritt, Abbrechen, Später,
     Überspringen, Protokoll, Installieren.
  4. Die deutschen Beschriftungen sind korrekt kodiert (Umlaute, kein "Spaeter").
  5. Der Updates-Bereich im Einstellungsfenster hat genau drei Knöpfe und nutzt für
     die neuen Elemente keine Fenster-Styles; die Knöpfe rufen die Blockfunktionen auf
     und diese Funktionen existieren wirklich.
  6. Der Block kann nie einen Prozess beenden und hat immer einen Rückfall
     (MessageBox), falls der Fensterbau scheitert.
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
SETTINGS_UI_START = "<!-- >>> ARENA-UPDATE-SETTINGS-UI >>>"
SETTINGS_UI_END = "<!-- <<< ARENA-UPDATE-SETTINGS-UI <<< -->"
SETTINGS_CODE_START = "# >>> ARENA-UPDATE-SETTINGS-CODE >>>"
SETTINGS_CODE_END = "# <<< ARENA-UPDATE-SETTINGS-CODE <<<"
XAML_NS = "{http://schemas.microsoft.com/winfx/2006/xaml}Name"

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


def main() -> int:
    source = app_source().replace("\r\n", "\n")
    block = marker_slice(source, BLOCK_START, BLOCK_END)
    check(bool(block), "Integrationsblock gefunden")

    # 1) Genau ein Fenster im Block, wohlgeformtes XML.
    windows = re.findall(r"@'\n(<Window[\s\S]*?\n</Window>)\n'@", block)
    check(len(windows) == 1, f"genau ein Update-Fenster im Block (gefunden: {len(windows)})")
    if len(windows) != 1:
        print("\nFAILED: " + str(len(FAILURES)) + " Prüfung(en).")
        return 1
    xaml = windows[0]
    try:
        root = ET.fromstring(xaml)
        parsed = True
    except ET.ParseError as exc:
        parsed = False
        root = None
        check(False, f"Update-Fenster ist wohlgeformtes XML ({exc})")
    if parsed:
        check(True, "Update-Fenster ist wohlgeformtes XML")

    names = {element.get(XAML_NS) for element in root.iter() if element.get(XAML_NS)}
    required = {
        "UpdateTitleBar", "UpdateTitleText", "UpdateVersionText", "UpdateCloseButton",
        "UpdateInfoText", "UpdateNotesText", "UpdateProgressPanel", "UpdateProgressBar",
        "UpdateProgressText", "UpdateInstallButton", "UpdateLaterButton", "UpdateSkipButton",
        "UpdateCancelButton", "UpdateLogButton",
    }
    missing = sorted(required - names)
    check(not missing, "alle erwarteten Bedienelemente existieren: "
                       + (", ".join(missing) if missing else "ok"))

    # 2) StaticResource nur aus eigenen Window.Resources.
    defined = set(re.findall(r'x:Key="([A-Za-z0-9_]+)"', xaml))
    used = set(re.findall(r"StaticResource\s+([A-Za-z0-9_]+)", xaml))
    unresolved = sorted(used - defined)
    check(not unresolved and "Window.Resources" in xaml,
          "das Fenster definiert seine Ressourcen selbst (keine geteilten Fensterressourcen): "
          + (", ".join(unresolved) if unresolved else "ok"))

    # 4) Deutsche Beschriftungen mit korrekter Kodierung.
    for label in ("Jetzt aktualisieren", "Später", "Diese Version überspringen",
                  "Abbrechen", "Protokoll öffnen", "Update verfügbar"):
        check(label in xaml, f"Beschriftung korrekt kodiert: {label}")

    # 6) Kein Prozessabbruch, immer ein Rückfall im Fehlerfall.
    check(not any(token in block for token in ("Stop-Process", "taskkill", ".Kill(")),
          "der Update-Block kann keinen Prozess beenden")
    check("Show-ArenaUpdateFallbackPrompt" in block and "MessageBox" in block,
          "bei einem Fensterfehler gibt es einen MessageBox-Rückfall (kein stiller Ausfall)")

    # 5) Einstellungsbereich: genau drei Knöpfe, keine Fenster-Styles für die neuen
    #    Elemente, und die Verdrahtung ruft echte Blockfunktionen auf.
    settings_ui = marker_slice(source, SETTINGS_UI_START, SETTINGS_UI_END)
    settings_code = marker_slice(source, SETTINGS_CODE_START, SETTINGS_CODE_END)
    check(bool(settings_ui) and bool(settings_code), "Updates-Bereich und Verdrahtung gefunden")
    check(settings_ui.count("<Button ") == 3,
          f"genau drei Knöpfe im Updates-Bereich (gefunden: {settings_ui.count('<Button ')})")
    check('UpdateCheckResultText' in settings_ui,
          "der Updates-Bereich hat ein Ergebnisfeld für die manuelle Prüfung")
    new_elements = re.findall(r"<(?:Button|TextBlock)[^>]*x:Name=\"Update(?:Check|Diagnose|Log|CheckResult)[^\"]*\"[^>]*>", settings_ui)
    check(all('Style="{StaticResource' not in element for element in new_elements),
          "die neuen Elemente nutzen keine Fenster-Styles (kein StaticResource-Absturz)")
    for function in ("Start-ArenaManualUpdateCheck", "Show-ArenaUpdateDiagnose", "Open-ArenaUpdateLog"):
        check(function in settings_code, f"Knopf ruft {function} auf")
        check(f"function {function}" in block, f"{function} existiert im Update-Block")

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} Oberflächen-Prüfung(en).")
        return 1
    print("\nOK: Update-Fenster, Einstellungsbereich und Verdrahtung sind geprüft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
