#!/usr/bin/env python3
"""Offline checks for the 7.7.0 update manifests (schema + fixtures + channel state).

No network and no PowerShell. Proves that:
  * the schema accepts the valid fixtures and rejects every invalid one,
  * the public channel files stay disabled with no artifact coordinates,
  * the Windows wrapper skips cleanly (exit 77) on non-Windows hosts.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "developer" / "tests"
CHANNELS = ROOT / "update-system" / "channels"
FIXTURES = TESTS / "fixtures" / "update"
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
        data = json.loads((CHANNELS / f"{channel}.json").read_text(encoding="utf-8"))
        artifact = data.get("artifact", {})
        check(data.get("channel") == channel and data.get("enabled") is False,
              f"{channel}.json is an explicitly disabled placeholder")
        check(data.get("testFixture") is False, f"{channel}.json is not a test fixture")
        check(data.get("minimumUpdaterVersion") == "1.1.0", f"{channel}.json requires updater 1.1.0")
        check(artifact.get("url") == "" and artifact.get("sha256") == "" and artifact.get("sizeBytes") == 0,
              f"{channel}.json publishes no artifact coordinates")
        check(not list(v.iter_errors(data)), f"{channel}.json validates against the schema")

    wrapper = TESTS / "test_v800_selfupdate_smoke.py"
    if sys.platform != "win32":
        result = subprocess.run([sys.executable, str(wrapper)], cwd=ROOT, capture_output=True, text=True, check=False)
        check(result.returncode == 77 and "SKIP" in result.stdout,
              "Windows self-update wrapper skips with exit 77 on this non-Windows host")

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} update manifest check(s).")
        return 1
    print("\nOK: manifest schema, fixtures, disabled channels and the Windows skip behaviour passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
