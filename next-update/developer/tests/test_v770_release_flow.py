#!/usr/bin/env python3
"""Offline test for the release flow (see developer/docs/RELEASE-ABLAUF.md).

Validates:
  1. RELEASE-ABLAUF.md and RELEASE-SESSION-PROMPT.md exist and contain all mandatory rules.
  2. Build-EXE.bat passes no test parameters and uses -Channel stable -NonInteractive.
  3. No untracked or unexpected EXEs exist in the repository (only release/ArenaBridge.exe if present).
  4. Consistency of active manifests against schema, version, sha256, sizeBytes, canonical URL, lock approval.
  5. Negative unit tests on manifest validation (tampered hash, wrong version, evil URL, enabled without approval)
     using temporary fixtures without touching real manifests.
"""
from __future__ import annotations

import copy
import datetime as _dt
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "developer" / "docs"
CHANNELS = ROOT / "update-system" / "channels"
LOCK = ROOT / "update-system" / "update_system_guard.lock.json"
SCHEMA_PATH = CHANNELS / "manifest.schema.json"
APP = ROOT / "app" / "ArenaBridge.ps1"
VERSION_FILE = ROOT / "app" / "version.json"
BAT_PATH = ROOT / "Build-EXE.bat"
RELEASE_DIR = ROOT / "release"

FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("  ok   " if condition else "  FAIL ") + message)
    if not condition:
        FAILURES.append(message)


def parse_semver(v: str) -> tuple | None:
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$", v.strip())
    if not m:
        return None
    major, minor, patch, prerelease = m.groups()
    return (int(major), int(minor), int(patch), prerelease or "")


def semver_gt(v1: str, v2: str) -> bool:
    p1 = parse_semver(v1)
    p2 = parse_semver(v2)
    if not p1 or not p2:
        return False
    if p1[:3] != p2[:3]:
        return p1[:3] > p2[:3]
    if not p1[3] and p2[3]:
        return True
    if p1[3] and not p2[3]:
        return False
    return p1[3] > p2[3]


def get_last_published_version(readme_text: str) -> str:
    m = re.search(r"Letzte ver[öo]ffentlichte Version:\s*([^\s\n\(\)]+)", readme_text, re.IGNORECASE)
    if m:
        val = m.group(1).strip()
        if val.lower() in ("keine", "none", ""):
            return ""
        return val
    return ""


def validate_manifest(data: dict, exe_path: Path, current_version: str,
                      last_pub_version: str, lock_data: dict, schema: dict) -> list[str]:
    import jsonschema  # type: ignore
    validator = jsonschema.Draft202012Validator(schema)
    errors = [e.message for e in validator.iter_errors(data)]
    if errors:
        return [f"schema error: {errors[0]}"]

    errs: list[str] = []
    ver = data.get("version", "")
    if ver != current_version:
        errs.append(f"version ({ver}) != app/version.json ({current_version})")

    art = data.get("artifact", {})
    actual_sha = ""
    if exe_path.is_file():
        exe_bytes = exe_path.read_bytes()
        actual_sha = hashlib.sha256(exe_bytes).hexdigest().lower()
        actual_size = len(exe_bytes)
        if str(art.get("sha256", "")).lower() != actual_sha:
            errs.append(f"sha256 ({art.get('sha256')}) != EXE sha256 ({actual_sha})")
        if art.get("sizeBytes") != actual_size:
            errs.append(f"sizeBytes ({art.get('sizeBytes')}) != EXE size ({actual_size})")
    else:
        errs.append(f"release EXE missing at {exe_path}")

    # Regel 3 des Release-Ablaufs: Downgrade verboten, Gleichstand nur mit identischem
    # Artefakt (sonst version-conflict). Ein aktiviertes Manifest darf nicht am Tag nach
    # der Freigabe umfallen, nur weil README und Manifest dieselbe Version nennen.
    if last_pub_version:
        p_ver, p_last = parse_semver(ver), parse_semver(last_pub_version)
        if not p_ver or not p_last:
            errs.append(f"version ({ver}) or last published ({last_pub_version}) is not X.Y.Z")
        elif p_ver == p_last:
            if not actual_sha or str(art.get("sha256", "")).lower() != actual_sha:
                errs.append(f"version-conflict: ({ver}) equals the last published version "
                            f"with a different artifact hash")
        elif not semver_gt(ver, last_pub_version):
            errs.append(f"version ({ver}) not higher than last published ({last_pub_version})")

    canonical_url = "https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/next-update/release/ArenaBridge.exe"
    if art.get("url") != canonical_url:
        errs.append(f"URL is not canonical: {art.get('url')}")

    published_at = str(data.get("publishedAtUtc", ""))
    published_stamp = re.match(r"^(\d{4}-\d{2}-\d{2})T\d{2}:\d{2}:\d{2}Z$", published_at)
    if not published_stamp:
        errs.append(f"publishedAtUtc ({published_at}) is not ISO-8601 UTC YYYY-MM-DDTHH:MM:SSZ")
    approvals = lock_data.get("approvals", [])

    def release_approval(day: str) -> bool:
        return any(a.get("date") == day and ("release" in str(a.get("note", "")).lower()
                                             or "freigabe" in str(a.get("note", "")).lower())
                   for a in approvals)

    if published_stamp:
        if not release_approval(published_stamp.group(1)):
            errs.append(f"lock file has no release approval dated {published_stamp.group(1)} "
                        f"(publishedAtUtc of this manifest)")
    elif not release_approval(_dt.date.today().isoformat()):
        errs.append(f"lock file has no release approval dated today ({_dt.date.today().isoformat()})")

    return errs


