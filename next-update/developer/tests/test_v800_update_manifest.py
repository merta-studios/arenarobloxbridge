#!/usr/bin/env python3
"""Offline checks for the update manifests (schema + fixtures + channel state).

No network and no PowerShell. Proves that:
  * the schema accepts the valid fixtures and rejects every invalid one,
  * a DISABLED channel file stays a placeholder with no artifact coordinates,
  * an ENABLED (released) channel file satisfies every release gate of
    developer/docs/RELEASE-ABLAUF.md on its own: version == app/version.json, never a
    downgrade, sha256/sizeBytes identical with the real release/ArenaBridge.exe, the
    canonical repository URL, updater 1.1.0, mandatory == false and the release approval
    of the publication day recorded in the lock file,
  * the Windows wrapper skips cleanly (exit 77) on non-Windows hosts.

The release-state checks are deliberately independent of the guard test, so a tampered
manifest has to pass two separate implementations, not one.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
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
RELEASE_EXE = ROOT / "release" / "ArenaBridge.exe"
CANONICAL_URL = ("https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/"
                 "main/next-update/release/ArenaBridge.exe")
STAMP_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})T\d{2}:\d{2}:\d{2}Z$")
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("  ok   " if condition else "  FAIL ") + message)
    if not condition:
        FAILURES.append(message)


def validator():
    try:
        import jsonschema  # type: ignore
    except ImportError:
        print("FAILED: jsonschema is missing. Install developer/tests/requirements-test.txt.")
        raise SystemExit(1)
    schema = json.loads((CHANNELS / "manifest.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def parse_semver(value: str) -> tuple | None:
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$", value.strip())
    if not m:
        return None
    major, minor, patch, prerelease = m.groups()
    return (int(major), int(minor), int(patch), prerelease or "")


def semver_gt(v1: str, v2: str) -> bool:
    p1, p2 = parse_semver(v1), parse_semver(v2)
    if not p1 or not p2:
        return False
    if p1[:3] != p2[:3]:
        return p1[:3] > p2[:3]
    if not p1[3] and p2[3]:
        return True
    if p1[3] and not p2[3]:
        return False
    return p1[3] > p2[3]


def last_published_version() -> str:
    """The version recorded by the last release ("" when nothing was published yet)."""
    m = re.search(r"Letzte ver[öo]ffentlichte Version:\s*([^\s\n\(\)]+)",
                  README.read_text(encoding="utf-8"), re.IGNORECASE)
    if not m:
        return ""
    value = m.group(1).strip()
    return "" if value.lower() in ("keine", "none", "") else value


def release_approval_for(day: str) -> bool:
    """True when the lock file carries a release approval dated `day`."""
    if not LOCK.is_file():
        return False
    approvals = json.loads(LOCK.read_text(encoding="utf-8")).get("approvals", [])
    for entry in approvals:
        note = str(entry.get("note", "")).lower()
        if entry.get("date") == day and ("release" in note or "freigabe" in note):
            return True
    return False


def check_disabled_channel(channel: str, data: dict) -> None:
    check(data.get("enabled") is False, f"{channel}.json is an explicitly disabled placeholder")
    artifact = data.get("artifact", {})
    check(artifact.get("url") == "" and artifact.get("sha256") == "" and artifact.get("sizeBytes") == 0,
          f"{channel}.json publishes no artifact coordinates")


def check_released_channel(channel: str, data: dict) -> None:
    """Everything a channel must prove before users are offered an update."""
    artifact = data.get("artifact", {})
    source_version = str(json.loads(VERSION_FILE.read_text(encoding="utf-8")).get("version", ""))
    check(data.get("version") == source_version,
          f"{channel}.json publishes exactly app/version.json ({source_version})")
    check(artifact.get("fileName") == "ArenaBridge.exe", f"{channel}.json ships ArenaBridge.exe")
    check(artifact.get("url") == CANONICAL_URL,
          f"{channel}.json uses the canonical repository URL, nothing else")
    check(data.get("mandatory") is False, f"{channel}.json offers the update voluntarily (no forced update)")

    published = str(data.get("publishedAtUtc", ""))
    stamp = STAMP_RE.match(published)
    check(bool(stamp), f"{channel}.json publishedAtUtc is ISO-8601 UTC ({published or 'leer'})")

    exe_present = RELEASE_EXE.is_file()
    check(exe_present, f"{channel}.json artifact exists at {RELEASE_EXE.relative_to(ROOT)}")
    actual_sha = ""
    if exe_present:
        raw = RELEASE_EXE.read_bytes()
        actual_sha = hashlib.sha256(raw).hexdigest().lower()
        check(str(artifact.get("sha256", "")).lower() == actual_sha,
              f"{channel}.json sha256 matches the tested EXE ({actual_sha})")
        check(artifact.get("sizeBytes") == len(raw),
              f"{channel}.json sizeBytes matches the tested EXE ({len(raw)})")

    previous = last_published_version()
    version = str(data.get("version", ""))
    if not previous:
        check(True, f"{channel}.json: no earlier release recorded, {version} is the first")
    elif parse_semver(version) == parse_semver(previous):
        # Gleichstand ist nur mit identischem Artefakt erlaubt (kein version-conflict).
        check(bool(actual_sha) and str(artifact.get("sha256", "")).lower() == actual_sha,
              f"{channel}.json: version {version} equals the last release and must point at the same EXE")
    else:
        check(semver_gt(version, previous),
              f"{channel}.json: version {version} must be higher than the last release {previous}")

    if stamp:
        check(release_approval_for(stamp.group(1)),
              f"{channel}.json: lock file records the release approval of {stamp.group(1)}")


def check_channel(channel: str, data: dict, v) -> None:
    check(data.get("channel") == channel, f"{channel}.json names its own channel")
    check(data.get("testFixture") is False, f"{channel}.json is not a test fixture")
    check(data.get("minimumUpdaterVersion") == "1.1.0", f"{channel}.json requires updater 1.1.0")
    check(not list(v.iter_errors(data)), f"{channel}.json validates against the schema")
    if data.get("enabled"):
        check_released_channel(channel, data)
    else:
        check_disabled_channel(channel, data)


def main() -> int:
    v = validator()

    for path in sorted(FIXTURES.glob("valid-*.json")):
        errors = sorted(v.iter_errors(json.loads(path.read_text(encoding="utf-8"))), key=str)
        check(not errors, f"valid fixture is accepted: {path.name}" + (f" -> {errors[0].message}" if errors else ""))

    invalid = sorted(FIXTURES.glob("invalid-*.json"))
    check(len(invalid) >= 8, f"at least eight invalid fixtures exist (found {len(invalid)})")
    for path in invalid:
        rejected = not list(v.iter_errors(json.loads(path.read_text(encoding="utf-8"))))
        check(not rejected, f"invalid fixture is rejected: {path.name}")

    for channel in ("beta", "stable"):
        check_channel(channel, json.loads((CHANNELS / f"{channel}.json").read_text(encoding="utf-8")), v)

    wrapper = TESTS / "test_v800_selfupdate_smoke.py"
    if sys.platform != "win32":
        result = subprocess.run([sys.executable, str(wrapper)], cwd=ROOT, capture_output=True, text=True, check=False)
        check(result.returncode == 77 and "SKIP" in result.stdout,
              "Windows self-update wrapper skips with exit 77 on this non-Windows host")

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} update manifest check(s).")
        return 1
    print("\nOK: manifest schema, fixtures, channel state (disabled placeholder or released) "
          "and the Windows skip behaviour passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
