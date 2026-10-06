#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline regression checks for the Arena Roblox Bridge 7.1.4 organic build contract.

These checks model the server-side freshness/quality decision and inspect the
embedded Luau, HTTP guard, release metadata and requested UI states. They do not
replace a Windows/Roblox Studio live acceptance test.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "ArenaBridge.ps1"
VERSION = "7.2.9"
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("[GRUEN] " if condition else "[ROT]   ") + message)
    if not condition:
        FAILURES.append(message)


def load_source() -> str:
    raw = PS1.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf"), "ArenaBridge.ps1 muss die UTF-8-BOM behalten"
    return raw.decode("utf-8-sig")


def extract_plugin_lua(source: str) -> str:
    marker = "function Get-PluginSource {\n@'\n"
    begin = source.find(marker)
    assert begin >= 0, "Get-PluginSource here-string nicht gefunden"
    begin += len(marker)
    end = source.find("\n'@\n}", begin)
    assert end >= 0, "Get-PluginSource here-string nicht geschlossen"
    return source[begin:end]


def region(source: str, start: str, end: str) -> str:
    first = source.index(start)
    last = source.index(end, first + len(start))
    return source[first:last]


def organic_proof_result(record: dict | None, now_ticks: int = 500) -> str:
    """Model the per-model organic report_done gate (handoff is not an override)."""
    if record is None:  # no organic work was registered for this Place
        return "OK"
    if not isinstance(record, dict) or record.get("required") is not True:
        return "ORGANIC_AUDIT_REQUIRED"  # registered but malformed/incomplete state fails closed
    records = record.get("models")
    if not records:
        if "modelId" in record:
            records = [record]
        else:
            return "ORGANIC_AUDIT_REQUIRED"
    for model_record in records:
        if int(model_record.get("auditAtTicks", 0)) <= 0 or int(model_record.get("auditAtTicks", 0)) < int(model_record.get("lastWriteAtTicks", 0)):
            return "ORGANIC_AUDIT_REQUIRED"
        quality = model_record.get("auditQuality")
        if not quality or quality.get("detected") is not True:
            return "ORGANIC_AUDIT_REQUIRED"
        evidence = quality.get("models", [])
        target = next((model for model in evidence if model.get("id") == model_record.get("modelId")), None)
        if target is None:
            return "ORGANIC_AUDIT_REQUIRED"
        issues = list(quality.get("issues", [])) + list(target.get("issues", []))
        if int(target.get("polygonTriangles", 0)) <= 0:
            issues.append("NO_POLYGON_GEOMETRY")
        if int(target.get("uniqueColors", 0)) < 3:
            issues.append("PALETTE_TOO_FLAT")
        if float(target.get("dominantColorShare", 0)) > 0.90:
            issues.append("PALETTE_TOO_FLAT")
        if float(target.get("nearWhiteShare", 0)) > 0.90:
            issues.append("PALETTE_TOO_FLAT")
        if int(target.get("motionScripts", 0)) <= 0:
            issues.append("ANIMATION_NOT_INSTALLED")
        if issues:
            return "DETAIL_REQUIRED"
    return "OK"


def proof_record(**model_overrides: object) -> dict:
    model = {
        "id": "organic-fox-1",
        "polygonTriangles": 48,
        "uniqueColors": 5,
        "dominantColorShare": 0.58,
        "nearWhiteShare": 0.02,
        "motionScripts": 1,
        "issues": [],
    }
    model.update(model_overrides)
    return {
        "required": True,
        "models": [{
            "modelId": "organic-fox-1",
            "lastWriteAtTicks": 100,
            "auditAtTicks": 120,
            "auditQuality": {"detected": True, "issues": [], "models": [model]},
        }],
    }


