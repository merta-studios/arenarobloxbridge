#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline regression checks for optional organic diagnostics and UI behavior.

The former 7.1.4 completion-gate expectations are intentionally replaced: model
and organic audit data are descriptive, and report_done is not conditional on
lofts, colors, anatomy, movement, grade, or audit freshness. These checks retain
per-model diagnostic persistence, the no-op compatibility hook, and unrelated
window/progress/reset regressions. No Roblox Place is rendered here.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = ROOT / "app"
PS1 = APP_ROOT / "ArenaBridge.ps1"
VERSION = "7.7.2"
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("[GRUEN] " if condition else "[ROT]   ") + message)
    if not condition:
        FAILURES.append(message)


def load_source() -> str:
    raw = PS1.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf"), "ArenaBridge.ps1 must retain its UTF-8 BOM"
    return raw.decode("utf-8-sig")


def extract_plugin_lua(source: str) -> str:
    marker = "function Get-PluginSource {\n@'\n"
    begin = source.index(marker) + len(marker)
    end = source.index("\n'@\n}", begin)
    return source[begin:end]


def region(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    return source[begin:source.index(end, begin)]


def diagnostic_summary(record: dict) -> dict:
    """Summarize observed values without converting them into pass/fail policy."""
    return {
        "observations": list(record.get("observations", [])),
        "polygonTriangles": int(record.get("polygonTriangles", 0)),
        "uniqueColors": int(record.get("uniqueColors", 0)),
        "dominantColorShare": float(record.get("dominantColorShare", 0.0)),
        "nearWhiteShare": float(record.get("nearWhiteShare", 0.0)),
        "motionScripts": int(record.get("motionScripts", 0)),
    }


def main() -> int:
    source = load_source()
    plugin_lua = extract_plugin_lua(source)
    meta = json.loads((APP_ROOT / "version.json").read_text(encoding="utf-8"))
    check(meta.get("version") == VERSION, "version.json and source target the prepared 7.7.2 update")

    # Organic metadata and marker flags are optional inputs, not schema gates.
    builder = region(plugin_lua, "tools.build_polygon_model = function(args)", "tools.build_assembly = function(args)")
    for marker in ('local organicBuild=args.organic==true',
                   'local organicKind=string.lower(tostring(args.organicKind or ""))',
                   'return ok({model=describeRef(model),organic=organicBuild',
                   'model:SetAttribute("ArenaOrganicBuild",true)'):
        check(marker in builder, f"polygon build supports optional audit metadata: {marker}")
    for obsolete in ("ORGANIC_KIND_REQUIRED", "CREATURE_VOLUME_REQUIRED", "CREATURE_WINGS_REQUIRED",
                     "ORGANIC_POLYGON_REQUIRED", "ORGANIC_COLORS_REQUIRED", "ORGANIC_SEQUENCE_REQUIRED"):
        check(obsolete not in plugin_lua, f"builder contains no organic completion prerequisite {obsolete}")

    guides = region(source, "function Get-BridgeGuides", "function Get-SessionStartPackage")
    for marker in ("projectConsistencyRules = @{", "modelBuildRules = @{", "organicBuildRules = @{",
                   "Method priority: explicit user instructions", "the observed target-Place convention",
                   "Blender/build_mesh_model is recommended", "not mandatory",
                   "OPTIONAL ORGANIC MEASUREMENTS",
                   "model_audit is optional and its findings never block report_done"):
        check(marker in guides, f"session guide states current user-/Place-first policy: {marker}")
    for obsolete in ("BLENDER-FIRST (Version 7.5.5)", "POLYGON_BLENDER_FIRST",
                     "ORGANIC_AUDIT_REQUIRED", "DETAIL_REQUIRED", "every model must use build_mesh_model"):
        check(obsolete not in guides, f"session guide omits superseded mandate: {obsolete}")

    # Per-model measurements remain useful, with honest zero/false readings and
    # intent-aware text rather than required anatomy/geometry states.
    organic_audit = region(plugin_lua, "WORLD_ENGINE.auditOrganicCreature = function(organicModel)",
                           "WORLD_ENGINE.auditBuildQuality = function(parts, root)")
    for marker in ("Optional anatomy note", "may be intentional", "Optional wing-role note",
                   "review against the requested design", "bodyLoft={present=bodyNode~=nil",
                   "headLoft={present=headNode~=nil", "eyePairBilateral=eyePair", "pupils3D=pupils3D",
                   "faceOverlayCount=faceOverlayCount", "wingPairBilateral=wingPair"):
        check(marker in organic_audit, f"organic audit reports actual optional observation: {marker}")
    quality = region(plugin_lua, "WORLD_ENGINE.auditBuildQuality = function(parts, root)",
                     "tools.model_audit = function(args)")
    for marker in ("organicQuality = organicQuality", "Measurements are descriptive",
                   "Optional organic diagnostics are listed under organicQuality.observations"):
        check(marker in quality, f"model audit retains advisory diagnostic: {marker}")
    model_audit = plugin_lua[plugin_lua.index("tools.model_audit = function(args)"):]
    for marker in ("ORGANIC_DIAGNOSTICS (advisory)",
                   "Marked placeholders/blockout candidates are measurements, not automatic completion blockers.",
                   "buildQuality = quality"):
        check(marker in model_audit, f"model_audit result labels optional data advisory: {marker}")

    # Organic state is stored for per-model diagnostic continuity, but the
    # completion branch can only report a real unapplied mesh slot.
    guard = region(source, "function Get-OrganicBuildGuardResult", "\n    $context = $Context")
    check("return $null" in guard and "Test-PolygonBuildWithoutRequest" not in guard,
          "legacy organic completion hook is a no-op for normal and parallel calls")
    tracking_start = source.index("$organicRecord.auditAtTicks = $resultAtTicks")
    tracking = source[tracking_start:tracking_start + 1600]
    for marker in ("$organicRecord.auditAtTicks = $resultAtTicks", "$organicRecord.auditScope",
                   "$organicRecord.auditQuality = $perModelQuality", "$organicRecord.auditModels = @($modelEvidence)"):
        check(marker in tracking, f"per-model audit diagnostics are persisted: {marker}")
    done_start = source.index("# report_done may identify an explicitly generated, unapplied mesh slot below.")
    done_end = source.index("$doneProgress = Read-ProgressState $sessionId", done_start)
    done_gate = source[done_start:done_end]
    check("$meshSlotCount -gt 0" in done_gate and "$waitCount -gt 0" in done_gate
          and "MESH_UPLOAD_PENDING" in done_gate,
          "completion only holds an actual generated mesh slot with unapplied geometry")
    for marker in ("organicQuality", "auditAtTicks", "bodyLoft", "headLoft", "wingPairBilateral",
                   "DETAIL_REQUIRED", "ORGANIC_AUDIT_REQUIRED", "ANIMATION_NOT_INSTALLED"):
        check(marker not in done_gate, f"report_done does not gate on organic/audit value {marker}")

    # A small behavior model proves that adverse measurements still serialize
    # but do not become a completion verdict.
    observed = diagnostic_summary({"polygonTriangles": 0, "uniqueColors": 1,
                                  "dominantColorShare": 1.0, "nearWhiteShare": 0.0,
                                  "motionScripts": 0,
                                  "observations": ["no measured loft", "no motion", "plain palette"]})
    check(observed["polygonTriangles"] == 0 and observed["motionScripts"] == 0
          and len(observed["observations"]) == 3,
          "missing loft/motion and simple palette remain visible as diagnostic facts")
    check("organic completion" not in json.dumps(observed).casefold(),
          "serialized diagnostics do not imply an organic completion requirement")

    # Unrelated UI regressions retained from the original suite.
    xaml = re.search(r"\$xaml = @'\n([\s\S]*?)\n'@", source)
    check(xaml is not None, "main window XAML remains present")
    if xaml:
        main_xaml = xaml.group(1)
        check('Text="Arena Roblox Bridge"' in main_xaml
              and 'Text="bereit für verbundene Places"' in main_xaml
              and 'RuntimeLine' not in source,
              "title continues to show the product and fixed connected-Place hint")

    progress = region(source, "function Update-PlaceProgressVisual", "function Get-ProgressDiagnoseLines")
    check("if ($progressMode -eq 'hidden')" in progress
          and "Fortschritt nicht anwendbar" in progress
          and "$showNumericProgress = (($percentKnown -or $state -eq 'done') -and $progressMode -ne 'hidden')" in progress
          and "$Row.ProgressBar.Visibility = 'Collapsed'" in progress
          and "Seit über einer Minute kein Bridge Aufruf mehr" not in progress,
          "hidden progress is explicitly not applicable, with no bar, invented percent, or stale inactivity label")
    row_builder = region(source, "function New-Row {", "function New-MinimalPlaceRow {")
    fallback = region(source, "function New-MinimalPlaceRow {", "\nfunction ")
    check("$namePanel.VerticalAlignment = 'Stretch'" in row_builder
          and "$topCenterSpacer.Height = [System.Windows.GridLength]::new(1, [System.Windows.GridUnitType]::Star)" in row_builder
          and "$bottomCenterSpacer.Height = [System.Windows.GridLength]::new(1, [System.Windows.GridUnitType]::Star)" in row_builder
          and "$namePanel.VerticalAlignment = 'Center'" in fallback,
          "empty Place rows keep their name centered using star spacers/fallback")
    check("Show-CopyConfirm -Message 'Token wurde zurückgesetzt.' -Seconds 4" in source
          and "Show-CopyConfirm -Message 'Token für alle Places wurde zurückgesetzt.' -Seconds 4" in source,
          "token reset still displays its short confirmation")

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} check(s).")
        return 1
    print("\nOK: organic audits remain optional, per-model observations persist, mesh-only completion and independent UI regressions passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, ValueError, KeyError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
