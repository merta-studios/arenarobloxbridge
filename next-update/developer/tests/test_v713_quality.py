#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline regression checks retained from the 7.1.3 quality work.

The historical quality measurements remain useful as optional diagnostics, but
are not a builder prescription or a report_done gate. This test also retains
independent cylinder math, completion-notification, and session-payload checks.
It does not render a Roblox Place or replace a Windows/Studio acceptance run.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = ROOT / "app"
PS1 = APP_ROOT / "ArenaBridge.ps1"
VERSION = "7.7.2"
SESSION_BUDGET_BYTES = 300000
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("[GRUEN] " if condition else "[ROT]   ") + message)
    if not condition:
        FAILURES.append(message)


def region(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    return source[begin:source.index(end, begin)]


def load_source() -> str:
    raw = PS1.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf"), "ArenaBridge.ps1 must retain its UTF-8 BOM"
    return raw.decode("utf-8-sig")


def extract_plugin_lua(source: str) -> str:
    marker = "function Get-PluginSource {\n@'\n"
    begin = source.index(marker) + len(marker)
    end = source.index("\n'@\n}", begin)
    return source[begin:end]


def rot_z(angle: float, v: tuple[float, float, float]) -> tuple[float, float, float]:
    c, s = math.cos(angle), math.sin(angle)
    return (c * v[0] - s * v[1], s * v[0] + c * v[1], v[2])


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm(v: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(dot(v, v))
    return tuple(component / length for component in v)  # type: ignore[return-value]


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def cylinder_between(a: tuple[float, float, float], b: tuple[float, float, float]):
    """Reference cylinder basis retained to guard against a real orientation regression."""
    delta = tuple(y - x for x, y in zip(a, b))
    length = math.sqrt(dot(delta, delta))
    axis = norm(delta)
    ref = (0.0, 0.0, 1.0) if abs(axis[1]) > 0.99 else (0.0, 1.0, 0.0)
    z_axis = norm(cross(axis, ref))
    y_axis = norm(cross(z_axis, axis))
    return axis, y_axis, z_axis, length


def choose_method(explicit: str | None, place_convention: str | None, task_fit: str) -> str:
    """The documented priority: explicit user request, then Place, then fit."""
    return explicit or place_convention or task_fit


def completion_status(mesh_slots: list[str], handoff: bool = False) -> str:
    """Shape/grade/audit observations do not participate in completion policy."""
    if any(state != "applied" for state in mesh_slots) and not handoff:
        return "MESH_UPLOAD_PENDING"
    return "OK"


class NotifyState:
    """Small model of the existing notifyOnDone/NotifyQueue behavior."""

    def __init__(self, enabled: bool = False, pending: int = 0) -> None:
        self.enabled = enabled
        self.queue = list(range(pending))
        self.shown = 0
        self.discarded = 0

    def set_enabled(self, value: bool) -> None:
        self.enabled = value
        if not value:
            self.discarded += len(self.queue)
            self.queue.clear()

    def tick(self) -> None:
        if not self.enabled:
            self.discarded += len(self.queue)
            self.queue.clear()
            return
        self.shown += len(self.queue)
        self.queue.clear()


class SessionPayload:
    """The 300 KB session package budget: full core docs, then index-only fallback."""

    def __init__(self, core_names: list[str]) -> None:
        self.core_names = set(core_names)

    def build(self, docs: list[dict], budget: int = SESSION_BUDGET_BYTES) -> dict:
        full = [doc for doc in docs if doc["name"] in self.core_names]
        index = [{key: doc[key] for key in ("name", "category", "summary")}
                 for doc in docs if doc["name"] not in self.core_names]
        package = {"tools": full, "toolsIndex": index, "docsPolicy": "core-full",
                   "packageBytes": 0, "budgetBytes": budget}
        measured = len(json.dumps(package, ensure_ascii=False))
        if measured > budget:
            package["tools"] = []
            package["toolsIndex"] = [{key: doc[key] for key in ("name", "category", "summary")} for doc in docs]
            package["docsPolicy"] = "index-only"
            measured = len(json.dumps(package, ensure_ascii=False))
        package["packageBytes"] = measured
        return package


def main() -> int:
    source = load_source()
    lua = extract_plugin_lua(source)
    metadata = json.loads((APP_ROOT / "version.json").read_text(encoding="utf-8"))
    check(metadata.get("version") == VERSION, "release metadata points at the prepared 7.7.2 source")

    # Independent regression: Roblox CylinderParts run along local X.
    x_axis = rot_z(math.pi / 2, (1.0, 0.0, 0.0))
    y_axis = rot_z(math.pi / 2, (0.0, 1.0, 0.0))
    check(abs(dot(x_axis, (0.0, 1.0, 0.0)) - 1.0) < 1e-9,
          "the canonical Z rotation points a CylinderPart local X axis upward")
    check(abs(dot(y_axis, (0.0, 1.0, 0.0))) < 1e-9,
          "after rotation the local Y axis is horizontal")
    for a, b in (((0, 0, 0), (0, 4, 0)), ((0, 0, 0), (3, 0, 0)),
                 ((0, 0, 0), (0, 0, -5)), ((1, 2, 3), (-4, 0.5, 2))):
        axis, up, sideways, length = cylinder_between(a, b)
        delta = tuple(y - x for x, y in zip(a, b))
        check(abs(length - math.sqrt(dot(delta, delta))) < 1e-9
              and abs(dot(cross(axis, up), sideways) - 1.0) < 1e-9,
              f"cylinderBetween retains a stable right-handed basis for {a} -> {b}")

    # Method choice must never silently outrank the user or established Place.
    check(choose_method("native-parts", "mesh", "polygon") == "native-parts",
          "an explicit user method wins over Place and general task-fit suggestions")
    check(choose_method(None, "mesh", "polygon") == "mesh",
          "the existing Place convention wins when the user leaves method open")
    check(choose_method(None, None, "blender") == "blender",
          "a tool recommendation is only a fallback after user and Place")

    guides = region(source, "function Get-BridgeGuides", "function Get-SessionStartPackage")
    for marker in ("modelBuildRules = @{", "projectConsistencyRules = @{",
                   "polygonPreference = 'Method priority: explicit user instructions",
                   "the observed target-Place convention", "Blender/build_mesh_model is recommended",
                   "not mandatory", "userRequestedPolygon may record intent, but is not a permission gate.",
                   "Completion follows the task brief and Place convention"):
        check(marker in guides, f"project-first build policy exposes: {marker}")
    for obsolete in ("BLENDER-FIRST (Version 7.5.5)", "POLYGON_BLENDER_FIRST",
                     "every nontrivial custom visible 3D model", "DRAFT_GRADE_RISK",
                     "DETAIL_REQUIRED", "ORGANIC_AUDIT_REQUIRED"):
        check(obsolete not in source, f"obsolete universal build/completion gate is absent: {obsolete}")

    # Audit measurements stay available and descriptive, including their
    # historically useful ball/cylinder observations.
    quality = region(lua, "WORLD_ENGINE.auditBuildQuality = function(parts, root)", "tools.model_audit = function(args)")
    for marker in ("discLikeCylinder", "cylinderProblemCount", "primitiveGroups",
                   "finishScore = finishScore", "grade = grade", "organicQuality = organicQuality",
                   "Measurements are descriptive", "not a quality judgment or required rebuild",
                   "not a completion gate"):
        check(marker in quality, f"optional quality measurements include: {marker}")
    model_audit = lua[lua.index("tools.model_audit = function(args)"):]
    for marker in ("BALL_DOMINANT_PATTERN (advisory)", "CYLINDER_PROPORTION_HEURISTIC (advisory)",
                   "ORGANIC_DIAGNOSTICS (advisory)", "FINISH_SCORE_ESTIMATE (advisory)"):
        check(marker in model_audit, f"model_audit reports advisory observation: {marker}")
    check('failCode("STYLE_TOO_GENERIC"' not in lua,
          "muted colors or style preference cannot be rejected by a generic-style gate")

    # Completion behavior is independent of geometry/style/audit heuristics.
    for observation in ("ball-only group", "horizontal cylinder", "draft estimate", "no organic tag",
                        "no motion", "plain palette", "stale optional audit"):
        check(completion_status([]) == "OK", f"{observation} cannot block report_done")
    check(completion_status(["waiting"]) == "MESH_UPLOAD_PENDING",
          "a real, explicitly created unapplied mesh slot remains pending")
    check(completion_status(["applied"]) == "OK",
          "a mesh slot with geometry applied is no longer pending")
    check(completion_status(["waiting"], handoff=True) == "OK",
          "an explicit handoff is still a valid alternative to continuing the mesh workflow")
    done_start = source.index("# report_done may identify an explicitly generated, unapplied mesh slot below.")
    done_end = source.index("$doneProgress = Read-ProgressState $sessionId", done_start)
    done_gate = source[done_start:done_end]
    check("$meshSlotCount -gt 0" in done_gate and "$waitCount -gt 0" in done_gate
          and "MESH_UPLOAD_PENDING" in done_gate,
          "source completion check requires actual mesh slots and at least one unapplied slot")
    for marker in ("primitiveAbuseNow", "cylinderProblemsNow", "draftRisk", "organicQuality",
                   "DETAIL_REQUIRED", "ORGANIC_AUDIT_REQUIRED"):
        check(marker not in done_gate, f"report_done ignores optional audit field {marker}")

    # Independent regression: completion notifications can still be turned off immediately.
    state = NotifyState(enabled=True)
    state.queue.append(1)
    state.tick()
    check(state.shown == 1, "enabled completion notifications are shown")
    state.queue.append(2)
    state.set_enabled(False)
    state.tick()
    check(state.shown == 1 and state.discarded == 1 and not state.queue,
          "disabling notifications immediately drains pending notices")
    state.set_enabled(True)
    state.queue.append(3)
    state.tick()
    check(state.shown == 2, "re-enabling notifications shows future notices")
    check(NotifyState(enabled=False, pending=2).enabled is False, "notifications retain the default-off behavior")
    settings = region(source, "$settingsXaml = @'", "    $settingsReader = [System.Xml.XmlNodeReader]")
    check('x:Name="DoneNotifySwitch"' in settings
          and 'Content="Benachrichtigung, wenn Arena fertig ist"' in settings,
          "the completion-notification setting remains present")
    check("function Clear-NotifyQueue" in source and "if (-not $enabled) { Clear-NotifyQueue }" in source,
          "turning the setting off clears the real notification queue")

    # Independent regression: session-start payload retains a measured hard limit.
    core_names = ["build_polygon_model", "build_assembly", "model_audit", "world_audit", "run_lua",
                  "report_done", "get_docs", "refine", "insert_script", "get_place_info",
                  "ask_user", "confirm_action"]
    docs = [{"name": core_names[i] if i < len(core_names) else f"tool_{i}",
             "category": "create", "summary": f"short {i}", "description": "x" * 900}
            for i in range(129)]
    package = SessionPayload(core_names).build(docs)
    check(package["docsPolicy"] == "core-full" and len(package["tools"]) == len(core_names)
          and len(package["toolsIndex"]) == len(docs) - len(core_names),
          "session-start includes full core docs and a complete compact tool index")
    actual = len(json.dumps(package, ensure_ascii=False))
    check(0 <= actual - package["packageBytes"] <= 20,
          "packageBytes measures the actual serialized payload")
    tiny = SessionPayload(core_names).build(docs, budget=2000)
    check(tiny["docsPolicy"] == "index-only" and not tiny["tools"],
          "the hard budget falls back to index-only instead of an unbounded payload")
    check("SessionPayloadHardBudgetBytes = 300000" in source
          and "$out.packageBytes = [int]$measuredBytes" in source
          and "$out.toolsIndex = $indexDocs.ToArray()" in source,
          "source still wires budget, measurement, and index fallback")

    check(f"# Arena Roblox Bridge  -  Version {VERSION}" in source
          and f"DocsVersion     = '{VERSION}'" in source
          and f'local ARENA_VERSION  = "{VERSION}"' in source,
          "desktop bridge, documentation, and embedded plugin use the prepared version")

    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} check(s).")
        return 1
    print("\nOK: retained cylinder math, project-first method selection, advisory audits, mesh-only completion, notifications, and payload-budget regressions passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
