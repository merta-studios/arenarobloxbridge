#!/usr/bin/env python3
"""Offline structure check for Arena Roblox Bridge 4.0.1.

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
VERSION = "4.0.1"

# Luau allows at most 200 local variables per function scope. The plugin's top
# level is ONE such scope; exceeding it makes Studio refuse to compile the
# plugin ("Out of local registers ... exceeded limit 200"), so it never
# connects and the place list stays empty. 4.0.0 fixed a regression that had
# pushed the count to 202. Keep a safety margin below the hard limit.
LUAU_LOCAL_LIMIT = 200


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


def count_top_level_locals(lua: str) -> int:
    """Count column-0 `local` declarations in the plugin's main chunk.

    Embedded long-bracket strings ([==[ ... ]==], [=[ ... ]=]) are separate
    Luau chunks, so their contents must not be counted against the top-level
    scope. They are stripped (newlines preserved) before counting.
    """
    out: list[str] = []
    i = 0
    n = len(lua)
    while i < n:
        m = re.match(r"\[(=*)\[", lua[i:])
        if m:
            closer = "]" + m.group(1) + "]"
            j = lua.find(closer, i + m.end())
            if j == -1:
                out.append(lua[i:])
                break
            chunk = lua[i : j + len(closer)]
            out.append("\n" * chunk.count("\n"))
            i = j + len(closer)
        else:
            out.append(lua[i])
            i += 1
    clean = "".join(out)

    count = 0
    for line in clean.splitlines():
        if not line.startswith("local "):
            continue
        decl = line[len("local ") :]
        if decl.startswith("function "):
            count += 1
        else:
            lhs = decl.split("=")[0]
            count += len([nm for nm in lhs.split(",") if nm.strip()])
    return count


def xaml_blocks(source: str) -> list[str]:
    # All UI XAML is an @' ... '@ here-string beginning with Window/XML.
    return re.findall(r"@'\n((?:<\?xml[^\n]*\n)?<Window[\s\S]*?\n</Window>)\n'@", source)


def main() -> int:
    raw = PS1.read_bytes()
    require(raw.startswith(b"\xef\xbb\xbf"), "ArenaBridge.ps1 must retain its UTF-8 BOM")
    source = raw.decode("utf-8-sig")
    version = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    require(version["version"] == VERSION, "version.json is not 4.0.1")
    require("3.9.5" not in source, "stale 3.9.5 literal remains in ArenaBridge.ps1")

    # Stale FUNCTIONAL version literals (history comments may mention 3.9.8).
    stale_literals = [
        "DocsVersion     = '3.9.8'",
        'local ARENA_VERSION  = "3.9.8"',
        "bridgeVersion = '3.9.8'",
        "serverVersion = '3.9.8'",
        "version = '3.9.8'",
        "$versionText = '3.9.8'",
        "$verText = '3.9.8'",
        'Arena Studio Bridge - Studio Plugin  (Version 3.9.8)',
        'Text="Arena Roblox Bridge - Version 3.9.8"',
        "# Arena Roblox Bridge  -  Version 3.9.8",
    ]
    for marker in stale_literals:
        require(marker not in source, f"stale 3.9.8 literal remains: {marker}")

    # Stale FUNCTIONAL 4.0.0 literals (history comments may mention 4.0.0).
    stale_400_literals = [
        "DocsVersion     = '4.0.0'",
        'local ARENA_VERSION  = "4.0.0"',
        "bridgeVersion = '4.0.0'",
        "serverVersion = '4.0.0'",
        "version = '4.0.0'",
        "$versionText = '4.0.0'",
        "$verText = '4.0.0'",
        'Arena Studio Bridge - Studio Plugin  (Version 4.0.0)',
        'Text="Arena Roblox Bridge - Version 4.0.0"',
        "# Arena Roblox Bridge  -  Version 4.0.0",
    ]
    for marker in stale_400_literals:
        require(marker not in source, f"stale 4.0.0 literal remains: {marker}")

    required_markers = [
        "DocsVersion     = '4.0.1'",
        'local ARENA_VERSION  = "4.0.1"',
        "bridgeVersion = '4.0.1'",
        "serverVersion = '4.0.1'",
        "version = '4.0.1'",
        "$versionText = '4.0.1'",
        "$verText = '4.0.1'",
        'Text="Arena Roblox Bridge - Version 4.0.1"',
        # 4.0.0: the config table that keeps the top-level local count in check.
        "local ARENA_CFG = {",
        "ARENA_CFG.POLL_WAIT",
        "ARENA_CFG.CHUNK_SIZE",
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
        "SharedTableRegistry",
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

    # 4.0.0 regression guard: the plugin's top-level chunk is ONE Luau scope.
    # Count its column-0 `local` declarations (ignoring embedded long-bracket
    # strings, which are separate chunks) and require it to stay under Luau's
    # hard limit of 200 - otherwise Studio silently refuses to compile the
    # plugin and the place list stays empty.
    top_level_locals = count_top_level_locals(lua)
    require(
        top_level_locals < LUAU_LOCAL_LIMIT,
        f"plugin top-level declares {top_level_locals} locals; Luau's hard "
        f"limit is {LUAU_LOCAL_LIMIT} (the plugin would fail to compile and "
        f"never connect). Bundle constants into a table like ARENA_CFG.",
    )

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

    print("OK: 4.0.1 structure, Lua and XAML validation passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
