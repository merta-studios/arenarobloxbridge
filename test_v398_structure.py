#!/usr/bin/env python3
"""Offline structure check for Arena Roblox Bridge 3.9.8.

No PowerShell is invoked. The generated Roblox plugin is parsed with
luaparser, each XAML here-string is parsed as XML, and high-risk architecture
markers are checked directly in the PowerShell source.

Run:
    python -m pip install luaparser
    python test_v398_structure.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "ArenaBridge.ps1"
VERSION = "3.9.8"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def plugin_source(source: str) -> str:
    marker = "function Get-PluginSource {\n@'\n"
    begin = source.find(marker)
    require(begin >= 0, "Get-PluginSource here-string was not found")
    begin += len(marker)
    end = source.find("\n'@\n}", begin)
    require(end >= 0, "Get-PluginSource here-string is not closed")
    return source[begin:end]


def xaml_blocks(source: str) -> list[str]:
    # All UI XAML is an @' ... '@ here-string beginning with Window/XML.
    return re.findall(r"@'\n((?:<\?xml[^\n]*\n)?<Window[\s\S]*?\n</Window>)\n'@", source)


def main() -> int:
    raw = PS1.read_bytes()
    require(raw.startswith(b"\xef\xbb\xbf"), "ArenaBridge.ps1 must retain its UTF-8 BOM")
    source = raw.decode("utf-8-sig")
    version = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    require(version["version"] == VERSION, "version.json is not 3.9.8")
    require("3.9.5" not in source, "stale 3.9.5 literal remains in ArenaBridge.ps1")

    # Stale FUNCTIONAL version literals (history comments may mention 3.9.7).
    stale_literals = [
        "DocsVersion     = '3.9.7'",
        'local ARENA_VERSION  = "3.9.7"',
        "bridgeVersion = '3.9.7'",
        "serverVersion = '3.9.7'",
        "version = '3.9.7'",
        "$versionText = '3.9.7'",
        "$verText = '3.9.7'",
        'Arena Studio Bridge - Studio Plugin  (Version 3.9.7)',
        'Text="Arena Roblox Bridge - Version 3.9.7"',
        "# Arena Roblox Bridge  -  Version 3.9.7",
    ]
    for marker in stale_literals:
        require(marker not in source, f"stale 3.9.7 literal remains: {marker}")

    required_markers = [
        "DocsVersion     = '3.9.8'",
        'local ARENA_VERSION  = "3.9.8"',
        "bridgeVersion = '3.9.8'",
        "serverVersion = '3.9.8'",
        "version = '3.9.8'",
        "$versionText = '3.9.8'",
        "$verText = '3.9.8'",
        'Text="Arena Roblox Bridge - Version 3.9.8"',
        "SESSION_REPORTER_SOURCE",
        "SESSION_CLIENT_REPORTER_SOURCE",
        '\"#ARENA# \"',
        'kind="hello"',
        "StudioTestService:GetTestArgs()",
        "waitForEditMode(false, 20)",
        "editRunServiceStop",
        "reporterEndTest",
        "PLAY_STOP_NEEDS_USER",
        "REPORTER_NOT_CONNECTED",
        "session_diag",
        "SharedTableService",
        "sessionChannelCommand",
        "sessionDiagnosticsData",
        "reporterSeenInOutput",
        "reporterVariantUsed",
        "sweepEditReporterCopies",
        "testSessionActive",
        "stopped_by_arena_bridge",
        "Get-Utf8QueryValue",
        "[System.Web.HttpUtility]::UrlDecode",
        "LateResults",
        "PlayRetryDedupe",
        "plugin outdated - Tests warten",
        "Get-RawGitHubText",
        "$content -is [byte[]]",
        "[char]0xFEFF",
    ]
    for marker in required_markers:
        require(marker in source, f"required 3.9.8 marker missing: {marker}")

    # A no-HTTP fallback must not return an instructions-to-enable-HTTP error.
    start_chunk = source[source.index("local function startPlay"):source.index("local function stopPlay")]
    require("HttpEnabled" in start_chunk and "installSessionReporters" in start_chunk,
            "play_start does not install its no-HTTP reporters")
    require("waitForEditMode(false, 20)" in start_chunk,
            "play_start does not use EditModeActive as its 20-second success oracle")
    require("Allow HTTP Requests" not in start_chunk,
            "play_start still asks the user to change HTTP settings")
    require("reporterVariant = variant" in start_chunk or "reporterVariantUsed = variant" in start_chunk,
            "play_start does not carry the reporter variant through")

    # The stop ladder: reporter channel first, edit RunService:Stop() fallback,
    # then the bounded PLAY_STOP_NEEDS_USER handover (never an endless loop).
    stop_start = source.index("local function finishStopSuccess")
    stop_chunk = source[stop_start:stop_start + 8000]
    require("sessionChannelCommand" in stop_chunk and "reporterEndTest" in stop_chunk,
            "play_stop does not try the reporter command channel first")
    require("editRunServiceStop" in stop_chunk, "play_stop lost the edit RunService:Stop() fallback")
    require("PLAY_STOP_NEEDS_USER" in stop_chunk, "play_stop lost the bounded user handover")
    require("sweepEditReporterCopies" in stop_chunk, "play_stop does not sweep leftover reporter copies")

    # Session-aware tool guards (B4 of the 3.9.6 live test).
    require('failCode("REPORTER_NOT_CONNECTED"' in source,
            "no tool answers REPORTER_NOT_CONNECTED for a live session without reporter")

    # Lua parser check – this verifies the actual generated plugin, not a copy.
    try:
        from luaparser import ast  # type: ignore
    except ImportError as exc:
        raise AssertionError("luaparser is required: python -m pip install luaparser") from exc
    lua = plugin_source(source)
    ast.parse(lua)

    # The session helpers are Lua strings INSIDE the plugin: parse each of
    # them separately as well (a syntax error there would only fire live).
    embedded = re.findall(r"local (SESSION_AGENT_SOURCE|SESSION_CLIENT_REPORTER_SOURCE|SESSION_REPORTER_SOURCE|CLIENT_AGENT_SOURCE) = \[==\[(.+?)\]==\]", lua, re.S)
    names = [name for name, _ in embedded]
    for wanted in ("SESSION_AGENT_SOURCE", "SESSION_CLIENT_REPORTER_SOURCE", "SESSION_REPORTER_SOURCE"):
        require(wanted in names, f"embedded source missing from the plugin: {wanted}")
    for name, chunk in embedded:
        try:
            ast.parse(chunk)
        except Exception as exc:
            raise AssertionError(f"embedded Lua source {name} does not parse: {exc}") from exc
    # CLIENT_SOURCE lives nested one level deeper inside SESSION_AGENT_SOURCE.
    nested = re.findall(r"local CLIENT_SOURCE = \[=\[(.+?)\]=\]", lua, re.S)
    require(len(nested) == 1, "nested CLIENT_SOURCE not found")
    ast.parse(nested[0])

    blocks = xaml_blocks(source)
    require(len(blocks) == 3, f"expected 3 XAML Window blocks, found {len(blocks)}")
    for index, block in enumerate(blocks, 1):
        try:
            ET.fromstring(block)
        except ET.ParseError as exc:
            raise AssertionError(f"XAML block {index} is not XML: {exc}") from exc

    print("OK: 3.9.8 structure, Lua and XAML validation passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
