#!/usr/bin/env python3
"""Erzeugt next-update/release/latest.json aus der echten ArenaBridge.exe.

Aufgerufen von .github/workflows/publish-bridge.yml, sobald sich
next-update/release/ArenaBridge.exe auf main aendert. Das Werkzeug laedt nichts
herunter und veraendert nur latest.json. Es prueft:

- die Datei ist eine Windows-x64-EXE,
- die Dateiversion der EXE ist genau <Version aus app/version.json>.0,
- die Version ist hoeher als die bisher veroeffentlichte Version.

Die Download-Adresse zeigt auf den Commit, der die EXE enthaelt. Dadurch
bekommen Browser und Caches immer genau diese Datei.

Nutzung (Repository-Wurzel als Arbeitsordner):
    python next-update/developer/tools/publish_latest.py --commit <SHA>
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # next-update/
DEFAULT_EXE = PROJECT_ROOT / "release" / "ArenaBridge.exe"
DEFAULT_LATEST = PROJECT_ROOT / "release" / "latest.json"
DEFAULT_VERSION_JSON = PROJECT_ROOT / "app" / "version.json"
DEFAULT_REPO = "merta-studios/arenarobloxbridge"
EXE_PATH_IN_REPO = "next-update/release/ArenaBridge.exe"
MIN_BYTES = 100_000
MAX_BYTES = 64 * 1024 * 1024
MACHINE_X64 = 0x8664
SCHEMA_VERSION = 1


class PublishError(Exception):
    pass


def file_version(path: Path) -> str:
    """FileVersion der EXE (z. B. '7.9.0.0') oder Fehler."""
    try:
        import pefile  # type: ignore
    except ImportError as exc:  # pragma: no cover - Workflow installiert pefile
        raise PublishError("pefile fehlt: python -m pip install pefile") from exc
    pe = pefile.PE(str(path), fast_load=True)
    try:
        pe.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]])
        for group in pe.FileInfo or []:
            for entry in group:
                for table in getattr(entry, "StringTable", None) or []:
                    value = table.entries.get(b"FileVersion")
                    if value:
                        return value.decode("ascii", "replace").strip()
    finally:
        pe.close()
    raise PublishError("Die EXE enthaelt keine Dateiversion.")


def is_windows_x64(path: Path) -> bool:
    raw = path.read_bytes()[:4096]
    if len(raw) < 256 or raw[0:2] != b"MZ":
        return False
    offset = int.from_bytes(raw[0x3C:0x40], "little")
    if offset <= 0 or offset + 6 > len(raw) or raw[offset:offset + 4] != b"PE\x00\x00":
        return False
    return int.from_bytes(raw[offset + 4:offset + 6], "little") == MACHINE_X64


def read_version_json(path: Path) -> tuple[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    version = str(data.get("version", ""))
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise PublishError(f"app/version.json: Version ist ungueltig: {version!r}")
    notes = data.get("notes") or []
    note = str(notes[0]) if notes else ""
    note = re.sub(r"\s+", " ", note).strip()
    if len(note) > 600:
        note = note[:600].rstrip() + " ..."
    return version, note


def version_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def build_manifest(exe: Path, version: str, note: str, repo: str, commit: str,
                   now: dt.datetime) -> dict:
    if not exe.is_file():
        raise PublishError(f"EXE fehlt: {exe}")
    size = exe.stat().st_size
    if size < MIN_BYTES or size > MAX_BYTES:
        raise PublishError(f"EXE hat eine unplausible Groesse: {size} Bytes.")
    if not is_windows_x64(exe):
        raise PublishError("Die Datei ist keine Windows-x64-EXE.")
    fv = file_version(exe)
    if fv != version + ".0":
        raise PublishError(
            f"Dateiversion der EXE ist {fv}, erwartet {version}.0 (app/version.json). "
            "Die EXE wurde mit einer anderen Version gebaut.")
    sha256 = hashlib.sha256(exe.read_bytes()).hexdigest()
    return {
        "schemaVersion": SCHEMA_VERSION,
        "version": version,
        "sha256": sha256,
        "sizeBytes": size,
        "url": f"https://raw.githubusercontent.com/{repo}/{commit}/{EXE_PATH_IN_REPO}",
        "publishedAtUtc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "notes": note,
    }


def check_against_previous(new: dict, latest_path: Path) -> str:
    """'neu', 'unveraendert' oder Fehler, wenn die Version nicht hoeher ist."""
    if not latest_path.is_file():
        return "neu"
    old = json.loads(latest_path.read_text(encoding="utf-8"))
    old_version = str(old.get("version", ""))
    if version_tuple(new["version"]) < version_tuple(old_version):
        raise PublishError(
            f"Version {new['version']} ist niedriger als die veroeffentlichte {old_version}.")
    if new["version"] == old_version:
        if new["sha256"] == old.get("sha256"):
            return "unveraendert"
        raise PublishError(
            f"Version {new['version']} ist bereits veroeffentlicht, aber mit einer anderen Datei. "
            "Erhoehe die Version in app/version.json (z. B. 7.9.1), sonst bekommen Nutzer das Update nicht.")
    return "neu"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--latest", type=Path, default=DEFAULT_LATEST)
    parser.add_argument("--version-json", type=Path, default=DEFAULT_VERSION_JSON)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--commit", required=True, help="Commit-SHA, der die EXE enthaelt")
    parser.add_argument("--dry-run", action="store_true", help="nichts schreiben")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        print("FEHLER: --commit muss ein vollstaendiger 40-stelliger SHA sein.", file=sys.stderr)
        return 2
    try:
        version, note = read_version_json(args.version_json)
        manifest = build_manifest(args.exe, version, note, args.repo, args.commit,
                                  dt.datetime.now(dt.timezone.utc))
        state = check_against_previous(manifest, args.latest)
    except PublishError as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 1
    print(f"Version {manifest['version']} | {manifest['sizeBytes']} Bytes | "
          f"SHA-256 {manifest['sha256']} | Status: {state}")
    if state == "unveraendert":
        print("latest.json bleibt unveraendert.")
        return 0
    if args.dry_run:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0
    args.latest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"latest.json geschrieben: {args.latest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
