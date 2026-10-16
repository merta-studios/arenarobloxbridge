#!/usr/bin/env python3
"""Offline regression checks for 8.0.0 (GUI power, billboards, strict user
messages, place menu, questions without time pressure, language, logo).

No Windows, PowerShell or Roblox Studio needed - structural checks only.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
APP = ROOT / "app" / "ArenaBridge.ps1"
VERSION = ROOT / "app" / "version.json"

FAILURES = []


def check(condition, label):
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        FAILURES.append(label)


def region(source, start, end):
    a = source.find(start)
    b = source.find(end, a + 1) if a >= 0 else -1
    return source[a:b] if a >= 0 and b > a else ""


def main():
    source = APP.read_text(encoding="utf-8-sig")
    data = json.loads(VERSION.read_text(encoding="utf-8"))
    print("8.0.0 offline regression checks")

    # --- version + notes (Stichpunkt-Regel) ---
    check(tuple(map(int, str(data.get("version")).split("."))) >= (8, 0, 1), "app/version.json behält mindestens die 8.0.1-Fixes (8.0.0-Inhalte bleiben enthalten)")
    notes = [str(n) for n in data.get("notes", [])]
    note = next((n for n in notes if n.startswith("• 8.0.0 — ")), "")
    check(bool(note) and note.count("•") >= 5
          and len(" ".join(note.split())) <= 600,
          "Die 8.0.0-Notiz folgt weiter der Stichpunkt-Regel (Titel + >=5 Punkte, <600 Zeichen)")

    # --- billboards shrink with distance ---
    check("UI_ENGINE.ensureBillboard" in source and "UDim2.new(w, 0, h, 0)" in source,
          "BillboardGui size is studs-only (shrinks with distance, no pixel offset)")
    check("MaxDistance" in source and "StudsOffsetWorldSpace" in source
          and "AlwaysOnTop" in source,
          "Billboard engine sets MaxDistance, world-space lift and no forced AlwaysOnTop")
    check("billboardGuiRules" in source and "surfaceType" in source,
          "Arena rules + tool docs carry the billboard system")
    check("billboardOffsetSize" in source,
          "ui_audit flags offset-sized BillboardGuis")

    # --- 24 skins + texture backgrounds ---
    skins = region(source, "SKINS = {", "FONTFAMILY")
    for name in ("horror", "minimal", "simulator", "tycoon", "obby", "ocean",
                 "winter", "candy", "space", "military", "royal", "nature"):
        check(re.search(rf"{name}\s*=\s*\{{", skins) is not None,
              f"skin '{name}' exists")
    check("textureAsBackground" in source and "ArenaTextureBackground" in source,
          "texture-as-background is a first-class mode (opaque, untinted)")
    check('usage = "background"' in source or 'usage="background"' in source
          or "usage = 'background'" in source or 'usage = "background"' in source,
          "texture recipe declares background usage")
    check("textureWashedOut" in source, "ui_audit flags washed-out texture overlays")

    # --- strict user messages ---
    check("chatAcknowledgementRequired = $true" in source
          and "requiredSequence" in source,
          "every envelope forces the chat confirmation sequence")
    check("STRICT 8.0.0" in source and "visibly confirming" in source,
          "session rules make the chat acknowledgement mandatory")
    check("UNACKED_USER_MESSAGE" in source,
          "report_done stays blocked by unacknowledged user messages")

    # --- place preview: test pattern never visible ---
    check("SELFTEST_PROBE_OK" in source and "PreviewHasRealFrame" in source,
          "preview self-test is an in-memory probe; spinner stays until first real frame")

    # --- place menu order + token resets progress ---
    menu = region(source, "# Version 8.0.0 (Nutzerwunsch, exakte Reihenfolge)",
                  "$menuShell.Child = $menuStack")
    order = [menu.find("$menuStack.Children.Add($copyItem.Root)"),
             menu.find("$menuStack.Children.Add((New-Separator))", 10),
             menu.find("$menuStack.Children.Add($historyItem.Root)"),
             menu.find("$menuStack.Children.Add($messageItem.Root)"),
             menu.find("$menuStack.Children.Add($toggleItem.Root)"),
             menu.find("$menuStack.Children.Add($resetItem.Root)")]
    check(bool(menu) and all(x >= 0 for x in order) and order == sorted(order),
          "place menu order: copy, separator, history, message, read-only, token reset")
    check("function Reset-ArenaProgressState" in source
          and "Reset-ArenaProgressState $SessionId" in source,
          "token reset also resets the Arena progress bar")

    # --- questions: no countdown, focus survives typing ---
    countdown = region(source, "function Set-AskCountdownText", "function Start-AskCountdown")
    check("kein Zeitdruck" in countdown or "KEINE Restzeit" in countdown
          or "wird nicht unter Druck gesetzt" in source,
          "ask window shows no remaining-time pressure text")
    check('Visibility="Collapsed"' in source.split('x:Name="AskCountdownText"')[1][:300],
          "countdown element is collapsed")
    check("FocusedCustomQuestionId" in source and "CustomBoxes" in source,
          "custom-answer focus/caret is preserved across rebuilds")

    # --- settings: editor icons in PLACE-LISTE, language with flags ---
    place_list = region(source, '<TextBlock Text="PLACE-LISTE"', "ROBLOX OPEN CLOUD API-KEY")
    check('x:Name="EditorIconsSwitch"' in place_list,
          "editor-icons setting lives in the PLACE-LISTE category")
    check('x:Name="LanguageEnglishButton"' in source and 'x:Name="LanguageGermanButton"' in source
          and 'x:Name="LanguageMenuButton"' in source and 'x:Name="LanguageChoices"' in source
          and 'Fill="#FFCE00"' in source and 'Fill="#012169"' in source and "✓" in source,
          "8.0.3: collapsed language selector with vector flags and checkmarks exists")
    check("uiLanguage" in source and "Get-UiDisplayText" in source
          and "Get-LocalizedXamlText" in source,
          "full-program language system (default English, German optional)")

    # --- logo: rounded, glow, float ---
    check('x:Name="ProgramLogoBorder"' in source and 'CornerRadius="14"' in source
          and 'x:Name="EmptyStateLogoBorder"' in source and 'CornerRadius="24"' in source,
          "both logos are rounded with named borders")
    check("Start-ArenaLogoFloatAnimation" in source and "#00E5D0" in source,
          "logos float and glow")

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s).")
        return 1
    print("OK: 8.0.0 checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