def main() -> int:
    source = load_source()
    plugin_lua = extract_plugin_lua(source)
    meta = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    release_notes = "\n".join(meta.get("notes", []))

    # Release identity and release notes.
    check(meta.get("version") == VERSION, "version.json identifiziert 7.2.9")
    # 7.2.3 dokumentiert das UI-Mini-Update; 7.2.1 behaelt den Start-/Parser-
    # Fix, und 7.2.0 beschreibt Nutzer-Kanal, Meldungsmessung und Qualitaet.
    # Der organische Vertrag selbst wird weiter unten DIREKT
    # im Quellcode geprueft (und darf dort nicht fehlen).
    for marker in ("7.2.9", "7.2.4", "7.2.3", "report_done", "DRAFT_GRADE_RISK", "NOTIFICATION_UNVERIFIED"):
        check(marker in release_notes, f"Release-Notiz nennt {marker}")

    # The server guard only enforces explicitly marked organic builds; the
    # broad polygon-first preference is delivered for every model category.
    guard = region(source, "function Get-OrganicBuildGuardResult", "\n    $context = $Context")
    for marker in ("build_polygon_model", "organic=true", "$organicFlag = ($toolArgs.organic -eq $true)",
                   "if (-not $organicFlag)", "ORGANIC_POLYGON_REQUIRED", "ORGANIC_COLORS_REQUIRED",
                   "ORGANIC_SEQUENCE_REQUIRED", "colorAssignments", "ParallelCall", "start_job",
                   "model_audit", "if ($organicState -and [bool]$organicState.required)"):
        check(marker in guard, f"serverseitiger Organic-Vertrag enthaelt: {marker}")
    check("organicIntentPattern" not in guard and "organicPlantPattern" not in guard
          and "animal\\w*" not in guard and "plant\\w*" not in guard,
          "die Schreibsperre wird nicht durch Tier-/Baumnamen oder Beispiel-Keywords ausgeloest")

    guides = region(source, "function Get-BridgeGuides", "function Get-SessionStartPackage")
    for marker in ("modelBuildRules = @{", "regardless of subject, model name or whether it is organic",
                   "Prefer build_polygon_model", "in ANY category", "not an animal/tree-only rule",
                   "primitive-only placeholder", "GLOBAL 3D BUILD BAR, independent of names/examples"):
        check(marker in guides or marker in source,
              f"globaler Modellierungsstandard enthaelt: {marker}")
    check("The builder is preferred, not mandatory for every simple Part." in guides
          and "reduce how many assets are built instead of degrading the finish" in guides,
          "globale Polygon-Praeferenz laesst einfache Aufgaben einfach und bewahrt den Finish-Standard")
    polygon_tool = region(source, "name = 'build_polygon_model';", "name = 'ui_capabilities';")
    check("GLOBALER 3D-BAUSTANDARD" in polygon_tool
          and "nichttriviale Custom-Modelle aller Kategorien" in polygon_tool
          and "kein anhand von Namen ausgeloester Zwang" in polygon_tool,
          "Polygon-Tool beschreibt den allgemeinen Vorrang ohne Namens-Trigger")
    assembly_tool = region(source, "name = 'build_assembly';", "name = 'build_polygon_model';")
    check("build_polygon_model" in assembly_tool and "Wiederholungen" in assembly_tool,
          "Assembly-Tool ist als Ergaenzung fuer wiederholte/module Strukturen beschrieben")
    lua_tool = region(source, "name = 'run_lua';", "name = 'lua_state';")
    check("Fuer jedes nichttriviale sichtbare 3D-Modell" in lua_tool
          and "modelBuildRules" in lua_tool,
          "run_lua verweist auf den allgemeinen 3D-Baustandard")

    # The actual Studio builder tags and returns its created model. Audit metrics
    # are gathered per candidate, not borrowed from the rest of Workspace.
    for marker in ('local organicBuild=args.organic==true',
                   'model:SetAttribute("ArenaOrganicBuild",true)',
                   'return ok({model=describeRef(model),organic=organicBuild',
                   'part:GetAttribute("ArenaPolygonTriangle") ~= nil',
                   'if modelUniqueColors < 3 or modelDominantShare > 0.90 or modelNearWhiteShare > 0.90 then',
                   '"PALETTE_TOO_FLAT', '"ANIMATION_NOT_INSTALLED',
                   'node.Disabled', 'string.lower(node.Source)', 'organicQuality = organicQuality'):
        check(marker in plugin_lua, f"modellbezogene Polygon-/Farb-/Motion-Messung enthaelt: {marker}")
    check("ArenaMasterBuild is a broad model marker, not proof of polygon geometry" in plugin_lua,
          "der alte generische ArenaMasterBuild-Marker zaehlt nicht als Polygonbeweis")

    # Plugin's response wrapper is unwrapped before state/audit persistence;
    # successful writes stale the evidence, while a standalone model_audit
    # refreshes the exact target metrics.
    result_tracking = region(source, "if ($null -ne $resultJson) {\n                    Save-DedupedPlayResult", "if ($null -eq $resultJson) {\n                    $entryNow")
    for marker in ("$resultEnvelope = $resultJson | ConvertFrom-Json",
                   "$pluginPayload = $resultEnvelope.result",
                   "$resultSucceeded = ([bool]$resultEnvelope.ok -eq $true)",
                   "$Shared.OrganicBuilds[[string]$sessionId] = ($organicState | ConvertTo-Json",
                   "$organicRecord.auditAtTicks = 0L",
                   "$organicRecord.lastWriteAtTicks = $resultAtTicks",
                   "$organicRecord.auditQuality = $perModelQuality",
                   "$organicRecord.auditModels = @($modelEvidence)",
                   "$organicRecords += @($organicRecord)",
                   "$Shared.AuditFlags[[string]$sessionId]"):
        check(marker in result_tracking, f"Organic-Auditbeleg wird verarbeitet: {marker}")

    # Independent model of the report_done decision.
    passing = proof_record()
    check(organic_proof_result(None) == "OK", "ohne registrierte organische Arbeit bleibt report_done unverändert")
    check(organic_proof_result(passing) == "OK", "frischer Audit mit bestandenen Modellmetriken kann passieren")
    check(organic_proof_result({"required": False}) == "ORGANIC_AUDIT_REQUIRED",
          "registrierter, aber unvollständiger Organic-Zustand wird sicher abgewiesen")
    check(organic_proof_result({"required": True, "models": []}) == "ORGANIC_AUDIT_REQUIRED",
          "Organic-Zustand ohne Modell-Datensatz wird sicher abgewiesen")
    stale = proof_record()
    stale["models"][0]["lastWriteAtTicks"] = 121
    check(organic_proof_result(stale) == "ORGANIC_AUDIT_REQUIRED", "jeder spaetere Edit entwertet den vorherigen Audit")
    check(organic_proof_result(proof_record(id="another-model")) == "ORGANIC_AUDIT_REQUIRED",
          "Audit eines fremden Modells zaehlt nicht fuer das zurueckgegebene Tier")
    for overrides, label in (
        ({"polygonTriangles": 0}, "ohne Polygon-Dreiecke"),
        ({"uniqueColors": 2}, "mit weniger als drei Farben"),
        ({"dominantColorShare": 0.95}, "mit fast einfarbiger Palette"),
        ({"nearWhiteShare": 0.95}, "mit fast weisser/defaultartiger Palette"),
        ({"motionScripts": 0}, "ohne installiertes Bewegungsscript"),
        ({"issues": ["PLUGIN_REPORTED_ISSUE"]}, "mit Plugin-Audit-Issue"),
    ):
        check(organic_proof_result(proof_record(**overrides)) == "DETAIL_REQUIRED",
              f"report_done blockiert ein Tier {label}")
    check(organic_proof_result(proof_record(), now_ticks=500) == "OK",
          "ein frischer Beleg fuer ein einzelnes Modell kann passieren")
    several = proof_record()
    several["models"].append({
        "modelId": "organic-bear-2", "lastWriteAtTicks": 100, "auditAtTicks": 120,
        "auditQuality": {"detected": True, "issues": [], "models": [{
            "id": "organic-bear-2", "polygonTriangles": 60, "uniqueColors": 4,
            "dominantColorShare": 0.62, "nearWhiteShare": 0.01, "motionScripts": 1, "issues": []
        }]}
    })
    check(organic_proof_result(several) == "OK", "jeder separat erfasste Modellbeleg kann gemeinsam passieren")
    several["models"][1]["auditAtTicks"] = 99
    check(organic_proof_result(several) == "ORGANIC_AUDIT_REQUIRED",
          "ein einziges nicht frisch auditiertes Tier blockiert report_done")

    done_gate = region(source, "'report_done' {", "$doneTitle = ''")
    for marker in ("ORGANIC_AUDIT_REQUIRED", "foreach ($organicRecord in $organicRecords)", "matchingOrganicModel", "modelTriangles -le 0",
                   "modelUniqueColors -lt 3", "modelDominantShare -gt 0.90",
                   "modelNearWhiteShare -gt 0.90", "modelMotionScripts -le 0",
                   "auditAtTicks -lt $lastWriteAtTicks", "if ($hasOrganicState)",
                   "Organic completion state could not be decoded; report_done fails closed.",
                   "report_done fails closed and does not accept an unsupported completion claim.",
                   "If any later Place write succeeds, audit every registered organic model again.",
                   "DETAIL_REQUIRED"):
        check(marker in done_gate, f"report_done prueft den organischen Beleg: {marker}")
    organic_gate = done_gate[done_gate.index("# Organic quality is a separate, per-model proof."):]
    check("$handoffJson" not in organic_gate,
          "ein Handoff kann die explizite Organic-Qualitaetspruefung nicht umgehen")

    # User-facing UI contract and previously requested progress/reset behavior.
    xaml = re.search(r"\$xaml = @'\n([\s\S]*?)\n'@", source)
    check(xaml is not None, "Hauptfenster-XAML ist vorhanden")
    if xaml:
        main_xaml = xaml.group(1)
        check('Text="Arena Roblox Bridge"' in main_xaml
              and 'Text="bereit für verbundene Places"' in main_xaml
              and 'RuntimeLine' not in source,
              "Titelzeile zeigt nur Produktname und den festen Place-Hinweis")
    progress = region(source, "function Update-PlaceProgressVisual", "function Get-ProgressDiagnoseLines")
    for marker in ("'Fertig!'", "'Arena arbeitet gerade...'",
                   "'Seit über einer Minute kein Bridge Aufruf mehr'",
                   "ProgressPercent.Text = ($percent.ToString() + ' % • ' + $label)",
                   "SilentSeconds -ge 60"):
        check(marker in progress, f"Place-Fortschrittsvertrag enthaelt: {marker}")
    row_builder = region(source, "function New-Row {", "function New-MinimalPlaceRow")
    fallback = region(source, "function New-MinimalPlaceRow {", "\nfunction ")
    check("$namePanel.VerticalAlignment = 'Stretch'" in row_builder
          and "$topCenterSpacer.Height = [System.Windows.GridLength]::new(1, [System.Windows.GridUnitType]::Star)" in row_builder
          and "$bottomCenterSpacer.Height = [System.Windows.GridLength]::new(1, [System.Windows.GridUnitType]::Star)" in row_builder
          and "$namePanel.VerticalAlignment = 'Center'" in fallback,
          "leere Place-Zeilen halten den Namen mit symmetrischen Star-Spacern bzw. Center-Fallback mittig")
    check("Show-CopyConfirm -Message 'Token wurde zurückgesetzt.' -Seconds 4" in source
          and "Show-CopyConfirm -Message 'Token für alle Places wurde zurückgesetzt.' -Seconds 4" in source,
          "Token-Reset zeigt die kurze Fensterbestätigung")

    if FAILURES:
        print(f"\nFEHLGESCHLAGEN: {len(FAILURES)} Pruefung(en) rot.")
        return 1
    print("\nOK: 7.2.9: 7.1.4-Organic-Build-, Audit-Frische-, report_done- und UI-Regressionspruefungen bestanden.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, ValueError, KeyError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
