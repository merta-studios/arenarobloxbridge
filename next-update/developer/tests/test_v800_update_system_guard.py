#!/usr/bin/env python3
"""Guard for the protected self-update system (see update-system/PROTECTED.md).

Normal run (default):
    Compares every protected file with update-system/update_system_guard.lock.json
    and re-checks hard invariants. It never modifies the lock file.

Rebaseline (only after an explicit user approval, see PROTECTED.md):
    python developer/tests/test_v800_update_system_guard.py --rebaseline --approval "<text, >= 30 chars>"
    Recomputes the hashes and appends the approval (date + text) to the lock file.
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
CHANNELS = ROOT / "update-system" / "channels"
BLOCK_START = "# >>> ARENA-UPDATE-INTEGRATION >>>"
BLOCK_END = "# <<< ARENA-UPDATE-INTEGRATION <<<"
MIN_APPROVAL_CHARS = 30
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("  ok   " if condition else "  FAIL ") + message)
    if not condition:
        FAILURES.append(message)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def integration_block_text() -> str:
    """The protected block, from the start marker to the end marker (LF-normalised)."""
    text = APP.read_bytes().decode("utf-8-sig").replace("\r\n", "\n")
    begin = text.find(BLOCK_START)
    end = text.find(BLOCK_END, begin)
    if begin < 0 or end < 0:
        return ""
    return text[begin:end + len(BLOCK_END)]


def protected_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(p for p in (ROOT / "update-system").rglob("*") if p.is_file()):
        if path == LOCK:
            continue
        hashes[rel(path)] = sha256_bytes(path.read_bytes())
    for path in (BUILDER, ROOT / "developer" / "tests" / "run_offline_tests.py",
                 ROOT / "developer" / "tests" / "requirements-test.txt",
                 ROOT / "developer" / "tests" / "Invoke-SelfUpdateSmoke.ps1"):
        hashes[rel(path)] = sha256_bytes(path.read_bytes())
    for path in sorted((ROOT / "developer" / "tests").glob("test_v800_*.py")):
        hashes[rel(path)] = sha256_bytes(path.read_bytes())
    for path in sorted((ROOT / "developer" / "tests" / "fixtures" / "update").rglob("*")):
        if path.is_file():
            hashes[rel(path)] = sha256_bytes(path.read_bytes())
    hashes["app/ArenaBridge.ps1#ARENA-UPDATE-INTEGRATION"] = sha256_bytes(integration_block_text().encode("utf-8"))
    return hashes


def static_invariants() -> None:
    updater = UPDATER.read_text(encoding="ascii")
    check("Stop-Process" not in updater and "taskkill" not in updater and ".Kill(" not in updater,
          "updater never stops or kills a process")
    check("Invoke-WebRequest" not in updater and "Invoke-RestMethod" not in updater,
          "updater uses only the audited download function")
    check("$request.AllowAutoRedirect = $false" in updater,
          "updater follows redirects only through its own host check")
    check("$script:UpdaterVersion = '1.1.0'" in updater, "updater version is 1.1.0")
    check(all(ord(ch) < 128 for ch in updater), "updater is pure ASCII (PS 5.1 safe)")

    block = integration_block_text()
    check(block != "" and APP.read_text(encoding="utf-8-sig").count(BLOCK_START) == 1,
          "exactly one integration block exists in the app")
    check("ARENABRIDGE_SELFUPDATE_TEST_MANIFEST" in block
          and "if ([string]$script:TestFixtureBuild -cne '1') { return '' }" in block,
          "the test-manifest environment variable is gated by the build flag")
    check("Stop-Process" not in block and "taskkill" not in block, "the app block never stops a process")
    for marker in ("__ARENA_UPDATE_CHANNEL__", "__ARENA_UPDATER_BASE64__", "__ARENA_UPDATER_SHA256__",
                   "__ARENA_TEST_FIXTURE_BUILD__"):
        check(block.count(marker) == 1, f"placeholder {marker} appears exactly once in the block")
    check("channels/" not in APP.read_text(encoding="utf-8-sig"),
          "the app never references channel files directly")

    builder = BUILDER.read_text(encoding="utf-8-sig")
    check("must never write inside the repository" in builder and "release\\" in builder,
          "test-fixture builds are forbidden from writing into release\\")
    check("'$script:TestFixtureBuild = ''0'''" in builder,
          "normal builds inject the test flag as 0 (no test path in a normal EXE)")

    for channel in ("beta", "stable"):
        data = json.loads((CHANNELS / f"{channel}.json").read_text(encoding="utf-8"))
        check(data.get("enabled") is False and data.get("testFixture") is False,
              f"{channel}.json is disabled and not a fixture")

    schema = json.loads((CHANNELS / "manifest.schema.json").read_text(encoding="utf-8"))
    check("testFixture" in schema.get("properties", {}) and schema.get("additionalProperties") is False,
          "manifest schema has the testFixture flag and rejects unknown fields")


def load_lock() -> dict:
    if not LOCK.is_file():
        return {}
    return json.loads(LOCK.read_text(encoding="utf-8"))


def rebaseline(approval: str) -> int:
    if len(approval.strip()) < MIN_APPROVAL_CHARS:
        print(f"REFUSED: --approval needs at least {MIN_APPROVAL_CHARS} characters of explicit approval text.")
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
        "scope": "update-system/ and the update integration points listed in update-system/PROTECTED.md",
        "approvals": approvals,
        "files": protected_hashes(),
    }
    LOCK.write_text(json.dumps(lock_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"Lock rebaselined with {len(lock_data['files'])} protected entries and {len(approvals)} approval(s).")
    return 0


def main(argv: list[str]) -> int:
    if "--rebaseline" in argv:
        approval = ""
        if "--approval" in argv:
            index = argv.index("--approval")
            approval = argv[index + 1] if index + 1 < len(argv) else ""
        return rebaseline(approval)

    print("Guard: protected update-system files")
    lock = load_lock()
    check(bool(lock), "lock file exists and is readable")
    if lock:
        check(bool(lock.get("approvals")), "lock contains at least one explicit approval")
        expected = lock.get("files", {})
        current = protected_hashes()
        changed = sorted(k for k in expected if k in current and expected[k] != current[k])
        added = sorted(k for k in current if k not in expected)
        removed = sorted(k for k in expected if k not in current)
        check(not changed, "no protected file changed: " + (", ".join(changed) if changed else "ok"))
        check(not added, "no protected file was added: " + (", ".join(added) if added else "ok"))
        check(not removed, "no protected file was removed: " + (", ".join(removed) if removed else "ok"))
        if changed or added or removed:
            print("  -> Stop: this needs an explicit user approval and a rebaseline, see update-system/PROTECTED.md.")
    static_invariants()

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} update-system guard check(s).")
        return 1
    print("\nOK: update-system guard passed (protected files unchanged, invariants intact).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
