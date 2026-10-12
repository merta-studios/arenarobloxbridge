#!/usr/bin/env python3
"""Offline-Pruefung des einfachen Selbst-Updates (Version 7.9.1).

Geprueft wird, was auf Linux pruefbar ist:
- das Veroeffentlichungswerkzeug (publish_latest.py) gegen die echte EXE,
- der Workflow im Repository-Hauptordner,
- der Update-Block in app/ArenaBridge.ps1 (Struktur, Sicherheitsregeln, XAML),
- Versionen: eine einzige Quelle (app/version.json, Platzhalter im Quelltext),
- die Syntax der PowerShell-Dateien mit dem Tree-sitter-Parser.

Nicht pruefbar auf Linux und daher NICHT behauptet: das Verhalten von WPF,
Windows PowerShell 5.1, Virenscannern und dem Papierkorb. Das prueft der Nutzer
auf Windows (siehe developer/docs/UPDATE-SYSTEM.md).
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]   # next-update/
REPO_ROOT = PROJECT_ROOT.parent                      # Repository-Wurzel
APP = PROJECT_ROOT / "app" / "ArenaBridge.ps1"
BUILDER = PROJECT_ROOT / "builder" / "Build-EXE.ps1"
PUBLISH_TOOL = PROJECT_ROOT / "developer" / "tools" / "publish_latest.py"
RELEASE_EXE = PROJECT_ROOT / "release" / "ArenaBridge.exe"
VERSION_JSON = PROJECT_ROOT / "app" / "version.json"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "publish-bridge.yml"
TOKEN = "__ARENA_BUILD_VERSION__"
# Baseline des Tree-sitter-Parsers fuer app/ArenaBridge.ps1 (bekannte, harmlose Hinweise).
PARSER_BASELINE_APP = 8

failures: list[str] = []


def check(condition: bool, label: str) -> None:
    print(("  ok   " if condition else "  FAIL ") + label)
    if not condition:
        failures.append(label)


def block_text(text: str) -> str:
    start = text.find("# >>> ARENA-UPDATE-INTEGRATION >>>")
    end = text.find("# <<< ARENA-UPDATE-INTEGRATION <<<")
    if start < 0 or end < 0 or end < start:
        return ""
    return text[start:end]


def load_publish_tool():
    spec = importlib.util.spec_from_file_location("publish_latest", PUBLISH_TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_publish_tool(tool) -> None:
    print("\n-- Veroeffentlichungswerkzeug (echte EXE)")
    check(RELEASE_EXE.is_file(), "release/ArenaBridge.exe ist vorhanden")
    version = tool.file_version(RELEASE_EXE)
    check(re.fullmatch(r"\d+\.\d+\.\d+\.0", version) is not None,
          f"Dateiversion der EXE ist dreiteilig plus .0 (gefunden: {version})")
    core = version[:-2]
    commit = "0" * 40
    now = __import__("datetime").datetime(2026, 10, 12, 12, 0, tzinfo=__import__("datetime").timezone.utc)
    manifest = tool.build_manifest(RELEASE_EXE, core, "Test", "merta-studios/arenarobloxbridge", commit, now)
    check(manifest["sha256"] == __import__("hashlib").sha256(RELEASE_EXE.read_bytes()).hexdigest(),
          "SHA-256 im Manifest stimmt mit der Datei ueberein")
    check(manifest["sizeBytes"] == RELEASE_EXE.stat().st_size, "Groesse im Manifest stimmt")
    check(manifest["url"].endswith(f"/{commit}/next-update/release/ArenaBridge.exe"),
          "Download-Adresse zeigt auf den Commit (unveraenderlich)")
    try:
        tool.build_manifest(RELEASE_EXE, "9.9.9", "Test", "merta-studios/arenarobloxbridge", commit, now)
        check(False, "falsche Version wird abgelehnt")
    except tool.PublishError:
        check(True, "falsche Version wird abgelehnt")
    with tempfile.TemporaryDirectory() as tmp:
        latest = Path(tmp) / "latest.json"
        latest.write_text(json.dumps({"version": core, "sha256": "x" * 64}), encoding="utf-8")
        try:
            tool.check_against_previous(manifest, latest)
            check(False, "gleiche Version mit anderer Datei wird abgelehnt")
        except tool.PublishError:
            check(True, "gleiche Version mit anderer Datei wird abgelehnt")
        latest.write_text(json.dumps({"version": "99.0.0", "sha256": "x" * 64}), encoding="utf-8")
        try:
            tool.check_against_previous(manifest, latest)
            check(False, "niedrigere Version wird abgelehnt")
        except tool.PublishError:
            check(True, "niedrigere Version wird abgelehnt")
        latest.write_text(json.dumps({"version": core, "sha256": manifest["sha256"]}), encoding="utf-8")
        check(tool.check_against_previous(manifest, latest) == "unveraendert",
              "identische Datei bleibt unveraendert (kein Leer-Commit)")
    check(tool.version_tuple("7.10.0") > tool.version_tuple("7.9.9"),
          "Versionsvergleich ist numerisch (7.10.0 > 7.9.9)")


def test_version_source() -> None:
    print("\n-- Versionsquelle")
    data = json.loads(VERSION_JSON.read_text(encoding="utf-8"))
    check(re.fullmatch(r"\d+\.\d+\.\d+", str(data.get("version", ""))) is not None,
          "app/version.json hat eine dreiteilige Version")
    check(str(data["notes"][0]).startswith("• " + data["version"] + " "),
          "neueste Versionsnotiz gehoert zur aktuellen Version")
    app = APP.read_text(encoding="utf-8")
    check(app.count(TOKEN) >= 20, f"Versionsplatzhalter im Quelltext vorhanden ({app.count(TOKEN)}x)")
    literal = []
    for line in app.split("\n"):
        if line.lstrip().startswith("#"):
            continue
        if re.search(r"(?<!registry)(?i:version)\s*=\s*['\"]\d+\.\d+\.\d+['\"]", line):
            literal.append(line.strip()[:100])
    check(not literal, "keine festen Versionsnummern im Code (nur Platzhalter)" + (f": {literal[:3]}" if literal else ""))
    builder = BUILDER.read_text(encoding="utf-8")
    check("$versionMarker = '__ARENA_BUILD_VERSION__'" in builder
          and "$preparedSource.Replace($versionMarker, $BuildVersion)" in builder,
          "Builder setzt die Version aus version.json in den Quelltext")


def test_workflow() -> None:
    print("\n-- Workflow")
    check(WORKFLOW.is_file(), ".github/workflows/publish-bridge.yml liegt im Repository-Hauptordner")
    text = WORKFLOW.read_text(encoding="utf-8") if WORKFLOW.is_file() else ""
    check("next-update/release/ArenaBridge.exe" in text, "Workflow startet nur bei Aenderung der EXE")
    check("branches: [main]" in text, "Workflow laeuft nur auf main")
    check("contents: write" in text, "Workflow darf latest.json committen")
    check("next-update/developer/tools/publish_latest.py" in text, "Workflow ruft das Werkzeug auf")
    check("[skip ci]" in text, "Commit des Workflows loest keinen weiteren Lauf aus")


def test_app_block() -> None:
    print("\n-- Update-Block in app/ArenaBridge.ps1")
    text = APP.read_text(encoding="utf-8-sig")
    block = block_text(text)
    check(text.count("# >>> ARENA-UPDATE-INTEGRATION >>>") == 1 and len(block) > 1000,
          "Update-Block genau einmal vorhanden")
    check("https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/" in block,
          "Download nur von raw.githubusercontent.com (feste Adresse)")
    check("$script:UpdateLaterLimit = 5" in block, "Spaeter-Limit ist 5")
    check(re.search(r"Stop-Process|taskkill|\.Kill\(|Invoke-Expression|\biex\b", block) is None,
          "Update-Block beendet keine Prozesse und fuehrt keinen Code aus dem Netz aus")
    check("Remove-Item" not in block and "Move-Item" not in block and "Rename-Item" not in block,
          "Update-Block loescht oder verschiebt nichts direkt (Papierkorb nur ueber Microsoft.VisualBasic)")
    check("SendToRecycleBin" in block, "alte EXE geht in den Papierkorb")
    check("DeleteFile" in block and "OnlyErrorDialogs" in block, "Papierkorb-Aufruf ist vollstaendig")
    check(re.search(r"ArenaBridge\*\.exe", block) is not None, "nur ArenaBridge*.exe darf entfernt werden")
    code_lines = [l for l in text.split("\n") if not l.lstrip().startswith("#")]
    check(not any("Start-ArenaUpdateCheck" in l or "Start-ArenaManualUpdateCheck" in l for l in code_lines),
          "keine Aufrufe der entfernten alten Update-Funktionen")
    startup = text[text.find("$window.Add_ContentRendered"):]
    gate_pos = startup.find("Invoke-ArenaUpdateGate $window")
    runtime_pos = startup.find("Start-BridgeRuntime\n")
    check(gate_pos > 0 and runtime_pos > gate_pos,
          "Update-Pruefung laeuft vor den Diensten (Start-BridgeRuntime)")
    xaml_match = re.search(r'\$xaml = @"\n(.*?)\n"@', block, re.S)
    check(xaml_match is not None, "XAML des Update-Fensters gefunden")
    if xaml_match:
        xaml = xaml_match.group(1)
        check("StaticResource" not in xaml and "DynamicResource" not in xaml,
              "Update-Fenster nutzt keine geteilten Ressourcen (kein StaticResource-Absturz)")
        try:
            root = ET.fromstring(xaml)
            names = {el.get("{http://schemas.microsoft.com/winfx/2006/xaml}Name")
                     for el in root.iter()}
            for needed in ("UpdateInstallButton", "UpdateLaterButton", "UpdateNotesText", "UpdateStatusText"):
                check(needed in names, f"XAML enthaelt {needed}")
            check(True, "XAML ist wohlgeformtes XML")
        except ET.ParseError as exc:
            check(False, f"XAML ist wohlgeformtes XML ({exc})")
    check('Background="#16A34A"' in block, "Installieren-Knopf ist gruen")


def test_builder() -> None:
    print("\n-- Builder")
    text = BUILDER.read_text(encoding="utf-8")
    check("Update-Bridge" not in text and "updaterPath" not in text,
          "Builder bettet keinen Updater mehr ein")
    check("EmbeddedUpdater" not in text, "keine Updater-Platzhalter mehr")


def test_removed_old_system() -> None:
    print("\n-- Altes System entfernt")
    for rel in ("update-system", "developer/tools/release.py", "tools/ArenaBridge-Update-Holen.ps1",
                "developer/tests/Invoke-SelfUpdateSmoke.ps1", "developer/docs/UPDATE-KONZEPT.md",
                "release/ArenaBridge-7.8.0.exe"):
        check(not (PROJECT_ROOT / rel).exists(), f"entfernt: next-update/{rel}")


def test_parser() -> None:
    print("\n-- PowerShell-Syntax (Tree-sitter, bekannte Hinweise als Baseline)")
    try:
        import tree_sitter_powershell as tsp  # type: ignore
        from tree_sitter import Language, Parser  # type: ignore
    except ImportError as exc:
        check(False, f"Parser-Bibliothek fehlt ({exc}); python -m pip install -r developer/tests/requirements-test.txt")
        return
    parser = Parser(Language(tsp.language()))

    def errors(path: Path) -> int:
        tree = parser.parse(path.read_bytes())
        count = 0
        stack = [tree.root_node]
        while stack:
            node = stack.pop()
            if node.type == "ERROR" or node.is_missing:
                count += 1
            stack.extend(node.children)
        return count

    app_errors = errors(APP)
    check(app_errors <= PARSER_BASELINE_APP,
          f"app/ArenaBridge.ps1 hat nicht mehr Parser-Hinweise als die Baseline ({app_errors} <= {PARSER_BASELINE_APP})")
    check(errors(BUILDER) == 0, "builder/Build-EXE.ps1 ist syntaktisch sauber")


def main() -> int:
    tool = load_publish_tool()
    test_publish_tool(tool)
    test_version_source()
    test_workflow()
    test_app_block()
    test_builder()
    test_removed_old_system()
    test_parser()
    print()
    if failures:
        print(f"FEHLGESCHLAGEN: {len(failures)} Pruefung(en).")
        return 1
    print("OK: Selbst-Update (einfach) ist auf dieser Pruefebene in Ordnung. Windows-Verhalten ist NICHT geprueft.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
