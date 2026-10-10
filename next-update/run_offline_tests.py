#!/usr/bin/env python3
"""Run each self-contained offline regression script in deterministic order.

The test_v*.py files are executable acceptance scripts, not unittest test
cases. This runner gives users one command that actually executes them and
propagates any failing script as a nonzero exit status.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    scripts = sorted(ROOT.glob("test_*.py"))
    if not scripts:
        print("No offline test_*.py scripts found.", file=sys.stderr)
        return 2

    failures: list[tuple[Path, int]] = []
    print(f"Running {len(scripts)} offline regression scripts from {ROOT}.", flush=True)
    for script in scripts:
        print(f"\n========== {script.name} ==========", flush=True)
        result = subprocess.run(
            [sys.executable, "-u", str(script)],
            cwd=ROOT,
            check=False,
        )
        if result.returncode != 0:
            failures.append((script, result.returncode))
            print(f"[FAIL] {script.name} exited with {result.returncode}.", flush=True)
        else:
            print(f"[PASS] {script.name}", flush=True)

    print(f"\nFinished: {len(scripts) - len(failures)}/{len(scripts)} passed.")
    if failures:
        for script, code in failures:
            print(f"  {script.name}: exit {code}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
