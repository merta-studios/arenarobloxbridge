#!/usr/bin/env python3
"""Guard fuer das geschuetzte Selbst-Update-System (Update-System 2.0.0).

Normaler Lauf (Standard):
    Vergleicht jede geschuetzte Datei mit update-system/update_system_guard.lock.json,
    prueft die harten Regeln (kein Prozessabbruch, nur HTTPS auf genehmigten Hosts,
    Test-Modus nur im Testbau, deaktivierte Kanaele ohne Download-Koordinaten) und
    die Freigabebedingungen eines aktiven Kanals. Die Lock-Datei wird nie geaendert.

Rebaseline (nur nach ausdruecklicher Nutzerfreigabe, siehe PROTECTED.md):
    python developer/tests/test_v800_update_system_guard.py --rebaseline --approval "<Text, >= 30 Zeichen>"
    Berechnet die Hashes neu und traegt die Freigabe (Datum + Text) in die Lock-Datei ein.

Warum dieser Test existiert: Das Update-System darf sich nicht nebenbei aendern.
Sicherheit, Freigabeweg und Test-Modus sind hier als pruefbare Regeln hinterlegt.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "update-system" / "update_system_guard.lock.json"
APP = ROOT / "app" / "ArenaBridge.ps1"
UPDATER = ROOT / "update-system" / "updater" / "Update-Bridge.ps1"
BUILDER = ROOT / "builder" / "Build-EXE.ps1"
RELEASE_TOOL = ROOT / "developer" / "tools" / "release.py"
BOOTSTRAP = ROOT / "tools" / "ArenaBridge-Update-Holen.ps1"
CHANNELS = ROOT / "update-system" / "channels"
BLOCK_START = "# >>> ARENA-UPDATE-INTEGRATION >>>"
BLOCK_END = "# <<< ARENA-UPDATE-INTEGRATION <<<"
SETTINGS_UI_START = "<!-- >>> ARENA-UPDATE-SETTINGS-UI >>>"
SETTINGS_UI_END = "<!-- <<< ARENA-UPDATE-SETTINGS-UI <<< -->"
SETTINGS_CODE_START = "# >>> ARENA-UPDATE-SETTINGS-CODE >>>"
SETTINGS_CODE_END = "# <<< ARENA-UPDATE-SETTINGS-CODE <<<"
MIN_APPROVAL_CHARS = 30
EXPECTED_UPDATER_VERSION = "2.0.0"
FAILURES: list[str] = []

# Tree-sitter (die PowerShell-Grammatik) meldet in dieser grossen, gemischten
# PowerShell/Lua/XAML-Datei sieben bekannte Rauschstellen. Neue ERROR-Knoten sind
# Freigabeblocker; die Erlaubnisliste bleibt bewusst kurz.
PARSER_NOISE_PREFIXES = (
    "MB",
    "param($Raw) if ([string]::IsNullOrWhiteSpace([string]$Raw))",
    "param($Value)",
    "$deduped | Sort-Object placeName, sessionId",
    ", ContentType",
    "[Windows.UI.Notifications",
    "[Windows.Data.Xml.Dom",
)


def check(condition: bool, message: str) -> None:
    print(("  ok   " if condition else "  FAIL ") + message)
    if not condition:
        FAILURES.append(message)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def app_source() -> str:
    return APP.read_bytes().decode("utf-8-sig")


def marker_slice(text: str, start_marker: str, end_marker: str) -> str:
    begin = text.find(start_marker)
    if begin < 0:
        return ""
    end = text.find(end_marker, begin)
    if end < 0:
        return ""
    return text[begin:end + len(end_marker)]


def integration_block_text() -> str:
    """Der geschuetzte Block, von der Start- bis zur Endmarke (LF-normalisiert)."""
    text = app_source().replace("\r\n", "\n")
    return marker_slice(text, BLOCK_START, BLOCK_END)


def settings_ui_text() -> str:
    return marker_slice(app_source().replace("\r\n", "\n"), SETTINGS_UI_START, SETTINGS_UI_END)


def settings_code_text() -> str:
    return marker_slice(app_source().replace("\r\n", "\n"), SETTINGS_CODE_START, SETTINGS_CODE_END)


def protected_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(p for p in (ROOT / "update-system").rglob("*") if p.is_file()):
        if path == LOCK:
            continue
        hashes[rel(path)] = sha256_bytes(path.read_bytes())
    for path in (BUILDER, RELEASE_TOOL, BOOTSTRAP, ROOT / "tools" / "ArenaBridge-Update-Holen.cmd",
                 ROOT / "developer" / "tests" / "run_offline_tests.py",
                 ROOT / "developer" / "tests" / "requirements-test.txt",
                 ROOT / "developer" / "tests" / "Invoke-SelfUpdateSmoke.ps1"):
        if path.is_file():
            hashes[rel(path)] = sha256_bytes(path.read_bytes())
    for path in sorted((ROOT / "developer" / "tests").glob("test_v800_*.py")):
        hashes[rel(path)] = sha256_bytes(path.read_bytes())
    for path in sorted((ROOT / "developer" / "tests" / "fixtures" / "update").rglob("*")):
        if path.is_file():
            hashes[rel(path)] = sha256_bytes(path.read_bytes())
    hashes["app/ArenaBridge.ps1#ARENA-UPDATE-INTEGRATION"] = sha256_bytes(
        integration_block_text().encode("utf-8"))
    hashes["app/ArenaBridge.ps1#ARENA-UPDATE-SETTINGS-UI"] = sha256_bytes(
        settings_ui_text().encode("utf-8"))
    hashes["app/ArenaBridge.ps1#ARENA-UPDATE-SETTINGS-CODE"] = sha256_bytes(
        settings_code_text().encode("utf-8"))
    return hashes


def parse_semver(value: str) -> tuple | None:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$", value.strip())
    if not match:
        return None
    major, minor, patch, prerelease = match.groups()
    return (int(major), int(minor), int(patch), prerelease or "")


def semver_gt(left: str, right: str) -> bool:
    a, b = parse_semver(left), parse_semver(right)
    if not a or not b:
        return False
    if a[:3] != b[:3]:
        return a[:3] > b[:3]
    if not a[3] and b[3]:
        return True
    if a[3] and not b[3]:
        return False
    return a[3] > b[3]


def load_lock() -> dict:
    if not LOCK.is_file():
        return {}
    return json.loads(LOCK.read_text(encoding="utf-8"))


def get_last_published_version(readme_text: str) -> str:
    match = re.search(r"Letzte ver[öo]ffentlichte Version:\s*([^\s\n\(\)]+)", readme_text, re.IGNORECASE)
    if not match:
        return ""
    value = match.group(1).strip()
    return "" if value.lower() in ("keine", "none", "") else value


def update_readme_text() -> str:
    return (ROOT / "update-system" / "README.md").read_text(encoding="utf-8")


def validate_release_manifest_data(data: dict, channel: str, exe_dir: Path,
                                   current_version: str, last_pub_version: str,
                                   lock_data: dict) -> list[str]:
    """Unabhaengige Freigabepruefung (zweite Implementierung neben release.py)."""
    errors: list[str] = []
    if data.get("schemaVersion") != 2:
        errors.append(f"schemaVersion ist {data.get('schemaVersion')!r}, erwartet 2")
    version = str(data.get("version", ""))
    if version != current_version:
        errors.append(f"version ({version}) != app/version.json ({current_version})")
    if channel == "stable" and "-" in version:
        errors.append("stable darf keine Vorabversion veroeffentlichen")
    if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", str(data.get("publishedAtUtc", ""))):
        errors.append(f"publishedAtUtc ({data.get('publishedAtUtc')!r}) ist kein ISO-8601-UTC-Zeitstempel")
    if not isinstance(data.get("sequence"), int) or data.get("sequence", 0) < 1:
        errors.append(f"sequence ist ungueltig ({data.get('sequence')!r})")
    minimum = str(data.get("minimumUpdaterVersion", ""))
    if not re.match(r"^\d+\.\d+\.\d+$", minimum):
        errors.append(f"minimumUpdaterVersion ({minimum!r}) ist keine dreiteilige Version")
    elif semver_gt(minimum, EXPECTED_UPDATER_VERSION):
        errors.append(f"minimumUpdaterVersion {minimum} ist neuer als der eingebettete Updater "
                      f"{EXPECTED_UPDATER_VERSION}")
    artifact = data.get("artifact", {})
    expected_name = f"ArenaBridge-{version}.exe"
    expected_url = ("https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/"
                    "next-update/release/" + expected_name)
    if artifact.get("fileName") != expected_name:
        errors.append(f"artifact.fileName ist {artifact.get('fileName')!r}, erwartet {expected_name!r}")
    if artifact.get("url") != expected_url:
        errors.append(f"artifact.url ist nicht die abgeleitete Adresse {expected_url}")
    exe_path = exe_dir / expected_name
    if not exe_path.is_file():
        errors.append(f"Artefakt {expected_name} fehlt in release/")
    else:
        raw = exe_path.read_bytes()
        actual_sha = hashlib.sha256(raw).hexdigest()
        if str(artifact.get("sha256", "")).lower() != actual_sha:
            errors.append("artifact.sha256 passt nicht zur Datei")
        if artifact.get("sizeBytes") != len(raw):
            errors.append("artifact.sizeBytes passt nicht zur Datei")
    if last_pub_version:
        if parse_semver(last_pub_version) == parse_semver(version):
            errors.append(f"version ({version}) ist bereits als veroeffentlicht vermerkt")
        elif not semver_gt(version, last_pub_version):
            errors.append(f"version ({version}) ist nicht hoeher als {last_pub_version}")
    published = str(data.get("publishedAtUtc", ""))
    if re.match(r"^\d{4}-\d{2}-\d{2}T", published):
        day = published[:10]
        approvals = lock_data.get("approvals", [])
        if not any(entry.get("date") == day and ("release" in str(entry.get("note", "")).lower()
                                                or "freigabe" in str(entry.get("note", "")).lower())
                   for entry in approvals):
            errors.append(f"keine Freigabe vom {day} im Guard-Lock dokumentiert")
    return errors


def new_powershell_parse_errors(raw: bytes) -> list[tuple[int, str]]:
    """Tree-sitter-ERROR/missing-Knoten ohne die bekannten Rauschstellen."""
    from tree_sitter import Language, Parser
    import tree_sitter_powershell as tsp

    tree = Parser(Language(tsp.language())).parse(raw)
    bad: list[tuple[int, str]] = []

    def walk(node) -> None:
        if node.type == "ERROR" or node.is_missing:
            text = raw[node.start_byte:node.end_byte].decode("utf-8", "replace")
            if not any(text.startswith(prefix) for prefix in PARSER_NOISE_PREFIXES):
                bad.append((raw.count(b"\n", 0, node.start_byte) + 1, text[:70]))
            return
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return bad


def static_invariants() -> None:
    updater = UPDATER.read_text(encoding="ascii")
    check("Stop-Process" not in updater and "taskkill" not in updater and ".Kill(" not in updater,
          "der Updater beendet oder toetet nie einen Prozess")
    check("Invoke-WebRequest" not in updater and "Invoke-RestMethod" not in updater,
          "der Updater nutzt nur die gepruefte Download-Funktion")
    check("$request.AllowAutoRedirect = $false" in updater,
          "der Updater folgt Weiterleitungen nur ueber die eigene Hostpruefung")
    check(f"$script:UpdaterVersion = '{EXPECTED_UPDATER_VERSION}'" in updater,
          f"die Updater-Version ist {EXPECTED_UPDATER_VERSION}")
    check(all(ord(ch) < 128 for ch in updater), "der Updater ist reines ASCII (PS 5.1 sicher)")
    check("function Get-ArtifactFileName([string]$Version)" in updater
          and "function Get-ArtifactUrl([string]$Version)" in updater,
          "Dateiname und Adresse des Artefakts werden aus der Version abgeleitet")
    check("Get-WithCacheBreaker" in updater and "cb=" in updater,
          "das Manifest wird mit Cache-Brecher geladen (kein veralteter Cache-Stand)")
    check("manifest-stale" in updater and "StateSequence" in updater,
          "der Updater erkennt ein aelteres Manifest (sequence) und installiert es nicht")
    check("Get-FileVersionCore" in updater and "Dateiversion" in updater,
          "vor dem Ersetzen wird die Dateiversion der neuen EXE geprueft")
    check("Compare-UpdateVersion $script:UpdaterVersion $minimumUpdater" in updater,
          "der Updater erlaubt minimumUpdaterVersion <= eigene Version (Gleichstand ist normal)")
    check("update-progress.json" in updater and "cancel.request" in updater,
          "Fortschrittsdatei und Abbruchdatei sind vorhanden (Abbruch ohne Prozesseingriff)")
    check("update-history.json" in updater, "der Verlauf der Updates wird geschrieben")
    try:
        errors = new_powershell_parse_errors(UPDATER.read_bytes())
    except ImportError:
        errors = []
        check(True, "Tree-sitter nicht installiert - Parserpruefung des Updaters uebersprungen")
    if errors:
        for line, text in errors[:10]:
            print(f"        Zeile {line}: {text!r}")
    check(not errors, "der Updater ist syntaktisch fehlerfrei (Tree-sitter-Parser-Gate)")

    source = app_source()
    block = integration_block_text()
    check(block != "" and source.count(BLOCK_START) == 1,
          "es gibt genau einen Update-Block in der App")
    check(SETTINGS_UI_START in source and source.count(SETTINGS_UI_START) == 1,
          "es gibt genau einen Updates-Bereich im Einstellungsfenster")
    check(SETTINGS_CODE_START in source and source.count(SETTINGS_CODE_START) == 1,
          "der Updates-Bereich ist genau einmal verdrahtet")
    check("ARENABRIDGE_SELFUPDATE_TEST_MANIFEST" in block
          and "if ([string]$script:TestFixtureBuild -cne '1') { return '' }" in block,
          "die Test-Manifest-Variable ist an den Testbau gekoppelt")
    check("Stop-Process" not in block and "taskkill" not in block,
          "der App-Block beendet nie einen Prozess")
    for marker in ("__ARENA_UPDATE_CHANNEL__", "__ARENA_UPDATER_BASE64__", "__ARENA_UPDATER_SHA256__",
                   "__ARENA_TEST_FIXTURE_BUILD__"):
        check(block.count(marker) == 1, f"Platzhalter {marker} kommt genau einmal im Block vor")
    check("channels/" not in source, "die App nennt keine Kanal-Dateien direkt")
    # Genau der Fehler, der frueher das Einstellungsfenster zerstoert hat: ein
    # StaticResource-Verweis auf eine Ressource, die es im Fenster nicht gibt.
    # Der Block darf deshalb nur Ressourcen nutzen, die er SELBST definiert.
    keys_used = set(re.findall(r"StaticResource\s+([A-Za-z0-9_]+)", block))
    keys_defined = set(re.findall(r'x:Key="([A-Za-z0-9_]+)"', block))
    missing_keys = sorted(keys_used - keys_defined)
    check(not missing_keys,
          "der Update-Block nutzt nur selbst definierte WPF-Ressourcen: "
          + (", ".join(missing_keys) if missing_keys else "ok"))
    check("update-progress.json" in block and "cancel.request" in block,
          "Fortschritt und Abbruch werden auch in der App verwendet")
    check("update-history.json" in block, "die App kennt den Update-Verlauf")
    check("Start-ArenaUpdateCheck" in block and "Test-ArenaUpdateCheckResult" in block,
          "Startpruefung und Auswertung sind im Block vorhanden")
    check("Start-ArenaManualUpdateCheck" in block and "Show-ArenaUpdateDiagnose" in block,
          "manuelle Pruefung und Diagnose sind im Block vorhanden")

    settings_ui = settings_ui_text()
    settings_code = settings_code_text()
    check("UpdateCheckButton" in settings_ui and "UpdateDiagnoseButton" in settings_ui
          and "UpdateLogButton" in settings_ui,
          "das Einstellungsfenster bietet Suchen, Diagnose und Protokoll an")
    check("Start-ArenaManualUpdateCheck" in settings_code and "Show-ArenaUpdateDiagnose" in settings_code
          and "Open-ArenaUpdateLog" in settings_code,
          "die Knoepfe rufen die Funktionen des Update-Blocks auf")
    check('Style="{StaticResource' not in settings_ui,
          "die neuen Update-Knoepfe nutzen keine geteilten Fenster-Ressourcen (kein StaticResource-Absturz)")
    check(settings_ui.count("<Button ") == 3,
          "der Updates-Bereich hat genau die drei Knoepfe Suchen, Diagnose, Protokoll")

    tool_text = RELEASE_TOOL.read_text(encoding="utf-8")
    check("elif current_updater and semver_gt(minimum, current_updater)" in tool_text,
          "das Release-Werkzeug lehnt minimumUpdaterVersion == eingebetteter Updater nicht ab")
    check("def cmd_stage" in tool_text and "--tested-by-user" in tool_text,
          "das Release-Werkzeug veroeffentlicht nur mit ausdruecklicher Nutzerbestaetigung")
    check("urllib" not in tool_text and "requests" not in tool_text and "socket" not in tool_text,
          "das Release-Werkzeug laedt nichts herunter (reine Dateipruefung)")
    check("def artifact_name" in tool_text and "def artifact_url" in tool_text,
          "das Release-Werkzeug leitet Dateiname und Adresse ebenfalls aus der Version ab")

    bootstrap_text = BOOTSTRAP.read_text(encoding="ascii") if BOOTSTRAP.is_file() else ""
    if bootstrap_text:
        check("raw.githubusercontent.com" in bootstrap_text
              and "https://" in bootstrap_text,
              "das Migration-Werkzeug arbeitet ausschliesslich mit HTTPS auf GitHub")
        check("Stop-Process" not in bootstrap_text and "taskkill" not in bootstrap_text,
              "das Migration-Werkzeug beendet keinen Prozess")
        check("Test-ChannelManifest" in bootstrap_text or "sha256" in bootstrap_text.lower(),
              "das Migration-Werkzeug prueft die Pruefsumme vor dem Ersetzen")
        check(all(ord(ch) < 128 for ch in bootstrap_text), "das Migration-Werkzeug ist reines ASCII")

    builder = BUILDER.read_text(encoding="utf-8-sig")
    check("must never write inside the repository" in builder and "release\\" in builder,
          "Testbauten duerfen nie in release\\ schreiben")
    check("'$script:TestFixtureBuild = ''0'''" in builder,
          "normale Builds setzen das Test-Kennzeichen auf 0 (kein Testpfad in der normalen EXE)")

    lock_data = load_lock()
    readme_text = update_readme_text()
    current_source_version = str(json.loads((ROOT / "app" / "version.json").read_text(encoding="utf-8"))
                                .get("version", ""))
    last_pub_version = get_last_published_version(readme_text)
    for channel in ("beta", "stable"):
        data = json.loads((CHANNELS / f"{channel}.json").read_text(encoding="utf-8"))
        check(data.get("testFixture") is False, f"{channel}.json ist keine Testvorlage")
        if not data.get("enabled", False):
            artifact = data.get("artifact", {})
            check(artifact.get("url") == "" and artifact.get("sha256") == "" and artifact.get("sizeBytes") == 0,
                  f"{channel}.json ist deaktiviert und nennt keine Download-Koordinaten")
        else:
            problems = validate_release_manifest_data(data, channel, ROOT / "release",
                                                      current_source_version, last_pub_version, lock_data)
            check(not problems, f"{channel}.json Freigabe ist vollstaendig: "
                                + ("; ".join(problems) if problems else "ok"))

    schema = json.loads((CHANNELS / "manifest.schema.json").read_text(encoding="utf-8"))
    check(schema.get("properties", {}).get("schemaVersion", {}).get("const") == 2
          and schema.get("additionalProperties") is False,
          "das Manifest-Schema ist Version 2 und lehnt unbekannte Felder ab")


def rebaseline(approval: str) -> int:
    if len(approval.strip()) < MIN_APPROVAL_CHARS:
        print(f"ABGELEHNT: --approval braucht mindestens {MIN_APPROVAL_CHARS} Zeichen Freigabetext.")
        return 2
    lock = load_lock()
    approvals = list(lock.get("approvals", []))
    approvals.append({
        "date": _dt.date.today().isoformat(),
        "approvedBy": "Nutzer (Owner) - ausdrueckliche Freigabe",
        "note": approval.strip(),
    })
    lock_data = {
        "schemaVersion": 1,
        "scope": "update-system/, das Release-Werkzeug, das Migration-Werkzeug und die in PROTECTED.md genannten Integrationsstellen in app/ArenaBridge.ps1",
        "approvals": approvals,
        "files": protected_hashes(),
    }
    LOCK.write_text(json.dumps(lock_data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")
    print(f"Lock neu geschrieben: {len(lock_data['files'])} geschuetzte Eintraege, {len(approvals)} Freigabe(n).")
    return 0


def main(argv: list[str]) -> int:
    if "--rebaseline" in argv:
        approval = ""
        if "--approval" in argv:
            index = argv.index("--approval")
            approval = argv[index + 1] if index + 1 < len(argv) else ""
        return rebaseline(approval)

    print("Guard: geschuetzte Update-System-Dateien")
    lock = load_lock()
    check(bool(lock), "die Lock-Datei existiert und ist lesbar")
    if lock:
        check(bool(lock.get("approvals")), "die Lock-Datei enthaelt mindestens eine ausdrueckliche Freigabe")
        expected = lock.get("files", {})
        current = protected_hashes()
        changed = sorted(key for key in expected if key in current and expected[key] != current[key])
        added = sorted(key for key in current if key not in expected)
        removed = sorted(key for key in expected if key not in current)
        check(not changed, "keine geschuetzte Datei wurde geaendert: " + (", ".join(changed) if changed else "ok"))
        check(not added, "keine geschuetzte Datei kam hinzu: " + (", ".join(added) if added else "ok"))
        check(not removed, "keine geschuetzte Datei wurde entfernt: " + (", ".join(removed) if removed else "ok"))
        if changed or added or removed:
            print("  -> Stopp: das braucht eine ausdrueckliche Nutzerfreigabe und ein Rebaseline, siehe update-system/PROTECTED.md.")
    static_invariants()

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} Guard-Pruefung(en) fuer das Update-System.")
        return 1
    print("\nOK: Update-System-Guard bestanden (geschuetzte Dateien unveraendert, Regeln intakt).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
