#!/usr/bin/env python3
"""Offline checks for closed-loft geometry and optional creature diagnostics.

This file replaces the retired 7.3.2 hard organic-creature contract. Lofts,
polygon faces, bilateral anatomy, colors and movement are available when the
user request or target Place calls for them; absent measurements are advisory,
not build or report_done blockers. No Roblox Place is rendered here.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "ArenaBridge.ps1"
VERSION = "7.6.3"
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("[GRUEN] " if condition else "[ROT]   ") + message)
    if not condition:
        FAILURES.append(message)


def region(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    return source[begin:source.index(end, begin)]


def expected_loft_face_count(section_count: int, side_count: int) -> int:
    """Two end caps plus one quad per side between adjacent rings."""
    return 2 + max(0, section_count - 1) * side_count


def projected_depth_ratio(height_radius: float, depth_radius: float) -> float:
    larger = max(height_radius, depth_radius)
    return min(height_radius, depth_radius) / larger if larger > 0 else 0.0


def report_done_for_geometry(*, explicit_mesh_slots: tuple[str, ...] = (),
                             no_polygons: bool = False, plain_palette: bool = False,
                             no_motion: bool = False, missing_loft: bool = False,
                             nonbilateral_wings: bool = False, stale_audit: bool = False) -> str:
    """Only a generated, unapplied mesh slot enters the mesh waiting path."""
    if any(state != "applied" for state in explicit_mesh_slots):
        return "MESH_UPLOAD_PENDING"
    return "OK"


def main() -> int:
    raw = PS1.read_bytes()
    check(raw.startswith(b"\xef\xbb\xbf"), "ArenaBridge.ps1 retains its UTF-8 BOM")
    source = raw.decode("utf-8-sig")
    metadata = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    check(metadata.get("version") == VERSION, "release metadata targets 7.6.3")

    # Preserve the independent topology and shape-measurement checks.
    check(expected_loft_face_count(4, 8) == 26,
          "a four-station, eight-sided loft has two caps and 24 side faces")
    check(expected_loft_face_count(3, 6) == 14,
          "a three-station, six-sided loft produces a closed 14-face shell")
    check(projected_depth_ratio(0.7, 0.5) >= 0.16,
          "a deep cross-section has a measurable balanced depth ratio")
    check(projected_depth_ratio(2.0, 0.05) < 0.16,
          "a long/thin section is correctly measured without treating it as failure")

    loft = region(source, "function MASTER_BUILD.loftVolume(volume)", "function MASTER_BUILD.pointKey(v)")
    for marker in ("local sections=volume.sections or volume.stations or {}", "#sections<3",
                   "sides<6 or sides>16", "heightRadius or section.upRadius or section.radiusY",
                   "depthRadius or section.sideRadius or section.radiusZ",
                   "center-centers[i-1]).Magnitude<0.01", "local rings,previousSide={},nil",
                   'name=tostring(volume.name or "Loft").."_CapA"',
                   'name=tostring(volume.name or "Loft").."_CapB"',
                   "rings[i][j],rings[i][nextJ],rings[i+1][nextJ],rings[i+1][j]",
                   "closedEnds=true", "minCrossSectionRatio=minCrossSectionRatio"):
        check(marker in loft, f"optional loft builder retains valid topology logic: {marker}")

    plugin_marker = "function Get-PluginSource {\n@'\n"
    lua_start = source.index(plugin_marker) + len(plugin_marker)
    lua_end = source.index("\n'@\n}", lua_start)
    lua = source[lua_start:lua_end]
    builder = region(lua, "tools.build_polygon_model = function(args)", "tools.build_assembly = function(args)")
    for marker in ('local rawVolumes=args.volumes or {}',
                   'local organicKind=string.lower(tostring(args.organicKind or ""))',
                   'local organicBuild=args.organic==true', 'volumesBuilt=#generatedVolumeSpecs',
                   'volumeSummary=volumeSummary', 'facesSkipped=facesSkipped'):
        check(marker in builder, f"polygon/loft builder keeps optional metadata and result accounting: {marker}")
    docs = region(source, "function Get-ToolDocs {", "function Get-BridgeGuides {")
    polygon_doc = region(docs, "name = 'build_polygon_model';", "name = 'ui_capabilities';")
    check("organic=true/organicKind sind optionale Diagnose-Metadaten" in polygon_doc
          and "keine Geometrie-, Farb-, Anatomie- oder Animationspflicht" in polygon_doc,
          "tool docs describe organic flags as optional metadata, not build requirements")
    for obsolete in ("ORGANIC_KIND_REQUIRED", "CREATURE_VOLUME_REQUIRED", "CREATURE_WINGS_REQUIRED",
                     "ORGANIC_POLYGON_REQUIRED", "ORGANIC_COLORS_REQUIRED", "ORGANIC_SEQUENCE_REQUIRED"):
        check(obsolete not in lua, f"embedded plugin has no universal organic prerequisite {obsolete}")

    creature_audit = region(lua, "WORLD_ENGINE.auditOrganicCreature = function(organicModel)",
                            "WORLD_ENGINE.auditBuildQuality = function(parts, root)")
    for marker in ("Optional anatomy note", "Optional wing-role note", "may be intentional",
                   "review against the requested design", "bodyLoft={present=bodyNode~=nil",
                   "headLoft={present=headNode~=nil", "eyePairBilateral=eyePair", "pupils3D=pupils3D",
                   "faceOverlayCount=faceOverlayCount", "wingPairBilateral=wingPair"):
        check(marker in creature_audit, f"organic metrics are observation-based: {marker}")
    for marker in ("No ArenaPolygonTriangle parts were measured; this records representation only and is not a geometry requirement.",
                   "palette variation is a user/Place style choice.",
                   "static geometry remains valid unless motion was requested"):
        check(marker in lua, f"model audit explains optional style/representation measurement: {marker}")

    quality = region(lua, "WORLD_ENGINE.auditBuildQuality = function(parts, root)", "tools.model_audit = function(args)")
    for marker in ("organicQuality = organicQuality", "Measurements are descriptive",
                   "Optional organic diagnostics are listed under organicQuality.observations"):
        check(marker in quality, f"quality summary keeps organic observations advisory: {marker}")
    model_audit = lua[lua.index("tools.model_audit = function(args)"):]
    for marker in ("ORGANIC_DIAGNOSTICS (advisory)", "FINISH_SCORE_ESTIMATE (advisory)",
                   "not automatic completion blockers"):
        check(marker in model_audit, f"model_audit labels this observation non-blocking: {marker}")

    guides = region(source, "function Get-BridgeGuides", "function Get-SessionStartPackage")
    for marker in ("modelBuildRules = @{", "organicBuildRules = @{",
                   "Method priority: explicit user instructions", "the observed target-Place convention",
                   "Blender/build_mesh_model is recommended", "not mandatory",
                   "OPTIONAL ORGANIC MEASUREMENTS", "reference material, not a mandatory style",
                   "A low-poly or primitive style can be complete."):
        check(marker in guides, f"guide leaves representation/organic geometry optional: {marker}")
    for obsolete in ("BLENDER-FIRST (Version 7.5.5)", "every nontrivial custom visible 3D model",
                     "POLYGON_BLENDER_FIRST", "CREATURE_VOLUME_REQUIRED", "DETAIL_REQUIRED",
                     "ORGANIC_AUDIT_REQUIRED"):
        check(obsolete not in guides and obsolete not in source,
              f"retired universal completion/build rule is absent: {obsolete}")

    # Adverse observations do not change completion; a real mesh slot does.
    for example in (dict(no_polygons=True), dict(plain_palette=True), dict(no_motion=True),
                    dict(missing_loft=True), dict(nonbilateral_wings=True), dict(stale_audit=True)):
        check(report_done_for_geometry(**example) == "OK",
              f"an optional creature/quality observation does not gate completion: {example}")
    check(report_done_for_geometry(explicit_mesh_slots=("waiting",)) == "MESH_UPLOAD_PENDING",
          "an actual generated mesh slot with unapplied geometry remains pending")
    check(report_done_for_geometry(explicit_mesh_slots=("applied",)) == "OK",
          "an applied mesh slot is no longer pending")
    done_start = source.index("# report_done may identify an explicitly generated, unapplied mesh slot below.")
    done_end = source.index("$doneProgress = Read-ProgressState $sessionId", done_start)
    done_gate = source[done_start:done_end]
    check("$meshSlotCount -gt 0" in done_gate and "$waitCount -gt 0" in done_gate
          and "MESH_UPLOAD_PENDING" in done_gate,
          "the server gate requires a real mesh-slot count and an unapplied slot")
    for marker in ("bodyLoft", "headLoft", "wingPairBilateral", "polygonTriangles",
                   "uniqueColors", "motionScripts", "DETAIL_REQUIRED", "ORGANIC_AUDIT_REQUIRED"):
        check(marker not in done_gate, f"report_done does not use creature metric {marker} as a gate")

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} check(s).")
        return 1
    print("\nOK: closed-loft topology remains available; creature/quality audits are optional and report_done is mesh-only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
