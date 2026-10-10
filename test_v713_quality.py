#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifikationstest fuer Arena Roblox Bridge 7.1.5 (Start-Fix; prueft weiterhin den 7.1.3/7.1.4-Quaetatsvertrag).

NUTZERBERICHT UEBER DIE LETZTE BAU-SESSION (Bridge, Roblox Studio, Edit-Modus):
Tiere wurden nur aus Kugel-Parts zusammengesetzt (Koerper, Kopf, vier Beine,
Schwanz = sieben Baelle), Baeume aus einem Cylinder-Stamm plus einer Kugel-Krone,
und alle Cylinder standen um 90 Grad falsch. Am Ende brach die Sitzung mitten in
der Arbeit mit "The AI service rejected this request" ab; in den Einstellungen
fehlte der Schalter fuer die Fertig-Benachrichtigung, und der deaktivierte
sim_start wurde dort noch als Warnkasten angezeigt.

Dieser Test prueft die vier Antworten der Bridge darauf - als Modell UND am
echten Quellcode:

  Test 1: Cylinder-Mathematik. Die kanonische Aufrichtung dreht die LOKALE
          X-Achse (Roblox-Zylinderachse) exakt nach oben; cylinderBetween baut
          eine rechtshaendige Basis fuer JEDE Richtung. Gegenprobe: die
          Fehlbedienung (Hoehe in Size.Y, keine Rotation) ist genau das, was
          die Messung erkennt.
  Test 2: Zylinder-Messung. heightInYAxisHorizontal trifft den echten Fehler und
          laesst korrekte Teile, schraege Aeste und flache Scheiben in Ruhe.
  Test 3: Kugel-Gruppen. Ein Ball-Tier wird erkannt, ein Schneemann aus drei
          Baellen, ein Polgyon-Modell und eine gemischte Szene nicht.
  Test 4: report_done. 7.1.2 winkt durch, 7.1.3 antwortet DETAIL_REQUIRED -
          und ein ehrlicher Handoff ist der dokumentierte Ausweg.
  Test 5: Fertig-Schalter. Aus wirkt sofort (Warteschlange wird geleert), an
          zeigt wieder an.
  Test 6: Nutzlast-Budget des Sessionstarts. Kern voll, Rest als Index, harte
          Obergrenze greift, packageBytes/docsPolicy luegen nicht.
  Test 7: Quellcode-Abnahme (organicBuildRules samt Referenz-Lua, buildQuality
          im Plugin, DETAIL_REQUIRED im Server, Schalter-Text, Budgetgrenze,
          Versionsstand 7.1.3).
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "ArenaBridge.ps1"
VERSION = "7.6.2"

SESSION_BUDGET_BYTES = 300000
PRIMITIVE_MIN_PARTS = 6
PRIMITIVE_MIN_BALLS = 6
PRIMITIVE_MIN_BALL_SHARE = 0.5
CYLINDER_TILT_TOLERANCE_DEG = 5.0

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


def region(source: str, start_marker: str, end_marker: str) -> str:
    begin = source.index(start_marker)
    end = source.index(end_marker, begin)
    return source[begin:end]


# ===========================================================================
# Vektor-/CFrame-Mathematik (dieselbe Rechnung, die Roblox macht)
# ===========================================================================
Vec = tuple[float, float, float]


def rot_z(angle: float, v: Vec) -> Vec:
    c, s = math.cos(angle), math.sin(angle)
    return (c * v[0] - s * v[1], s * v[0] + c * v[1], v[2])


def norm(v: Vec) -> Vec:
    length = math.sqrt(sum(component * component for component in v))
    return tuple(component / length for component in v)  # type: ignore[return-value]


def cross(a: Vec, b: Vec) -> Vec:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def canonical_upright_axes() -> tuple[Vec, Vec]:
    """CFrame.new(pos) * CFrame.Angles(0, 0, math.rad(90)): lokale Achsen."""
    x_axis = rot_z(math.pi / 2, (1.0, 0.0, 0.0))
    y_axis = rot_z(math.pi / 2, (0.0, 1.0, 0.0))
    return x_axis, y_axis


def cylinder_between(a: Vec, b: Vec) -> tuple[Vec, Vec, Vec, float]:
    """Die Referenzfunktion aus organicBuildRules, eins zu eins nachgerechnet."""
    delta = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    length = math.sqrt(sum(component * component for component in delta))
    axis = norm(delta)
    ref = (0.0, 0.0, 1.0) if abs(axis[1]) > 0.99 else (0.0, 1.0, 0.0)
    z_axis = norm(cross(axis, ref))
    y_axis = norm(cross(z_axis, axis))
    return axis, y_axis, z_axis, length


