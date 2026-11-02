#!/usr/bin/env python3
"""Bind an unpublished Windows candidate to the exact source that built it.

No signing or publication is performed here. Promotion re-hashes the source and
EXE on main; a merge commit is fine when its relevant source fingerprint matches.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pefile

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "next-update/app"
BUILDER = ROOT / "next-update/builder"
EXE = ROOT / "next-update/beta-release/ArenaRobloxBridge.exe"
MANIFEST = ROOT / "next-update/beta-release/candidate.json"
VERSION = APP / "version.json"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def source_fingerprint() -> str:
    h = hashlib.sha256()
    count = 0
    for base in (APP, BUILDER):
        for path in sorted(base.rglob("*"), key=lambda p: p.relative_to(ROOT).as_posix()):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            rel = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            h.update(len(rel.encode()).to_bytes(4, "big"))
            h.update(rel.encode())
            h.update(len(data).to_bytes(8, "big"))
            h.update(data)
            count += 1
    if count < 2:
        raise RuntimeError("Application/builder source is missing")
    return h.hexdigest()


def exe_version(path: Path) -> str:
    pe = pefile.PE(str(path), fast_load=True)
    try:
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]])
        for fileinfo in getattr(pe, "FileInfo", []):
            for entry in fileinfo:
                if getattr(entry, "Key", b"") == b"StringFileInfo":
                    for table in entry.StringTable:
                        for key in (b"FileVersion", b"ProductVersion"):
                            value = table.entries.get(key, b"").decode("utf-8", "replace").strip()
                            match = re.search(r"\d+\.\d+\.\d+(?:\.\d+)?", value)
                            if match:
                                parts = match.group(0).split(".")
                                return ".".join((parts + ["0"])[:3]) if len(parts) == 3 else ".".join(parts[:4])
        # Fixed resource is authoritative when string metadata is localized.
        for fileinfo in getattr(pe, "FileInfo", []):
            for entry in fileinfo:
                fixed = getattr(entry, "FixedFileInfo", None)
                if fixed:
                    return f"{fixed.FileVersionMS >> 16}.{fixed.FileVersionMS & 65535}.{fixed.FileVersionLS >> 16}.{fixed.FileVersionLS & 65535}"
    finally:
        pe.close()
    raise RuntimeError("EXE has no version resource")


def version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(x) for x in value.split("."))


def validate(manifest: dict) -> None:
    if manifest.get("schema") != 1 or manifest.get("published") is not False or manifest.get("channel") != "rc":
        raise RuntimeError("Not an unpublished rc candidate manifest")
    expected_version = json.loads(VERSION.read_text(encoding="utf-8-sig"))["version"]
    if manifest.get("version") != expected_version:
        raise RuntimeError(f"Candidate version {manifest.get('version')} != source version {expected_version}")
    if not EXE.is_file() or EXE.stat().st_size < 1_000_000:
        raise RuntimeError("Candidate EXE missing or implausibly small")
    if manifest.get("sha256") != sha(EXE) or manifest.get("sizeBytes") != EXE.stat().st_size:
        raise RuntimeError("Candidate EXE hash/size mismatch")
    embedded = exe_version(EXE)
    if version_tuple(embedded)[:3] != version_tuple(expected_version)[:3]:
        raise RuntimeError(f"EXE version {embedded} != source version {expected_version}")
    if manifest.get("sourceFingerprint") != source_fingerprint():
        raise RuntimeError("App/builder source changed after the candidate build; rebuild before promotion")
    if not re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("sourceCommit", ""))):
        raise RuntimeError("Invalid source commit")
    if not str(manifest.get("branch", "")).strip() or not str(manifest.get("runId", "")).strip():
        raise RuntimeError("Missing branch/run provenance")


def write(args: argparse.Namespace) -> None:
    version = json.loads(VERSION.read_text(encoding="utf-8-sig"))["version"]
    manifest = {
        "schema": 1, "channel": "rc", "published": False, "version": version,
        "asset": "ArenaRobloxBridge.exe", "sha256": sha(EXE), "sizeBytes": EXE.stat().st_size,
        "exeVersion": exe_version(EXE), "sourceFingerprint": source_fingerprint(),
        "sourceCommit": args.source_commit, "branch": args.branch, "runId": args.run_id,
        "note": "Unpublished beta candidate. Verify source+EXE before explicit promotion; never served by release/latest.json.",
    }
    validate(manifest)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    w = sub.add_parser("write")
    w.add_argument("--source-commit", required=True)
    w.add_argument("--branch", required=True)
    w.add_argument("--run-id", required=True)
    sub.add_parser("verify")
    args = parser.parse_args()
    try:
        if args.command == "write":
            write(args)
        else:
            validate(json.loads(MANIFEST.read_text(encoding="utf-8-sig")))
            print("Candidate source fingerprint, EXE hash/size/version and unpublished status verified.")
        return 0
    except Exception as exc:
        print(f"candidate_manifest: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
