#!/usr/bin/env python3
"""Release-Werkzeug fuer das neue Update-System (next-update).

Ein Befehl statt Handarbeit. Dieses Werkzeug ist die einzige erlaubte Art,
einen Kanal in ``update-system/channels/`` zu aktivieren, und es prueft dabei
alles, was sich frueher still widersprechen konnte:

  * ``app/version.json`` == Version der getesteten EXE (PE-Dateiversion),
  * ``release/ArenaBridge.exe`` ist eine x64-Windows-EXE mit passender Version,
  * Dateiname und URL des Artefakts sind aus der Version abgeleitet
    (``release/ArenaBridge-<version>.exe``) und damit unveraenderlich,
  * SHA-256 und Groesse im Manifest sind exakt die Werte der Datei,
  * ``sequence`` ist echt groesser als die der letzten Veroeffentlichung,
  * die Freigabe des Nutzers ist ausdruecklich bestaetigt und wird im
    Guard-Lock dokumentiert (Rebaseline).

Befehle
-------
  status                 Gesamtstand + naechste sinnvolle Schritte (Release-Doctor)
  check                  Nur pruefen, Exit 1 bei Widerspruch (fuer CI/Test)
  stage                  Release vorbereiten: Artefakt kopieren, Manifest setzen,
                         README fortschreiben, Guard-Lock neu baseline'n
  disable --channel X    Kanal wieder auf den deaktivierten Platzhalter setzen
  prune --keep N         Alte, nicht mehr referenzierte Versionsdateien entfernen

Beispiele
---------
  python developer/tools/release.py status
  python developer/tools/release.py stage --version 7.8.0 --channel stable \
      --tested-by-user --smoke-test-passed
  python developer/tools/release.py disable --channel stable
  python developer/tools/release.py prune --keep 2

Das Werkzeug benoetigt nur die Python-Standardbibliothek. Es aendert NIE
Quellcode, niemals ``release/ArenaBridge.exe`` und niemals eine EXE.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = ROOT / "app" / "version.json"
RELEASE_DIR = ROOT / "release"
SOURCE_EXE = RELEASE_DIR / "ArenaBridge.exe"
CHANNEL_DIR = ROOT / "update-system" / "channels"
UPDATER = ROOT / "update-system" / "updater" / "Update-Bridge.ps1"
UPDATE_README = ROOT / "update-system" / "README.md"
LOCK_FILE = ROOT / "update-system" / "update_system_guard.lock.json"
GUARD_TEST = ROOT / "developer" / "tests" / "test_v800_update_system_guard.py"
RELEASE_URL_BASE = ("https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/"
                    "main/next-update/release/")
CHANNELS = ("beta", "stable")
MAX_ARTIFACT_BYTES = 67108864
MIN_ARTIFACT_BYTES = 1024
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?$")
CORE_RE = re.compile(r"^(\d+\.\d+\.\d+)")
STAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
LAST_RELEASE_RE = re.compile(
    r"^Letzte ver[öo]ffentlichte Version:\s*(?P<version>[^\s(]+)\s*(?:\((?P<detail>[^)]*)\))?\s*$",
    re.IGNORECASE | re.MULTILINE)
TABLE_HEADER = "| Version | Datum (UTC) | Kanal | Sequence | Artefakt |"


# --------------------------------------------------------------------------- Hilfen
def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_name(version: str) -> str:
    return f"ArenaBridge-{version}.exe"


def artifact_url(version: str) -> str:
    return RELEASE_URL_BASE + artifact_name(version)


def core_version(version: str) -> str:
    match = CORE_RE.match(version)
    return match.group(1) if match else ""


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


def app_version() -> str:
    return str(read_json(VERSION_FILE).get("version", "")).strip()


def updater_version() -> str:
    match = re.search(r"^\$script:UpdaterVersion = '([^']+)'", UPDATER.read_text(encoding="ascii"),
                      re.MULTILINE)
    return match.group(1) if match else ""


def versioned_artifacts() -> list[Path]:
    found = []
    for path in sorted(RELEASE_DIR.glob("ArenaBridge-*.exe")):
        stem = path.name[len("ArenaBridge-"):-len(".exe")]
        if VERSION_RE.match(stem):
            found.append(path)
    return found


# ------------------------------------------------------------------ EXE-Pruefungen
def exe_embedded_version_strings(path: Path) -> set[str]:
    """Versionen, die als Text im EXE-Kopf stehen (UTF-16LE und ASCII)."""
    raw = path.read_bytes()[:4 * 1024 * 1024]
    found: set[str] = set()
    for candidate in re.findall(rb"\x00\d[\x00.](?:\x00\d[\x00.]){3}", raw):
        text = candidate.decode("utf-16le", "replace")
        if re.match(r"^\d+\.\d+\.\d+\.\d+$", text):
            found.add(text)
    return found


def exe_is_windows_x64(path: Path, header: bytes | None = None) -> bool:
    raw = header if header is not None else path.read_bytes()[:4096]
    if len(raw) < 256 or raw[0:2] != b"MZ":
        return False
    offset = int.from_bytes(raw[0x3C:0x40], "little")
    if offset <= 0 or offset + 6 > len(raw) or raw[offset:offset + 4] != b"PE\x00\x00":
        return False
    return int.from_bytes(raw[offset + 4:offset + 6], "little") == 0x8664


def exe_file_version(path: Path) -> tuple[str, str]:
    """(Dateiversion, Quelle). Quelle ist 'pefile' oder 'textsuche'."""
    try:
        import pefile  # type: ignore

        pe = pefile.PE(str(path), fast_load=True)
        try:
            pe.parse_data_directories(
                directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]])
            for group in pe.FileInfo or []:
                for entry in group:
                    if getattr(entry, "StringTable", None):
                        for table in entry.StringTable:
                            value = table.entries.get(b"FileVersion")
                            if value:
                                return value.decode("ascii", "replace").strip(), "pefile"
        finally:
            pe.close()
    except Exception:
        pass
    raw = path.read_bytes()
    candidates = [text for text in exe_embedded_version_strings(path)
                  if re.match(r"^\d+\.\d+\.\d+\.0$", text)]
    if len(candidates) == 1:
        return candidates[0], "textsuche"
    if candidates:
        return sorted(candidates)[-1], "textsuche"
    return "", "keine"


def validate_exe(path: Path, expected_version: str) -> list[str]:
    problems: list[str] = []
    if not path.is_file():
        return [f"Datei fehlt: {path}"]
    size = path.stat().st_size
    if size < MIN_ARTIFACT_BYTES or size > MAX_ARTIFACT_BYTES:
        problems.append(f"Groesse ausserhalb des Limits: {size}")
    if not exe_is_windows_x64(path):
        problems.append("keine Windows-x64-EXE (PE-Kopf falsch)")
    version, source = exe_file_version(path)
    want_core = core_version(expected_version)
    if not version:
        problems.append("keine Dateiversion im EXE-Kopf gefunden")
    else:
        got_core = core_version(version)
        if got_core != want_core:
            problems.append(f"Dateiversion {version} (Quelle {source}) passt nicht zu {expected_version}")
    return problems


# ------------------------------------------------------------------ Kanal-Pruefungen
def validate_channel(data: dict, channel: str, *, exe_path: Path | None = None,
                     require_enabled: bool | None = None) -> list[str]:
    problems: list[str] = []
    if data.get("schemaVersion") != 2:
        problems.append(f"schemaVersion ist {data.get('schemaVersion')!r}, erwartet 2")
    if data.get("channel") != channel:
        problems.append(f"channel ist {data.get('channel')!r}, erwartet {channel!r}")
    if not isinstance(data.get("enabled"), bool):
        problems.append("enabled muss true/false sein")
    if data.get("testFixture") is not False:
        problems.append("testFixture muss in der Repository-Datei false sein")
    sequence = data.get("sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or not 1 <= sequence <= 999999999:
        problems.append(f"sequence ungueltig: {sequence!r}")
    artifact = data.get("artifact") or {}
    if not isinstance(artifact, dict):
        problems.append("artifact fehlt")
        return problems
    if data.get("enabled") is False:
        if artifact.get("url") != "" or artifact.get("sha256") != "" or artifact.get("sizeBytes") != 0:
            problems.append("deaktivierter Kanal darf keine Artefakt-Koordinaten nennen")
        if str(data.get("version", "")) != "" or str(data.get("publishedAtUtc", "")) != "":
            problems.append("deaktivierter Kanal muss version/publishedAtUtc leer lassen")
        if require_enabled:
            problems.append("Kanal ist deaktiviert, aber als aktiv erwartet")
        return problems
    if require_enabled is False:
        problems.append("Kanal ist aktiviert, aber als deaktiviert erwartet")

    version = str(data.get("version", ""))
    if not VERSION_RE.match(version):
        problems.append(f"version ungueltig: {version!r}")
        return problems
    if channel == "stable" and "-" in version:
        problems.append("stable darf keine Vorabversion veroeffentlichen")
    if not STAMP_RE.match(str(data.get("publishedAtUtc", ""))):
        problems.append(f"publishedAtUtc ist kein ISO-8601-UTC-Zeitstempel: {data.get('publishedAtUtc')!r}")
    minimum = str(data.get("minimumUpdaterVersion", ""))
    current_updater = updater_version()
    if not VERSION_RE.match(minimum):
        problems.append(f"minimumUpdaterVersion ungueltig: {minimum!r}")
    elif current_updater and semver_gt(minimum, current_updater):
        # Gleichstand ist der Normalfall (der eingebettete Updater erfuellt die
        # Mindestanforderung selbst); nur eine echt neuere Anforderung ist ein Fehler.
        problems.append(f"minimumUpdaterVersion {minimum} ist neuer als der eingebettete Updater {current_updater}")
    expected_name = artifact_name(version)
    if artifact.get("fileName") != expected_name:
        problems.append(f"artifact.fileName ist {artifact.get('fileName')!r}, erwartet {expected_name!r}")
    expected_url = artifact_url(version)
    if artifact.get("url") != expected_url:
        problems.append(f"artifact.url ist {artifact.get('url')!r}, erwartet {expected_url!r}")
    if not re.match(r"^[0-9a-f]{64}$", str(artifact.get("sha256", "")).lower()):
        problems.append("artifact.sha256 ist keine 64-stellige Hexadezimalzahl")
    size = artifact.get("sizeBytes")
    if not isinstance(size, int) or isinstance(size, bool) or not MIN_ARTIFACT_BYTES <= size <= MAX_ARTIFACT_BYTES:
        problems.append(f"artifact.sizeBytes ungueltig: {size!r}")
    notes = data.get("notes")
    if not isinstance(notes, list) or not notes:
        problems.append("notes muss eine nicht leere Liste sein")
    else:
        for index, item in enumerate(notes):
            if not isinstance(item, str) or not item.strip():
                problems.append(f"notes[{index}] ist leer")
            elif len(item) > 800:
                problems.append(f"notes[{index}] ist laenger als 800 Zeichen ({len(item)})")

    if exe_path is not None:
        if not exe_path.is_file():
            problems.append(f"Artefakt fehlt: {exe_path.relative_to(ROOT)}")
        else:
            if sha256_file(exe_path) != str(artifact.get("sha256", "")).lower():
                problems.append("artifact.sha256 passt nicht zur Datei")
            if exe_path.stat().st_size != size:
                problems.append("artifact.sizeBytes passt nicht zur Datei")
            problems.extend(validate_exe(exe_path, version))
    return problems


def last_release(readme_text: str) -> tuple[str, str]:
    match = LAST_RELEASE_RE.search(readme_text)
    if not match:
        return "", ""
    value = match.group("version").strip()
    if value.lower() in ("keine", "none", ""):
        return "", match.group(0)
    return value, match.group(0)


def readme_rows() -> list[list[str]]:
    """Zellen der Veroeffentlichungstabelle aus update-system/README.md."""
    if not UPDATE_README.is_file():
        return []
    rows: list[list[str]] = []
    in_table = False
    for line in UPDATE_README.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("| Version |"):
            in_table = True
            continue
        if not in_table:
            continue
        if not stripped.startswith("|"):
            break
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        rows.append(cells)
    return rows


def release_sequences() -> dict[str, int]:
    """Hoechste jemals veroeffentlichte sequence je Kanal (README-Tabelle und Kanal-Datei)."""
    result = {channel: 0 for channel in CHANNELS}
    for cells in readme_rows():
        if len(cells) < 4:
            continue
        channel = cells[2]
        if channel in result and cells[3].isdigit():
            result[channel] = max(result[channel], int(cells[3]))
    for channel in CHANNELS:
        data = read_json(CHANNEL_DIR / f"{channel}.json")
        if data.get("enabled"):
            result[channel] = max(result[channel], int(data.get("sequence", 0)))
    return result


def channel_artifact(data: dict) -> Path | None:
    name = str((data.get("artifact") or {}).get("fileName", ""))
    if not VERSION_RE.match(str(data.get("version", ""))) or not name.endswith(".exe"):
        return None
    if name == "ArenaBridge.exe":
        return None
    return RELEASE_DIR / name


# ------------------------------------------------------------------------- Befehle
def collect_status() -> dict:
    source_version, _ = last_release(UPDATE_README.read_text(encoding="utf-8") if UPDATE_README.is_file() else "")  # letzte Veroeffentlichung
    channels = {}
    for channel in CHANNELS:
        data = read_json(CHANNEL_DIR / f"{channel}.json")
        exe = channel_artifact(data)
        channels[channel] = {
            "enabled": bool(data.get("enabled")),
            "version": str(data.get("version", "")),
            "sequence": int(data.get("sequence", 0)),
            "artifact": str(exe.relative_to(ROOT)) if exe else "",
            "problems": validate_channel(data, channel, exe_path=exe),
        }
    staged = None
    if SOURCE_EXE.is_file():
        version, source = exe_file_version(SOURCE_EXE)
        staged = {
            "path": str(SOURCE_EXE.relative_to(ROOT)),
            "sizeBytes": SOURCE_EXE.stat().st_size,
            "sha256": sha256_file(SOURCE_EXE),
            "fileVersion": version,
            "fileVersionSource": source,
            "problems": validate_exe(SOURCE_EXE, app_version()),
        }
    return {
        "appVersion": app_version(),
        "updaterVersion": updater_version(),
        "lastPublishedVersion": source_version,
        "releaseSequences": release_sequences(),
        "testBuild": staged,
        "channels": channels,
        "versionedArtifacts": [path.name for path in versioned_artifacts()],
    }


def cmd_status(args: argparse.Namespace) -> int:
    status = collect_status()
    if args.json:
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return 0
    print("Arena Roblox Bridge - Release-Status")
    print(f"  Quellversion (app/version.json): {status['appVersion']}")
    print(f"  Eingebetteter Updater:           {status['updaterVersion']}")
    print(f"  Letzte Veroeffentlichung:        {status['lastPublishedVersion'] or '(keine)'}")
    print(f"  Veroeffentlichte Dateien:        {', '.join(status['versionedArtifacts']) or '(keine)'}")
    print("")
    print("  Lokaler Test-Build (release/ArenaBridge.exe):")
    test = status["testBuild"]
    if not test:
        print("    fehlt - erst Build-EXE.bat ausfuehren.")
    else:
        print(f"    Dateiversion: {test['fileVersion'] or '(unbekannt)'} (Quelle: {test['fileVersionSource']})")
        print(f"    Groesse:      {test['sizeBytes']} Bytes")
        print(f"    SHA-256:      {test['sha256']}")
        for problem in test["problems"]:
            print(f"    PROBLEM:      {problem}")
    print("")
    for channel, info in status["channels"].items():
        state = "AKTIV" if info["enabled"] else "deaktiviert"
        print(f"  Kanal {channel}: {state}"
              + (f" -> {info['version']} (sequence {info['sequence']}, {info['artifact']})" if info["enabled"] else ""))
        for problem in info["problems"]:
            print(f"    PROBLEM:      {problem}")
    print("")
    print("  Naechste Schritte fuer eine Veroeffentlichung:")
    if not test:
        print("    1. next-update/Build-EXE.bat ausfuehren (baut release/ArenaBridge.exe, Kanal stable).")
        print("    2. EXE privat starten und testen, danach mit developer/tests/Invoke-SelfUpdateSmoke.ps1 pruefen.")
        print("    3. Getestete EXE ins Repository nach next-update/release/ArenaBridge.exe hochladen.")
        print("    4. In der Release-Session: python developer/tools/release.py stage --version <version> --tested-by-user")
    elif test["problems"]:
        print("    Der Test-Build passt noch nicht zur Quellversion. Erst neu bauen (Build-EXE.bat),")
        print("    dann die getestete EXE nach next-update/release/ArenaBridge.exe hochladen.")
    else:
        version = core_version(test["fileVersion"]) or status["appVersion"]
        print(f"    Getestete EXE gefunden. Veroeffentlichen mit:")
        print(f"      python developer/tools/release.py stage --version {version} --channel stable \\")
        print(f"          --tested-by-user --smoke-test-passed")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    status = collect_status()
    problems: list[str] = []
    for channel, info in status["channels"].items():
        problems.extend(f"{channel}.json: {item}" for item in info["problems"])
    if status["testBuild"] and status["testBuild"]["problems"] and args.require_test_build:
        problems.extend(f"release/ArenaBridge.exe: {item}" for item in status["testBuild"]["problems"])
    for problem in problems:
        print(f"FEHLER: {problem}")
    if problems:
        print(f"\n{len(problems)} Widerspruch/Widersprueche gefunden.")
        return 1
    print("OK: Quellversion, Kanal-Dateien und veroeffentlichte Artefakte sind widerspruchsfrei.")
    return 0


def pack_notes(text: str, limit: int = 760, max_items: int = 8) -> list[str]:
    """Zerlegt einen langen Versionshinweis in lesbare Eintraege <= limit Zeichen."""
    cleaned = " ".join(str(text).split())
    cleaned = cleaned.lstrip("•-* ").strip()
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.;!?])\s+", cleaned)
    items: list[str] = []
    current = ""
    for part in parts:
        candidate = (current + " " + part).strip() if current else part
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            items.append(current)
        while len(part) > limit:
            cut = part.rfind(" ", 0, limit)
            if cut < limit // 2:
                cut = limit
            items.append(part[:cut].strip())
            part = part[cut:].strip()
        current = part
    if current:
        items.append(current)
    if len(items) > max_items:
        head = items[:max_items - 1]
        rest = " ".join(items[max_items - 1:])
        if len(rest) > limit:
            rest = rest[:limit - 4].rstrip() + " ..."
        head.append(rest)
        items = head
    return items


def build_manifest(version: str, channel: str, sequence: int, exe_path: Path,
                   notes: list[str], published_at: str) -> dict:
    return {
        "schemaVersion": 2,
        "channel": channel,
        "enabled": True,
        "testFixture": False,
        "sequence": sequence,
        "version": version,
        "publishedAtUtc": published_at,
        "minimumUpdaterVersion": updater_version(),
        "artifact": {
            "fileName": artifact_name(version),
            "url": artifact_url(version),
            "sha256": sha256_file(exe_path),
            "sizeBytes": exe_path.stat().st_size,
        },
        "notes": notes,
    }


def disabled_manifest(channel: str, sequence: int | None = None, notes: list[str] | None = None) -> dict:
    data = read_json(CHANNEL_DIR / f"{channel}.json")
    keep_sequence = int(data.get("sequence", 1)) if sequence is None else sequence
    return {
        "schemaVersion": 2,
        "channel": channel,
        "enabled": False,
        "testFixture": False,
        "sequence": max(1, keep_sequence),
        "version": "",
        "publishedAtUtc": "",
        "minimumUpdaterVersion": updater_version(),
        "artifact": {"fileName": "ArenaBridge.exe", "url": "", "sha256": "", "sizeBytes": 0},
        "notes": notes if notes is not None else [
            "Kanal ist DEAKTIVIERT. Es laeuft gerade keine Veroeffentlichung ueber das neue Update-System.",
            "Veroeffentlichen ist ein eigener, ausdruecklicher Schritt ueber developer/tools/release.py stage.",
        ],
    }


def update_readme_release(version: str, channel: str, artifact: Path, notes: list[str],
                          published_day: str, sequence: int) -> None:
    text = UPDATE_README.read_text(encoding="utf-8")
    stamp = f"Letzte veröffentlichte Version: {version} (freigegeben am {published_day}, Kanal {channel})"
    if not LAST_RELEASE_RE.search(text):
        raise SystemExit("FEHLER: In update-system/README.md fehlt die Zeile "
                         "'Letzte veröffentlichte Version: ...'. Bitte zuerst wiederherstellen.")
    text = LAST_RELEASE_RE.sub(stamp, text, count=1)
    size_text = f"{artifact.stat().st_size:,}".replace(",", ".")
    row = (f"| {version} | {published_day} | {channel} | {sequence} | "
           f"`release/{artifact.name}`, {size_text} Bytes, "
           f"SHA-256 `{sha256_file(artifact)}` |")
    lines = text.splitlines()
    header_index = next((index for index, line in enumerate(lines)
                         if line.strip().startswith("| Version |")), None)
    if header_index is None:
        raise SystemExit("FEHLER: In update-system/README.md fehlt die Tabelle der "
                         "Veroeffentlichungen (" + TABLE_HEADER + ").")
    lines.insert(header_index + 2, row)
    UPDATE_README.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def run_guard_rebaseline(approval: str) -> int:
    result = subprocess.run([sys.executable, str(GUARD_TEST), "--rebaseline",
                             "--approval", approval], cwd=ROOT, check=False)
    return result.returncode


def cmd_stage(args: argparse.Namespace) -> int:
    version = args.version.strip()
    channel = args.channel
    if not VERSION_RE.match(version):
        print("FEHLER: --version muss x.y.z oder x.y.z-beta.n sein.")
        return 2
    if channel == "stable" and "-" in version:
        print("FEHLER: Der Stable-Kanal veroeffentlicht keine Vorabversionen.")
        return 2
    if not args.tested_by_user:
        print("FEHLER: Ohne --tested-by-user wird nichts veroeffentlicht. Der Nutzer muss den")
        print("        privaten Windows-Test der EXE ausdruecklich bestaetigt haben.")
        return 2
    if not args.smoke_test_passed and not args.smoke_test_skipped:
        print("FEHLER: Bitte den Selbst-Update-Test bestaetigen (--smoke-test-passed) oder")
        print("        ausdruecklich ueberspringen (--smoke-test-skipped).")
        return 2

    source = app_version()
    if version != source:
        print(f"FEHLER: --version {version} passt nicht zu app/version.json ({source}).")
        return 2
    if not SOURCE_EXE.is_file():
        print(f"FEHLER: {SOURCE_EXE.relative_to(ROOT)} fehlt. Der Nutzer muss die getestete EXE hochladen.")
        return 2

    exe_problems = validate_exe(SOURCE_EXE, version)
    if exe_problems:
        for problem in exe_problems:
            print(f"FEHLER: release/ArenaBridge.exe: {problem}")
        return 2

    target = RELEASE_DIR / artifact_name(version)
    if target.exists() and not args.force:
        print(f"FEHLER: {target.relative_to(ROOT)} existiert bereits. Eine veroeffentlichte Datei wird")
        print("        nie ueberschrieben. Erhoehe die Version in app/version.json (und baue neu).")
        return 2

    sequences = release_sequences()
    previous_version, _ = last_release(UPDATE_README.read_text(encoding="utf-8"))
    if previous_version:
        if previous_version == version:
            print(f"FEHLER: Version {version} ist bereits veroeffentlicht. Kein zweites Mal mit anderem Inhalt.")
            return 2
        if not semver_gt(version, previous_version):
            print(f"FEHLER: Version {version} ist nicht hoeher als die letzte Veroeffentlichung {previous_version}.")
            return 2
    for other in CHANNELS:
        if other == channel:
            continue
        other_data = read_json(CHANNEL_DIR / f"{other}.json")
        if other_data.get("enabled") and str(other_data.get("version", "")) == version:
            print(f"FEHLER: Version {version} ist bereits im Kanal {other} aktiv.")
            return 2

    sequence = sequences.get(channel, 0) + 1
    published_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    notes = pack_notes(args.notes) if args.notes else pack_notes(str(
        read_json(VERSION_FILE).get("notes", [""])[0]))
    if not notes:
        notes = ["Arena Roblox Bridge " + version]

    for problem in validate_channel(build_manifest(version, channel, sequence, SOURCE_EXE, notes, published_at),
                                    channel, exe_path=SOURCE_EXE):
        print(f"FEHLER: geplantes Manifest: {problem}")
        return 2

    print(f"Release {version} auf Kanal {channel} (sequence {sequence}) wird vorbereitet:")
    print(f"  Quelle:  release/ArenaBridge.exe ({SOURCE_EXE.stat().st_size} Bytes, "
          f"SHA-256 {sha256_file(SOURCE_EXE)[:16]}...)")
    print(f"  Artefakt: release/{target.name} (unveraenderliche Datei dieser Version)")

    dry = args.dry_run
    if not dry:
        shutil.copy2(SOURCE_EXE, target)
        manifest = build_manifest(version, channel, sequence, target, notes, published_at)
        write_json(CHANNEL_DIR / f"{channel}.json", manifest)
        update_readme_release(version, channel, target, notes, published_at[:10], sequence)
        approval = (f"Release-Freigabe Version {version}: Kanal {channel} aktiviert; Artefakt "
                    f"release/{target.name}, SHA-256 {sha256_file(target)}, getestet vom Nutzer"
                    + (" mit bestandenem Selbst-Update-Test." if args.smoke_test_passed
                       else " (Selbst-Update-Test ausdruecklich uebersprungen)."))
        if not args.no_rebaseline:
            if run_guard_rebaseline(approval) != 0:
                print("FEHLER: Guard-Rebaseline fehlgeschlagen. Bitte Zustand pruefen (git diff).")
                return 1

    print("")
    print("Fertig vorbereitet." if not dry else "Probelauf (--dry-run): es wurde nichts geschrieben.")
    print("  Naechste Schritte:")
    print(f"    1. Release-Doctor:  python developer/tools/release.py status")
    print(f"    2. Offline-Tests:   python developer/tests/run_offline_tests.py")
    print(f"    3. Pull Request erstellen und NICHT selbst mergen; dem Nutzer ehrlich sagen,")
    print(f"       dass raw.githubusercontent.com nach dem Merge einige Minuten den alten Stand")
    print(f"       liefern kann (der Updater bricht dann ab und versucht es beim naechsten Start erneut).")
    if not args.smoke_test_passed:
        print("  HINWEIS: Der Selbst-Update-Test wurde uebersprungen - das muss im PR ehrlich stehen.")
    return 0


def cmd_disable(args: argparse.Namespace) -> int:
    if not args.channel:
        print("FEHLER: --channel beta|stable angeben.")
        return 2
    data = read_json(CHANNEL_DIR / f"{args.channel}.json")
    if not data.get("enabled") and not args.force:
        print(f"Hinweis: Kanal {args.channel} ist bereits deaktiviert.")
        return 0
    manifest = disabled_manifest(args.channel, notes=[
        f"Kanal ist DEAKTIVIERT (zurueckgenommen am {dt.date.today().isoformat()}).",
        "Eine zurueckgenommene Veroeffentlichung wird im README dokumentiert; die Versionsdatei bleibt liegen.",
    ])
    write_json(CHANNEL_DIR / f"{args.channel}.json", manifest)
    print(f"Kanal {args.channel} ist jetzt deaktiviert (sequence bleibt {manifest['sequence']}).")
    print("Bitte die Offline-Tests laufen lassen und den Guard-Lock neu baseline'n:")
    print("  python developer/tests/run_offline_tests.py")
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    keep = max(1, int(args.keep))
    referenced = set()
    for channel in CHANNELS:
        data = read_json(CHANNEL_DIR / f"{channel}.json")
        path = channel_artifact(data)
        if path:
            referenced.add(path.name)
    versioned = versioned_artifacts()

    def sort_key(path: Path) -> tuple:
        version = path.name[len("ArenaBridge-"):-len(".exe")]
        parsed = parse_semver(version)
        return parsed if parsed else (0, 0, 0, "")

    ordered = sorted(versioned, key=sort_key, reverse=True)
    keep_names = {path.name for path in ordered[:keep]} | referenced
    removed = []
    for path in ordered:
        if path.name in keep_names:
            continue
        if args.dry_run:
            removed.append(path.name)
            continue
        path.unlink()
        removed.append(path.name)
    if removed:
        print(("Wuerde entfernen: " if args.dry_run else "Entfernt: ") + ", ".join(removed))
        print("Bitte den Guard-Lock neu baseline'n, damit die Aenderung dokumentiert ist.")
    else:
        print(f"Keine alten Versionsdateien zu entfernen (behalten: {', '.join(sorted(keep_names)) or '(keine)'}).")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Release-Werkzeug fuer das neue Update-System.")
    parser.add_argument("--json", action="store_true", help="status als JSON ausgeben")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Gesamtstand und naechste Schritte")
    check = sub.add_parser("check", help="Nur pruefen, Exit 1 bei Widerspruch")
    check.add_argument("--require-test-build", action="store_true",
                       help="auch release/ArenaBridge.exe muss zur Quellversion passen")

    stage = sub.add_parser("stage", help="Veroeffentlichung vorbereiten")
    stage.add_argument("--version", required=True)
    stage.add_argument("--channel", default="stable", choices=list(CHANNELS))
    stage.add_argument("--notes", default="", help="Hinweistexte (sonst aus app/version.json)")
    stage.add_argument("--tested-by-user", action="store_true",
                       help="der Nutzer hat die EXE privat getestet")
    stage.add_argument("--smoke-test-passed", action="store_true",
                       help="Invoke-SelfUpdateSmoke.ps1 ist auf Windows bestanden")
    stage.add_argument("--smoke-test-skipped", action="store_true",
                       help="Selbst-Update-Test bewusst uebersprungen (ehrlich dokumentieren)")
    stage.add_argument("--dry-run", action="store_true")
    stage.add_argument("--force", action="store_true", help="vorhandene Versionsdatei ueberschreiben")
    stage.add_argument("--no-rebaseline", action="store_true")

    disable = sub.add_parser("disable", help="Kanal deaktivieren")
    disable.add_argument("--channel", required=True, choices=list(CHANNELS))
    disable.add_argument("--force", action="store_true")

    prune = sub.add_parser("prune", help="Alte Versionsdateien entfernen")
    prune.add_argument("--keep", default="2")
    prune.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    command = args.command or "status"
    if command == "status":
        return cmd_status(args)
    if command == "check":
        return cmd_check(args)
    if command == "stage":
        return cmd_stage(args)
    if command == "disable":
        return cmd_disable(args)
    if command == "prune":
        return cmd_prune(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