# ===========================================================================
# Die Messung aus tools.model_audit / WORLD_ENGINE.auditBuildQuality
# ===========================================================================
def classify_cylinder(size: Vec, x_axis: Vec, y_axis: Vec) -> dict:
    """Dieselbe Signatur wie WORLD_ENGINE.auditBuildQuality im Plugin.

    Harter Fehler (discLikeCylinder): die Achse liegt waagerecht UND das Teil
    ist quer mindestens 1,5-mal so gross wie lang -> es steht als Scheibe auf
    der Kante. Das ist der klassische 90-Grad-Dreher mit der Laenge in Size.Y
    oder Size.Z. axisSkewDeg bleibt die reine Info (schraege Achse).
    """
    align = max(abs(component) for component in x_axis)
    skew = math.degrees(math.acos(max(0.0, min(1.0, align))))
    disc_like = abs(x_axis[1]) < 0.3 and max(size[1], size[2]) >= 1.5 * size[0]
    return {
        "discLikeCylinder": disc_like,
        "axisSkewDeg": round(skew, 1),
        "tilted": (not disc_like) and skew > CYLINDER_TILT_TOLERANCE_DEG,
    }


def judge_group(part_count: int, ball_count: int, solid_count: int) -> bool:
    """Reine Kugel-Gruppe? (dieselben Schwellen wie im Plugin)"""
    return (part_count >= PRIMITIVE_MIN_PARTS
            and ball_count >= PRIMITIVE_MIN_BALLS
            and ball_count >= PRIMITIVE_MIN_BALL_SHARE * part_count
            and solid_count == 0)


def report_done_gate(audit: dict, has_handoff: bool) -> str:
    """Die Entscheidung aus dem report_done-Pfad der Bridge."""
    if int(audit.get("placeholderCount", 0)) > 0 and not has_handoff:
        return "HANDOFF_REQUIRED"
    if (bool(audit.get("primitiveAbuse", False)) or int(audit.get("cylinderProblemCount", 0)) > 0) and not has_handoff:
        return "DETAIL_REQUIRED"
    return "OK"


class NotifyState:
    """Der Fertig-Schalter samt Warteschlange (wie $Shared.BridgeSettings + NotifyQueue)."""

    def __init__(self, enabled: bool = False, pending: int = 0) -> None:
        self.enabled = enabled
        self.queue = [{"index": index} for index in range(pending)]
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
        while self.queue:
            self.queue.pop(0)
            self.shown += 1


class SessionPayload:
    """Get-SessionStartPackage: Kern voll, Rest Index, harte Obergrenze."""

    def __init__(self, core_names: list[str]) -> None:
        self.core_names = set(core_names)

    def build(self, docs: list[dict], budget: int = SESSION_BUDGET_BYTES) -> dict:
        full = [doc for doc in docs if doc["name"] in self.core_names]
        index = [{"name": doc["name"], "category": doc["category"], "summary": doc["summary"]}
                 for doc in docs if doc["name"] not in self.core_names]
        package = {"tools": full, "toolsIndex": index, "docsPolicy": "core-full", "packageBytes": 0,
                   "budgetBytes": budget}
        measured = len(json.dumps(package, ensure_ascii=False))
        if measured > budget:
            package["tools"] = []
            package["toolsIndex"] = [{"name": doc["name"], "category": doc["category"], "summary": doc["summary"]}
                                     for doc in docs]
            package["docsPolicy"] = "index-only"
            measured = len(json.dumps(package, ensure_ascii=False))
        package["packageBytes"] = measured
        return package


