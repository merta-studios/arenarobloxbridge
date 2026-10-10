#!/usr/bin/env python3
"""Offline structure check for Arena Roblox Bridge 7.6.3.

No PowerShell is invoked. The generated Roblox plugin is parsed with
luaparser, each XAML here-string is parsed as XML, and high-risk architecture
markers are checked directly in the PowerShell source.

Run:
    python -m pip install -r requirements-test.txt
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
VERSION = "7.6.3"

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
    require(version["version"] == VERSION, f"version.json is not {VERSION}")
    release_notes = "\n".join(str(note) for note in version.get("notes", []))
    latest_note = str(version.get("notes", [""])[0])
    for marker in ("7.6.3", "Nutzerwünsche", "Place-Konventionen", "keine Pflicht",
                   "keine erfundene 0 %", "API-Pfade", "IP-Einrichtung",
                   "Root-Updater bleibt unangetastet", "EXEs baut der Nutzer selbst"):
        require(marker in latest_note, f"7.6.3 release note omits current scope: {marker}")
    require("7.6.2" in release_notes and "creator_dashboard" in release_notes
            and "game-pass:read" in release_notes and "ask_user" in release_notes,
            "version history omits the Open Cloud/user-channel technical baseline")
    require("NOTIFICATION_UNVERIFIED" in source and "progress-diagnose.txt" in source,
            "independent notification-verification and progress-diagnosis code was lost")
    require("DRAFT_GRADE_RISK" not in latest_note and "ORGANIC_AUDIT_REQUIRED" not in latest_note,
            "latest release note describes superseded quality gates as active")

    # 6.1.1 shipped seven accidental fragments after the intended final exit,
    # including a bare closing parenthesis. Windows PowerShell parses the
    # complete file before it can show the updater notice or main WPF window,
    # so that one trailing token made the program appear not to start at all.
    # Keep the intentional final fallback exit as the actual physical end of
    # the script; no source may be appended after it.
    expected_final_lines = [
        "# Sicherheitsnetz (Version 3.4): Falls das Closed-Ereignis doch nicht zum",
        "# Exit gefuehrt haben sollte, wird der Prozess hier garantiert beendet.",
        "try { Write-RuntimeLog '=== Programmende ===' } catch {}",
        "[System.Environment]::Exit(0)",
    ]
    require(
        source.rstrip().splitlines()[-4:] == expected_final_lines,
        "ArenaBridge.ps1 has content after or instead of its intentional final fallback exit",
    )
    require("3.9.5" not in source, "stale 3.9.5 literal remains in ArenaBridge.ps1")

    # Stale FUNCTIONAL 5.2 literals (history comments may mention 5.2).
    stale_52_literals = [
        "DocsVersion     = '5.2'",
        'local ARENA_VERSION  = "5.2"',
        "bridgeVersion = '5.2'",
        "serverVersion = '5.2'",
        "version = '5.2'",
        "$versionText = '5.2'",
        "$verText = '5.2'",
        'Arena Studio Bridge - Studio Plugin  (Version 5.2)',
        'Text="Arena Roblox Bridge - Version 5.2"',
        "# Arena Roblox Bridge  -  Version 5.2",
    ]
    for marker in stale_52_literals:
        require(marker not in source, f"stale 5.2 literal remains: {marker}")

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

    # Stale FUNCTIONAL 4.0.1 literals (history comments may mention 4.0.1).
    stale_401_literals = [
        "DocsVersion     = '4.0.1'",
        'local ARENA_VERSION  = "4.0.1"',
        "bridgeVersion = '4.0.1'",
        "serverVersion = '4.0.1'",
        "version = '4.0.1'",
        "$versionText = '4.0.1'",
        "$verText = '4.0.1'",
        'Arena Studio Bridge - Studio Plugin  (Version 4.0.1)',
        'Text="Arena Roblox Bridge - Version 4.0.1"',
        "# Arena Roblox Bridge  -  Version 4.0.1",
    ]
    for marker in stale_401_literals:
        require(marker not in source, f"stale 4.0.1 literal remains: {marker}")

    # Stale FUNCTIONAL 4.0.2 literals (history comments may mention 4.0.2).
    stale_402_literals = [
        "DocsVersion     = '4.0.2'",
        'local ARENA_VERSION  = "4.0.2"',
        "bridgeVersion = '4.0.2'",
        "serverVersion = '4.0.2'",
        "version = '4.0.2'",
        "$versionText = '4.0.2'",
        "$verText = '4.0.2'",
        'Arena Studio Bridge - Studio Plugin  (Version 4.0.2)',
        'Text="Arena Roblox Bridge - Version 4.0.2"',
        "# Arena Roblox Bridge  -  Version 4.0.2",
    ]
    for marker in stale_402_literals:
        require(marker not in source, f"stale 4.0.2 literal remains: {marker}")

    # Stale FUNCTIONAL 4.0.4 literals (history comments may mention 4.0.4).
    stale_404_literals = [
        "DocsVersion     = '4.0.4'",
        'local ARENA_VERSION  = "4.0.4"',
        "bridgeVersion = '4.0.4'",
        "serverVersion = '4.0.4'",
        "version = '4.0.4'",
        "$versionText = '4.0.4'",
        "$verText = '4.0.4'",
        'Arena Studio Bridge - Studio Plugin  (Version 4.0.4)',
        'Text="Arena Roblox Bridge - Version 4.0.4"',
        "# Arena Roblox Bridge  -  Version 4.0.4",
    ]
    for marker in stale_404_literals:
        require(marker not in source, f"stale 4.0.4 literal remains: {marker}")

    # Stale FUNCTIONAL 5.0.1 literals (history comments may mention 5.0.1).
    stale_501_literals = [
        "DocsVersion     = '5.0.1'",
        'local ARENA_VERSION  = "5.0.1"',
        "bridgeVersion = '5.0.1'",
        "serverVersion = '5.0.1'",
        "version = '5.0.1'",
        "$versionText = '5.0.1'",
        "$verText = '5.0.1'",
        'Arena Studio Bridge - Studio Plugin  (Version 5.0.1)',
        'Text="Arena Roblox Bridge - Version 5.0.1"',
        "# Arena Roblox Bridge  -  Version 5.0.1",
    ]
    for marker in stale_501_literals:
        require(marker not in source, f"stale 5.0.1 literal remains: {marker}")

    # Stale FUNCTIONAL 5.0.2 literals (history comments may mention 5.0.2).
    stale_502_literals = [
        "DocsVersion     = '5.0.2'",
        'local ARENA_VERSION  = "5.0.2"',
        "bridgeVersion = '5.0.2'",
        "serverVersion = '5.0.2'",
        "version = '5.0.2'",
        "$versionText = '5.0.2'",
        "$verText = '5.0.2'",
        'Arena Studio Bridge - Studio Plugin  (Version 5.0.2)',
        'Text="Arena Roblox Bridge - Version 5.0.2"',
        "# Arena Roblox Bridge  -  Version 5.0.2",
    ]
    for marker in stale_502_literals:
        require(marker not in source, f"stale 5.0.2 literal remains: {marker}")

    # Stale FUNCTIONAL 6.0 literals (history comments may mention 6.0; the
    # Liquid-Glass design markers from 6.0 stay required below, only the
    # exact version-number literals must have moved on to 6.0.3).
    stale_60_literals = [
        "DocsVersion     = '6.0'",
        'local ARENA_VERSION  = "6.0"',
        "bridgeVersion = '6.0'",
        "serverVersion = '6.0'",
        "version = '6.0'",
        "$versionText = '6.0'",
        "$verText = '6.0'",
        'Arena Studio Bridge - Studio Plugin  (Version 6.0)',
        'Text="Arena Roblox Bridge - Version 6.0"',
        # "6.0" is a string-prefix of "6.0.1", so the top banner line must be
        # matched including its trailing newline to avoid a false positive.
        "# Arena Roblox Bridge  -  Version 6.0\n",
    ]
    for marker in stale_60_literals:
        require(marker not in source, f"stale 6.0 literal remains: {marker}")

    # Stale FUNCTIONAL 6.0.1 literals (history comments may mention 6.0.1 -
    # e.g. the live-preview design notes - but every functional literal must
    # have moved on to 6.0.3).
    stale_601_literals = [
        "DocsVersion     = '6.0.1'",
        'local ARENA_VERSION  = "6.0.1"',
        "bridgeVersion = '6.0.1'",
        "bridgeVersion='6.0.1'",
        "serverVersion = '6.0.1'",
        "version = '6.0.1'",
        "$versionText = '6.0.1'",
        "$verText = '6.0.1'",
        'Arena Studio Bridge - Studio Plugin  (Version 6.0.1)',
        'Text="Arena Roblox Bridge - Version 6.0.1"',
        "Version 6.0.1 - aktuell. Beim naechsten Start",
        "# Arena Roblox Bridge  -  Version 6.0.1",
    ]
    for marker in stale_601_literals:
        require(marker not in source, f"stale 6.0.1 literal remains: {marker}")

    # Stale FUNCTIONAL 6.0.2 literals (history comments may mention 6.0.2).
    stale_602_literals = [
        "DocsVersion     = '6.0.2'",
        'local ARENA_VERSION  = "6.0.2"',
        "bridgeVersion = '6.0.2'",
        "serverVersion = '6.0.2'",
        "version = '6.0.2'",
        "$versionText = '6.0.2'",
        "$verText = '6.0.2'",
        'Arena Studio Bridge - Studio Plugin  (Version 6.0.2)',
        'Text="Arena Roblox Bridge - Version 6.0.2"',
        "Version 6.0.2 - aktuell. Beim naechsten Start",
    ]
    for marker in stale_602_literals:
        require(marker not in source, f"stale 6.0.2 literal remains: {marker}")

    # Stale FUNCTIONAL 6.0.3 literals (history comments may mention 6.0.3 -
    # e.g. the changelog header and the ps-runspace-fallback notes - but every
    # functional literal must have moved on to 6.0.4).
    stale_603_literals = [
        "DocsVersion     = '6.0.3'",
        'local ARENA_VERSION  = "6.0.3"',
        "bridgeVersion = '6.0.3'",
        "bridgeVersion='6.0.3'",
        "serverVersion = '6.0.3'",
        "version = '6.0.3'",
        "$versionText = '6.0.3'",
        "$verText = '6.0.3'",
        'Arena Studio Bridge - Studio Plugin  (Version 6.0.3)',
        'Text="Arena Roblox Bridge - Version 6.0.3"',
        "Version 6.0.3 - aktuell. Beim naechsten Start",
    ]
    for marker in stale_603_literals:
        require(marker not in source, f"stale 6.0.3 literal remains: {marker}")

    # Stale FUNCTIONAL 6.0.4 literals (history comments may mention 6.0.4 -
    # the changelog and the "was bis 6.0.4 falsch war" notes - but every
    # functional literal must have moved on to 6.0.5).
    stale_604_literals = [
        "DocsVersion     = '6.0.4'",
        'local ARENA_VERSION  = "6.0.4"',
        "bridgeVersion = '6.0.4'",
        "bridgeVersion='6.0.4'",
        "serverVersion = '6.0.4'",
        "version = '6.0.4'",
        "$versionText = '6.0.4'",
        "$verText = '6.0.4'",
        'Arena Studio Bridge - Studio Plugin  (Version 6.0.4)',
        'Text="Arena Roblox Bridge - Version 6.0.4"',
        "Version 6.0.4 - aktuell. Beim naechsten Start",
        "Laufzeit-Identitaet: Bridge-Version=6.0.4",
    ]
    for marker in stale_604_literals:
        require(marker not in source, f"stale 6.0.4 literal remains: {marker}")

    # Stale FUNCTIONAL 6.0.5 literals. The 6.0.5 changelog remains on
    # purpose, but every value consumed at runtime must have moved to 6.1.3.
    stale_605_literals = [
        "DocsVersion     = '6.0.5'",
        'local ARENA_VERSION  = "6.0.5"',
        "bridgeVersion = '6.0.5'",
        "bridgeVersion='6.0.5'",
        "serverVersion = '6.0.5'",
        "version = '6.0.5'",
        "$versionText = '6.0.5'",
        "$verText = '6.0.5'",
        'Arena Studio Bridge - Studio Plugin  (Version 6.0.5)',
        'Text="Arena Roblox Bridge - Version 6.0.5"',
        "Version 6.0.5 - aktuell. Beim naechsten Start",
        "Laufzeit-Identitaet: Bridge-Version=6.0.5",
        "Kurzbericht Fenster-Vorschau (Version 6.0.5)",
    ]
    for marker in stale_605_literals:
        require(marker not in source, f"stale functional 6.0.5 literal remains: {marker}")

    # 6.1.1 must not remain in executable version fields. It is valid in
    # historical release notes only; clients and the updater compare these
    # literals at runtime.
    stale_611_literals = [
        "DocsVersion     = '6.1.1'",
        'local ARENA_VERSION  = "6.1.1"',
        "bridgeVersion = '6.1.1'",
        "bridgeVersion='6.1.1'",
        "serverVersion = '6.1.1'",
        "version = '6.1.1'",
        "$versionText = '6.1.1'",
        "$verText = '6.1.1'",
        'Arena Studio Bridge - Studio Plugin  (Version 6.1.1)',
        'Text="Arena Roblox Bridge - Version 6.1.1"',
    ]
    for marker in stale_611_literals:
        require(marker not in source, f"stale functional 6.1.1 literal remains: {marker}")

    # 6.1.2 must not remain in executable version fields either. Its changelog
    # heading stays on purpose, but every literal the updater, the plugin and
    # the UI compare at runtime has to have moved to 6.1.3.
    stale_612_literals = [
        "DocsVersion     = '6.1.2'",
        'local ARENA_VERSION  = "6.1.2"',
        "bridgeVersion = '6.1.2'",
        "bridgeVersion='6.1.2'",
        "serverVersion = '6.1.2'",
        "version = '6.1.2'",
        "$versionText = '6.1.2'",
        "$verText = '6.1.2'",
        'Arena Studio Bridge - Studio Plugin  (Version 6.1.2)',
        'Text="Arena Roblox Bridge - Version 6.1.2"',
        "Version 6.1.2 - aktuell. Beim naechsten Start",
        "Laufzeit-Identitaet: Bridge-Version=6.1.2",
        "Kurzbericht Fenster-Vorschau (Version 6.1.2)",
    ]
    for marker in stale_612_literals:
        require(marker not in source, f"stale functional 6.1.2 literal remains: {marker}")

    # 6.1.3 must not remain in executable version fields either. Its changelog
    # heading stays on purpose (the polygon-builder gap fix is still
    # documented there), but every literal the updater, the plugin and the UI
    # compare at runtime has to have moved to 6.2.0.
    stale_613_literals = [
        "DocsVersion     = '6.1.3'",
        'local ARENA_VERSION  = "6.1.3"',
        "bridgeVersion = '6.1.3'",
        "bridgeVersion='6.1.3'",
        "serverVersion = '6.1.3'",
        "version = '6.1.3'",
        "$versionText = '6.1.3'",
        "$verText = '6.1.3'",
        'Arena Studio Bridge - Studio Plugin  (Version 6.1.3)',
        'Text="Arena Roblox Bridge - Version 6.1.3"',
        "Version 6.1.3 - aktuell. Beim naechsten Start",
        "Laufzeit-Identitaet: Bridge-Version=6.1.3",
        "Kurzbericht Fenster-Vorschau (Version 6.1.3)",
    ]
    for marker in stale_613_literals:
        require(marker not in source, f"stale functional 6.1.3 literal remains: {marker}")

    # 6.1.4 is now historical too. The changelog heading remains, but no
    # executable updater/plugin/server/UI version field may still advertise it.
    stale_614_literals = [
        "DocsVersion     = '6.1.4'",
        'local ARENA_VERSION  = "6.1.4"',
        "bridgeVersion = '6.1.4'",
        "bridgeVersion='6.1.4'",
        "serverVersion = '6.1.4'",
        "version = '6.1.4'",
        "$versionText = '6.1.4'",
        "$verText = '6.1.4'",
        'Arena Studio Bridge - Studio Plugin  (Version 6.1.4)',
        'Text="Arena Roblox Bridge - Version 6.1.4"',
        "Version 6.1.4 - aktuell. Beim naechsten Start",
        "Laufzeit-Identitaet: Bridge-Version=6.1.4",
        "Kurzbericht Fenster-Vorschau (Version 6.1.4)",
    ]
    for marker in stale_614_literals:
        require(marker not in source, f"stale functional 6.1.4 literal remains: {marker}")

    # 6.2.0 is historical as of 7.0.0. Its changelog heading stays (UI Engine
    # 1.0 is still documented there and its code guards below still apply),
    # but no executable version field may advertise it anymore.
    stale_620_literals = [
        "DocsVersion     = '6.2.0'",
        'local ARENA_VERSION  = "6.2.0"',
        "bridgeVersion = '6.2.0'",
        "bridgeVersion='6.2.0'",
        "serverVersion = '6.2.0'",
        "version = '6.2.0'",
        "$versionText = '6.2.0'",
        "$verText = '6.2.0'",
        'Arena Studio Bridge - Studio Plugin  (Version 6.2.0)',
        'Text="Arena Roblox Bridge - Version 6.2.0"',
        "Version 6.2.0 - aktuell. Beim naechsten Start",
        "Laufzeit-Identitaet: Bridge-Version=6.2.0",
        "Kurzbericht Fenster-Vorschau (Version 6.2.0)",
    ]
    for marker in stale_620_literals:
        require(marker not in source, f"stale functional 6.2.0 literal remains: {marker}")

    # 6.1.5 is historical as of 6.2.0. Its changelog heading stays (the polygon
    # welding fix is still documented there and its code guards below still
    # apply), but no executable version field may advertise it anymore.
    stale_615_literals = [
        "DocsVersion     = '6.1.5'",
        'local ARENA_VERSION  = "6.1.5"',
        "bridgeVersion = '6.1.5'",
        "bridgeVersion='6.1.5'",
        "serverVersion = '6.1.5'",
        "version = '6.1.5'",
        "$versionText = '6.1.5'",
        "$verText = '6.1.5'",
        'Arena Studio Bridge - Studio Plugin  (Version 6.1.5)',
        'Text="Arena Roblox Bridge - Version 6.1.5"',
        "Version 6.1.5 - aktuell. Beim naechsten Start",
        "Laufzeit-Identitaet: Bridge-Version=6.1.5",
        "Kurzbericht Fenster-Vorschau (Version 6.1.5)",
    ]
    for marker in stale_615_literals:
        require(marker not in source, f"stale functional 6.1.5 literal remains: {marker}")

    required_markers = [
        'local ARENA_CFG = {',
        'ARENA_CFG.POLL_WAIT_ACTIVE',
        'ARENA_CFG.POLL_GAP_ACTIVE',
        'ARENA_CFG.POLL_WAIT_QUIET',
        'ARENA_CFG.POLL_GAP_QUIET',
        'ARENA_CFG.HEARTBEAT_FALLBACK',
        'ARENA_CFG.CHUNK_SIZE',
        'PLAY_STOP_NEEDS_USER',
        'REPORTER_NOT_CONNECTED',
        'session_diag',
        'SharedTableRegistry',
        'sessionChannelCommand',
        'reporterSeenInOutput',
        'testSessionActive',
        'stopped_by_arena_bridge',
        'Get-Utf8QueryValue',
        '[System.Web.HttpUtility]::UrlDecode',
        'LateResults',
        'PlayRetryDedupe',
        "plugin outdated - simulations/version checks wait",
        'Get-RawGitHubText',
        '$content -is [byte[]]',
        '[char]0xFEFF',
        'reporterPostFailCount',
        'pluginReporterLoopCount',
        'local sessionDm = isSessionDataModel',
        'Retry once before reporting nil',
        'function Set-StateField',
        "Set-StateField $newState 'userPlaytestActive'",
        'MultiPlaceToken',
        'MULTI_PLACE_SELECTION_REQUIRED',
        'targetPlace',
        'ActivityLogs',
        'Open-ArenaHistoryWindow',
        'Alle Places',
        'function Write-UiErrorLog',
        'InvocationInfo.ScriptLineNumber',
        '$ErrorRecord.ScriptStackTrace',
        'function Add-PlaceRowToPlaceList',
        "Add-PlaceRowToPlaceList $row $sid $label",
        'function New-MinimalPlaceRow',
        'function Write-PlaceRowFailure',
        '$script:PlaceRowFailureLogAt = @{}',
        'PLACE_ROW_FALLBACK',
        'PLACE_LIST_INCOMPLETE connectedCount=',
        'function Get-PlaceDisplayName',
        'x:Name="PlaceListStatusText"',
        "Add-PlaceRowToPlaceList $script:AllPlacesRow $allSid 'Alle-Places-Zeile'",
        'hinzugefuegt (sid={1}): PlaceList.Children={2}',
        'hart auf sichtbar gestellt',
        'Einblend-Animation kam nie an',
        'Place-Liste konnte nicht neu angeordnet werden',
        'Place-Zeile: Vorschau-Visual konnte nicht erstellt werden',
        'Place-Zeile: Auswahlmenue/Popup konnte nicht erstellt werden',
        'Arena-Verlaufsfenster konnte nicht geoeffnet werden',
        '$script:PlaceVisibleSeconds = 15',
        '$script:PlaceOrphanGraceSeconds = 4',
        '$script:PlaceCleanupSeconds = 120',
        'function Remove-DeadSession',
        'Remove-DeadSession $sessionId',
        'function New-HistoryButton',
        '$head.Add_MouseLeftButtonDown($dragHandler)',
        '$shell.Add_MouseLeftButtonDown($dragHandler)',
        'function Get-ActivityToolSets',
        'previousLines = select(2, string.gsub(oldSource',
        'function Get-ResultNumber',
        'x:Name="RootShell"',
        'RoundGlassStyle',
        'SettingsPillStyle',
        'GlassFill',
        'SweepBrush',
        'function New-AuroraLayer',
        'New-AuroraLayer -Width 880 -Height 760',
        "$RootShell       = $window.FindName('RootShell')",
        '$RootShell.RenderTransform.BeginAnimation',
        '$popup.Add_Opened',
        'PopupAnimation]::None',
        "'#D900D5C4'",
        "'#F238D16C'",
        "'#47FFFFFF'",
        '$rowBg.GradientStops.Add',
        "$hoverGlow.Background = Get-Brush '#5900E5D0'",
        '$Item.Thumb.RenderTransform.BeginAnimation',
        '$copy.Background = $greenBg',
        'RectangleGeometry Rect="0,0,920,620"',
        'Add_ContentRendered',
        '$script:PlacePreviewHandles = @{}',
        '$script:PlacePreviewLastCaptureAt = @{}',
        '$script:PlacePreviewIntervalSeconds = 3.0',
        '$script:PlacePreviewCaptureHeight = 88',
        'function Get-StudioWindowInfos',
        'function Resolve-PlacePreviewHandle',
        'function Set-PlacePreviewImage',
        'function New-PlacePreviewVisual',
        'function Start-PlacePreviewCapture',
        'function Update-PlacePreviewCaptures',
        'Place-Zeile: Vorschau-Aufnahme fehlgeschlagen',
        '$script:PlacePreviewFailLogAt = @{}',
        'PreviewFailCount = 0',
        'PreviewLoggedOnce = $true',
        'Place-Vorschau ($sessionId): Aufnahme fehlgeschlagen',
        'Place-Vorschau ($sessionId): Live-Vorschau aktiv',
        'Studio-Fenster ist minimiert',
        '$previousRaw = $script:PlacePreviewHandles[$sessionId]',
        '[System.StringComparison]::OrdinalIgnoreCase',
        "if (-not ('Arena.ScreenHelper' -as [type])) {",
        'return $script:PreviewWindowCache',
        'return $script:WindowNameCache',
        '[Arena.ScreenHelper]::PrintWindow($hwnd, $hdc, 2)',
        'CopyFromScreen-Fallback',
        'Aufnahme-Worker nach 10 Sekunden beendet',
        'kein passendes Roblox-Studio-Fenster gefunden',
        '$script:SelfUpdateVerifyTimeout = 6',
        'Invoke-AutostartSelfUpdate -VerifyMode',
        "$starterProvesFreshInstall = ((@('update-erfolgreich', 'erster-start') -contains $UpdateStatus) -eq $true)",
        'param([string]$Branch, [string]$File, [int]$TimeoutSec = 0)',
        'function Write-PreviewTrace',
        'function New-PreviewFlowId',
        'function Clear-PreviewFlow',
        'function Save-PreviewHandleMeta',
        'PREVIEW [{0}] {1} sid={2} pid={3} hwnd={4}',
        "'CAPTURE_START'",
        "'WINDOWS_ENUMERATED'",
        "'HANDLE_RESOLVED'",
        "'WORKER_STARTED'",
        "'WORKER_COMPLETED'",
        "'RESULT_RECEIVED'",
        "'PNG_DECODED'",
        "'IMAGE_ASSIGNED'",
        "'IMAGE_VISIBLE'",
        'function Invoke-PlacePreviewUiSelfTest',
        'function New-PlacePreviewSelfTestImage',
        'PREVIEW_UI_SELFTEST_OK',
        'PREVIEW_UI_SELFTEST_FAILED',
        'Invoke-PlacePreviewUiSelfTest $Row $SessionId',
        'namespace Arena {',
        'public sealed class PreviewCaptureResult',
        'public static Task<PreviewCaptureResult> CaptureAsync(long hwndValue, int targetHeight)',
        'private const uint PW_RENDERFULLCONTENT = 2;',
        'TryWindowDcBitBlt',
        'TryCopyFromScreen',
        'HasVisibleContent',
        'true-aber-nichts-sichtbar',
        '[Arena.PreviewCapture]::CaptureAsync($handleValue, [int]$targetHeight)',
        'kind=csharp-helper',
        'ps-runspace-fallback',
        'Get-FileHash -Algorithm SHA256',
        'LanguageMode',
        '$script:PreviewFlowContexts = @{}',
        '$script:PreviewHandleInfos = @{}',
        '$script:PreviewSelfTestDone = $false',
        'Clear-PreviewFlow $flow',
        'DispatcherPriority]::Render',
        'GetNewClosure()',
        "Move-Item -LiteralPath $script:RuntimeLog -Destination ($script:RuntimeLog + '.old') -Force",
        'function Get-PlacePreviewVisualState',
        'function Format-PlacePreviewVisualState',
        'function Start-PlacePreviewVisibilityVerify',
        'function Write-PreviewDiagnoseFile',
        'function Add-PreviewDiagLine',
        'PREVIEW_UI_VERIFY sid=',
        'PREVIEW_OPACITY_RESCUE sid=',
        'preview-diagnose.txt',
        '$fade.FillBehavior = [System.Windows.Media.Animation.FillBehavior]::Stop',
        '$fadeGuard.Interval = [System.TimeSpan]::FromMilliseconds(400)',
        '$verifyTimer.Interval = [System.TimeSpan]::FromMilliseconds(1500)',
        'PreviewVerifyDone = $false',
        "$script:PreviewSelfTestVerdict = ''",
        'reallyVisible',
        'tools.sim_start = function(args)',
        'tools.sim_stop = function(args)',
        'tools.sim_status = function(args)',
        'ExecuteRunModeAsync',
        'waitForEditMode(true, 12)',
        'SIM_STOP_NEEDS_USER',
        'SIM_DISABLED',
        'SIM_RUNNING',
        'simAllowedNow',
        'simStateData',
        'USER_PLAYTEST_ACTIVE',
        'allowInSimMode',
        'progressContract',
        'ProgressStates',
        'progressPercent',
        'HANDOFF_NOT_ALLOWED',
        'HANDOFF_INCOMPLETE',
        'HANDOFF_REQUIRED',
        'AuditFlags',
        'previousHandoff',
        'function Get-PlaceIdentityKey',
        'PreviewHandleInfos',
        'UI_ENGINE.ENGINE_VERSION = "2.0"',
        'function UI_ENGINE.textureRecipe',
        'function UI_ENGINE.glowEmitter',
        'function UI_ENGINE.radialMenu',
        'tools.ui_glow = function(args)',
        'tools.ui_texture = function(args)',
        'tools.ui_radial = function(args)',
        'TEXTURE_ASSET_MISSING',
        'RADIAL_ASSET_MISSING',
        'glowStacks',
        'radialMenus',
        'textureImages',
        'worldEngineRules = @{',
        'tools.world_style = function(args)',
        'tools.style_lock = function(args)',
        'tools.site_survey = function(args)',
        'tools.variation = function(args)',
        'tools.prop_place = function(args)',
        'tools.prop_save = function(args)',
        'tools.prop_list = function(args)',
        'tools.model_audit = function(args)',
        'tools.world_audit = function(args)',
        'tools.world_glow = function(args)',
        'tools.refine = function(args)',
        'WORLD_ENGINE.PRESETS',
        'placeholderCount',
        'styleCompliance',
    ]
    for marker in required_markers:
        require(marker in source, f"required marker missing: {marker}")

    # Every functional version location is intentional. Exact counts catch a
    # forgotten endpoint, footer or fallback while allowing historical notes.
    functional_version_counts = {
        "DocsVersion     = '7.6.3'": 1,
        'local ARENA_VERSION  = "7.6.3"': 1,
        "version = '7.6.3'": 2,  # normal health response plus isolated build smoke report
        "bridgeVersion = '7.6.3'": 3,
        "bridgeVersion='7.6.3'": 1,
        "serverVersion = '7.6.3'": 2,
        "$versionText = '7.6.3'": 1,
        "$verText = '7.6.3'": 1,
        "ArenaRobloxBridge/7.6.3": 1,
        "Arena Studio Bridge - Studio Plugin  (Version 7.6.3)": 1,
        'Text="Arena Roblox Bridge - Version 7.6.3"': 1,
        "Version 7.6.3 - aktuell. Beim naechsten Start": 2,
        "Bridge-Version=7.6.3": 2,
        "Kurzbericht Fenster-Vorschau (Version 7.6.3)": 1,
        "Kurzbericht Fortschrittsanzeige (Version 7.6.3)": 1,
        "Kurzbericht Fertig-Meldung (Version 7.6.3)": 1,
        "Arena Roblox Bridge - Leistungsbericht (Version 7.6.3)": 1,
        "Arena Roblox Bridge - Place-Diagnose (Version 7.6.3)": 1,
        "Version: 7.6.3": 3,  # existing diagnostics plus duplicate-start report
        "Version=7.6.3": 3,
        "Bridge/Plugin-Stand: 7.6.3": 1,
        "Arena Roblox Bridge - Start-Diagnose (Version 7.6.3)": 2,
        "RuntimeInfo.Version = '7.6.3'": 1,
        "# Version 7.3.2 (HISTORICAL; superseded by project-first policy 7.6.3).": 1,
        "# Version 7.4.0 (2026-10-07)": 1,
        "# Version 7.4.1 (2026-10-07)": 1,
        "# Version 7.5.0 (2026-10-07)": 1,
        "# Version 7.5.3 (2026-10-08)": 1,
        "# Version 7.5.6 (2026-10-09)": 1,
        "# Version 7.5.7 (2026-10-09)": 1,
        "# Version 7.5.8 (2026-10-09)": 1,
        "# Version 7.5.9 (2026-10-09)": 1,
        "# Version 7.6.3 (2026-10-10)": 1,
        "# Version 7.6.2 (2026-10-10)": 1,
        "# Version 7.6.1 (HISTORICAL; scope-gate details superseded by 7.6.2)": 1,
        "# Version 7.6.0 (2026-10-09)": 1,
        "# Version 7.5.5 (2026-10-08, HISTORICAL)": 1,
    }

    for marker, expected_count in functional_version_counts.items():
        actual_count = source.count(marker)
        require(actual_count == expected_count,
                f"functional version marker count for {marker!r}: "
                f"expected {expected_count}, found {actual_count}")

    # 7.0.2 performance guards: avoid full-frame idle animation and redundant
    # preview/polling work while keeping the connection/server independent.
    main_xaml_start = source.index("$xaml = @'\n") + len("$xaml = @'\n")
    main_xaml_end = source.index("\n'@", main_xaml_start)
    main_xaml = source[main_xaml_start:main_xaml_end]
    require('RepeatBehavior="Forever"' not in main_xaml,
            "the transparent main window regained permanent XAML animations")
    require('$script:UiRefreshVisibleMs = 1800' in source
            and '$script:UiRefreshMinimizedMs = 5000' in source,
            "the 7.0.2 low-frequency UI refresh cadence is missing")
    refresh_fn = source[source.index("function Refresh-Ui {"):source.index("# ----------------------------------------------------------------------------\n# Version 5.0.2: Zeile sichtbar")]
    require("$window.WindowState -eq 'Minimized'" in refresh_fn
            and "Update-HandoffCard\n    Sync-PlaceList $activeStudios" in refresh_fn,
            "minimized refresh or once-per-tick handoff scheduling regressed")
    row_update_fn = source[source.index("function Update-Row {"):source.index("# AKTUALISIERUNG DER OBERFLAECHE")]
    require("Update-HandoffCard" not in row_update_fn,
            "handoff state is once again scanned for every Place row")
    require("function Set-PlacePreviewSpinnerAnimation" in source
            and "Set-PlacePreviewSpinnerAnimation $Row.IconVisual $false" in source
            and "Set-PlacePreviewSpinnerAnimation $Row.IconVisual $true" in source,
            "preview spinner animation cannot be stopped/restarted with its setting")
    add_row_fn = source[source.index("function Add-PlaceRowToPlaceList"):source.index("function New-MinimalPlaceRow")]
    require("$script:SettingsCache.editorIconsEnabled -ne $false" in add_row_fn,
            "preview self-test still runs when editor preview is disabled")
    require("task.wait(1.5)" in plugin_source(source),
            "Studio idle watcher returned to a 0.5-second polling cadence")

    # ------------------------------------------------------------------
    # 7.0.3 performance guards remain active in the 7.0.4 release.
    # The Studio plugin used to hold an HTTP request open permanently: a 12 s
    # long-poll that was immediately followed by the next request (100 % duty
    # cycle), plus a second permanent channel (a 5 s heartbeat). Roblox Studio
    # only runs 3 HTTP requests at a time and Roblox confirms that long polling
    # "can currently stall next requests" - that is why the lag started as soon
    # as a place connected, independent of preview capture or UI cadence.
    # ------------------------------------------------------------------
    plugin = plugin_source(source)
    require("HEARTBEAT_EVERY" not in plugin,
            "the plugin regained a second permanent heartbeat channel")
    require(plugin.count('post("/plugin/poll"') == 1,
            "the plugin must use exactly one command channel (one poll call site)")
    require(plugin.count('post("/plugin/heartbeat"') == 1,
            "the plugin must keep at most one fallback heartbeat call site")
    require("os.clock() - lastHeartbeat > ARENA_CFG.HEARTBEAT_FALLBACK" in plugin,
            "the fallback heartbeat is no longer gated on a failed poll channel")
    require("HEARTBEAT_FALLBACK   = 20" in plugin,
            "the fallback heartbeat interval is missing")

    poll_block = plugin[plugin.index("local waitSeconds = ARENA_CFG.POLL_WAIT_ACTIVE"):
                        plugin.index('game:GetPropertyChangedSignal("Name")')]
    require(poll_block.count("task.wait(gapSeconds)") == 1,
            "the mandatory pause after every poll request is missing or duplicated")
    require(poll_block.index('post("/plugin/poll"') < poll_block.index("task.wait(gapSeconds)"),
            "the pause must run AFTER the poll request so the HTTP slot is released")
    require("task.wait(0.5)" in poll_block,
            "a failed poll is no longer paced")
    require("ARENA_CFG.QUIET_AFTER_POLLS" in poll_block and "quiet = true" in poll_block,
            "the quiet mode is no longer entered after empty polls")
    require("emptyPolls = 0" in poll_block and "quiet = false" in poll_block,
            "a delivered command no longer returns the channel to active mode")
    require("perfWanted = (response.perf == true)" in poll_block,
            "the plugin no longer follows the bridge diagnostics switch")
    require("if perfWanted then payload.perf = perfReport() end" in plugin,
            "performance counters must travel with the existing poll request")
    require(plugin.count("perfStats.requests = perfStats.requests + 1") == 1,
            "HTTP request counting must live in exactly one place (post)")

    # The promised numbers are bounded: a request must never become "long
    # running" and the pause must stay a real fraction of the cycle.
    def cfg_number(name: str) -> float:
        m = re.search(rf"^\s*{name}\s*=\s*([0-9.]+)", plugin, re.M)
        require(m is not None, f"ARENA_CFG.{name} is missing")
        return float(m.group(1))

    require(cfg_number("POLL_WAIT_ACTIVE") <= 4.0, "active poll wait grew again")
    require(cfg_number("POLL_WAIT_QUIET") <= 8.0, "quiet poll wait grew again")
    require(cfg_number("POLL_GAP_ACTIVE") >= 0.2, "active duty cycle has no pause")
    require(cfg_number("POLL_GAP_QUIET") >= 1.0, "quiet duty cycle has no pause")
    quiet_duty = cfg_number("POLL_WAIT_QUIET") / (
        cfg_number("POLL_WAIT_QUIET") + cfg_number("POLL_GAP_QUIET"))
    require(quiet_duty <= 0.85,
            f"quiet mode still holds the Studio HTTP slot {quiet_duty:.0%} of the time")

    # Bridge: the 337 KB handler must be compiled once instead of per request.
    require("[ScriptBlock]::Create($HandlerScript)" in source,
            "the HTTP handler is no longer compiled once for the listener")
    require("$workerScript = 'param($Context, $Shared, $Handler, $HandlerText) & $Handler $Context $Shared'" in source,
            "the tiny worker wrapper that invokes the cached handler is missing")
    require("$workerScript = 'param($Context, $Shared, $Handler, $HandlerText) & ([ScriptBlock]::Create($HandlerText)) $Context $Shared'" in source,
            "the self-test fallback that re-parses the handler text is missing "
            "(a ScriptBlock from [ScriptBlock]::Create cannot be assumed to run "
            "inside every pool runspace)")
    require(".AddScript($workerScript)" in source,
            "the listener no longer uses the cached handler wrapper")
    require(".AddScript($HandlerScript)" not in source,
            "every HTTP request still re-parses the full handler text")
    require(".AddArgument($handlerBlock).AddArgument($HandlerScript)" in source,
            "the worker no longer receives both the cached ScriptBlock and the "
            "handler text used by the fallback")
    require("$fastWorkers = ($null -ne $probeResult" in source,
            "the listener lost the security probe that proves a cached, unbound "
            "ScriptBlock really runs inside its own runspace pool")
    require("$handlerBlock = $null\n        Write-BridgeLog" in source,
            "the fallback path must drop the unusable ScriptBlock before the "
            "worker falls back to the handler text")
    require("$waitSeconds = [Math]::Min([double]$body.wait, 8)" in source,
            "the server-side cap that keeps any poll request short is missing")
    perf_needle = '"perf":' + "' + $perfFlag"
    require(perf_needle in source,
            "the poll response no longer carries the diagnostics switch")
    require("if ($body.perf) { Record-PluginPerf $sid $body.perf }" in source,
            "the plugin counters are no longer read from the poll payload")
    require("Leistungswarnung: Sitzung " in source,
            "the poll rate warning that proves runaway polling is missing")

    # Diagnostics: opt-in, sparse, and never inside the request path.
    handler_fn = source[source.index("$script:BridgeHandlerScript = {"):
                        source.index("$script:BridgeListenerScript = {")]
    require("Write-PerfReport" not in handler_fn,
            "the performance report must not run inside an HTTP request")
    perf_fn = source[source.index("function Write-PerfReport {"):
                     source.index("function Refresh-Ui {")]
    require("if (-not (Test-PerfDiagnosticsEnabled)) {" in perf_fn,
            "the performance report no longer respects the off switch")
    require(".TotalSeconds -lt 30" in perf_fn,
            "the performance report lost its 30 second throttle")
    require("performance.txt" in perf_fn,
            "the shareable performance report file is missing")
    require("perfDiagnostics = $false" in source,
            "the performance diagnostics are no longer OFF by default")
    require("if (Test-PerfDiagnosticsEnabled) { $perfWatch = [System.Diagnostics.Stopwatch]::StartNew() }" in source,
            "the UI tick timer measures even when diagnostics are off")
    require("Update-PerfUiTick $perfWatch.Elapsed.TotalMilliseconds" in source,
            "the UI tick timing is not reported through the throttled writer")
    settings_start = source.index("function Open-SettingsWindow")
    settings_end = source.index("# Version 3.8: Die Update-Infos", settings_start)
    settings_ui = source[settings_start:settings_end]
    settings_xaml_start = settings_ui.index("$settingsXaml = @'\n") + len("$settingsXaml = @'\n")
    settings_xaml_end = settings_ui.index("\n'@", settings_xaml_start)
    settings_xaml = settings_ui[settings_xaml_start:settings_xaml_end]
    require('Text="DIAGNOSE"' not in settings_xaml
            and 'x:Name="PerfSwitch"' not in settings_xaml
            and "$perfSwitch.Add_Click(" not in settings_ui,
            "the removed settings Diagnose area or performance switch has returned")
    settings_loader_start = source.index("function Get-BridgeSettingsFile")
    settings_loader_end = source.index("function Save-BridgeSettingsFile", settings_loader_start)
    settings_loader = source[settings_loader_start:settings_loader_end]
    require("perfDiagnostics = $false" in settings_loader
            and "$loaded.perfDiagnostics" not in settings_loader
            and "alte opt-ins werden ignoriert" in settings_loader,
            "a legacy performance-diagnostics opt-in would be restored silently")
    require("Set-PlacePreviewSpinnerAnimation" in source,
            "preview handling was removed while fixing the channel")

    stale_700_functional = [
        "DocsVersion     = '7.0.0'",
        'local ARENA_VERSION  = "7.0.0"',
        "version = '7.0.0'",
        "bridgeVersion = '7.0.0'",
        "bridgeVersion='7.0.0'",
        "serverVersion = '7.0.0'",
        "$versionText = '7.0.0'",
        "$verText = '7.0.0'",
        "Arena Studio Bridge - Studio Plugin  (Version 7.0.0)",
        'Text="Arena Roblox Bridge - Version 7.0.0"',
        "Version 7.0.0 - aktuell. Beim naechsten Start",
        "Bridge-Version=7.0.0",
        "Kurzbericht Fenster-Vorschau (Version 7.0.0)",
    ]
    for marker in stale_700_functional:
        require(marker not in source, f"stale functional 7.0.0 literal remains: {marker}")

    # 7.0.3: the functional 7.0.2 markers must all be gone (history notes in
    # the changelog may still mention 7.0.2 on purpose).
    stale_702_functional = [
        "DocsVersion     = '7.0.2'",
        'local ARENA_VERSION  = "7.0.2"',
        "version = '7.0.2'",
        "bridgeVersion = '7.0.2'",
        "bridgeVersion='7.0.2'",
        "serverVersion = '7.0.2'",
        "$versionText = '7.0.2'",
        "$verText = '7.0.2'",
        "Arena Studio Bridge - Studio Plugin  (Version 7.0.2)",
        'Text="Arena Roblox Bridge - Version 7.0.2"',
        "Version 7.0.2 - aktuell. Beim naechsten Start",
        "Bridge-Version=7.0.2",
        "Kurzbericht Fenster-Vorschau (Version 7.0.2)",
        "Place-Diagnose (Version 7.0.2)",
        "Plugin {1}, Bridge 7.0.2)",
    ]
    for marker in stale_702_functional:
        require(marker not in source, f"stale functional 7.0.2 literal remains: {marker}")

    # 7.0.4 executor/queue recovery and Place-row presentation contract.
    watchdog_start = source.index("function Invoke-SessionExecutorWatchdog")
    watchdog_end = source.index("function Get-PendingCommands", watchdog_start)
    watchdog = source[watchdog_start:watchdog_end]
    for marker in (
        "COMMAND_DELIVERY_UNCONFIRMED",
        "EXECUTOR_UNAVAILABLE",
        "EXECUTOR_DROPPED_COMMAND",
        "STUDIO_ABANDONED",
        "EXECUTOR_UNRESPONSIVE",
        "$budget + 15",
        "heartbeatAt -gt 0",
        "queuedCommandIds",
    ):
        require(marker in watchdog, f"executor watchdog is missing recovery marker: {marker}")
    require("function Mark-CommandDelivered" in source
            and "phase -eq 'received_batch'" in source
            and "phase -eq 'started'" in source
            and "phase -eq 'heartbeat'" in source,
            "command delivery/receipt/start/heartbeat state transitions are incomplete")
    require("if ($executorSnapshot.alive)" in watchdog
            and "if ($isRunning -and $executorSnapshot.alive)" in watchdog
            and "after command receipt. The command was abandoned" in watchdog,
            "lost acknowledgements are not reconciled against a fresh executor snapshot")
    require("CompletedCommandIds.TryAdd($dedupeKey" in source
            and "CommandOwners" in source
            and "ResultChunkAt" in source,
            "commandId-bound result ownership/deduplication/chunk cleanup is incomplete")
    require("GET /api/queue" in source and "POST /api/queue" in source
            and "if ($path -eq '/api/queue')" in source
            and "action -eq 'cancel'" in source
            and "action -eq 'reset'" in source,
            "queue status/cancel/reset API controls are missing")
    require("64 queued commands" in source and "function Test-CommandArguments" in source,
            "queue limit or pre-queue argument validation is missing")
    require("$isReferenceList = ($typeName -match '(?i)^\\s*ref\\[\\]')" in source
            and "resolveMany intentionally accepts either ref[] or one ref" in source,
            "argument validation rejects supported single-reference/selector forms")
    require("function Enqueue-Command" in source and "CommandQueueLock" in source
            and source.count("Enqueue-Command $sessionId $queue") >= 2,
            "single/parallel queue insertion is not guarded by the atomic queue-cap helper")
    require("Monitor]::Enter($Shared.CommandQueueLock)" in source
            and "while ($queue.TryDequeue([ref]$raw))" in source
            and "while ($collected.Count -lt 16 -and $queue.TryDequeue([ref]$itemJson))" in source,
            "queue removal, reset and plugin dequeue are not serialized")
    parallel_fn = source[source.index("function Invoke-PluginToolsParallel"):source.index("function New-Envelope", source.index("function Invoke-PluginToolsParallel"))]
    require("progressPayload = $null" in parallel_fn
            and "Update-ArenaProgressState $sessionId $callTool" in parallel_fn
            and "PSObject.Properties.Remove('progress')" in parallel_fn,
            "parallel calls do not report work/progress or strip metadata before queueing")
    require("The plugin did not acknowledge receiving this command within 30 seconds" in source,
            "a dropped plugin poll response can leave a command pending forever")

    ground_start = source.index("tools.ground_height = function(args)")
    ground_end = source.index("tools.measure_height = function(args)", ground_start)
    ground_tool = source[ground_start:ground_end]
    require("firstNonEmpty(args.positions, args.points)" in ground_tool
            and "local z = minZ + iz * step" in ground_tool
            and "estimate > 4000" in ground_tool
            and "index % 128 == 0" in ground_tool,
            "ground_height aliases/grid traversal/early sample cap/cooperative yield regressed")
    probe_start = source.index("tools.probe_world = function(args)")
    probe_end = source.index("tools.fill_region = function(args)", probe_start)
    probe_tool = source[probe_start:probe_end]
    require("estimatedSquare > 4000" in probe_tool
            and "measuredRays % 128 == 0" in probe_tool
            and "World probe job was cancelled" in probe_tool,
            "probe_world can still run an unbounded, unresponsive ground scan")
    measure_start = source.index("tools.measure_height = function(args)")
    measure_end = source.index("tools.verify_measurable = function(args)", measure_start)
    measure_tool = source[measure_start:measure_end]
    require("decodeValue(args.point)" in measure_tool
            and 'directionName == "up"' in measure_tool
            and "resolveExcluded(firstNonEmpty(args.exclude, args.ignore))" in measure_tool,
            "measure_height does not honor its documented point/direction/ignore arguments")
    ray_many_start = source.index("tools.raycast_many = function(args)")
    ray_many_end = source.index("tools.ground_height = function(args)", ray_many_start)
    ray_many = source[ray_many_start:ray_many_end]
    require("firstNonEmpty(args.rays, args.casts)" in ray_many
            and "cast.length" in ray_many
            and "max 500 per call" in ray_many,
            "raycast_many ignores its documented rays/length contract or lacks a finite batch cap")
    box_start = source.index("tools.parts_in_box = function(args)")
    box_end = source.index("tools.what_is_in_the_way = function(args)", box_start)
    spatial_queries = source[box_start:box_end]
    require("args.center" in spatial_queries and "args.refA" in spatial_queries
            and "spatialFilter(args)" in spatial_queries and "args.ref then" in spatial_queries
            and "args.position or args.origin" in spatial_queries,
            "documented spatial query aliases or filters are ignored by their handlers")
    obstacle_start = source.index("tools.what_is_in_the_way = function(args)")
    obstacle_end = source.index("tools.raycast_many = function(args)", obstacle_start)
    require("args.from or args.origin" in source[obstacle_start:obstacle_end]
            and "args.to or args.target" in source[obstacle_start:obstacle_end],
            "what_is_in_the_way ignores its documented origin/target arguments")
    require("function Test-CommandArgumentPresent" in source
            and "probe_world grid would contain about" in source
            and "ground_height grid would contain" in source
            and "'measure_height'" in source,
            "spatial one-of validation or pre-queue oversized-raster rejection is missing")
    require("Keep any outstanding cancellation request until the plugin acknowledges" in source,
            "cancel/reset requests would be removed before the plugin can act on them")
    measurable_start = source.index("local function waitMeasurableCore")
    measurable_end = source.index("local function waitMeasurable(", measurable_start)
    measurable = source[measurable_start:measurable_end]
    require("Enum.RaycastFilterType.Include" in measurable
            and "hit.Instance:IsDescendantOf(inst)" in measurable,
            "geometry verification excludes the object it is supposed to measure")
    verify_start = source.index("tools.verify_measurable = function(args)")
    verify_end = source.index("tools.", verify_start + len("tools.verify_measurable = function(args)"))
    verify_tool = source[verify_start:verify_end]
    snap_start = source.index("tools.snap_to_ground = function(args)")
    snap_end = source.index("tools.look_at = function(args)", snap_start)
    snap_tool = source[snap_start:snap_end]
    require("args.maxSeconds or args.seconds" in verify_tool
            and "math.min(tonumber(args.maxSeconds" in verify_tool
            and "args.waitForMeasurable ~= false" in snap_tool
            and "or 2000" in snap_tool,
            "ground-tool timeout, verification, or documented fall-limit defaults regressed")

    progress_visual = source[source.index("function Update-PlaceProgressVisual"):source.index("function Get-ProgressDiagnoseLines")]
    require("if ($progressMode -eq 'hidden')" in progress_visual
            and "Fortschritt nicht anwendbar" in progress_visual
            and "$showNumericProgress = (($percentKnown -or $state -eq 'done') -and $progressMode -ne 'hidden')" in progress_visual
            and "$Row.ProgressBar.Visibility = 'Collapsed'" in progress_visual
            and "ProgressBar.Foreground = Get-Brush $color" in progress_visual
            and "ProgressText.Visibility = 'Visible'" in progress_visual
            and "ProgressPercent.Text = ($percent.ToString() + ' %')" in progress_visual
            and "SilentSeconds -ge 60" in progress_visual
            and "Seit über einer Minute kein Bridge Aufruf mehr" not in progress_visual,
            "the Place row does not hide non-applicable progress without inventing 0%/inactivity")
    history_card = source[source.index("function New-ArenaHistoryProgressCard {"):source.index("function Update-ArenaHistoryProgressCard {")]
    require("$bar.Background = Get-Brush '#F3F6FC'" in history_card,
            "history progress track is not distinctly light/near-white")
    new_row = source[source.index("function New-Row {"):source.index("function New-MinimalPlaceRow")]
    fallback_start = source.index("function New-MinimalPlaceRow {")
    fallback_end = source.find("\nfunction ", fallback_start + 1)
    fallback_row = source[fallback_start:fallback_end]
    require("$namePanel.VerticalAlignment = 'Stretch'" in new_row
            and "$topCenterSpacer.Height = [System.Windows.GridLength]::new(1, [System.Windows.GridUnitType]::Star)" in new_row
            and "$bottomCenterSpacer.Height = [System.Windows.GridLength]::new(1, [System.Windows.GridUnitType]::Star)" in new_row
            and "$namePanel.VerticalAlignment = 'Center'" in fallback_row,
            "empty Place titles are not centered by symmetric star rows in both rich and fallback builders")
    require("[System.Windows.Controls.Grid]::SetColumn($progressRow, 1)" in new_row,
            "the blue work row is not placed under the Place name (it lands under the preview and stretches the row)")
    require("[System.Windows.Controls.Grid]::SetRowSpan($placeIcon.Frame, 4)" in new_row
            and "$placeIcon.Frame.VerticalAlignment = 'Center'" in new_row,
            "the preview does not span all four centered name/status grid rows")
    require("$border.Padding = [System.Windows.Thickness]::new(16, 6, 16, 6)" in new_row,
            "the Place row lost its symmetric compact interior padding (content sits too high)")
    require("$progressText.Text = 'Arena arbeitet gerade...'" not in new_row
            and "Fortschrittsvertrag" not in progress_visual,
            "an implementation contract label leaked into the Place-row UI")

    # 7.0.1 UI contract: the link belongs to the main-list footer, settings
    # have padding, all four remaining toggles are initialized, and a broken rich Place
    # row has a visible minimal fallback.
    main_xaml_match = re.search(r"\$xaml = @'\n([\s\S]*?)\n'@", source)
    settings_xaml_match = re.search(r"\$settingsXaml = @'\n([\s\S]*?)\n'@", source)
    require(main_xaml_match is not None and settings_xaml_match is not None,
            "main/settings XAML here-strings were not found")
    main_xaml = main_xaml_match.group(1)
    settings_xaml = settings_xaml_match.group(1)
    require('Text="Arena Roblox Bridge"' in main_xaml
            and 'Text="bereit für verbundene Places"' in main_xaml
            and 'RuntimeLine' not in source,
            "the title bar must show only the product title and the fixed requested subtitle")
    require('x:Name="ArenaAiButton"' in main_xaml and 'Grid.Row="1"' in main_xaml,
            "Arena AI button is not in the main-list footer")
    require('ArenaAiButton' not in settings_xaml,
            "Arena AI button is still in Settings")
    require('<Grid Margin="24">' in settings_xaml,
            "Settings content grid has no interior padding")
    require('Background="{StaticResource GreenBtnBg}"' in main_xaml,
            "Arena AI footer button does not use the green Prompt-copy design resource")
    switch_names = ("StartupSwitch", "EditorIconsSwitch", "ProgressSwitch", "DoneNotifySwitch")
    open_settings = source[source.index("function Open-SettingsWindow"):source.index("# Version 3.8: Die Update-Infos")]
    switch_variables = {
        "StartupSwitch": "$startupSwitch",
        "EditorIconsSwitch": "$editorIconsSwitch",
        "ProgressSwitch": "$progressSwitch",
        "DoneNotifySwitch": "$doneNotifySwitch",
    }
    # 7.1.3 keeps the old "Mitteilungen" section gone but adds the requested
    # DoneNotifySwitch, so only the EXACT legacy names may reappear.
    require('x:Name="NotifySwitch"' not in settings_xaml and 'Mitteilungen' not in settings_xaml,
            "the Mitteilungen section is still present in Settings")
    require("FindName('NotifySwitch')" not in open_settings and '$notifySwitch' not in open_settings
            and '$notifyNow' not in open_settings,
            "removed notification settings remain bound in Open-SettingsWindow")
    for name in switch_names:
        require(f'x:Name="{name}"' in settings_xaml, f"missing settings switch {name}")
        require(f"$settingsWindow.FindName('{name}')" in open_settings,
                f"settings switch {name} is not bound to code")
        require(f"{switch_variables[name]}.Add_Click" in open_settings,
                f"settings switch {name} has no change handler")
    require("Set-StartupEnabled ([bool]$s.IsChecked)" in open_settings
            and "Set-EditorIconsEnabled ([bool]$s.IsChecked)" in open_settings
            and "$script:Shared.BridgeSettings.progressInPlaceList = [bool]$s.IsChecked" in open_settings
            and "$script:Shared.BridgeSettings.notifyOnDone = $enabled" in open_settings
            and open_settings.count("Save-BridgeSettingsFile") >= 4,
            "settings switches do not persist their expected values")
    for marker in (
        "$autoStartNow = Get-StartupEnabled",
        "$editorIconsNow = [bool]$script:SettingsCache.editorIconsEnabled",
        "$progressNow = [bool]$script:Shared.BridgeSettings.progressInPlaceList",
        "$doneNotifyNow = [bool]$script:Shared.BridgeSettings.notifyOnDone",
        "$startupSwitch.IsChecked = $autoStartNow",
        "$editorIconsSwitch.IsChecked = $editorIconsNow",
        "$progressSwitch.IsChecked = $progressNow",
        "$doneNotifySwitch.IsChecked = $doneNotifyNow",
    ):
        require(marker in open_settings, f"settings switch does not initialize from its persisted value: {marker}")
    # 7.1.3: the notification switch sits directly under the progress switch
    # (user request) and the SIMULATION warning card is gone completely.
    progress_card = settings_xaml[settings_xaml.index('x:Name="ProgressSwitch"'):]
    require('x:Name="DoneNotifySwitch"' in progress_card
            and progress_card.index('x:Name="DoneNotifySwitch"') < progress_card.index("</Border>"),
            "the finish-notification switch is not in the PLACE-LISTE card under the progress switch")
    require('Content="Benachrichtigung, wenn Arena fertig ist"' in settings_xaml,
            "the finish-notification switch is not labelled as requested")
    require('SimSwitch' not in settings_xaml, "disabled sim_start is still presented as an enable switch")
    require('SIMULATION' not in settings_xaml and 'sim_start ist deaktiviert' not in settings_xaml,
            "the removed SIMULATION warning card is still in the settings window")
    require("Set-ArenaSwitchVisualState $toggleSwitch" in open_settings
            and "$toggleSwitch.Add_Loaded" in open_settings,
            "switch visual state is not synchronized after loading")
    require("function Set-ArenaSwitchVisualState" in source
            and "$thumb.RenderTransform.X = if ([bool]$Switch.IsChecked)" in source,
            "switch thumb does not reflect its saved IsChecked state")
    place_sync = source[source.index("function Sync-PlaceList"):source.index("# FENSTERSTEUERUNG")]
    for marker in ("New-MinimalPlaceRow $studio $sid", "PLACE_ROW_FALLBACK",
                   "PlaceList.Children.Count -lt $desired.Count", "Get-PlaceDisplayName"):
        require(marker in place_sync or marker in source,
                f"connected Place row fallback/diagnostic missing: {marker}")

    # Version 6.0 negative guards: the pre-6.0 palette must really be gone
    # from the redesigned surfaces (the tech-dark slate/indigo scheme).
    require("Text=\"Arena Roblox Bridge - Version 5.2\"" not in source,
            "settings window still shows the 5.2 footer")
    require("$border.Background = Get-Brush '#111827'" not in source,
            "place rows still use the old slate background")

    # Version 5.2 negative guards: the wish items must really be gone.
    require("AllAccessButton" not in source,
            "aggregate row still carries its direct read-only switch")
    require("LastArenaMessage" not in source,
            "last Arena message still lives in the settings window")
    require("TOKEN=$script:AllPlacesToken`r`nMODE=ALLE_PLACES" not in source,
            "all-places prompt still carries the MODE/HINWEIS lines")
    require("+[PLATZHALTER]" not in source,
            "a [PLATZHALTER] text survived in the activity log texts")
    require("'[Platzhalter]'" not in source,
            "a [Platzhalter] fallback survived in the activity helpers")
    require("static.wikia.nocookie.net/roblox/images/e/e1" not in source,
            "the dead wikia studio-logo URL is still in the icon worker")

    # Version 6.0.1 negative guards: the entire Roblox-icon download pipeline
    # must be gone, replaced only by the live Studio-window preview (no mix
    # of both approaches).
    require("Start-PlaceIconLoad" not in source,
            "the old icon download job launcher is still present")
    require("Update-PlaceIconLoads" not in source,
            "the old icon job poller is still present")
    require("Get-PlaceIconKey" not in source,
            "the old icon cache key helper is still present")
    require("Update-AllPlacesIcon" not in source,
            "the old aggregate-row icon mosaic builder is still present")
    require("function Test-PngFile" not in source,
            "the old PNG validity checker is still present")
    require("function New-LocalFallbackIcon" not in source,
            "the old locally-drawn fallback icon is still present")
    require("upload.wikimedia.org/wikipedia/commons/4/44/RobloxStudioLogo2025.png" not in source,
            "the old wikimedia fallback icon URL is still present")
    require("$script:PlaceIconFails = @{}" not in source,
            "the old icon-failure tracker is still present")
    require("$script:AllPlacesMosaicSignature = $null" not in source,
            "the old aggregate-row icon mosaic signature is still present")
    require("$script:IconFolder" not in source,
            "the old on-disk icon cache folder is still present")
    # 6.0.3: window previews must start locally and immediately; never put a
    # synchronous thumbnail request back onto the WPF dispatcher thread.
    require("thumbnails.roblox.com/v1/games/icons" not in source,
            "the blocking Roblox game-icon request is back in the window-preview path")
    # 6.0.4: Der Primaerweg der Aufnahme ist der kompilierte C#-Helfer im
    # Hauptprozess; der 6.0.3-Runspace-Worker darf nur noch als Fallback
    # existieren, und jede Aufnahme schreibt die Stationen ins Log.
    capture_fn = source[source.index("function Start-PlacePreviewCapture"):source.index("function Update-PlacePreviewCaptures")]
    require("[Arena.PreviewCapture]::CaptureAsync($handleValue, [int]$targetHeight)" in capture_fn,
            "primary C# capture path is missing from Start-PlacePreviewCapture")
    require("kind=csharp-helper" in capture_fn and "kind=ps-runspace-fallback" in capture_fn,
            "capture worker kinds (helper/fallback) are not both wired")
    require("thumbnails.roblox.com" not in capture_fn,
            "a synchronous Roblox thumbnail request crept back into the capture path")
    update_fn = source[source.index("function Update-PlacePreviewCaptures"):source.index("function Get-ArenaHistoryEntries")]
    require("$job.Task.Result" in update_fn,
            "Update-PlacePreviewCaptures does not read the C# task result")
    require("[System.IO.File]::WriteAllBytes($tmpPath, $bytes)" in update_fn
            and "[System.IO.File]::Move($tmpPath, $pngPath)" in update_fn,
            "atomic per-session PNG handover (tmp write + move) is missing")
    # 6.1.3 REGRESSION GUARD (live 6.0.5 failure): Windows PowerShell 5.1
    # could not bind object[] from @(4.0, 8.0) to a one-argument
    # DoubleCollection constructor. New-PlacePreviewVisual then aborted, so
    # the row had no IconImage and the self-test necessarily skipped assign.
    visual_fn = source[source.index("function New-PlacePreviewVisual"):source.index("function Start-PlacePreviewCapture")]
    require("DoubleCollection]::new(@(" not in visual_fn,
            "the live-failing one-argument DoubleCollection constructor returned")
    dash_steps = [
        "$strokeDashArray = [System.Windows.Media.DoubleCollection]::new()",
        "[void]$strokeDashArray.Add(4.0)",
        "[void]$strokeDashArray.Add(8.0)",
        "$spinner.StrokeDashArray = $strokeDashArray",
    ]
    for marker in dash_steps:
        require(marker in visual_fn, f"safe StrokeDashArray step missing: {marker}")
    dash_positions = [visual_fn.index(marker) for marker in dash_steps]
    require(dash_positions == sorted(dash_positions) and len(set(dash_positions)) == len(dash_positions),
            "safe StrokeDashArray steps are not in constructor/add/add/assign order")

    assign_fn = source[source.index("function Set-PlacePreviewImage"):source.index("function New-PlacePreviewSelfTestImage")]
    require("CheckAccess()" in assign_fn and "BeginInvoke(" in assign_fn,
            "Set-PlacePreviewImage must route through the WPF dispatcher")
    require("$Bytes[0] -eq 0x89" in assign_fn,
            "PNG magic-byte verification is missing from the assign path")
    # 6.0.5 REGRESSION GUARD (this was the live defect): the first frame must
    # never be handed to the UI with Opacity 0 and then depend on a fade-in
    # animation to become visible. If that animation does not run - which is
    # documented for this very program since 5.0.2 ("Einblend-Animation kam
    # nie an") - the tile stays empty forever while the log claims success.
    require("$Row.IconImage.Opacity = 0" not in assign_fn,
            "the preview image is made invisible again (Opacity = 0) and only "
            "an animation would bring it back - that was the 6.0.4 defect")
    require("$Row.IconImage.Opacity = 1\n                try {" in assign_fn
            or "$Row.IconImage.Opacity = 1" in assign_fn,
            "the first preview frame must be visible without any animation")
    require("FillBehavior]::Stop" in assign_fn,
            "the decorative fade must release the local opacity value again")
    require("PREVIEW_OPACITY_RESCUE" in assign_fn,
            "the fade-in watchdog for the preview image is missing")
    require("Start-PlacePreviewVisibilityVerify $Row $flow $isSelfTest" in assign_fn,
            "the delayed visibility verification is not wired into the assign path")
    # The self-test verdict must NOT be written straight after assignment any
    # more (6.0.4 logged PREVIEW_UI_SELFTEST_OK even at opacity 0).
    require("PREVIEW_UI_SELFTEST_OK" not in assign_fn,
            "the self-test still reports success before visibility was measured")
    verify_fn = source[source.index("function Start-PlacePreviewVisibilityVerify"):source.index("function Write-PreviewTrace")]
    require("PREVIEW_UI_SELFTEST_OK" in verify_fn and "PREVIEW_UI_SELFTEST_FAILED" in verify_fn,
            "the measured self-test verdict is missing from the verification step")
    require("$state.reallyVisible" in verify_fn,
            "the self-test verdict is not bound to the measured visibility")
    state_fn = source[source.index("function Get-PlacePreviewVisualState"):source.index("function Format-PlacePreviewVisualState")]
    for needle in ("effOpacity", "IsVisible", "ActualWidth", "$Row.IconFrame", "$Row.Root"):
        require(needle in state_fn,
                f"visibility measurement does not look at {needle}")
    diag_fn = source[source.index("function Write-PreviewDiagnoseFile"):source.index("function Get-PlacePreviewVisualState")]
    for needle in ("preview-diagnose.txt", "preview-cache", "$script:PreviewDiagIdentity",
                   "$script:PreviewCaptureMode", "$script:PreviewSelfTestVerdict"):
        require(needle in diag_fn, f"the short preview report does not contain {needle}")
    preview_fn = source[source.index("function Get-StudioWindowInfos"):source.index("function Resolve-PlacePreviewHandle")]
    require("return , $script:PreviewWindowCache" not in preview_fn,
            "window info cache is nested again by unary comma (breaks multiple Studio windows)")
    window_name_fn = source[source.index("function Get-StudioWindowName"):source.index("function Get-PlaceName")]
    require("return , $script:WindowNameCache" not in window_name_fn,
            "window title cache is nested again by unary comma (breaks multi-window title matching)")

    # 7.0.1: the playtest machinery is gone and sim_start is disabled.
    lua_text = plugin_source(source)
    require("startPlay" not in lua_text and "stopPlay" not in lua_text and "sessionAgent" not in lua_text,
            "playtest helpers survived the 7.0.0 cut")
    require("tools.play_start" not in lua_text and "tools.play_stop" not in lua_text and "tools.gui_click" not in lua_text,
            "a removed playtest tool is still registered")
    sim_start = lua_text[lua_text.index("tools.sim_start = function"):lua_text.index("tools.sim_stop = function")]
    require("return simDisabledResult()" in sim_start,
            "sim_start does not use the central disabled-result helper")
    sim_disabled_fn = lua_text[lua_text.index("local function simDisabledResult()"):lua_text.index("local function simStateData")]
    require('code = "SIM_DISABLED"' in sim_disabled_fn
            and 'severity = "notice"' in sim_disabled_fn
            and 'EDIT_MODE_SIMULATION_UNAVAILABLE' in sim_disabled_fn
            and 'documented Studio API' in sim_disabled_fn,
            "sim_start is not explicitly disabled with the correct notice and Edit-mode reason")
    require("ExecuteRunModeAsync" not in sim_start,
            "disabled sim_start still contains a reachable Studio Run start path")
    require("StudioTestService:ExecuteRunModeAsync()" not in lua_text
            and "RunService:Run()" not in lua_text
            and "Enum.KeyCode.F8" not in lua_text,
            "an executable Studio Run start path survived outside the sim_start stub")
    sim_stop = lua_text[lua_text.index("tools.sim_stop = function"):lua_text.index("tools.sim_status = function")]
    require("RunService:Stop()" in sim_stop and "waitForEditMode(true, 12)" in sim_stop,
            "sim_stop lost its RunService:Stop() + EditModeActive return")
    require("SIM_STOP_NEEDS_USER" in sim_stop,
            "sim_stop lost the bounded user handover instead of retrying forever")
    execute_start = lua_text.index("executeTool = function(tool")
    guard_end = lua_text.index("local okRun, result = xpcall(function()", execute_start)
    guard = lua_text[execute_start:guard_end]
    require("USER_PLAYTEST_ACTIVE" in guard and "SIM_RUNNING" in guard and "allowInSimMode" in guard,
            "the persistent-edit guard no longer blocks with USER_PLAYTEST_ACTIVE/SIM_RUNNING")
    require("play_start" not in lua_text and "play_stop" not in lua_text and "play_here" not in lua_text,
            "a playtest name survived inside the plugin Lua")

    # 7.0.1: sim_start stays blocked at HTTP and plugin boundaries; all other
    # tools remain available, including calls nested inside batch/start_job.
    require("New-SimBlockedResult" in source and "New-SelfTestBlockedResult" not in source,
            "the sim-disabled result helper is missing or the old self-test helper survived")
    require("if ($tool -eq 'sim_start')" in source and "if ([string]$call.tool -eq 'sim_start')" in source,
            "the direct/parallel SIM_DISABLED guards do not target sim_start")
    require('if tool == "sim_start" then' in lua_text and 'SIM_DISABLED' in lua_text,
            "nested plugin calls can bypass the sim_start disable guard")
    sim_allowed_fn = lua_text[lua_text.index("local function simAllowedNow"):lua_text.index("local function simStateData")]
    require("return false" in sim_allowed_fn and "_bridgeSimAllowed" not in lua_text,
            "simAllowed must remain false even for legacy or caller-supplied opt-ins")
    sim_status = lua_text[lua_text.index("tools.sim_status = function"):lua_text.index("function SimSendKey")]
    require("simAllowed = simAllowedNow()" in sim_status,
            "sim_status does not report the same effective setting as sim_start")
    mode_fn = lua_text[lua_text.index("local function currentMode()"):lua_text.index("local function currentPlayerCount()")]
    require('isRunMode == true then return "run"' in mode_fn
            and 'isRunMode == false then return "play"' in mode_fn
            and 'return "unknown"' in mode_fn,
            "Studio Run and player Play/F5 are conflated in the mode detector")
    sim_state_fn = lua_text[lua_text.index("local function simStateData()"):lua_text.index("tools.sim_start = function")]
    require("playerCount = currentPlayerCount()" in sim_state_fn
            and "mode='run' is official Studio Run" in sim_state_fn
            and "mode='play' is a separate player Play/F5 test" in sim_state_fn
            and "mode='play' is a separate player Play/F5 test" in sim_status,
            "sim_status does not report the distinct mode/player state clearly")
    sim_stop = lua_text[lua_text.index("tools.sim_stop = function"):lua_text.index("tools.sim_status = function")]
    require('simStartedByBridge ~= true or userPlaytestActive == true' in sim_stop
            and 'SIM_NOT_BRIDGE_OWNED' in sim_stop
            and 'user-started Studio Run or Play/F5 test' in sim_stop
            and sim_stop.index('SIM_NOT_BRIDGE_OWNED') < sim_stop.index('RunService:Stop()'),
            "sim_stop could interrupt a session that is not confirmed bridge-owned")
    require("exits Edit mode" in source and "documented Studio API has no supported true Edit-mode physics/script path" in source,
            "Run/Edit-mode limitation is not stated accurately")
    require("([string]$newState.mode -eq 'play')" in source,
            "USER_PLAYTEST_ACTIVE must be reserved for actual Play/F5 mode, not Studio Run")
    require("$newState.simRunning" in source and "$newState.startedByBridge" in source
            and "startedByBridge = simStartedByBridge" in lua_text,
            "known bridge ownership is not preserved for safe cleanup after a server reconnect")
    require("simAllowed      = $false" in source and "$settings.simAllowed = [bool]$loaded.simAllowed" not in source,
            "legacy settings can re-enable the unsupported Studio Run simulation")
    require("code = 'SELF_TEST_DISABLED'" not in source
            and "BridgeSettings.selfTestAllowed" not in source
            and "plugin:GetSetting(\"arenaSelfTest\")" not in source,
            "the old self-test setting/code survived (only the historical notes may mention it)")

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

    # 7.0.0: the injected session/client/reporter sources are GONE. No
    # embedded Lua chunk may come back, and no reporter marker may survive -
    # the simulation block is plain plugin code now.
    for gone in ("SESSION_AGENT_SOURCE", "SESSION_CLIENT_REPORTER_SOURCE", "SESSION_REPORTER_SOURCE",
                 "CLIENT_AGENT_SOURCE", "CLIENT_SOURCE"):
        require(gone not in lua, f"removed 7.0.0 embedded source is back: {gone}")
    for gone in ("reporterLoopAlive", 'action == "move_character"', "end_test",
                 "SharedTableRegistry", "reporterEndTest"):
        require(gone not in lua, f"removed 7.0.0 reporter/session marker is back: {gone}")

    # 7.2.4: the question window became XAML-based too, so the bridge ships
    # five Window here-strings (main, settings, handoff, user message,
    # question); 7.4.0 added a sixth (Mesh-Uploads) and 7.5.0 REMOVED it
    # again - the mesh upload is a tool call now (upload_asset), the user
    # uploads nothing by hand and needs no window. 7.6.2 adds the Open Cloud
    # permission window (Introspect result before saving), so six is the
    # truth now. Every block is parsed here - that is what catches a broken
    # dialog before PowerShell ever sees the file.
    blocks = xaml_blocks(source)
    require(len(blocks) == 6, f"expected 6 XAML Window blocks, found {len(blocks)}")
    for index, block in enumerate(blocks, 1):
        try:
            ET.fromstring(block)
        except ET.ParseError as exc:
            raise AssertionError(f"XAML block {index} is not XML: {exc}") from exc
    # The two dialogs must resolve every StaticResource from the one shared
    # block; an unresolved key would throw at XamlReader.Load, i.e. the window
    # would simply never appear.
    shared = re.search(r"\$script:ArenaDialogStyles = @'\n([\s\S]*?)\n'@", source)
    require(shared is not None, "shared dialog resource block is missing")
    shared_keys = set(re.findall(r'x:Key="([A-Za-z0-9_]+)"', shared.group(1)))
    # 7.5.0: the mesh-uploads window is GONE (upload_asset does the upload),
    # so only the two dialogs built from here-strings remain here. The
    # settings window is checked below through its own XAML block instead.
    for name, func in (("question", "function Get-AskWindowXaml"),
                       ("user message", "function Get-UserMessageWindowXaml"),
                       ("cloud permissions", "function Show-CloudPermissionsWindow")):
        start = source.index(func)
        tpl = re.search(r"@'\n([\s\S]*?)\n'@", source[start:start + 12000]).group(1)
        used = set(re.findall(r"\{StaticResource ([A-Za-z0-9_]+)\}", tpl))
        require(not (used - shared_keys),
                f"{name} window references unknown resources: {sorted(used - shared_keys)}")
        require("<!--ARENA_DIALOG_STYLES-->" in tpl,
                f"{name} window does not embed the shared resource block")

    # 6.1.3 mini-update guards: modelling hierarchy/seams/caps/welds,
    # detached asset sanitation and the opt-in performance gate stay present.
    for marker in (
        "tools.build_polygon_model = function(args)",
        "tools.build_assembly = function(args)",
        "side-corrected skin placement + ear-clipping + two WedgeParts per triangle",
        "function MASTER_BUILD.closeBoundaryLoops(entries)",
        "function MASTER_BUILD.weldContainer(container,weldName)",
        'local mainWelds=args.mainWelds or {}',
        'args.sanitize == true or args.removeScripts == true',
        'inst:IsA("RemoteEvent") or inst:IsA("RemoteFunction")',
        "EditorIconsSwitch",
        "function Set-EditorIconsEnabled",
        "editorIconsEnabled = $true",
        "$editorIconsSwitch.IsChecked = $editorIconsNow",
        "Set-EditorIconsEnabled ([bool]$s.IsChecked)",
        "titleCharacters = 70",
        "messageCharacters = 140",
        "$script:PlacePreviewIntervalSeconds = 3.0",
        "return @($entries | Sort-Object",
    ):
        require(marker in source, f"required 6.1 marker missing: {marker}")
    require("return , @($entries | Sort-Object" not in source, "history entries are nested again")

    # 6.1.4 Polygon Engine 2.0 guards: the canonical WedgePart axis rule and
    # its reference Lua snippet must ship as permanent AI-facing guidance
    # (Get-BridgeGuides), reaching every new session via session-start /
    # get_docs, not just live in a one-off human changelog note.
    for marker in (
        "polygonEngineRules = @{",
        "Local X = thickness / face normal",
        "CFrame.fromMatrix(position, normal, up, dir)",
        "skinOffset = -normal * thickness * 0.5",
        "local function drawSeamlessTriangle(p1, p2, p3, parent, props)",
        "local skinOffset = -normal * (thickness * 0.5)",
        "HARD CONSTRAINT for any hand-written WedgePart/triangle geometry",
    ):
        require(marker in source, f"required Polygon Engine 2.0 marker missing: {marker}")

    # 7.6.3 project-first guides preserve the user's method and Place patterns.
    for marker in (
        'local shouldWeld=args.autoWeld~=false',
        'if spec.autoWeld~=nil then shouldWeld=spec.autoWeld~=false end',
        'local geometryOwned={cframe=true,position=true,orientation=true,rotation=true,size=true,pivotoffset=true}',
        'if not geometryOwned[string.lower(tostring(key))] then safeProperties[key]=value end',
        '-- Size and CFrame are geometry invariants. Set them LAST',
        'autoWeldDefault=true',
        'weldedSubmodels=weldedSubmodels',
        'ignoredGeometryProperties=ignoredGeometryProperties',
        'geometryInvariant="Size/CFrame applied after safe style properties"',
        "autoWeld=@{type='bool';required=$false;default='true'",
        "projectConsistencyRules = @{",
        "Use the user-requested representation or the Place convention",
        "Blender is a recommendation for suitable greenfield geometry",
        "userRequestedPolygon may record intent, but is not a permission gate.",
        "polygonPreference = 'Method priority: explicit user instructions",
        "Completion follows the task brief and Place convention",
        "OPTIONAL ORGANIC MEASUREMENTS",
        "organic=true/organicKind is an optional per-model audit marker",
        "polygonInputContract = 'Structured form: build_polygon_model",
        "polygonWorkflow = '1 inspect the Place, selection and user brief",
        "polygonPatterns = 'Facade/roof/shield/panel",
        "polygonBudget = 'Each n-vertex face usually produces n-2 triangles",
        "polygonTemplate = 'build_polygon_model",
        "A low-poly or primitive style can be complete.",
    ):
        require(marker in source, f"project-first build-policy marker missing: {marker}")
    guides_block = source[source.index("function Get-BridgeGuides"):source.index("function Get-SessionStartPackage")]
    for obsolete in ("first model-creation call is build_mesh_model",
                     "POLYGON WITHOUT USER REQUEST", "ORGANIC_POLYGON_REQUIRED",
                     "FORBIDDEN - FORGOTTEN COLOUR OR MOTION", "DETAIL_REQUIRED",
                     "Blender-first"):
        require(obsolete not in guides_block, f"active guides still contain obsolete mandate: {obsolete}")
    require('local shouldWeld=args.autoWeld==true' not in source,
            'polygon autoWeld silently defaulted back to false')
    universal_contract = ROOT / "MODEL_BUILD_CONTRACT.md"
    require(universal_contract.exists(), "MODEL_BUILD_CONTRACT.md is missing")
    universal_text = universal_contract.read_text(encoding="utf-8")
    for marker in ("Method priority", "does not impose one builder",
                   "is a recommendation for suitable greenfield",
                   "does not require a special permission flag",
                   "LowPolyHouse", "- **Vehicles:** possible options", "facesSkipped", "model_audit",
                   "A deliberately simple or blockout result can be",
                   "complete; grade metadata is optional"):
        require(marker in universal_text, f"project-first model contract is missing: {marker}")
    for obsolete in ("every nontrivial visible 3D build", "is the first model-building call",
                     "POLICY 7.5.5 (Blender-first)"):
        require(obsolete not in universal_text, f"model contract still contains obsolete mandate: {obsolete}")
    house_example = universal_text.split("## Working example:", 1)[1].split("## Shape-specific patterns", 1)[0]
    for face in ("FrontGable", "BackGable", "LeftWall", "RightWall", "Floor", "LeftSlope", "RightSlope"):
        require(face in house_example, f"LowPolyHouse shell is missing face {face}")
    require('name="Back"' in source and 'name="Bottom"' in source,
            "generic polygon template must not imply a single-front-face shell")

    wedge_fn = source[source.index('function MASTER_BUILD.triangleWedges'):source.index('function MASTER_BUILD.weldContainer')]
    require(wedge_fn.index('applyProperties(w,safeProperties)') < wedge_fn.index('w.Size=Vector3.new(') < wedge_fn.index('w.CFrame=cf+shift'),
            'safe style properties must run before final immutable Size/CFrame assignment')

    # Studio minimization must no longer pre-block periodic preview capture.
    require("if (IsIconic(hwnd)) { result.Minimized = true" not in source, "C# preview still blocks minimized Studio")
    require("if ([Arena.ScreenHelper]::IsIconic($hwnd))" not in source, "fallback preview still blocks minimized Studio")


    # ------------------------------------------------------------------
    # 6.2.0 regression guards: UI Engine 1.0.
    # These lock in the invariants the engine exists to own, exactly like the
    # polygon guards above. If any of them is lost, the old GUI bugs return.
    # ------------------------------------------------------------------
    require("local UI_ENGINE" not in lua,
            "UI_ENGINE must stay a GLOBAL table like MASTER_BUILD: a top-level "
            "local would push the plugin over Luau's 200-register limit")
    for marker in (
        "UI_ENGINE = {}",
        'UI_ENGINE.ENGINE_VERSION = "2.0"',
        # Rule 1 - transform wrapper owns AnchorPoint and UIScale.
        'wrapper.AnchorPoint = Vector2.new(0.5, 0.5)',
        'local scale = Instance.new("UIScale"); scale.Name = "ArenaScale"',
        # Rule 1b - layout children get an outer slot so the layout drives the
        # position while the scale animation still grows from the centre.
        'slot.AnchorPoint = Vector2.new(0, 0)',
        # Rule 2 - design space compiles to scale-only UDim2.
        "pos = UDim2.fromScale(math.clamp(x, -50, 150) / 100",
        "offsetUsed = 0",
        # Rule 3 - preserve an explicit padding value (including zero), then derive only the omitted value from the corner radius.
        "local padScale = tonumber(opts.padding)",
        "if padScale == nil then padScale = math.max(radius * 0.36, 0.04) end",
        "padScale = math.clamp(padScale, 0, 0.5)",
        # Rule 4 - stroke thickness scales.
        "stroke.StrokeSizingMode = Enum.StrokeSizingMode.ScaledSize",
        # Rule 5 - a UIGradient is parented INTO a UIStroke.
        'UI_ENGINE.gradient(stroke, stops, skin.gradStroke or 0, nil, "ArenaStrokeGradient")',
        # Rule 7 - CanvasGroup only on purpose, never nested.
        "local useGroup = wantsGroupFade and caps.canvasGroup and opts.insideCanvasGroup ~= true",
        "screen.ZIndexBehavior = Enum.ZIndexBehavior.Sibling",
        # Rule 8 - shadows in scale.
        "shadow.BlurRadius = UDim.new(math.clamp(tonumber(spec.blur) or 0.08, 0, 1), 0)",
        # Capability probing instead of training-data assumptions.
        "function UI_ENGINE.caps(force)",
        'c.uiShadow = UI_ENGINE.probeClass("UIShadow")',
        # Generic colors remain an audit observation, never a build gate.
        "function UI_ENGINE.isGeneric(c)",
        "genericColors",
        "descriptive only",
        "blandnessScore = blandness",
        # The five tools.
        "tools.ui_capabilities = function(args)",
        "tools.ui_skin = function(args)",
        "tools.build_surface = function(args)",
        "tools.build_interface = function(args)",
        "tools.ui_audit = function(args)",
        # Engine 2.0 - glow, real textures, radial menus.
        'UI_ENGINE.ENGINE_VERSION = "2.0"',
        "function UI_ENGINE.textureRecipe",
        "function UI_ENGINE.glowEmitter",
        "function UI_ENGINE.radialMenu",
        "tools.ui_glow = function(args)",
        "tools.ui_texture = function(args)",
        "tools.ui_radial = function(args)",
        "TEXTURE_ASSET_MISSING",
        "RADIAL_ASSET_MISSING",
        "glowStacks",
        "radialMenus",
        # Write protection and permanent session rule.
        "build_surface = true, build_interface = true,",
        "uiEngineRules = @{",
    ):
        require(marker in source, f"required UI Engine 1.0 marker missing: {marker}")
    require('failCode("STYLE_TOO_GENERIC"' not in plugin_source(source),
            "neutral/muted requested UI colors are still rejected by a style heuristic")

    require(source.count("category = 'ui'") == 8,
            "expected exactly 8 documented UI Engine tools (5 from 1.0 + glow/texture/radial)")
    require(source.count("category = 'world'") == 11,
            "expected exactly 11 documented World Engine tools")
    require(source.count("category = 'sim'") == 3,
            "expected exactly 3 documented simulation tools")
    require(source.count("category = 'play'") == 0,
            "a playtest-category tool is still documented")

    # The transform wrapper must be anchored BEFORE the UIScale exists, and the
    # content padding must be computed AFTER the corner radius is known.
    surface_fn = lua[lua.index("function UI_ENGINE.surface(opts)"):lua.index("function UI_ENGINE.textNode")]
    require(surface_fn.index("wrapper.AnchorPoint") < surface_fn.index('local scale = Instance.new("UIScale")'),
            "the transform wrapper must get its AnchorPoint before its UIScale")
    require(surface_fn.index("local radius = UI_ENGINE.applyCorner")
            < surface_fn.index("local padScale = tonumber(opts.padding)")
            < surface_fn.index("if padScale == nil then padScale = math.max(radius * 0.36, 0.04) end"),
            "default content padding must follow the corner radius while preserving explicit values")

    # The runtime motion LocalScript is a separate Luau chunk - parse it too,
    # otherwise a syntax error there would only surface in a live playtest.
    motion = re.findall(r"UI_ENGINE\.MOTION = \[==\[(.+?)\]==\]", lua, re.S)
    require(len(motion) == 1, "UI_ENGINE.MOTION source block not found exactly once")
    try:
        ast.parse(motion[0])
    except Exception as exc:
        raise AssertionError(f"UI_ENGINE.MOTION does not parse as Luau: {exc}") from exc
    require("scale.Scale = P.from" in motion[0] and "TweenService:Create(scale, info, { Scale = 1 })" in motion[0],
            "the motion script must animate the UIScale of the transform wrapper, not the element size")

    # ------------------------------------------------------------------
    # 7.0.1 regression guards: disabled simulation, progress contract, handoff,
    # UI Engine 2.0 and World Engine 1.0.
    # ------------------------------------------------------------------
    for marker in (
        # Simulation tools and their honest state report.
        "local function simStateData()",
        "simStartedByBridge",
        # Progress contract: never block on a missing percent.
        "Missing percent",
        "progressPercent",
        "$Shared.ProgressStates",
        # Handoff: complete games only, file under LOCALAPPDATA, session start.
        "HANDOFF_NOT_ALLOWED",
        "HANDOFF_INCOMPLETE",
        "handoffId",
        "'handoff'",
        # Stable window/place identity.
        "Get-PlaceIdentityKey",
        "PreviewHandleInfos",
        # World Engine 1.0 surface.
        "WORLD_ENGINE = {}",
        'WORLD_ENGINE.VERSION = "1.0"',
        "workspace.ArenaProps",
        "ArenaProps",
        "ArenaDetail",
        "lcg(seed)",
        "placeholderCount",
        "styleCompliance",
        # UI Engine 2.0 surface.
        "textureRecipe",
        "glowEmitter",
        "radialMenu",
        "TEXTURE_ASSET_MISSING",
        "RADIAL_ASSET_MISSING",
    ):
        require(marker in source, f"required 7.0.0 marker missing: {marker}")
    require("tools.play_start" not in lua and "SESSION_AGENT_SOURCE" not in source
            and "CLIENT_AGENT_SOURCE" not in source and "SESSION_REPORTER_SOURCE" not in source,
            "removed 7.0.0 playtest machinery is still present")

    # ------------------------------------------------------------------
    # 7.0.5: independent server-side watchdog, reconnect-safe commandIds,
    # Cloudflare-safe deadlines, admin reset and the centered Place row.
    # ------------------------------------------------------------------
    sweep_start = source.index("$script:BridgeSweepScript = {")
    sweep_end = source.index("$script:BridgeListenerScript = {", sweep_start)
    sweep = source[sweep_start:sweep_end]
    for marker in (
        "while ($true)",
        "Start-Sleep -Seconds 2",
        "STUDIO_ABANDONED",
        "EXECUTOR_UNRESPONSIVE",
        "EXECUTOR_UNAVAILABLE",
        "EXECUTOR_DROPPED_COMMAND",
        "COMMAND_DELIVERY_UNCONFIRMED",
        "QUEUE_EXPIRED",
        "abandonedBy = 'server-watchdog'",
        "$Shared.CompletedCommandIds.TryAdd($dedupeKey, $now)",
        "Queue-LateResult",  # never: the sweep is self-contained -> check the queue write instead
    )[:-1]:
        require(marker in sweep, f"independent server watchdog is missing: {marker}")
    require("$Shared.LateResults.TryGetValue($origin, [ref]$lateQueue)" in sweep
            and "$Shared.CommandResults[$id] = $failureJson" in sweep
            and "$signal.Set()" in sweep,
            "the watchdog cannot deliver its failure to a waiter or as a lateResult")
    require("$Shared.SweepState.LastSweepAt" in sweep and "$Shared.SweepState.Abandoned" in sweep,
            "the watchdog does not publish its liveness proof (SweepState)")
    require("$sweepPs = [PowerShell]::Create()" in source
            and "[void]$sweepPs.AddScript([string]$script:BridgeSweepScript).AddArgument($script:Shared)" in source
            and "$script:SweepPowerShell = $sweepPs" in source,
            "the independent watchdog is not started next to the listener")

    # reconnect-safe routing
    for marker in (
        "CommandOrigins",
        "CommandInstanceGuids",
        "SessionSuccessors",
        "function Get-CommandOrigin",
        "function Test-CommandInstanceMatches",
        "function Get-DeliverySession",
        "function Register-SessionSuccessor",
        "Queue-LateResult (Get-CommandOrigin $id) $id $resultJson $pendingInfo",
        "Get-SessionInstanceGuid",
    ):
        require(marker in source, f"reconnect-safe result routing is missing: {marker}")
    require("Get-CommandOrigin $id" in source
            and "if (-not (Test-CommandInstanceMatches $sidForResult $commandId))" in source,
            "the result endpoint still rejects results from the same plugin instance after a reconnect")
    require("$Shared.SessionSuccessors[$old] = $new" in source
            and "if ($Shared.PendingCommands.TryGetValue($old, [ref]$oldBag))" in source
            and "$newBag[$id] = (To-Json $info 10)" in source,
            "waiting commands are not handed over to the successor session")
    require("Register-SessionSuccessor ([string]$predecessor.sessionId) $sessionId" in source
            and "$candidatePolls -le 0 -and $candidateAge -gt 20 -and $candidatePending -gt 0" in source,
            "a plugin restart does not adopt the waiting commands of the dead predecessor")
    require("Reset-SessionQueue $sessionId 'The Studio plugin instance restarted." not in source,
            "a plugin reconnect still throws the waiting queue away")

    # Cloudflare-safe HTTP deadlines and the admin reset
    require("$timeout = 55" in source and "[Math]::Min([int]$body.timeoutSeconds, 85)" in source
            and "[Math]::Min([int]$toolArgs.timeoutSeconds + 25, 85)" in source,
            "tool answers are not capped below the Cloudflare 524 limit")
    require("function Force-FailSessionQueue" in source
            and "action -eq 'force_fail'" in source
            and "action -eq 'clear_pending'" in source
            and "$tool -eq 'clear_pending' -or $tool -eq 'force_fail'" in source
            and "FORCE_CLEARED" in source,
            "the admin reset (force_fail / clear_pending) is missing")
    require("Clear_pending" not in source and "clear_pending" in source,
            "admin reset naming regressed")
    require("$Shared.ExecutorResetRequests[$sid] = Get-UnixSeconds" in source
            and "while ($queue.TryDequeue([ref]$raw)) { $raw = $null }" in source,
            "the admin reset does not empty the FIFO and ask Studio to drop its local queue")

    # plugin-side duplicate protection / result cache
    require("local completedResults = {}" in source
            and "local function rememberCompletedResult(commandId, result)" in source
            and "rememberCompletedResult(commandId, commandResult)" in source,
            "the plugin does not remember its results for a duplicate delivery")
    require("local cached = completedResults[commandId]" in source
            and "pcall(postResult, commandId, cached)" in source,
            "a re-delivered commandId would be executed a second time instead of re-sending its result")
    require("resultOutbox = outboxCount" in source and "cachedResults = completedCount" in source,
            "the executor snapshot does not report cached results / outbox size")

    # 7.0.6 guarantees: one self-report answer that proves deployment, stable
    # session identity instead of a new session per handshake, a delivery
    # timeline per command, instant answers for dead/busy executors and a
    # visible plugin state in Studio.
    for marker in (
        "if ($path -eq '/api/version')",
        "function Get-VersionReport",
        "InstanceSessions = [System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()",
        "function Resolve-InstanceSession",
        "function Get-StudioDeliveryHealth",
        "STUDIO_UNREACHABLE",
        "STUDIO_BUSY",
        "timelineRule",
        "'get_bridge_log' {",
        "local function setWidgetStatus(extra)",
        "ARENA-PLUGIN-FEHLER",
        "function Invoke-PlaceRowCancel",
        "function Get-PlaceOpenCommand",
        "preview = @{",
    ):
        require(marker in source, f"7.0.6 marker missing: {marker}")
    require("sessionId = $(if ([string]::IsNullOrWhiteSpace($knownSessionId))" in source,
            "an unknown session poll would no longer receive the known sessionId")
    require("if ($deliveryHealth.state -eq 'wedged')" in source
            and "commandSent = $false" in source,
            "the executor pre-flight (STUDIO_UNREACHABLE before queueing) is missing")
    require("queuedAt = [int64]$item.queuedAt" in source
            and "deliveredAt = [int64]$item.deliveredAt" in source
            and "heartbeatAt = [int64]$item.heartbeatAt" in source,
            "the per-command delivery timeline is incomplete")

    # 7.0.7 LIVE FIX: Both row builders must DECLARE CommandCancelButton in
    # their [pscustomobject] initializer. Without the declaration the assignment
    # throws in Windows PowerShell, the whole row build aborts - and with the
    # minimal fallback carrying the same line, NO row is ever attached (live
    # symptom: "Place-Liste wird repariert" with an empty list).
    require(source.count("CommandCancelButton = $null") == 2,
            "CommandCancelButton is not declared in BOTH row initializers (7.0.6 live bug)")
    require(source.count("$row.CommandCancelButton = $cancelButton") == 2,
            "the optional cancel button is not built in exactly both row builders")
    cancel_builder = source[source.index("function New-Row {"):source.index("function New-MinimalPlaceRow {")]
    fallback_builder = source[source.index("function New-MinimalPlaceRow {"):source.index("function Sync-PlaceList {")]
    for builder, name in ((cancel_builder, "New-Row"), (fallback_builder, "New-MinimalPlaceRow")):
        require("try {" in builder and "Abbrechen-Knopf konnte" in builder,
                f"{name} builds the optional cancel button without try/catch protection")
    # The UI runs in the MAIN runspace: it must never call the server handler's
    # functions (Get-DeliverySession / Request-CommandCancel only exist there).
    cancel_fn = source[source.index("function Invoke-PlaceRowCancel {"):source.index("function Update-PlaceProgressVisual {")]
    # Kommentarzeilen zaehlen nicht: geprueft wird der ausfuehrbare Code.
    cancel_code = "\n".join(line for line in cancel_fn.splitlines() if not line.strip().startswith("#"))
    require("Get-DeliverySession " not in cancel_code and "Request-CommandCancel" not in cancel_code,
            "the place-row cancel path calls server-runspace functions again")
    require("function Get-UiDeliverySession" in source
            and "$script:Shared.CancelRequests[$cancelKey] = $now" in cancel_fn
            and "'COMMAND_CANCELLED'" in cancel_fn
            and "CompletedCommandIds[$cancelKey] = $now" in cancel_fn,
            "the place-row cancel does not resolve the delivery chain / answer the waiter itself")
    require("Get-PlaceOpenCommand (Get-UiDeliverySession $sessionId)" in source,
            "Update-PlaceProgressVisual still resolves the delivery session with the handler function")
    require("$script:LastPlaceRowError" in source
            and "'Ursache: ' + [string]$script:LastPlaceRowError" in source,
            "the repair notice does not show the real row error")

    # 7.0.8 LIVE FIX: Im 7.0.x-Plugin fehlten drei Funktionen KOMPLETT, und
    # firstNonEmpty wurde VOR seiner Deklaration benutzt. In Lua ist so ein
    # Name beim Aufruf ein GLOBAL-Zugriff -> nil -> "attempt to call a nil
    # value" -> der Befehl endet als RUNTIME_ERROR (live: "fast alle Werkzeuge
    # kaputt"). Gefunden mit einer Scope-Analyse (luaparser + Scope-Resolver),
    # bestaetigt mit echtem Luau (v739, WebAssembly) im Lauf.
    plugin_lua = plugin_source(source)
    require(plugin_lua.count("local function findByPath(path)") == 1,
            "findByPath fehlt im Plugin - jede Pfad-Referenz stirbt mit RUNTIME_ERROR")
    require(plugin_lua.count("local function resolveGroups(kind, args)") == 1,
            "resolveGroups fehlt im Plugin - union/intersect sterben mit RUNTIME_ERROR")
    require(plugin_lua.count("local function runSolidOperation(kind, base, others, args)") == 1,
            "runSolidOperation fehlt im Plugin - union/subtract/negate/intersect sind tot")
    require("local firstNonEmpty\n" in plugin_lua
            and "firstNonEmpty = function(...)" in plugin_lua,
            "firstNonEmpty wird weiterhin vor seiner Deklaration benutzt (nil-Global)")
    require("local nextInst = childByToken(current, segments[index])" in plugin_lua
            and "game:GetService(segments[index])" in plugin_lua,
            "findByPath findet Dienste nicht (GetService-Rueckfall fehlt)")
    require("local loopOk, loopErr = xpcall(function()" in plugin_lua
            and "Die Poll-Schleife hat einen Fehler abgefangen" in plugin_lua,
            "die Poll-Schleife ist nicht fehlerfest (still beendete Aufgabe = keine Befehle)")
    require("local tplName = (type(with) == \"table\" and with.name) or nil" in plugin_lua,
            "tplName wird weiterhin ausserhalb seines Gueltigkeitsbereichs gelesen")

    # 7.1.0 LIVE FIX: BindReason in Get-PlaceIdentity, safe To-Json array
    # serialization, Ack-Outbox + Result-Outbox, and Re-Delivery.
    require("BindReason = ''" in source and "function Write-PreviewCaptureError" in source,
            "7.1.0 BindReason declaration or preview error throttle is missing")
    require("executorState.sendOrQueueAckBatch" in plugin_lua
            and "executorState.deliverOrQueueResult" in plugin_lua
            and "ackOutbox = {}" in plugin_lua,
            "7.1.0 plugin Ack-Outbox / deliverOrQueueResult missing")
    require("CommandPayloads" in source and "Update-PollerCount" in source,
            "7.1.0 CommandPayloads re-delivery or Update-PollerCount missing")

    # 7.1.1 LIVE HOTFIX: Studio executes commands again.
    #  a) Get-SessionCancellationIds must return a FLAT array. With the 7.1.0
    #     comma operator every @(Get-SessionCancellationIds ...) caller saw a
    #     1-element array (the empty array as element), so the /plugin/poll
    #     loop broke before the dequeue and no command ever reached Studio.
    cancel_ids_fn = source[source.index("function Get-SessionCancellationIds"):source.index("function Get-QueueSnapshot")]
    require("return , $items.ToArray()" not in cancel_ids_fn and "return $items.ToArray()" in cancel_ids_fn,
            "Get-SessionCancellationIds nests its array again (7.1.0 regression: poll never delivers)")
    poll_block = source[source.index("if ($path -eq '/plugin/poll') {"):source.index("if ($path -eq '/plugin/result') {")]
    require("$cancelledNow = @(Get-SessionCancellationIds $sid)" in poll_block
            and "'{\"ok\":true,\"sessionId\":' + (To-Json $sid 3)" in poll_block,
            "/plugin/poll must keep the @() cancellation check and announce sessionId in every answer")
    #  b) Windows PowerShell 5.1 throws "Die Argumenttypen stimmen nicht
    #     ueberein." for @($var) when $var holds a List[object]. Never wrap a
    #     List[object] variable in @(); use .ToArray() / [object[]] instead.
    snapshot_fn = source[source.index("function Get-QueueSnapshot"):source.index("function Get-SessionEntry")]
    require("@($pending)" not in snapshot_fn and "@($recentCommands)" not in snapshot_fn
            and "foreach ($item in $pending)" in snapshot_fn and "recent = $recentCommands.ToArray()" in snapshot_fn,
            "Get-QueueSnapshot wraps a List[object] in @() again (/api/status and /api/queue answer 500 on PowerShell 5.1)")
    require("commands=@($items)" not in source and "commands=$items.ToArray()" in source,
            "/plugin/agent heartbeat wraps a List[object] in @() again")
    list_object_vars = set(re.findall(r"\$(\w+)\s*=\s*New-Object System\.Collections\.Generic\.List\[object\]", source))
    list_object_vars |= {"pending", "events", "late"}  # returned by Get-PendingCommands / Take-Events / Take-LateResults
    offenders = sorted(name for name in list_object_vars if re.search(r"@\(\s*\$" + re.escape(name) + r"\s*\)", source))
    require(not offenders, f"@($var) around List[object] variables (PowerShell 5.1 ArgumentException): {offenders}")
    #  c) Get-PendingCommands returns ", $list"; wrapping the CALL in @() turns
    #     the whole list into one element, so reset/clear_pending missed every
    #     command once two were pending.
    require("@(Get-PendingCommands" not in source,
            "a caller wraps Get-PendingCommands in @() again (admin reset/clear_pending become no-ops)")
    force_fn = source[source.index("function Force-FailSessionQueue"):source.index("function Reset-SessionQueue")]
    reset_fn = source[source.index("function Reset-SessionQueue"):source.index("function Mark-CommandDelivered")]
    require("$pendingItems = Get-PendingCommands $sid" in force_fn and "foreach ($item in $pendingItems)" in force_fn,
            "Force-FailSessionQueue does not iterate the real pending list")
    require("$pending = Get-PendingCommands $sid" in reset_fn and "return $resetCount" in reset_fn,
            "Reset-SessionQueue does not iterate the real pending list / report the real count")
    #  d) Plugin identity: statePayload carries sessionId (lost since 7.0.0) and
    #     the bridge resolves polls/heartbeats by instanceGuid as a fallback.
    state_fn = plugin_lua[plugin_lua.index("local function statePayload()"):plugin_lua.index("local function handshake()")]
    require("sessionId = sessionId," in state_fn and "payload.gameId = tostring(game.GameId)" in state_fn,
            "plugin statePayload() lacks sessionId/gameId (every poll becomes a reconnect, heartbeat says 'Sitzung unbekannt')")
    require(plugin_lua.index("local sessionId") < plugin_lua.index("local function statePayload()"),
            "sessionId must be declared before statePayload() (Lua upvalue order)")
    update_fn = source[source.index("function Update-Session"):source.index("function New-Blob")]
    require("$Shared.InstanceSessions.TryGetValue($instanceGuidForUpdate" in update_fn
            and "$Shared.Sessions.ContainsKey($mappedSessionId)" in update_fn,
            "Update-Session has no instanceGuid fallback for polls without sessionId")
    require('if type(response.sessionId) == "string" and response.sessionId ~= "" and response.sessionId ~= sessionId then' in plugin_lua,
            "plugin does not adopt the sessionId announced in poll answers")
    #  e) GET /api/places for a normal token, degraded /api/status, watchdog
    #     safety net for never-delivered commands.
    require("if ($path -eq '/api/places') {" in source and "multiPlace=$false; places=$ownPlaces" in source,
            "per-place /api/places route missing (404 for normal tokens)")
    require("queueError = $queueError" in source and "Status: Queue-Schnappschuss fehlgeschlagen (degradiert)" in source,
            "/api/status does not degrade gracefully when the queue snapshot fails")
    require("COMMAND_NEVER_DELIVERED" in source and "undeliveredCommands = $undelivered" in source,
            "watchdog safety net / undeliveredCommands counter missing")

    # 7.6.3: optional audits and user/Place method priority; only an explicit
    # unapplied mesh slot can create a geometry Pending state.
    guides_block = source[source.index("function Get-BridgeGuides"):source.index("function Get-SessionStartPackage")]
    for marker in ("projectConsistencyRules = @{", "modelBuildRules = @{",
                   "organicBuildRules = @{", "OPTIONAL ORGANIC MEASUREMENTS",
                   "model_audit is optional and its findings never block report_done"):
        require(marker in guides_block, f"current project-first guide missing: {marker}")
    organic_guard = source[source.index("function Get-OrganicBuildGuardResult"):source.index("$context = $Context", source.index("function Get-OrganicBuildGuardResult"))]
    require("return $null" in organic_guard,
            "organic markers still activate a build/completion guard")
    for obsolete in ("DRAFT_GRADE_RISK", "DETAIL_REQUIRED", "ORGANIC_AUDIT_REQUIRED",
                     "ORGANIC_POLYGON_REQUIRED", "ORGANIC_COLORS_REQUIRED"):
        require(obsolete not in source, f"obsolete blocking code/text remains in bridge source: {obsolete}")

    audit_gate = source[source.index("# report_done may identify an explicitly generated, unapplied mesh slot below."):
                         source.index("$doneProgress = Read-ProgressState $sessionId")]
    require("$meshSlotCount -gt 0" in audit_gate and "$waitCount -gt 0" in audit_gate
            and "MESH_UPLOAD_PENDING" in audit_gate,
            "report_done does not check only actual, unapplied mesh slots")
    for obsolete in ("$primitiveAbuseNow", "$cylinderProblemCount -gt", "$auditAtTicks",
                     "ORGANIC_AUDIT_REQUIRED", "DETAIL_REQUIRED"):
        require(obsolete not in audit_gate,
                f"report_done audit section still gates on non-mesh audit data: {obsolete}")
    require("MESH_UPLOAD_PENDING" not in organic_guard,
            "mesh pending is incorrectly routed through the organic marker guard")
    quality_fn = plugin_lua[plugin_lua.index("WORLD_ENGINE.auditBuildQuality = function(parts, root)"):
                            plugin_lua.index("tools.model_audit = function(args)")]
    for marker in ("finishScore = finishScore", "grade = grade", "primitiveGroups = primitiveGroups",
                   "organicQuality = organicQuality", "Measurements are descriptive",
                   "not a completion gate"):
        require(marker in quality_fn, f"model audit does not clearly mark measurement advisory: {marker}")
    model_audit = plugin_lua[plugin_lua.index("tools.model_audit = function(args)"):]
    for marker in ("BALL_DOMINANT_PATTERN (advisory)", "CYLINDER_PROPORTION_HEURISTIC (advisory)",
                   "ORGANIC_DIAGNOSTICS (advisory)", "FINISH_SCORE_ESTIMATE (advisory)",
                   "Marked placeholders/blockout candidates are measurements, not automatic completion blockers."):
        require(marker in model_audit, f"model_audit warning is not advisory: {marker}")

    # Model the visible completion policy: all presentation/shape/audit labels
    # pass; only an actual non-applied mesh slot is pending (unless handed off).
    def report_done_policy(*, mesh_states=(), generic_placeholders=0, blockouts=0,
                           primitive_pattern=False, cylinder_heuristic=False,
                           grade="draft", organic_observations=(), audit_fresh=False,
                           handoff=False):
        pending = [state for state in mesh_states if state != "applied"]
        if pending and not handoff:
            return "MESH_UPLOAD_PENDING"
        return "OK"

    for example in (
        dict(generic_placeholders=5), dict(blockouts=4), dict(primitive_pattern=True),
        dict(cylinder_heuristic=True), dict(grade="draft"),
        dict(organic_observations=["no polygons", "no motion", "plain palette"]),
        dict(audit_fresh=False),
    ):
        require(report_done_policy(**example) == "OK",
                f"non-mesh heuristic incorrectly blocks report_done: {example}")
    require(report_done_policy(mesh_states=["waiting"]) == "MESH_UPLOAD_PENDING",
            "an explicitly-created mesh slot without applied geometry is not pending")
    require(report_done_policy(mesh_states=["applied"]) == "OK",
            "an applied explicit mesh slot still blocks completion")
    require(report_done_policy(mesh_states=["waiting"], handoff=True) == "OK",
            "a real handoff cannot close the explicit mesh workflow")

    # Session payload budget: core tools in full, everything else as an index,
    # a hard byte limit and an honest measurement in every session start.
    require("SessionPayloadHardBudgetBytes = 300000" in source
            and "$Shared.SessionPayloadHardBudgetBytes" in source,
            "the hard session payload budget is not defined in $Shared (handler runspace)")
    core_list = source[source.index("$coreToolNames = @("):source.index("$coreDocs = New-Object")]
    for tool in ("build_polygon_model", "build_assembly", "model_audit", "world_audit", "run_lua",
                 "report_done", "get_docs", "refine", "insert_script", "ask_user", "confirm_action"):
        require(f"'{tool}'" in core_list, f"core tool {tool} is missing from the session start core list")
    for deferred in ("search_assets", "insert_asset", "fill_region", "sim_start"):
        require(f"'{deferred}'" not in core_list, f"{deferred} must stay in the compact index, not in the core list")
    for marker in ("$out.toolsIndex = $indexDocs.ToArray()", "'core-full'", "'index-only'",
                   "$out.packageBytes = [int]$measuredBytes", "$out.budgetBytes = $packageBudget",
                   'get_docs { tool = "<name>" }'):
        require(marker in source, f"session payload policy marker missing: {marker}")

    # The finish-notification switch: bound to the setting, persisted, effective
    # immediately and honoured by the notification path itself.
    require("function Clear-NotifyQueue" in source, "Clear-NotifyQueue is missing")
    require("if (-not $enabled) { Clear-NotifyQueue }" in source,
            "switching the finish notification off does not clear pending messages")
    require("Fertig-Meldung verworfen: der Schalter" in source,
            "the notification path does not check the switch right before showing")
    require("$notifyAllowed = [bool]$script:Shared.BridgeSettings.notifyOnDone" in source
            and "if (-not $notifyAllowed) { [void](Clear-NotifyQueue) }" in source,
            "the notification timer does not honour/clear on the switch state")

    print("OK: 7.1.1 hotfix (flat cancellation ids, no @() on List[object], real admin reset, "
          "plugin sessionId, /api/places), 7.1.0 structure, reliable command delivery, BindReason preview fix, "
          "plugin tool repair, robust poll loop, place-row hotfix, "
          "self-report, session identity, delivery timeline, organic build contract, measured build quality, "
          "session payload budget, finish-notification switch, Lua and XAML validation passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
