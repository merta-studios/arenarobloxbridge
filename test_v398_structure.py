#!/usr/bin/env python3
"""Offline structure check for Arena Roblox Bridge 6.0.4.

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
VERSION = "6.0.4"

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

    required_markers = [
        "DocsVersion     = '6.0.4'",
        'local ARENA_VERSION  = "6.0.4"',
        "bridgeVersion = '6.0.4'",
        "serverVersion = '6.0.4'",
        "version = '6.0.4'",
        "$versionText = '6.0.4'",
        "$verText = '6.0.4'",
        'Text="Arena Roblox Bridge - Version 6.0.4"',
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
        # 4.0.4: the session reporter loop must be while-true + supervised,
        # carry its loop counter + post-fail counter in EVERY heartbeat, and
        # the edit plugin must poll the reporter state during a session so
        # arenaLineCount visibly counts up (4.0.2 live bug: exactly ONE
        # heartbeat, arenaLineCount frozen at 1).
        "state.reporterLoopCount = sessionAgent.reporterLoopCount",
        "reporterPostFailCount",
        "pluginReporterLoopCount",
        "notRunningStreak",
        "local lastSessionPoll = 0",
        "local sessionDm = isSessionDataModel",
        "loopCountViaSharedTable",
        "reporterSeenInOutput = active and sessionAgent.reporterSeenInOutput == true or false",
        "and testSessionActive()",
        "reporterLoopAlive=true",
        "agentNotRunningStreak",
        "clearSessionReporterState",
        "wasSessionActive and not sessionActiveNow",
        "Retry once before reporting nil",
        # 5.0.1 regression guards: the heartbeat handler must never let a
        # state-tracking failure swallow the command queue (that live bug made
        # play_stop/move_character impossible: loopCount 501 / postFail 500),
        # and play_stop must keep its queued end_test last resort.
        "function Set-StateField",
        "Set-StateField $newState 'userPlaytestActive'",
        "queuedEndTest",
        "queuedSessionEndTest",
        "or testSessionActive() or (sessionAgent and sessionAgent.httpConnected)",
        "sessionAgent.key ~= nil",
        # Version 5: stale session keys cannot block movement/stop, aggregate
        # multi-place routing and the UI history/icon layer stay present.
        "action = \"register\"",
        "sessionKeyRegistered",
        "Humanoid:Move is frame-scoped",
        "MultiPlaceToken",
        "MULTI_PLACE_SELECTION_REQUIRED",
        "targetPlace",
        "ActivityLogs",
        "Open-ArenaHistoryWindow",
        "Alle Places",
        # 5.0.2: place-list hard diagnosis + safety net (live bug: count badge
        # correct, EmptyState hidden, but no row ever rendered; 5.0.1's $host
        # fix was correct but not sufficient - so errors must now be measured,
        # not guessed: full type/line/stacktrace logging, post-add tree state,
        # and every optional row feature individually guarded so a minimal row
        # (name + copy button) always lands in the tree).
        "function Write-UiErrorLog",
        "InvocationInfo.ScriptLineNumber",
        "$ErrorRecord.ScriptStackTrace",
        "function Add-PlaceRowToPlaceList",
        "Add-PlaceRowToPlaceList $row $sid 'Place-Zeile'",
        "Add-PlaceRowToPlaceList $script:AllPlacesRow $allSid 'Alle-Places-Zeile'",
        "hinzugefuegt (sid={1}): PlaceList.Children={2}",
        "hart auf sichtbar gestellt",
        "Einblend-Animation kam nie an",
        "Place-Liste konnte nicht neu angeordnet werden",
        "Place-Zeile: Vorschau-Visual konnte nicht erstellt werden",
        "Place-Zeile: Auswahlmenue/Popup konnte nicht erstellt werden",
        "Arena-Verlaufsfenster konnte nicht geoeffnet werden",
        # Version 5.2 user-wish update: lean aggregate row, repaired game
        # icons (dead fallback URL replaced, PNG-verified, retried, locally
        # drawn last resort), styled+draggable history window with real
        # numbers instead of [PLATZHALTER], no last-message settings card,
        # short all-places prompt, and a much quicker ghost-free place list.
        "$script:PlaceVisibleSeconds = 15",
        "$script:PlaceOrphanGraceSeconds = 4",
        "$script:PlaceCleanupSeconds = 120",
        "function Remove-DeadSession",
        "Remove-DeadSession $sessionId",
        "function New-HistoryButton",
        "$head.Add_MouseLeftButtonDown($dragHandler)",
        "$shell.Add_MouseLeftButtonDown($dragHandler)",
        "function Get-ActivityToolSets",
        "previousLines = select(2, string.gsub(oldSource",
        "function Get-ResultNumber",
        # Version 6.0 (Liquid Glass redesign): the glass shell, the aurora
        # layer behind it, the teal glass rows, the green glass action
        # buttons and the animation patterns must stay present.
        'x:Name="RootShell"',
        "RoundGlassStyle",
        "SettingsPillStyle",
        "GlassFill",
        "SweepBrush",
        "function New-AuroraLayer",
        "New-AuroraLayer -Width 660 -Height 620",
        "$RootShell       = $window.FindName('RootShell')",
        "$RootShell.RenderTransform.BeginAnimation",
        "$popup.Add_Opened",
        "PopupAnimation]::None",
        "'#D900D5C4'",
        "'#F238D16C'",
        "'#47FFFFFF'",
        "$rowBg.GradientStops.Add",
        "$hoverGlow.Background = Get-Brush '#5900E5D0'",
        "$Item.Thumb.RenderTransform.BeginAnimation",
        "$copy.Background = $greenBg",
        "RectangleGeometry Rect=\"0,0,920,620\"",
        "Add_ContentRendered",
        # Version 6.0.1: the game-icon download is fully replaced by a live
        # Studio-window preview (throttled, frozen while minimized, no
        # preview at all for the aggregate "Alle Places" row).
        "$script:PlacePreviewHandles = @{}",
        "$script:PlacePreviewLastCaptureAt = @{}",
        "$script:PlacePreviewIntervalSeconds = 2.5",
        "$script:PlacePreviewCaptureHeight = 88",
        "function Get-StudioWindowInfos",
        "function Resolve-PlacePreviewHandle",
        "function Set-PlacePreviewImage",
        "function New-PlacePreviewVisual",
        "function Start-PlacePreviewCapture",
        "function Update-PlacePreviewCaptures",
        "[Arena.ScreenHelper]::IsIconic($hwnd)",
        "Place-Zeile: Vorschau-Aufnahme fehlgeschlagen",
        # Version 6.0.2: preview can no longer fail silently - failures are
        # counted, logged with a reason (throttled), and after 3 consecutive
        # failures the placeholder glyph replaces the eternal spinner.
        "$script:PlacePreviewFailLogAt = @{}",
        "PreviewFailCount = 0",
        "PreviewLoggedOnce = $true",
        "Place-Vorschau ($sessionId): Aufnahme fehlgeschlagen",
        "Place-Vorschau ($sessionId): Live-Vorschau aktiv",
        "Studio-Fenster ist minimiert",
        # Version 6.0.2: window-handle resolution is null-safe and tolerant
        # (trim, case-insensitive, prefix match, versionMismatch suffix).
        "$previousRaw = $script:PlacePreviewHandles[$sessionId]",
        "[System.StringComparison]::OrdinalIgnoreCase",
        # Version 6.0.2: the capture worker carries its own ScreenHelper
        # fallback so a failed main-runspace Add-Type cannot kill every
        # capture with a silent TypeNotFound.
        "if (-not ('Arena.ScreenHelper' -as [type])) {",
        # Version 6.0.3: truly flat window enumeration, occlusion-safe direct
        # window rendering, and self-healing capture workers.
        "return $script:PreviewWindowCache",
        "return $script:WindowNameCache",
        "[Arena.ScreenHelper]::PrintWindow($hwnd, $hdc, 2)",
        "CopyFromScreen-Fallback",
        "Aufnahme-Worker nach 10 Sekunden beendet",
        "kein passendes Roblox-Studio-Fenster gefunden",
        # Version 6.0.2: update safety net - after a launcher start whose
        # status does not prove a fresh install, the app verifies version.json
        # itself and pulls the update directly if the launcher failed to.
        "$script:SelfUpdateVerifyTimeout = 6",
        "Invoke-AutostartSelfUpdate -VerifyMode",
        "$starterProvesFreshInstall = ((@('update-erfolgreich', 'erster-start') -contains $UpdateStatus) -eq $true)",
        "param([string]$Branch, [string]$File, [int]$TimeoutSec = 0)",
        # Version 6.0.4: Laufzeit-Diagnose + robuste Aufnahme fuer die
        # Fenster-Vorschau (Ablauf-ID + neun Stationen, sichtbarer
        # UI-Selbsttest, C#-Helfer im Hauptprozess, vier Aufnahmewege,
        # atomare PNG-Ablage, Laufzeit-Identitaet mit SHA-256/Sprachmodus).
        "function Write-PreviewTrace",
        "function New-PreviewFlowId",
        "function Clear-PreviewFlow",
        "function Save-PreviewHandleMeta",
        "PREVIEW [{0}] {1} sid={2} pid={3} hwnd={4}",
        "'CAPTURE_START'",
        "'WINDOWS_ENUMERATED'",
        "'HANDLE_RESOLVED'",
        "'WORKER_STARTED'",
        "'WORKER_COMPLETED'",
        "'RESULT_RECEIVED'",
        "'PNG_DECODED'",
        "'IMAGE_ASSIGNED'",
        "'IMAGE_VISIBLE'",
        "function Invoke-PlacePreviewUiSelfTest",
        "function New-PlacePreviewSelfTestImage",
        "PREVIEW_UI_SELFTEST_OK",
        "PREVIEW_UI_SELFTEST_FAILED",
        "Invoke-PlacePreviewUiSelfTest $Row $SessionId",
        "namespace Arena {",
        "public sealed class PreviewCaptureResult",
        "public static Task<PreviewCaptureResult> CaptureAsync(long hwndValue, int targetHeight)",
        "private const uint PW_RENDERFULLCONTENT = 2;",
        "TryWindowDcBitBlt",
        "TryCopyFromScreen",
        "HasVisibleContent",
        "true-aber-nichts-sichtbar",
        "[Arena.PreviewCapture]::CaptureAsync($handleValue, [int]$targetHeight)",
        "kind=csharp-helper",
        "ps-runspace-fallback",
        "Get-FileHash -Algorithm SHA256",
        "Laufzeit-Identitaet: Bridge-Version=6.0.4",
        "LanguageMode",
        "$script:PreviewFlowContexts = @{}",
        "$script:PreviewHandleInfos = @{}",
        "$script:PreviewSelfTestDone = $false",
        "Clear-PreviewFlow $flow",
        "DispatcherPriority]::Render",
        "GetNewClosure()",
        "Move-Item -LiteralPath $script:RuntimeLog -Destination ($script:RuntimeLog + '.old') -Force",
    ]
    for marker in required_markers:
        require(marker in source, f"required marker missing: {marker}")

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
    assign_fn = source[source.index("function Set-PlacePreviewImage"):source.index("function New-PlacePreviewSelfTestImage")]
    require("CheckAccess()" in assign_fn and "BeginInvoke(" in assign_fn,
            "Set-PlacePreviewImage must route through the WPF dispatcher")
    require("$Bytes[0] -eq 0x89" in assign_fn,
            "PNG magic-byte verification is missing from the assign path")
    preview_fn = source[source.index("function Get-StudioWindowInfos"):source.index("function Resolve-PlacePreviewHandle")]
    require("return , $script:PreviewWindowCache" not in preview_fn,
            "window info cache is nested again by unary comma (breaks multiple Studio windows)")
    window_name_fn = source[source.index("function Get-StudioWindowName"):source.index("function Get-PlaceName")]
    require("return , $script:WindowNameCache" not in window_name_fn,
            "window title cache is nested again by unary comma (breaks multi-window title matching)")

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
    reporter_chunks = re.findall(r"local SESSION_REPORTER_SOURCE = \[==\[(.+?)\]==\]", lua, re.S)
    require(len(reporter_chunks) == 1, "SESSION_REPORTER_SOURCE not found")
    require("reporterLoopAlive=true" in reporter_chunks[0], "injected reporter does not publish loop liveness")
    require('action == "move_character"' in reporter_chunks[0], "injected reporter lacks move_character fallback")

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

    print("OK: 6.0.4 structure, Lua and XAML validation passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
