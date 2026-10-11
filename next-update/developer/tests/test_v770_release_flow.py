#!/usr/bin/env python3
"""Offline-Test für den Release-Ablauf (siehe developer/docs/RELEASE-ABLAUF.md).

Geprüft wird:
  1. RELEASE-ABLAUF.md und RELEASE-SESSION-PROMPT.md existieren und enthalten alle Regeln
     (inklusive unveränderlicher Artefaktnamen und des Werkzeugs release.py).
  2. Build-EXE.bat übergibt keine Testparameter.
  3. Es gibt keine unerwarteten EXE-Dateien im Repository: erlaubt sind nur
     release/ArenaBridge.exe (privater Testbau) und release/ArenaBridge-<Version>.exe
     (veröffentlichte, unveränderliche Artefakte).
  4. Aktivierte Kanal-Manifeste sind vollständig konsistent – geprüft mit den echten
     Regeln aus developer/tools/release.py (keine zweite, driftende Implementierung).
  5. Negativtests gegen genau diese Regeln: falscher Hash, falscher Dateiname, fremde
     URL, deaktivierter Kanal mit Koordinaten, ungültige sequence, zu neue
     minimumUpdaterVersion, zu lange notes, Vorabversion in stable, Schema 1, testFixture.

Hinweis: Versionen werden NICHT fest verdrahtet. Für Prüfungen, die eine echte EXE
brauchen, wird die Dateiversion der vorhandenen release/ArenaBridge.exe gelesen; fehlt
sie, werden diese Fälle ehrlich übersprungen.
"""
from __future__ import annotations

import datetime as _dt
import importlib.util
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "developer" / "docs"
CHANNELS = ROOT / "update-system" / "channels"
LOCK = ROOT / "update-system" / "update_system_guard.lock.json"
SCHEMA_PATH = CHANNELS / "manifest.schema.json"
VERSION_FILE = ROOT / "app" / "version.json"
BAT_PATH = ROOT / "Build-EXE.bat"
RELEASE_DIR = ROOT / "release"
SOURCE_EXE = RELEASE_DIR / "ArenaBridge.exe"
UPDATE_README = ROOT / "update-system" / "README.md"
RELEASE_TOOL = ROOT / "developer" / "tools" / "release.py"

FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("  ok   " if condition else "  FAIL ") + message)
    if not condition:
        FAILURES.append(message)


