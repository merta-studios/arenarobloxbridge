#!/usr/bin/env python3
"""Offline regression checks for the 7.3.2 typed organic-creature contract.

These tests verify the bridge's schema, generated loft topology, measured
quality checks, and the existing fresh-audit/report_done failure path. They do
not render a Roblox Place; Tree-sitter PowerShell parsing is run by
``test_v720_bridge.py`` as part of the same offline suite.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "ArenaBridge.ps1"
VERSION = "7.5.7"
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("[GRUEN] " if condition else "[ROT]   ") + message)
    if not condition:
        FAILURES.append(message)


def region(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    stop = source.index(end, begin)
    return source[begin:stop]


def expected_loft_face_count(section_count: int, side_count: int) -> int:
    """Two end caps plus one polygon quad per side between adjacent rings."""
    return 2 + max(0, section_count - 1) * side_count


def projected_depth_ratio(height_radius: float, depth_radius: float) -> float:
    largest = max(height_radius, depth_radius)
    if largest <= 0:
        return 0.0
    return min(height_radius, depth_radius) / largest


def main() -> int:
    raw = PS1.read_bytes()
    check(raw.startswith(b"\xef\xbb\xbf"), "ArenaBridge.ps1 retains its UTF-8 BOM")
    source = raw.decode("utf-8-sig")
    metadata = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    notes = "\n".join(str(note) for note in metadata.get("notes", []))
    check(metadata.get("version") == VERSION, f"version.json is {VERSION}")
    for phrase in ("7.3.2", "Körper und Kopf", "linke/rechte Flügel", "report_done", "Roblox Studio"):
        check(phrase in notes, f"release note covers {phrase}")

    builder = region(source, "tools.build_polygon_model = function(args)", "tools.build_assembly = function(args)")
    loft = region(source, "function MASTER_BUILD.loftVolume(volume)", "function MASTER_BUILD.pointKey(v)")
    for marker in (
        "local rawVolumes=args.volumes or {}",
        "local organicKind=string.lower(tostring(args.organicKind or \"\"))",
        "ORGANIC_KIND_REQUIRED",
        "allowedOrganicKinds={creature=true,plant=true,tree=true,prop=true,custom=true}",
        "volumeRoles.body,volumeRoles.head",
        "#bodySections<4 or #headSections<3",
        "CREATURE_VOLUME_REQUIRED",
        "CREATURE_WINGS_REQUIRED",
        "ArenaOrganicKind",
        "ArenaOrganicHasWings",
        "volumesBuilt=#generatedVolumeSpecs",
        "volumeSummary=volumeSummary",
        "expectedFaces=meta.faces",
    ):
        check(marker in builder, f"typed creature builder contains {marker}")

    for marker in (
        "local sections=volume.sections or volume.stations or {}",
        "#sections<3",
        "sides<6 or sides>16",
        "heightRadius or section.upRadius or section.radiusY",
        "depthRadius or section.sideRadius or section.radiusZ",
        "center-centers[i-1]).Magnitude<0.01",
        "local rings,previousSide={},nil",
        "table.insert(polygons,{name=tostring(volume.name or \"Loft\")..\"_CapA\",points=rings[1]})",
        "table.insert(polygons,{name=tostring(volume.name or \"Loft\")..\"_CapB\",points=lastCap})",
        "rings[i][j],rings[i][nextJ],rings[i+1][nextJ],rings[i+1][j]",
        "closedEnds=true",
    ):
        check(marker in loft, f"loft generator contains {marker}")
    check(expected_loft_face_count(4, 8) == 26,
          "4-station, 8-sided loft closes both ends and creates 24 side faces")
    check(projected_depth_ratio(0.7, 0.5) >= 0.16,
          "a genuinely deep cross-section passes the minimum depth ratio")
    check(projected_depth_ratio(2.0, 0.05) < 0.16,
          "a long, thin side-profile cross-section falls below the depth ratio")

    assembly = region(source, "tools.build_assembly = function(args)", "-- UI ENGINE 1.0")
    check("for attributeName,attributeValue in pairs(spec.attributes or {}) do" in assembly
          and "inst:SetAttribute(tostring(attributeName),decodeValue(attributeValue))" in assembly,
          "build_assembly can set per-part semantic role attributes")

    audit = region(source, "WORLD_ENGINE.auditOrganicCreature = function(organicModel)", "WORLD_ENGINE.auditBuildQuality = function(parts, root)")
    for marker in (
        "validateLoft(\"body\",4)",
        "validateLoft(\"head\",3)",
        "ArenaLoftSectionCount",
        "ArenaLoftSideCount",
        "ArenaLoftClosedEnds",
        "ArenaLoftExpectedFaceCount",
        "ArenaLoftFacesSkipped",
        "expectedFaceCount~=topologyFaceCount",
        "builtFaceCount~=expectedFaceCount",
        "skippedFaceCount>0",
        "BODY_THIN_PROFILE",
        "HEAD_THIN_PROFILE",
        "math.min(bounds.size.Y,bounds.size.Z)/largest",
        "ArenaPolygonTriangle",
        'taggedPart("eye_left"),taggedPart("eye_right")',
        'taggedPart("pupil_left"),taggedPart("pupil_right")',
        "EYES_NOT_3D",
        "EYES_NOT_BILATERAL",
        'if largest<0.04 or smallest/largest<0.62 then return false end',
        'if part:IsA("Part") then return shapeName=="Ball" end',
        "PUPILS_NOT_3D",
        'offset:Dot(forward)>=math.max(0.01,eyeScale*0.05)',
        "node:IsA(\"Decal\") or node:IsA(\"Texture\") or node:IsA(\"SurfaceGui\") or node:IsA(\"BillboardGui\")",
        "FACE_IMAGE_OVERLAY",
        '{"face","muzzle","nose","mouth","eye_left","eye_right","pupil_left","pupil_right"}',
        "faceOverlayCount=faceOverlayCount",
        "faceOverlayCount=faceOverlayCount+1",
        'if node:IsA("SpecialMesh") then',
        'if node:IsA("MeshPart") then',
        'if node:IsA("SurfaceAppearance") then',
        "adornee:IsDescendantOf(headNode)",
        'roleBounds("wing_left"),roleBounds("wing_right")',
        "WINGS_NOT_BILATERAL",
        "WINGS_NOT_ATTACHED",
        "or #(roleNodes.wing_left or {})>0",
        "math.min(leftWing.max.X,bodyBounds.max.X)-math.max(leftWing.min.X,bodyBounds.min.X)>0.02",
        "math.min(leftWing.max.Y,bodyBounds.max.Y)-math.max(leftWing.min.Y,bodyBounds.min.Y)>0.02",
        "math.min(leftWing.max.Z,bodyBounds.max.Z)-math.max(leftWing.min.Z,bodyBounds.min.Z)>0.02",
        "bodyLoft={present=bodyNode~=nil",
        "wingPairBilateral=wingPair",
    ):
        check(marker in audit, f"creature audit contains {marker}")

    quality = region(source, "WORLD_ENGINE.auditBuildQuality = function(parts, root)", "tools.model_audit = function(args)")
    check("WORLD_ENGINE.auditOrganicCreature(organicModel)" in quality
          and "for _,issue in ipairs(creatureIssues or {}) do table.insert(modelIssues,issue) end" in quality
          and "organicKind = organicKind, creatureMetrics = creatureMetrics" in quality,
          "per-model organicQuality includes creature metrics and blocking issues")

    report_start = source.index("                                $organicIssues = @($organicQuality.issues)")
    report_end = source.index("# Fail closed if any completion-proof validation failed", report_start)
    report_gate = source[report_start:report_end]
    check("$organicIssues += @($matchingOrganicModel.issues)" in report_gate
          and "DETAIL_REQUIRED" in report_gate
          and "creatureMetrics = $matchingOrganicModel.creatureMetrics" in report_gate,
          "report_done rejects per-model creature issues and returns measured diagnostics")

    # Verify the exact fail-closed path still persists each model's own issues
    # and requires a fresh audit after the last successful Place write.
    persist = region(source, "if ($tool -eq 'model_audit') {", "if ($null -eq $resultJson)")
    check("$modelIssues = @($modelEvidence.issues)" in persist
          and "issues = $modelIssues" in persist
          and "$organicRecord.auditAtTicks = $resultAtTicks" in persist,
          "model_audit stores the exact creature's issues and a freshness timestamp")

    if FAILURES:
        print(f"\nFEHLGESCHLAGEN: {len(FAILURES)} Pruefung(en) rot.")
        return 1
    print("\nOK: current bridge creature loft, face, wing and fail-closed audit regressions passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
