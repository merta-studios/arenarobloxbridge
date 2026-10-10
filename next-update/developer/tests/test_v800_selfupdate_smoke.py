#!/usr/bin/env python3
"""Windows-only wrapper for Invoke-SelfUpdateSmoke.ps1 (7.7.0 self-update).

Exit 0  = every self-update check passed on Windows.
Exit 1  = at least one check failed.
Exit 77 = skipped: this host is not Windows, so the PowerShell 5.1 harness cannot run.

The harness builds two test-fixture EXEs with the real builder, serves them from
127.0.0.1 and never touches release/, channels/*.json or the real user data.
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "developer" / "tests" / "Invoke-SelfUpdateSmoke.ps1"
SKIP = 77


def windows_powershell() -> str:
    system_root = os.environ.get("WINDIR") or os.environ.get("SystemRoot") or r"C:\Windows"
    return os.path.join(system_root, "System32", "WindowsPowerShell", "v1.0", "powershell.exe")


def main() -> int:
    if os.name != "nt" and platform.system() != "Windows":
        print("SKIP: test_v800_selfupdate_smoke needs Windows PowerShell 5.1 (exit 77).")
        return SKIP
    if not HARNESS.is_file():
        print(f"FAIL: harness missing: {HARNESS}")
        return 1
    result = subprocess.run(
        [windows_powershell(), "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HARNESS)],
        cwd=ROOT,
        check=False,
    )
    if result.returncode == SKIP:
        print("SKIP: harness reported non-Windows host (exit 77).")
        return SKIP
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
