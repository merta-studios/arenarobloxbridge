#!/usr/bin/env python3
"""Offline-Regressionsgate für den 7.9.4-Baubruch beim Einsetzen der EXE.

Gemeldeter Fehler des Nutzers (Windows PowerShell 5.1, zweiter und jeder
weitere Build, weil release/ArenaRobloxBridge.exe dann schon existiert):

    Ausnahme beim Aufrufen von "Replace" mit 4 Argument(en):
    "Der Pfad hat ein ungültiges Format."
    ... Could not safely publish the local build output. ...
    BUILD FEHLGESCHLAGEN (Exit-Code 1).

Ursache: Windows PowerShell wandelt $null beim Aufruf einer .NET-Methode mit
string-Parameter in eine LEERE ZEICHENKETTE um. File.Replace hält "" für einen
Sicherungspfad und wirft ArgumentException ("The path is not of a legal form").
Der Aufruf [IO.File]::Replace($Staging,$Target,$null,$true) konnte daher niemals
funktionieren - der erste Build ging nur deshalb durch, weil er den Move-Zweig
(Zieldatei fehlt noch) benutzte.

Geprüft wird hier auf Quellebene: die kaputte Übergabe ist weg, der Ersatz
liefert ein echtes .NET-null, und der 7.9.4-Vertrag "genau eine Datei im
Ausgabeordner" bleibt bestehen. Windows-PowerShell, ReplaceFile und der echte
ps2exe-Build sind hier nicht ausführbar und bleiben ein Windows-Test.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # next-update/
BUILDER = ROOT / "builder" / "Build-EXE.ps1"
BUILD_TEXT = BUILDER.read_text(encoding="utf-8")
BUILD_LINES = BUILD_TEXT.splitlines()
FAILURES: list[str] = []


def check(condition: bool, label: str) -> None:
    print(("  ok   " if condition else "  FAIL ") + label)
    if not condition:
        FAILURES.append(label)


def code_lines() -> list[str]:
    """Alle Zeilen ohne reine Kommentarzeilen (Kommentare dürfen $null nennen)."""
    return [line for line in BUILD_LINES if not line.lstrip().startswith("#")]


def code_text() -> str:
    return "\n".join(code_lines())


def function_block(name: str) -> str:
    """Quelltext einer PowerShell-Funktion (bis zur schließenden Klammer in Spalte 0)."""
    start = BUILD_TEXT.find(f"function {name} {{")
    if start < 0:
        return ""
    end = BUILD_TEXT.find("\n}\n", start)
    return BUILD_TEXT[start:end + 3] if end > start else ""


def test_broken_call_is_gone() -> None:
    print("\n-- Der kaputte Aufruf ist weg")
    # Der exakte Baubruch: $null als drittes Argument von File.Replace.
    broken = re.compile(r"\[IO\.File\]::Replace\([^)]*\$null", re.DOTALL)
    check(broken.search(code_text()) is None,
          "Kein [IO.File]::Replace(...) bekommt mehr $null direkt übergeben")
    # Allgemeine Regel: keine .NET-Datei-API bekommt $null in einer Pfad-Stelle.
    loose = re.compile(
        r"\[IO\.File\]::(Replace|Move|Copy|Delete|Open|ReadAllText|WriteAllText)"
        r"\([^)\n]*\$null",
    )
    check(loose.search(code_text()) is None,
          "Keine .NET-Datei-API bekommt mehr $null als Pfad-Argument")
    check("[IO.File]::Replace(" not in code_text(),
          "File.Replace wird im Code nie direkt aufgerufen, sondern nur über den Helfer")


def test_real_null_helper() -> None:
    print("\n-- Ersatz: echtes .NET-null über Reflection")
    block = function_block("Invoke-FileReplaceWithoutBackup")
    check(block != "", "Die Funktion Invoke-FileReplaceWithoutBackup ist vorhanden")
    check("[IO.File].GetMethod('Replace'," in block
          and "[System.String]" in block and "[System.Boolean]" in block,
          "Sie holt genau die File.Replace(String, String, String, Boolean)-Überladung")
    check("$null -eq $replaceMethod" in block,
          "Ein fehlendes Replace im .NET-Laufzeitumfeld wird gemeldet statt still zu passieren")
    invoke = re.search(r"\.Invoke\(\s*\$null\s*,\s*\[Object\[\]\]@\(([^)]*)\)", block)
    check(invoke is not None,
          "Der Aufruf läuft über eine [Object[]]-Argumentliste (umgeht die $null-Leerstring-Umwandlung)")
    if invoke:
        args = [part.strip() for part in invoke.group(1).split(",")]
        check(len(args) == 4, "Es werden genau vier Argumente übergeben")
        check(args[:2] == ["$SourcePath", "$DestinationPath"],
              "Quelle und Ziel stehen an Position 1 und 2")
        check(len(args) == 4 and args[2] == "$null",
              "Der Sicherungspfad bleibt $null (in der object[]-Liste ein echtes .NET-null)")
        check(len(args) == 4 and args[3] == "$true",
              "ignoreMetadataErrors bleibt $true")
    check("$_.Exception.InnerException" in block and "throw $inner" in block,
          "Die verpackte TargetInvocationException wird ausgepackt, damit die echte Meldung erscheint")
    check("$replaceMethod.Invoke" in block and "[void]" in block,
          "Der Rückgabewert des Reflection-Aufrufs wird verworfen")


def test_publish_flow() -> None:
    print("\n-- Publish-LocalBuild setzt atomar ein")
    block = function_block("Publish-LocalBuild")
    check(block != "", "Die Funktion Publish-LocalBuild ist vorhanden")
    check("Invoke-FileReplaceWithoutBackup -SourcePath $StagingPath -DestinationPath $TargetPath" in block,
          "Eine vorhandene EXE wird über den Helfer ersetzt")
    check("[IO.File]::Move($StagingPath,$TargetPath)" in block
          and "Test-Path -LiteralPath $TargetPath -PathType Leaf" in block,
          "Fehlt die EXE noch, wird sie weiter einfach hineingeschoben (erster Build)")
    check(block.count("$attempt -le 3") == 1 and "Start-Sleep -Milliseconds 400" in block,
          "Kurze Sperren (Virenscanner/Explorer) werden mit drei Anläufen abgefangen")
    check("Close every running ArenaRobloxBridge window and run Build-EXE.bat again." in block,
          "Die Fehlermeldung nennt weiter den echten Rat (Fenster schließen, erneut bauen)")
    check("return" in block, "Ein gelungener Austausch beendet die Funktion sofort")
    check("Publish-LocalBuild -StagingPath $stagingExePath -TargetPath $exePath" in BUILD_TEXT,
          "Der Bau ruft Publish-LocalBuild weiter nach dem bestandenen Smoke-Test auf")


def test_one_file_contract() -> None:
    print("\n-- 7.9.4-Vertrag: genau eine Datei im Ausgabeordner")
    helper = function_block("Invoke-FileReplaceWithoutBackup")
    check("Join-Path" not in helper and ".bak" not in helper and "previous" not in helper,
          "Der Helfer legt keinen Sicherungsdateinamen an")
    check("Remove-LegacyReleaseArtifacts -Directory $buildOutputDirectory" in BUILD_TEXT
          and "'*.previous-*.exe'" in BUILD_TEXT,
          "Alte Backup-Kopien werden beim Bauen weiter aus release/ entfernt")
    check("outputFileCount = 1" in BUILD_TEXT and "schemaVersion = 4" in BUILD_TEXT,
          "Die lokalen Metadaten beschreiben weiter genau eine Datei")
    release = ROOT / "release"
    check(not list(release.glob("*.previous-*.exe"))
          and not (release / "ArenaBridge-Diagnose.exe").exists(),
          "release/ enthält aktuell keine Backup-Kopie und keine zweite EXE")


def test_preflight_probe() -> None:
    print("\n-- Selbsttest vor dem teuren Kompilieren")
    block = function_block("Test-AtomicReplaceSupport")
    check(block != "", "Die Funktion Test-AtomicReplaceSupport ist vorhanden")
    check("Invoke-FileReplaceWithoutBackup -SourcePath $probeStaging -DestinationPath $probeTarget" in block,
          "Der Selbsttest ersetzt eine echte Datei über denselben Helfer")
    check("-ne 1" in block and "backup copy" in block,
          "Entsteht dabei eine Sicherungskopie, bricht der Bau ab")
    check("Remove-Item -LiteralPath $probeDirectory -Recurse -Force" in block,
          "Der Selbsttest räumt seinen Temp-Ordner wieder weg")
    probe_line = next((index for index, line in enumerate(BUILD_LINES)
                       if line.strip() == "Test-AtomicReplaceSupport"), -1)
    compile_line = next((index for index, line in enumerate(BUILD_LINES)
                         if line.startswith("    Invoke-BridgeCompiler -InputPath")), -1)
    check(probe_line >= 0 and compile_line > probe_line,
          "Der Selbsttest läuft vor dem Kompilieren (kein vergeudeter EXE-Bau bei einem Fehler)")
    check(BUILD_TEXT.count("Test-AtomicReplaceSupport") >= 2,
          "Der Selbsttest ist definiert und wird aufgerufen")


def powershell_parse_errors(path: Path) -> list[tuple[int, str]]:
    """Sammelt Tree-sitter-Fehler; das führt keine PowerShell-Laufzeit aus."""
    from tree_sitter import Language, Parser
    import tree_sitter_powershell as tsp

    raw = path.read_bytes()
    root = Parser(Language(tsp.language())).parse(raw).root_node
    pending = [root]
    errors: list[tuple[int, str]] = []
    while pending:
        node = pending.pop()
        if node.type == "ERROR" or node.is_missing:
            line = raw.count(b"\n", 0, node.start_byte) + 1
            fragment = raw[node.start_byte:node.end_byte].decode("utf-8", "replace")[:120]
            errors.append((line, fragment))
        pending.extend(node.children)
    return errors


def test_builder_parses() -> None:
    print("\n-- Echte PowerShell-Grammatik über den geänderten Builder")
    try:
        errors = powershell_parse_errors(BUILDER)
    except ImportError:
        print("  --   tree_sitter_powershell fehlt (pip install -r developer/tests/requirements-test.txt)")
        return
    check(errors == [],
          "builder/Build-EXE.ps1 parst fehlerfrei mit der PowerShell-Grammatik"
          + ("" if not errors else f" (erster Fehler Zeile {errors[0][0]}: {errors[0][1]!r})"))


def test_builder_stays_ascii() -> None:
    print("\n-- Dateiform des Builders")
    raw = BUILDER.read_bytes()
    check(all(byte < 128 for byte in raw),
          "builder/Build-EXE.ps1 bleibt reines ASCII (keine Umlaute im Konsolenskript)")
    check(not raw.startswith(b"\xef\xbb\xbf") and b"\r\n" not in raw,
          "builder/Build-EXE.ps1 bleibt UTF-8 ohne BOM mit LF-Zeilenenden")


def main() -> int:
    print("7.9.4 build-publish offline regression checks")
    test_broken_call_is_gone()
    test_real_null_helper()
    test_publish_flow()
    test_one_file_contract()
    test_preflight_probe()
    test_builder_parses()
    test_builder_stays_ascii()
    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s).")
        return 1
    print("OK: Der Baubruch beim Einsetzen der EXE ist auf dieser Prüfebene behoben.")
    print("Windows-Verhalten (ReplaceFile, ps2exe-Build, gesperrte EXE) ist hier NICHT geprüft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