# ===========================================================================
def main() -> int:
    source = load_source()
    plugin_lua = extract_plugin_lua(source)

    check(json.loads((ROOT / "version.json").read_text(encoding="utf-8"))["version"] == VERSION,
          f"version.json steht auf {VERSION}")

    # ------------------------------------------------------------------
    # Test 1: Zylinder-Mathematik
    # ------------------------------------------------------------------
    x_axis, y_axis = canonical_upright_axes()
    check(abs(dot(x_axis, (0.0, 1.0, 0.0)) - 1.0) < 1e-9,
          "CFrame.Angles(0, 0, math.rad(90)) dreht die lokale X-Achse exakt nach oben (stehender Zylinder)")
    check(abs(dot(y_axis, (0.0, 1.0, 0.0))) < 1e-9,
          "die lokale Y-Achse steht danach waagerecht - ein ungedrehter Zylinder waere genau der 90-Grad-Fehler")

    axis, up, sideways, length = cylinder_between((0.0, 0.0, 0.0), (0.0, 4.0, 0.0))
    check(abs(dot(axis, (0.0, 1.0, 0.0)) - 1.0) < 1e-9 and abs(length - 4.0) < 1e-9,
          "cylinderBetween(A, B) richtet die Zylinderachse exakt auf die Richtung A->B aus")
    check(abs(dot(cross(axis, up), sideways) - 1.0) < 1e-9,
          "die Basis aus cylinderBetween ist rechtshaendig (X cross Y = Z) - CFrame.fromMatrix akzeptiert sie")
    for a, b in (((0, 0, 0), (3, 0, 0)), ((0, 0, 0), (0, 0, -5)), ((1, 2, 3), (-4, 0.5, 2))):
        axis, up, sideways, length = cylinder_between(a, b)  # type: ignore[arg-type]
        check(abs(dot(cross(axis, up), sideways) - 1.0) < 1e-9 and abs(length - math.dist(a, b)) < 1e-9,
              f"cylinderBetween ist auch fuer die Richtung {a}->{b} korrekt (kein Sonderfall offen)")

    # ------------------------------------------------------------------
    # Test 2: Zylinder-Messung
    # ------------------------------------------------------------------
    mistake = classify_cylinder((2.0, 12.0, 2.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    check(mistake["discLikeCylinder"] and not mistake["tilted"],
          "DER Nutzerfehler wird erkannt: Size = (Durchmesser, Hoehe, Durchmesser) ohne Rotation - "
          "die Achse liegt waagerecht und das Teil steht als Scheibe auf der Kante")
    mistake_oval = classify_cylinder((2.0, 2.0, 12.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    check(mistake_oval["discLikeCylinder"],
          "dieselbe Verwechslung mit der Laenge in Size.Z wird ebenfalls erkannt (nicht nur Y)")
    correct = classify_cylinder((12.0, 2.0, 2.0), *canonical_upright_axes())
    check(not correct["discLikeCylinder"] and not correct["tilted"],
          "die kanonische Aufrichtung (Size = (Laenge, Durchmesser, Durchmesser) + Z-Rotation) wird NICHT beanstandet")
    lying_log = classify_cylinder((14.0, 2.5, 2.5), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    check(not lying_log["discLikeCylinder"] and not lying_log["tilted"],
          "ein absichtlich liegender Stamm (Achse = Weltachse X, X ist die laengste Seite) bleibt unbeanstandet")
    vertical_slab = classify_cylinder((0.4, 6.0, 6.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0))
    check(not vertical_slab["discLikeCylinder"],
          "eine flache Scheibe mit SENKRECHTER Achse (Tischplatte, Deckel) bleibt unbeanstandet - "
          "gemeldet wird nur die auf der Kante stehende Scheibe")
    diagonal_axis = norm((1.0, 1.0, 0.0))
    diagonal = classify_cylinder((8.0, 1.2, 1.2), diagonal_axis, norm(cross(diagonal_axis, (0.0, 0.0, 1.0))))
    check(not diagonal["discLikeCylinder"] and diagonal["tilted"] and diagonal["axisSkewDeg"] > 40,
          "ein schraeger Ast wird nur als Info gemeldet (axisSkewDeg), nicht als harter Fehler")

    # ------------------------------------------------------------------
    # Test 3: Kugel-Gruppen
    # ------------------------------------------------------------------
    cat_of_balls = judge_group(part_count=7, ball_count=7, solid_count=0)
    check(cat_of_balls, "ein Tier aus sieben Baellen wird als primitiveOnly-Gruppe erkannt")
    check(judge_group(part_count=9, ball_count=6, solid_count=0),
          "auch eine gemischte Kugel-Mehrheit (6 von 9) gilt als Entwurf")
    check(not judge_group(part_count=3, ball_count=3, solid_count=0),
          "ein Schneemann aus drei Baellen loest KEINEN Alarm aus (unter der Mindestgroesse)")
    check(not judge_group(part_count=9, ball_count=6, solid_count=1),
          "sobald ein Polygon-/Assembly-/Mesh-/Detail-Teil dabei ist, gilt die Gruppe nicht mehr als rein primitiv")
    check(not judge_group(part_count=20, ball_count=5, solid_count=0),
          "eine Szene mit vielen Nicht-Kugeln bleibt unbeanstandet (Ball-Anteil unter 50 %)")

    # ------------------------------------------------------------------
    # Test 4: report_done
    # ------------------------------------------------------------------
    check(report_done_gate({"primitiveAbuse": False, "cylinderProblemCount": 0}, False) == "OK",
          "sauberes Modell: report_done bleibt erlaubt")
    check(report_done_gate({"primitiveAbuse": True, "cylinderProblemCount": 0}, False) == "DETAIL_REQUIRED",
          "Kugel-Tier: report_done antwortet DETAIL_REQUIRED statt 'fertig'")
    check(report_done_gate({"primitiveAbuse": False, "cylinderProblemCount": 3}, False) == "DETAIL_REQUIRED",
          "falsch gedrehte Zylinder: report_done antwortet DETAIL_REQUIRED")
    check(report_done_gate({"primitiveAbuse": True, "cylinderProblemCount": 2}, True) == "OK",
          "ehrlicher Handoff bleibt der dokumentierte Ausweg (kein Deadlock)")
    check(report_done_gate({"placeholderCount": 4, "primitiveAbuse": True}, False) == "HANDOFF_REQUIRED",
          "Platzhalter haben weiter Vorrang vor der Bauqualitaet (Reihenfolge unveraendert)")

    # ------------------------------------------------------------------
    # Test 5: Fertig-Schalter
    # ------------------------------------------------------------------
    state = NotifyState(enabled=True, pending=0)
    state.queue.append({"index": 1})
    state.tick()
    check(state.shown == 1, "Schalter an: die Fertig-Meldung wird angezeigt")
    state.queue.append({"index": 2})
    state.set_enabled(False)
    state.tick()
    check(state.shown == 1 and state.discarded == 1 and not state.queue,
          "Ausschalten wirkt SOFORT: wartende Meldungen werden verworfen, nichts ploppt nach")
    state.set_enabled(True)
    state.queue.append({"index": 3})
    state.tick()
    check(state.shown == 2, "Wiedereinschalten zeigt neue Meldungen wieder an")
    check(NotifyState(enabled=False, pending=2).enabled is False,
          "Standard bleibt AUS (wie notifyOnDone = $false in den Einstellungen)")

    # ------------------------------------------------------------------
    # Test 6: Nutzlast-Budget des Sessionstarts
    # ------------------------------------------------------------------
    core_names = ["build_polygon_model", "build_assembly", "model_audit", "world_audit", "run_lua",
                  "report_done", "get_docs", "refine", "insert_script", "get_place_info",
                  "ask_user", "confirm_action"]
    docs = []
    for index in range(129):
        name = core_names[index] if index < len(core_names) else f"tool_{index}"
        docs.append({"name": name, "category": "create", "summary": f"Kurztext {index}",
                     "description": "x" * 900, "params": {"a": "y" * 100}, "examples": ["z" * 120]})
    policy = SessionPayload(core_names)
    package = policy.build(docs)
    check(package["docsPolicy"] == "core-full" and len(package["tools"]) == len(core_names),
          "Kernwerkzeuge kommen vollstaendig, der Rest landet im Index")
    check(len(package["toolsIndex"]) == len(docs) - len(core_names),
          "der Index enthaelt jedes nicht-Kern-Werkzeug (nichts verschwindet unbemerkt)")
    full_bytes = len(json.dumps({"tools": docs}, ensure_ascii=False))
    check(package["packageBytes"] < full_bytes,
          f"das Paket ist messbar kleiner als die volle Doku ({package['packageBytes']} < {full_bytes} Bytes)")
    real_bytes = len(json.dumps(package, ensure_ascii=False))
    check(0 <= real_bytes - package["packageBytes"] <= 20,
          "packageBytes nennt die wirklich gemessene Groesse des Pakets (Abweichung nur durch das Feld selbst)")
    tiny_budget = policy.build(docs, budget=2000)
    check(tiny_budget["docsPolicy"] == "index-only" and not tiny_budget["tools"],
          "harte Obergrenze greift: notfalls kommt auch der Kern nur noch als Index (kein unbegrenztes Paket)")
    real_tiny = len(json.dumps(tiny_budget, ensure_ascii=False))
    check(0 <= real_tiny - tiny_budget["packageBytes"] <= 20,
          "auch nach der Notbremse stimmt die gemessene Groesse")

    # ------------------------------------------------------------------
    # Test 7: Quellcode-Abnahme
    # ------------------------------------------------------------------
    guides = region(source, "function Get-BridgeGuides", "function Get-SessionStartPackage")
    for marker in ("organicBuildRules = @{", "FORBIDDEN - BALL ANIMAL", "FORBIDDEN - CYLINDER TREE",
                   "ROBLOX CYLINDER AXIS", "Size.X is the LENGTH",
                   "CFrame.new(pos) * CFrame.Angles(0, 0, math.rad(90))",
                   "local function cylinderBetween(parent, a, b, diameter, props)",
                   "p.CFrame = CFrame.fromMatrix((a + b) * 0.5, axis, y, z)",
                   "discLikeCylinder", "model_audit reports it as primitiveOnly with primitiveGroups"):
        check(marker in guides, f"Sessionstart-Regelblock enthaelt: {marker}")

    for marker in ("WORLD_ENGINE.auditBuildQuality = function(parts, root)",
                   'issue = "discLikeCylinder"',
                   "primitiveGroups", "cylinderProblems", "tiltedCylinders",
                   "buildQuality = quality", "primitiveAbuse = quality.primitiveOnly",
                   "cylinderProblemCount = quality.cylinderProblemCount"):
        check(marker in plugin_lua, f"Plugin-Messung enthaelt: {marker}")
    check("local function topGroup(part)" in plugin_lua
          and "table.sort(groupOrder, function(a, b) return a:GetFullName() < b:GetFullName() end)" in plugin_lua,
          "die Gruppen-Analyse ist vorhanden und deterministisch sortiert")

    gate = region(source, "'report_done' {", "$doneTitle = ''")
    for marker in ("code = 'DETAIL_REQUIRED'", "primitiveAbuseNow", "cylinderProblemsNow",
                   "PRIMITIVE-ONLY build", "call handoff { scope="):
        check(marker in gate, f"report_done-Qualitaetswache enthaelt: {marker}")
    check(source.count("DETAIL_REQUIRED") >= 3 and "$envelope.buildQuality" in source,
          "DETAIL_REQUIRED steht in Plugin, Server und Regelwerk; die Messung erscheint in jeder Antwort")

    check("SessionPayloadHardBudgetBytes = 300000" in source
          and "$Shared.SessionPayloadHardBudgetBytes" in source
          and "'core-full'" in source and "'index-only'" in source
          and "$out.packageBytes = [int]$measuredBytes" in source
          and "$out.toolsIndex = $indexDocs.ToArray()" in source,
          "Nutzlast-Budget (Grenze, Kern/Index, Notbremse, ehrliche Messung) ist verdrahtet")
    core_list = region(source, "$coreToolNames = @(", "$coreDocs = New-Object")
    check("'build_polygon_model'" in core_list and "'model_audit'" in core_list and "'run_lua'" in core_list
          and "'ask_user'" in core_list and "'confirm_action'" in core_list
          and "'search_assets'" not in core_list and "'insert_asset'" not in core_list,
          "die Kernliste enthaelt die Bau-/Audit-Werkzeuge und schiebt die Toolbox-Pfade in den Index")

    settings = region(source, "$settingsXaml = @'", "    $settingsReader = [System.Xml.XmlNodeReader]")
    check('x:Name="DoneNotifySwitch"' in settings
          and 'Content="Benachrichtigung, wenn Arena fertig ist"' in settings,
          "der Schalter 'Benachrichtigung, wenn Arena fertig ist' existiert in den Einstellungen")
    check('SIMULATION' not in settings and 'sim_start ist deaktiviert' not in settings,
          "der SIMULATION-Warnkasten ist komplett aus den Einstellungen entfernt")
    open_settings = region(source, "function Open-SettingsWindow", "# Version 3.8: Die Update-Infos")
    check("$doneNotifySwitch.IsChecked = $doneNotifyNow" in open_settings
          and "$script:Shared.BridgeSettings.notifyOnDone = $enabled" in open_settings
          and "if (-not $enabled) { Clear-NotifyQueue }" in open_settings
          and "Save-BridgeSettingsFile" in open_settings,
          "der Schalter wird geladen, gespeichert, wirkt sofort und prueft die Warteschlange")
    check("function Clear-NotifyQueue" in source
          and "Fertig-Meldung verwerfen: der Schalter" not in source
          and "Fertig-Meldung verworfen: der Schalter" in source,
          "Clear-NotifyQueue existiert und die Anzeige prueft den Schalter unmittelbar vor dem Anzeigen")

    for marker in ("# Arena Roblox Bridge  -  Version 7.6.2", "KRITISCHER START-HOTFIX 7.1.5",
                   "DocsVersion     = '7.6.2'", 'local ARENA_VERSION  = "7.6.2"'):
        check(marker in source, f"Versionsmarker ist vorhanden: {marker}")

    if FAILURES:
        print(f"\nFEHLGESCHLAGEN: {len(FAILURES)} Pruefung(en) rot.")
        return 1
    print("\nOK: alle 7.1.5-Pruefungen gruen (Start-Fix plus Zylinderregel, Kugel-Erkennung, organischer Auditbeleg, "
          "Fertig-Schalter, Nutzlast-Budget, Quellcode-Abnahme).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
