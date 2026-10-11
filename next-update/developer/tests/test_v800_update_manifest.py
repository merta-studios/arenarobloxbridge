#!/usr/bin/env python3
"""Offline-Checks fuer die Kanal-Manifeste (Schema 2, Update-System 2.0.0).

Kein Netz, kein PowerShell. Nachgewiesen wird:
  * das Schema akzeptiert jede gueltige Vorlage und lehnt jede ungueltige ab,
  * zusaetzlich gibt es semantische Vorlagen: schema-gueltig, aber von den
    Laufzeitregeln abgelehnt (Dateiname/URL muessen aus der Version folgen),
  * eine DEAKTIVIERTE Kanal-Datei ist ein reiner Platzhalter ohne Download-
    Koordinaten,
  * eine AKTIVIERTE Kanal-Datei erfuellt alle Freigabebedingungen aus
    developer/docs/RELEASE-ABLAUF.md: Version == app/version.json, Dateiname und
    URL aus der Version abgeleitet, Groesse/SHA-256 identisch mit der echten
    Datei release/ArenaBridge-<version>.exe, sequence echt groesser als die
    letzte Veroeffentlichung und die Freigabe im Guard-Lock dokumentiert,
  * der Windows-Wrapper sauber mit Exit 77 ueberspringt.

Die Freigabepruefung liegt bewusst in developer/tools/release.py (dieselbe
Implementierung, die auch veroeffentlicht) - ein veraendertes Manifest muss also
zwei unabhaengige Implementierungen bestehen: das JSON-Schema und diese Regeln.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "developer" / "tests"
CHANNELS = ROOT / "update-system" / "channels"
FIXTURES = TESTS / "fixtures" / "update"
LOCK = ROOT / "update-system" / "update_system_guard.lock.json"
README = ROOT / "update-system" / "README.md"
VERSION_FILE = ROOT / "app" / "version.json"
RELEASE_DIR = ROOT / "release"
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("  ok   " if condition else "  FAIL ") + message)
    if not condition:
        FAILURES.append(message)


def load_release_tool():
    """developer/tools/release.py als Modul laden (eine Regelquelle)."""
    spec = importlib.util.spec_from_file_location("arena_release_tool",
                                                  ROOT / "developer" / "tools" / "release.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def validator():
    try:
        import jsonschema  # type: ignore
    except ImportError:
        print("FAILED: jsonschema fehlt. developer/tests/requirements-test.txt installieren.")
        raise SystemExit(1)
    schema = json.loads((CHANNELS / "manifest.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    check(schema.get("properties", {}).get("schemaVersion", {}).get("const") == 2,
          "das Schema beschreibt schemaVersion 2")
    check(schema.get("additionalProperties") is False,
          "das Schema lehnt unbekannte Felder ab")
    check("sequence" in schema.get("required", []),
          "sequence ist Pflichtfeld (Schutz vor einem veralteten Manifest)")
    check(schema.get("properties", {}).get("artifact", {}).get("additionalProperties") is False,
          "artifact erlaubt keine Zusatzfelder")
    return jsonschema.Draft202012Validator(schema)


def release_approval_for(day: str) -> bool:
    if not LOCK.is_file():
        return False
    approvals = json.loads(LOCK.read_text(encoding="utf-8")).get("approvals", [])
    for entry in approvals:
        note = str(entry.get("note", "")).lower()
        if entry.get("date") == day and ("release" in note or "freigabe" in note):
            return True
    return False


def last_published_version() -> str:
    text = README.read_text(encoding="utf-8") if README.is_file() else ""
    import re
    match = re.search(r"Letzte ver[öo]ffentlichte Version:\s*([^\s\n\(\)]+)", text, re.IGNORECASE)
    if not match:
        return ""
    value = match.group(1).strip()
    return "" if value.lower() in ("keine", "none", "") else value


def check_disabled_channel(channel: str, data: dict) -> None:
    check(data.get("enabled") is False, f"{channel}.json ist ein ausdruecklich deaktivierter Platzhalter")
    artifact = data.get("artifact", {})
    check(artifact.get("url") == "" and artifact.get("sha256") == "" and artifact.get("sizeBytes") == 0,
          f"{channel}.json veroeffentlicht keine Download-Koordinaten")
    check(str(data.get("version", "")) == "" and str(data.get("publishedAtUtc", "")) == "",
          f"{channel}.json nennt keine Version und kein Datum")


def check_released_channel(channel: str, data: dict, tool) -> None:
    version = str(data.get("version", ""))
    source_version = str(json.loads(VERSION_FILE.read_text(encoding="utf-8")).get("version", ""))
    check(version == source_version,
          f"{channel}.json veroeffentlicht genau app/version.json ({source_version})")

    artifact = data.get("artifact", {})
    expected_name = tool.artifact_name(version)
    check(artifact.get("fileName") == expected_name,
          f"{channel}.json nutzt den aus der Version abgeleiteten Dateinamen ({expected_name})")
    check(artifact.get("url") == tool.artifact_url(version),
          f"{channel}.json nutzt die aus der Version abgeleitete Adresse")

    exe_path = RELEASE_DIR / expected_name
    check(exe_path.is_file(), f"{channel}.json Artefakt liegt als {exe_path.relative_to(ROOT)} vor")
    problems = tool.validate_channel(data, channel, exe_path=exe_path)
    check(not problems, f"{channel}.json besteht die Freigabepruefung: " + ("; ".join(problems) or "ok"))

    previous = last_published_version()
    actual_sha = tool.sha256_file(exe_path).lower() if exe_path.is_file() else ""
    artifact_sha = str(artifact.get("sha256", "")).lower()
    if not previous:
        check(True, f"{channel}.json: keine fruehere Veroeffentlichung eingetragen")
    elif tool.parse_semver(version) == tool.parse_semver(previous):
        # Gleichstand ist nur mit genau demselben Artefakt erlaubt (version-conflict bei
        # anderem Hash). Die README-Zeile "Letzte veröffentlichte Version" nennt nach dem
        # Veroeffentlichen die Version dieses Manifests selbst - das ist der Normalfall.
        check(bool(actual_sha) and artifact_sha == actual_sha,
              f"{channel}.json: Version {version} gleicht der letzten Veroeffentlichung und "
              f"muss genau dasselbe Artefakt nennen (version-conflict bei anderem Hash)")
    else:
        check(tool.semver_gt(version, previous),
              f"{channel}.json: Version {version} ist hoeher als die letzte ({previous})")

    published = str(data.get("publishedAtUtc", ""))
    check(bool(tool.STAMP_RE.match(published)), f"{channel}.json publishedAtUtc ist ISO-8601 UTC ({published})")
    stamp = tool.STAMP_RE.match(published)
    if stamp:
        day = published[:10]
        check(release_approval_for(day),
              f"{channel}.json: Guard-Lock dokumentiert die Freigabe vom {day}")


def main() -> int:
    v = validator()
    tool = load_release_tool()

    valid = sorted(FIXTURES.glob("valid-*.json"))
    for path in valid:
        errors = sorted(v.iter_errors(json.loads(path.read_text(encoding="utf-8"))), key=str)
        check(not errors, f"gueltige Vorlage wird akzeptiert: {path.name}"
                          + (f" -> {errors[0].message}" if errors else ""))

    invalid = sorted(FIXTURES.glob("invalid-*.json"))
    check(len(invalid) >= 12, f"mindestens zwoelf ungueltige Vorlagen vorhanden (gefunden {len(invalid)})")
    for path in invalid:
        rejected = not list(v.iter_errors(json.loads(path.read_text(encoding="utf-8"))))
        check(not rejected, f"ungueltige Vorlage wird abgelehnt: {path.name}")

    semantic = sorted(FIXTURES.glob("semantic-*.json"))
    check(len(semantic) >= 1, "es gibt semantische Vorlagen (schema-gueltig, aber abgelehnt)")
    for path in semantic:
        data = json.loads(path.read_text(encoding="utf-8"))
        schema_errors = list(v.iter_errors(data))
        runtime_problems = tool.validate_channel(data, str(data.get("channel", "beta")))
        check(not schema_errors and bool(runtime_problems),
              f"semantische Vorlage wird erst durch die Laufzeitregeln abgelehnt: {path.name}")

    for channel in ("beta", "stable"):
        data = json.loads((CHANNELS / f"{channel}.json").read_text(encoding="utf-8"))
        check(data.get("channel") == channel, f"{channel}.json nennt den eigenen Kanal")
        check(data.get("testFixture") is False, f"{channel}.json ist keine Testvorlage")
        check(isinstance(data.get("sequence"), int) and data["sequence"] >= 1,
              f"{channel}.json hat eine gueltige sequence")
        check(not list(v.iter_errors(data)), f"{channel}.json entspricht dem Schema")
        if data.get("enabled"):
            check_released_channel(channel, data, tool)
        else:
            check_disabled_channel(channel, data)

    wrapper = TESTS / "test_v800_selfupdate_smoke.py"
    if sys.platform != "win32":
        result = subprocess.run([sys.executable, str(wrapper)], cwd=ROOT, capture_output=True,
                                text=True, check=False)
        check(result.returncode == 77 and "SKIP" in result.stdout,
              "Windows-Selbst-Update-Wrapper ueberspringt auf diesem Host mit Exit 77")

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} Manifest-Pruefung(en).")
        return 1
    print("\nOK: Schema 2, Vorlagen, Kanalzustand und die Windows-Ueberspringung sind in Ordnung.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