def test_documentation_and_rules() -> None:
    flow_doc = DOCS / "RELEASE-ABLAUF.md"
    prompt_doc = DOCS / "RELEASE-SESSION-PROMPT.md"
    check(flow_doc.is_file(), "RELEASE-ABLAUF.md exists")
    check(prompt_doc.is_file(), "RELEASE-SESSION-PROMPT.md exists")

    flow_text = flow_doc.read_text(encoding="utf-8")
    mandatory_flow_markers = [
        "Aenderungs-Session" in flow_text or "Änderungs-Session" in flow_text,
        "Release-Session" in flow_text,
        "update-system/channels" in flow_text,
        "raw.githubusercontent.com" in flow_text,
        "isPrivate" in flow_text,
        "Invoke-SelfUpdateSmoke.ps1" in flow_text,
        "mandatory" in flow_text,
        "version-conflict" in flow_text or "Letzte veröffentlichte Version" in flow_text,
    ]
    check(all(mandatory_flow_markers), "RELEASE-ABLAUF.md contains all mandatory rules and gates")

    prompt_text = prompt_doc.read_text(encoding="utf-8")
    mandatory_prompt_markers = [
        "<VERSION>" in prompt_text,
        "<KURZBESCHREIBUNG DER GEMERGTEN AENDERUNG>" in prompt_text,
        "RELEASE-ABLAUF.md" in prompt_text,
        "next-update/release/ArenaBridge.exe" in prompt_text,
        "isPrivate" in prompt_text,
        "Invoke-SelfUpdateSmoke.ps1" in prompt_text,
        "pefile" in prompt_text or "FileVersion" in prompt_text,
        "--rebaseline" in prompt_text,
    ]
    check(all(mandatory_prompt_markers), "RELEASE-SESSION-PROMPT.md contains all template fields and prompt rules")


def test_builder_bat() -> None:
    bat_text = BAT_PATH.read_text(encoding="utf-8")
    check("-Channel stable" in bat_text, "Build-EXE.bat builds channel stable")
    check("-NonInteractive" in bat_text, "Build-EXE.bat passes -NonInteractive")
    check("-TestFixtureBuild" not in bat_text, "Build-EXE.bat passes no test parameter -TestFixtureBuild")
    check("-OutputDirectory" not in bat_text, "Build-EXE.bat passes no test parameter -OutputDirectory")
    check("-TestFileVersion" not in bat_text, "Build-EXE.bat passes no test parameter -TestFileVersion")


def test_tracked_executables() -> None:
    # Only release/ArenaBridge.exe may exist in the repository; no other EXE.
    all_exes = sorted(ROOT.rglob("*.exe"))
    unexpected = [p for p in all_exes if p.relative_to(ROOT).as_posix() != "release/ArenaBridge.exe"]
    check(len(unexpected) == 0, "no unexpected EXE tracked in repository: " + ", ".join(str(p) for p in unexpected))


def test_active_manifest_consistency() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    readme_text = (ROOT / "update-system" / "README.md").read_text(encoding="utf-8")
    version_json = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
    current_source_version = str(version_json.get("version", ""))
    last_pub = get_last_published_version(readme_text)
    lock_data = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.is_file() else {}

    for ch_name in ("beta", "stable"):
        data = json.loads((CHANNELS / f"{ch_name}.json").read_text(encoding="utf-8"))
        if data.get("enabled"):
            errs = validate_manifest(data, RELEASE_DIR / "ArenaBridge.exe",
                                     current_source_version, last_pub, lock_data, schema)
            check(not errs, f"active manifest {ch_name}.json is consistent: " + ", ".join(errs))


