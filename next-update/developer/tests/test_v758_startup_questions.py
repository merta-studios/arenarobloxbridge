#!/usr/bin/env python3
"""Offline regression checks for Arena Roblox Bridge 7.5.9.

Covers the two requested mini-update areas without requiring Windows, Arena,
Roblox Studio, or a compiled updater EXE:

1. Bridge-only user questions: the first session payload has the full
   ask_user/confirm_action docs, every tool response repeats the mandatory
   protocol, and chat is explicitly not an answer channel.
2. Updater-only autostart: the Bridge discovers ArenaBridge.exe, migrates the
   current user's stale PowerShell/duplicate startup entries to one Run value,
   and refuses to create a PowerShell fallback if no updater can be found.
3. Single instance: duplicate launchers cannot open a second Bridge window;
   the self-update restart releases the mutex before starting its replacement.

These checks inspect structure only. A real Windows logon/startup, registry,
mutex, compiled updater, and Roblox Studio acceptance test are still required.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = ROOT / "app"
PS1 = APP_ROOT / "ArenaBridge.ps1"
VERSION = "7.7.2"
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("[OK]   " if condition else "[FAIL] ") + message)
    if not condition:
        FAILURES.append(message)


def region(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    stop = source.index(end, begin)
    return source[begin:stop]


def main() -> int:
    raw = PS1.read_bytes()
    check(raw.startswith(b"\xef\xbb\xbf"), "PowerShell source retains its UTF-8 BOM")
    check(b"\r\n" not in raw, "PowerShell source retains LF line endings")
    source = raw.decode("utf-8-sig")
    metadata = json.loads((APP_ROOT / "version.json").read_text(encoding="utf-8"))
    check(metadata.get("version") == VERSION, f"version.json matches {VERSION}")
    latest_note = str(metadata.get("notes", [""])[0])
    check(latest_note.startswith("• 7.7.2") and "PROJEKT ZUERST" in latest_note,
          "the newest release note documents the current project-first update")
    check(any(str(note).startswith("• 7.6.2") and "open_cloud" in str(note)
              for note in metadata.get("notes", [])),
          "historical Open Cloud key scope remains documented")
    prior_notes = [str(note) for note in metadata.get("notes", [])[1:]]
    check(any("7.5.9" in note and "creator_dashboard" in note for note in prior_notes),
          "the historical 7.5.9 Creator Dashboard release note remains available")
    check(any("7.5.8" in note and "ask_user" in note and "ArenaBridge.exe" in note
              for note in prior_notes),
          "the historical 7.5.8 question/updater release note remains available")

    # ------------------------------------------------------------------
    # 1) Ask through the Bridge, never as a normal chat question
    # ------------------------------------------------------------------
    protocol = region(source, "function Get-BridgeAskUserProtocol {", "function Get-BridgeGuides {")
    guides = region(source, "function Get-BridgeGuides {", "function Get-SessionStartPackage {")
    session_start = region(source, "function Get-SessionStartPackage {", "function Get-Manifest {")
    envelope_start = source.index("function New-Envelope($sessionId) {")
    envelope = source[envelope_start:envelope_start + 1800]
    tool_docs = region(source, "function Get-ToolDocs {", "function Get-BridgeGuides {")

    check("required = $true" in protocol and "Never ask the user" in protocol
          and "Do not fall back to a normal chat question" in protocol,
          "shared question protocol is mandatory and rejects chat fallback")
    check("askUserProtocol = $askUserProtocol" in guides
          and "BRIDGE-ONLY QUESTIONS (mandatory, 7.5.8)" in guides
          and "Never pose the question in normal chat" in guides,
          "guide/importantRules explicitly require Bridge questions")
    check("ALWAYS use ask_user/confirm_action through this Bridge" in session_start
          and "'ask_user','confirm_action'" in session_start,
          "first session response includes the rule and full question-tool docs")
    check("askUserProtocol = $askUserProtocol" in envelope,
          "every tool response repeats the Bridge-only question protocol")
    check("PFLICHT statt Chat-Frage" in tool_docs
          and "nicht in den Chat ausweichen" in tool_docs,
          "ask_user and confirm_action descriptions make Bridge use the default")
    check("Do NOT ask in normal chat" in source and "same askId" in source,
          "open question instructions resume the same askId rather than switching channels")

    # ------------------------------------------------------------------
    # 2) Updater-only autostart; never register powershell.exe -File
    # ------------------------------------------------------------------
    updater_validate = region(source, "function Test-BridgeUpdaterExecutable {", "function Get-BridgeUpdaterPathFromCommandLine {")
    startup_scan = region(source, "function Get-BridgeStartupItems {", "function Get-BridgeUpdaterPathFromParent {")
    registry_paths = region(source, "$script:BridgeStartupRegistryPaths = @(", "$script:BridgeStartupApprovedPaths = @(")
    resolve = region(source, "function Resolve-BridgeUpdaterExePath {", "function Save-BridgeUpdaterExePath {")
    remove = region(source, "function Remove-BridgeStartupEntries {", "function Set-StartupEnabled {")
    set_startup = region(source, "function Set-StartupEnabled {", "function Get-StartupEnabled {")
    get_startup = region(source, "function Get-StartupEnabled {", "# Alte Installationen werden")

    check("$baseName -ine 'ArenaBridge'" in updater_validate
          and "ArenaRobloxBridge'" not in updater_validate
          and "ArenaBridgeUpdater'" not in updater_validate
          and "Test-Path -LiteralPath $candidate -PathType Leaf" in updater_validate,
          "only an existing, named updater EXE is accepted")
    check("Get-BridgeUpdaterPathFromParent" in resolve
          and "Get-BridgeStartupItems" in resolve
          and "UpdaterPathFile" in resolve
          and "ArenaBridge.exe" in resolve,
          "updater path can come from the parent EXE, existing startup entries, or saved local path")
    check("HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" in registry_paths
          and "RunOnce" in registry_paths
          and "WScript.Shell" in startup_scan
          and "powershell.exe" not in set_startup,
          "current-user Run/RunOnce and Startup shortcuts are scanned, not launched through PowerShell")
    check("Remove-BridgeStartupEntries" in set_startup
          and "Resolve-BridgeUpdaterExePath" in set_startup
          and "ArenaRobloxBridge' -Value ('\"'" in set_startup
          and "powershell.exe" not in set_startup
          and "-File" not in set_startup,
          "enabling autostart writes one quoted updater EXE and no PowerShell script command")
    check("StartupApprovedPaths" in remove
          and "Remove-ItemProperty" in remove
          and "Remove-Item -LiteralPath" in remove,
          "duplicate registry entries, disabled markers, and per-user Startup wrappers are cleaned")
    check("Resolve-BridgeUpdaterExePath" in get_startup
          and "Set-StartupEnabled -Enabled $true -UpdaterPath $updater" in get_startup
          and "Remove-BridgeStartupEntries" in get_startup,
          "legacy startup is migrated automatically, or safely disabled if no updater exists")
    check("try { [void](Get-StartupEnabled) }" in source,
          "migration runs during Bridge startup, not only after opening Settings")

    # ------------------------------------------------------------------
    # 3) Duplicate process protection and update handoff
    # ------------------------------------------------------------------
    lock_start = source.index("$script:BridgeSingleInstanceMutex = $null")
    # The isolated EXE smoke-test branch may load WPF before the normal
    # single-instance guard, then exits without starting the Bridge. Check the
    # first WPF load on the normal path, after the guard itself.
    wpf_load = source.index("Add-Type -AssemblyName PresentationFramework", lock_start)
    check(lock_start < wpf_load
          and "[System.Threading.Mutex]::new($false, $mutexName)" in source
          and "$script:BridgeSingleInstanceMutex.WaitOne(0)" in source
          and "SINGLE_INSTANCE_DUPLICATE" in source
          and "exit 0" in source[lock_start:wpf_load],
          "duplicate Bridge processes exit before WPF creates a second window")
    updater_restart = region(source, "function Invoke-AutostartSelfUpdate {", "function Get-BridgeSettingsFile {")
    check(updater_restart.index("Release-BridgeSingleInstanceMutex")
          < updater_restart.index("Start-Process -FilePath $psExe"),
          "the current process releases the mutex before an update restart takes it")

    if FAILURES:
        print(f"\n{len(FAILURES)} regression check(s) failed.")
        return 1
    print("\nOK: 7.5.8 Bridge question protocol, updater-only startup and single-instance checks passed in the 7.5.9 release.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