def load_release_tool():
    spec = importlib.util.spec_from_file_location("arena_release_tool", RELEASE_TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def last_published_version(readme_text: str) -> str:
    match = re.search(r"Letzte ver[öo]ffentlichte Version:\s*([^\s\n\(\)]+)", readme_text, re.IGNORECASE)
    if not match:
        return ""
    value = match.group(1).strip()
    return "" if value.lower() in ("keine", "none", "") else value


def lock_has_release_approval(lock: dict, day: str) -> bool:
    for entry in lock.get("approvals", []) or []:
        note = str(entry.get("note", "")).lower()
        if str(entry.get("date", "")) == day and ("release" in note or "freigabe" in note):
            return True
    return False


def test_documentation_and_rules() -> None:
    flow_doc = DOCS / "RELEASE-ABLAUF.md"
    prompt_doc = DOCS / "RELEASE-SESSION-PROMPT.md"
    concept_doc = DOCS / "UPDATE-KONZEPT.md"
    check(flow_doc.is_file(), "RELEASE-ABLAUF.md existiert")
    check(prompt_doc.is_file(), "RELEASE-SESSION-PROMPT.md existiert")
    check(concept_doc.is_file(), "UPDATE-KONZEPT.md existiert (Konzept gehört zum Ablauf)")

    flow_text = flow_doc.read_text(encoding="utf-8")
    mandatory_flow_markers = [
        "Änderungs-Session" in flow_text,
        "Release-Session" in flow_text,
        "update-system/channels" in flow_text,
        "raw.githubusercontent.com" in flow_text,
        "isPrivate" in flow_text,
        "Invoke-SelfUpdateSmoke.ps1" in flow_text,
        "release.py stage" in flow_text,
        "ArenaBridge-<VERSION>.exe" in flow_text,
        "--dry-run" in flow_text,
        "--tested-by-user" in flow_text,
        "Letzte veröffentlichte Version" in flow_text,
        "version-conflict" in flow_text,
        "disable --channel" in flow_text,
    ]
    check(all(mandatory_flow_markers), "RELEASE-ABLAUF.md enthält alle Regeln und Tore")

    prompt_text = prompt_doc.read_text(encoding="utf-8")
    mandatory_prompt_markers = [
        "<VERSION>" in prompt_text,
        "<KURZBESCHREIBUNG DER GEMERGTEN AENDERUNG>" in prompt_text,
        "RELEASE-ABLAUF.md" in prompt_text,
        "UPDATE-KONZEPT.md" in prompt_text,
        "next-update/release/ArenaBridge.exe" in prompt_text,
        "release.py stage" in prompt_text,
        "--rebaseline" in prompt_text,
        "isPrivate" in prompt_text,
        "Invoke-SelfUpdateSmoke.ps1" in prompt_text,
        "pefile" in prompt_text,
        "FileVersion" in prompt_text,
        "ArenaBridge-<VERSION>.exe" in prompt_text,
    ]
    check(all(mandatory_prompt_markers), "RELEASE-SESSION-PROMPT.md enthält alle Vorlagenfelder und Regeln")


def test_builder_bat() -> None:
    bat_text = BAT_PATH.read_text(encoding="utf-8")
    check("-Channel stable" in bat_text, "Build-EXE.bat baut Kanal stable")
    check("-NonInteractive" in bat_text, "Build-EXE.bat übergibt -NonInteractive")
    check("-TestFixtureBuild" not in bat_text, "Build-EXE.bat übergibt keinen Testparameter -TestFixtureBuild")
    check("-OutputDirectory" not in bat_text, "Build-EXE.bat übergibt keinen Testparameter -OutputDirectory")
    check("-TestFileVersion" not in bat_text, "Build-EXE.bat übergibt keinen Testparameter -TestFileVersion")


def test_tracked_executables() -> None:
    # Erlaubt: der private Testbau release/ArenaBridge.exe und unveränderliche
    # veröffentlichte Artefakte release/ArenaBridge-<Version>.exe. Nichts sonst.
    pattern = re.compile(r"^release/ArenaBridge\.exe$|^release/ArenaBridge-\d+\.\d+\.\d+(?:-[0-9A-Za-z][0-9A-Za-z.-]*)?\.exe$")
    unexpected = [p.relative_to(ROOT).as_posix() for p in sorted(ROOT.rglob("*.exe"))
                  if not pattern.match(p.relative_to(ROOT).as_posix())]
    check(not unexpected, "keine unerwartete EXE im Repository: " + (", ".join(unexpected) if unexpected else "ok"))


def test_active_manifest_consistency() -> None:
    arena = load_release_tool()
    schema = load_json(SCHEMA_PATH)
    readme_text = UPDATE_README.read_text(encoding="utf-8")
    app_version = str(load_json(VERSION_FILE).get("version", ""))
    previous = last_published_version(readme_text)
    lock = load_json(LOCK) if LOCK.is_file() else {}
    import jsonschema  # type: ignore
    validator = jsonschema.Draft202012Validator(schema)

    for channel in ("beta", "stable"):
        data = load_json(CHANNELS / f"{channel}.json")
        schema_errors = sorted(e.message for e in validator.iter_errors(data))
        check(not schema_errors, f"{channel}.json erfüllt das Schema 2: " + ("; ".join(schema_errors) if schema_errors else "ok"))
        if not data.get("enabled"):
            check(data.get("version") == "" and (data.get("artifact") or {}).get("url") == "",
                  f"{channel}.json ist ein leerer, deaktivierter Platzhalter")
            continue
        check(str(data.get("version")) == app_version,
              f"{channel}.json: Version entspricht app/version.json")
        version = str(data.get("version"))
        artifact_file = RELEASE_DIR / str((data.get("artifact") or {}).get("fileName", ""))
        artifact_sha = str((data.get("artifact") or {}).get("sha256", "")).lower()
        actual_sha = arena.sha256_file(artifact_file).lower() if artifact_file.is_file() else ""
        # Regel 4 des Release-Ablaufs: hoeher als die letzte Veroeffentlichung;
        # Gleichstand ist nur mit genau demselben Artefakt erlaubt (sonst version-conflict).
        # Die Zeile "Letzte veröffentlichte Version" nennt nach dem Veroeffentlichen die
        # Version dieses Manifests selbst - das ist kein Rueckschritt, sondern der Normalfall.
        if not previous:
            check(True, f"{channel}.json: keine frühere Veröffentlichung eingetragen")
        elif arena.parse_semver(version) == arena.parse_semver(previous):
            check(bool(actual_sha) and artifact_sha == actual_sha,
                  f"{channel}.json: Version {version} gleicht der letzten Veröffentlichung und "
                  f"muss genau dasselbe Artefakt nennen (version-conflict bei anderem Hash)")
        else:
            check(arena.semver_gt(version, previous),
                  f"{channel}.json: Version ist höher als die letzte Veröffentlichung ({previous})")
        problems = arena.validate_channel(data, channel, exe_path=artifact_file)
        check(not problems, f"aktiviertes Manifest {channel}.json ist konsistent: "
                            + ("; ".join(problems) if problems else "ok"))
        day = str(data.get("publishedAtUtc", ""))[:10]
        check(lock_has_release_approval(lock, day),
              f"{channel}.json: Guard-Lock enthält die Release-Freigabe vom {day}")


def test_negative_unit_tests() -> None:
    arena = load_release_tool()
    app_version = str(load_json(VERSION_FILE).get("version", ""))
    today = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Die Regeln von release.py werden gegen echte Dateien geprüft. Dafür wird die
    # vorhandene private Test-EXE in einen Temp-Ordner unter dem abgeleiteten Namen
    # kopiert. Die Version kommt aus der Datei selbst (kein fest verdrahteter Wert).
    if not SOURCE_EXE.is_file():
        print("  skip release/ArenaBridge.exe fehlt; dateibasierte Negativtests übersprungen")
        return
    exe_version, source = arena.exe_file_version(SOURCE_EXE)
    core = arena.core_version(exe_version)
    if not core:
        print(f"  skip keine Dateiversion in release/ArenaBridge.exe gefunden (Quelle {source}); übersprungen")
        return
    print(f"  info lokale Test-EXE meldet Dateiversion {exe_version} (Quelle {source})")

    temp_dir = Path(tempfile.mkdtemp(prefix="arena-release-"))
    try:
        fixture_exe = temp_dir / arena.artifact_name(core)
        shutil.copy2(SOURCE_EXE, fixture_exe)
        notes = ["Erster Satz der Neuerungen.", "Zweiter Satz der Neuerungen."]
        base = arena.build_manifest(core, "stable", 2, fixture_exe, notes, today)

        # 1) Grundlage: das geplante Manifest muss fehlerfrei sein.
        problems = arena.validate_channel(base, "stable", exe_path=fixture_exe)
        check(not problems, "Negativtest-Basis: geplantes Manifest ist fehlerfrei: "
                            + ("; ".join(problems) if problems else "ok"))

        def expect(name: str, mutant: dict, needle: str, *, exe_path: Path | None = fixture_exe) -> None:
            data = json.loads(json.dumps(base))
            mutant(data)
            found = arena.validate_channel(data, "stable", exe_path=exe_path)
            check(any(needle in problem for problem in found),
                  f"Negativtest {name}: abgelehnt ({needle})"
                  + ("" if found else " -- aber es gab keinen Fehler"))

        expect("falscher SHA-256", lambda d: d["artifact"].__setitem__("sha256", "0" * 64), "sha256")
        expect("falscher Dateiname", lambda d: d["artifact"].__setitem__("fileName", "ArenaBridge.exe"), "fileName")
        expect("fremde URL", lambda d: d["artifact"].__setitem__("url", "https://evil.example/ArenaBridge-" + core + ".exe"), "url")
        expect("falsche Größe", lambda d: d["artifact"].__setitem__("sizeBytes", 12345), "sizeBytes")
        expect("sequence 0", lambda d: d.__setitem__("sequence", 0), "sequence")
        expect("testFixture im Repository", lambda d: d.__setitem__("testFixture", True), "testFixture")
        expect("Schema 1", lambda d: d.__setitem__("schemaVersion", 1), "schemaVersion")
        expect("leere notes", lambda d: d.__setitem__("notes", []), "notes")
        expect("zu lange notes", lambda d: d.__setitem__("notes", ["x" * 900]), "800")
        expect("zu neue minimumUpdaterVersion",
               lambda d: d.__setitem__("minimumUpdaterVersion", "99.0.0"), "minimumUpdaterVersion")
        expect("Vorabversion in stable", lambda d: d.__setitem__("version", core + "-beta.1"), "Vorabversion")

        # Ungültige Dateiversion im Artefakt: Manifest nennt eine höhere Version als die Datei.
        wrong_version = f"{core.split('.')[0]}.{core.split('.')[1]}.{int(core.split('.')[2]) + 1}"
        wrong_path = temp_dir / arena.artifact_name(wrong_version)
        shutil.copy2(SOURCE_EXE, wrong_path)
        wrong = arena.build_manifest(wrong_version, "stable", 3, wrong_path, notes, today)
        found = arena.validate_channel(wrong, "stable", exe_path=wrong_path)
        check(any("Dateiversion" in problem for problem in found),
              "Negativtest falsche Dateiversion im Artefakt: abgelehnt")

        # Deaktivierter Kanal darf keine Koordinaten nennen.
        disabled = json.loads(json.dumps(base))
        disabled["enabled"] = False
        found = arena.validate_channel(disabled, "stable")
        check(any("deaktivierter Kanal" in problem for problem in found),
              "Negativtest deaktivierter Kanal mit Koordinaten: abgelehnt")
        empty_disabled = arena.disabled_manifest("stable")
        found = arena.validate_channel(empty_disabled, "stable")
        check(not found, "deaktivierter Platzhalter aus release.py ist fehlerfrei: "
                         + ("; ".join(found) if found else "ok"))

        # Versionsregel (kein Gleichstand mit anderem Inhalt, kein Downgrade).
        check(arena.semver_gt("7.8.0", "7.7.2"), "semver_gt: 7.8.0 ist höher als 7.7.2")
        check(not arena.semver_gt("7.7.2", "7.7.2"), "semver_gt: Gleichstand ist kein Fortschritt")
        check(not arena.semver_gt("7.6.9", "7.7.2"), "semver_gt: 7.6.9 ist kein Fortschritt gegenüber 7.7.2")
        stage_source = RELEASE_TOOL.read_text(encoding="utf-8")
        check("ist bereits veroeffentlicht" in stage_source and "nicht hoeher als die letzte Veroeffentlichung" in stage_source,
              "release.py lehnt Gleichstand (anderer Inhalt) und Downgrades ab")
        check("exists() and not args.force" in stage_source and "nie ueberschrieben" in stage_source,
              "release.py überschreibt kein veröffentlichtes Artefakt")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main() -> int:
    print("Release-Ablauf- und Freigabetest (Stand 7.8.0)")
    test_documentation_and_rules()
    test_builder_bat()
    test_tracked_executables()
    test_active_manifest_consistency()
    test_negative_unit_tests()

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} Release-Ablauf-Prüfung(en).")
        return 1
    print("\nOK: Ablauf, Dokumentation, Builder, EXE-Bestand, Kanäle und Freigaberegeln geprüft.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