def test_negative_unit_tests() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    exe_file = RELEASE_DIR / "ArenaBridge.exe"
    exe_bytes = exe_file.read_bytes() if exe_file.is_file() else b"dummy"
    real_sha = hashlib.sha256(exe_bytes).hexdigest().lower()
    real_size = len(exe_bytes)
    current_ver = "7.7.0"
    last_pub = ""
    today_iso = _dt.date.today().isoformat()

    valid_base = {
        "schemaVersion": 1,
        "channel": "stable",
        "enabled": True,
        "testFixture": False,
        "version": current_ver,
        "publishedAtUtc": f"{today_iso}T12:00:00Z",
        "minimumUpdaterVersion": "1.1.0",
        "mandatory": False,
        "artifact": {
            "fileName": "ArenaBridge.exe",
            "url": "https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/next-update/release/ArenaBridge.exe",
            "sha256": real_sha,
            "sizeBytes": real_size
        },
        "notes": ["Test-Notiz"]
    }
    valid_lock = {
        "approvals": [
            {
                "date": today_iso,
                "approvedBy": "Nutzer",
                "note": "Release-Freigabe Version 7.7.0 fuer alle Nutzer."
            }
        ]
    }

    # Case 1: valid base should have 0 errors if exe exists
    if exe_file.is_file():
        errs0 = validate_manifest(valid_base, exe_file, current_ver, last_pub, valid_lock, schema)
        check(len(errs0) == 0, "negative test base: valid manifest passes")

    # Case 2: tampered hash
    bad_hash = copy.deepcopy(valid_base)
    bad_hash["artifact"]["sha256"] = "0" * 64
    errs2 = validate_manifest(bad_hash, exe_file, current_ver, last_pub, valid_lock, schema)
    check(any("sha256" in e for e in errs2), "negative test: tampered sha256 is rejected")

    # Case 3: wrong version vs version.json
    bad_ver = copy.deepcopy(valid_base)
    bad_ver["version"] = "7.8.0"
    errs3 = validate_manifest(bad_ver, exe_file, current_ver, last_pub, valid_lock, schema)
    check(any("version" in e for e in errs3), "negative test: mismatch with app/version.json is rejected")

    # Case 4: version not higher than last published
    old_ver = copy.deepcopy(valid_base)
    old_ver["version"] = "7.6.5"
    errs4 = validate_manifest(old_ver, exe_file, "7.6.5", "7.7.0", valid_lock, schema)
    check(any("not higher" in e for e in errs4), "negative test: version <= last published is rejected")

    # Case 5: non-canonical evil URL
    bad_url = copy.deepcopy(valid_base)
    bad_url["artifact"]["url"] = "https://evil.com/ArenaBridge.exe"
    errs5 = validate_manifest(bad_url, exe_file, current_ver, last_pub, valid_lock, schema)
    check(len(errs5) > 0, "negative test: evil URL is rejected")

    # Case 6: enabled without release approval in lock
    no_approval_lock = {"approvals": [{"date": today_iso, "approvedBy": "Nutzer", "note": "Feature-PR normaler Umbau"}]}
    errs6 = validate_manifest(valid_base, exe_file, current_ver, last_pub, no_approval_lock, schema)
    check(any("lock" in e for e in errs6), "negative test: enabled without release approval in lock is rejected")

    # Case 7: release approval exists, but not for the day this manifest was published
    other_day_lock = {"approvals": [{"date": "2020-01-01", "approvedBy": "Nutzer",
                                     "note": "Release-Freigabe Version 7.7.0 an einem anderen Tag."}]}
    errs7 = validate_manifest(valid_base, exe_file, current_ver, last_pub, other_day_lock, schema)
    check(any("lock" in e for e in errs7),
          "negative test: release approval from another day than publishedAtUtc is rejected")

    # Case 8: a published manifest whose version equals the recorded last published version
    # stays valid while it points at the same artifact; a different hash is a version-conflict.
    same_version_lock = {"approvals": [{"date": today_iso, "approvedBy": "Nutzer",
                                        "note": "Release-Freigabe Version 7.7.0."}]}
    if exe_file.is_file():
        errs8 = validate_manifest(valid_base, exe_file, current_ver, current_ver, same_version_lock, schema)
        check(not errs8, "live release state: same version and same artifact stays valid -> " + (", ".join(errs8) if errs8 else "ok"))
    tampered_same = copy.deepcopy(valid_base)
    tampered_same["artifact"]["sha256"] = "0" * 64
    errs9 = validate_manifest(tampered_same, exe_file, current_ver, current_ver, same_version_lock, schema)
    check(any("version-conflict" in e for e in errs9),
          "negative test: same version with a different artifact hash is a version-conflict")


def main() -> int:
    print("Release flow & validation test")
    test_documentation_and_rules()
    test_builder_bat()
    test_tracked_executables()
    test_active_manifest_consistency()
    test_negative_unit_tests()

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} release flow check(s).")
        return 1
    print("\nOK: release flow, documentation, builder BAT, tracked EXEs and manifest gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
