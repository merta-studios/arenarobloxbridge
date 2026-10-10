#!/usr/bin/env python3
"""Run every self-contained offline regression script in deterministic order.

Tests live under developer/tests; ROOT is the next-update project directory so
all scripts can locate app/, builder/, update-system/ and documentation files.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Exit code 77 = "skipped, not applicable on this host" (e.g. Windows-only tests on Linux).
SKIP_EXIT_CODE = 77
TEST_DIR = Path(__file__).resolve().parent


def main() -> int:
    scripts = sorted(TEST_DIR.glob("test_*.py"))
    if not scripts:
        print("No offline test_*.py scripts found in developer/tests.", file=sys.stderr)
        return 2

    failures: list[tuple[Path, int]] = []
    skipped: list[Path] = []
    print(f"Running {len(scripts)} offline regression scripts from {TEST_DIR}.", flush=True)
    for script in scripts:
        print(f"\n========== {script.name} ==========", flush=True)
        result = subprocess.run(
            [sys.executable, "-u", str(script)],
            cwd=PROJECT_ROOT,
            check=False,
        )
        if result.returncode == SKIP_EXIT_CODE:
            skipped.append(script)
            print(f"[SKIP] {script.name} (exit {SKIP_EXIT_CODE}: not applicable on this host).", flush=True)
        elif result.returncode != 0:
            failures.append((script, result.returncode))
            print(f"[FAIL] {script.name} exited with {result.returncode}.", flush=True)
        else:
            print(f"[PASS] {script.name}", flush=True)

    ran = len(scripts) - len(skipped)
    print(f"\nFinished: {ran - len(failures)}/{ran} run tests passed; {len(skipped)} skipped (exit {SKIP_EXIT_CODE}).")
    if failures:
        for script, code in failures:
            print(f"  {script.name}: exit {code}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
