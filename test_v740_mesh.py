#!/usr/bin/env python3
"""Offline-Abnahme fuer den 7.4.0-Blender-/Mesh-Weg (ohne Windows/PowerShell).

Geprueft wird, was ohne laufende Bridge pruefbar ist:

* Schritt 4 des Starts liegt VOR dem Tunnel, hat ein Zeitlimit, laesst den
  Start NIE haengen und deaktiviert bei einem Fehlschlag nur den Mesh-Bau.
* Die neuen Werkzeuge existieren als Schema (Tool-Doku = Argumentpruefung) und
  die Server-Werkzeuge sind im Handler verdrahtet.
* Blender-Skripte werden vor dem Start geprueft (Sperrliste), das OBJ wird von
  der Bridge gemessen (Dreiecke, Groesse, Dateigroesse, Limit).
* Der Plugin-Teil setzt Geometrie ausschliesslich ueber
  InsertService:CreateMeshPartAsync + MeshPart:ApplyMesh - niemals per
  MeshPart.MeshId - und markiert/loescht ArenaPlaceholder korrekt.
* model_audit trennt Mesh-Platzhalter von vergessenen Platzhaltern und
  report_done antwortet MESH_UPLOAD_PENDING.
* Das Fenster "Mesh-Uploads" ist echtes XAML im gemeinsamen Design und das
  Place-Menue oeffnet es.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "ArenaBridge.ps1"
VERSION = "7.4.0"
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("[GRUEN] " if condition else "[ROT]   ") + message)
    if not condition:
        FAILURES.append(message)


def region(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    stop = source.index(end, begin)
    return source[begin:stop]


def main() -> int:
    raw = PS1.read_bytes()
    check(raw.startswith(b"\xef\xbb\xbf"), "ArenaBridge.ps1 behaelt die UTF-8-BOM")
    source = raw.decode("utf-8-sig")
    metadata = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    notes = "\n".join(str(note) for note in metadata.get("notes", []))
    check(metadata.get("version") == VERSION, "version.json ist 7.4.0")
    for phrase in ("7.4.0", "Blender", "MESH_UPLOAD_PENDING", "Mesh-Uploads",
                   "CreateMeshPartAsync"):
        check(phrase in notes, f"Release-Notiz nennt {phrase}")

    # ------------------------------------------------------------------
    # 1) Schritt 4 des Starts: vor dem Tunnel, ohne Startblocker
    # ------------------------------------------------------------------
    runtime = region(source, "function Start-BridgeRuntime {", "# START: Ereignisse stehen VOR ShowDialog")
    check("Start-BlenderStartupGate" in runtime and "Start-CloudflareTunnel" in runtime,
          "Start-BridgeRuntime ruft den Blender-Schritt und den Tunnel auf")
    check(runtime.index("Start-BlenderStartupGate") < runtime.index("Start-CloudflareTunnel"),
          "Schritt 4 laeuft VOR dem Tunnelstart")
    check("if ($blenderReady) { Start-CloudflareTunnel }" in runtime,
          "der Tunnel startet nur, wenn der Blender-Schritt fertig ist")
    tunnel = region(source, "function Start-CloudflareTunnel {", "function Restart-CloudflareTunnel {")
    check(tunnel.index("if ($script:BlenderGatePending)") < tunnel.index("Get-CloudflaredPath"),
          "kein Tunnelstart (auch nicht aus der Selbstheilung), solange Schritt 4 laeuft")
    gate = region(source, "function Start-BlenderStartupGate {", "function Update-BlenderSplashRow {")
    check("[bool]$script:BlenderGatePending" in source
          and "AddMinutes(12)" in gate,
          "der Blender-Schritt hat ein hartes Zeitlimit und setzt den Warte-Zustand")
    complete = region(source, "function Complete-BlenderStartupGate {", "function Update-BlenderSplashRow {")
    check("Start-CloudflareTunnel" in complete and "$script:BlenderGatePending = $false" in complete,
          "der UI-Takt loest den Tunnel nach dem Schritt aus")
    refresh = region(source, "function Refresh-Ui {", "$line = $null")
    check("Complete-BlenderStartupGate" in refresh and "Update-BlenderSplashRow $null" in refresh
          and "Update-MeshTick" in refresh,
          "Refresh-Ui fuehrt Gate, Splash-Zeile und Mesh-Takt aus")
    for mode in ("'ready'", "'failed'", "'skipped'", "'installing'"):
        check(mode in region(source, "function Update-BlenderSplashRow {", "function Get-BlenderReport {"),
              f"Zeile 4 kennt den Zustand {mode}")
    check("$SplashBlenderDot" in source and "$SplashBlenderState" in source
          and "SplashBlenderDot" in source,
          "Zeile 4 des Startbildschirms existiert (XAML + FindName)")
    state = region(source, "function Set-BlenderState {", "function Get-BlenderExeInFolder {")
    check("BlenderState" in state and "GateResolved" in state,
          "der Blender-Zustand liegt in Shared (Handler und UI lesen mit)")
    install = region(source, "function Start-BlenderInstall {", "function Start-BlenderStartupGate {")
    check("portables ZIP" in install or "portable" in install.lower(),
          "die Installation nutzt das portable ZIP (kein Admin/UAC)")
    check("Set-BlenderState -State 'failed'" in install,
          "ein gescheiterter Installationsstart wird rot gemeldet, nicht verschluckt")
    worker = region(source, "function Test-BlenderCapability {", "function Get-BlenderDownloadCandidates {")
    check("BridgeBlenderProbeScript" in source and "ARENA_MESH_STATS" in source,
          "die Faehigkeitsprobe baut wirklich ein OBJ und misst es")
    probe = region(source, "$script:BridgeBlenderProbeScript = {", "# Der Mesh-Job-Worker")
    check("$markerIndex + $marker.Length" in probe and "$markerIndex + 18" not in source,
          "die Probenzeile wird exakt hinter dem Marker gelesen (kein Zeichenversatz)")
    check("if ($null -eq $stats -or [string]::IsNullOrWhiteSpace([string]$jsonText)) {" in probe
          and "$state.enabled = $false" in probe,
          "eine unlesbare Messzeile faellt GESCHLOSSEN durch (kein falscher Erfolg)")

    # ------------------------------------------------------------------
    # 2) Werkzeuge: Schema (Tool-Doku) und Handler-Verdrahtung
    # ------------------------------------------------------------------
    mesh_docs = region(source, "# ---------------- MESH / BLENDER", "# ---------------- JOBS ----------------")
    for tool in ("blender_status", "build_mesh_model", "mesh_status", "mesh_cancel",
                 "mesh_apply_asset", "mesh_slots", "mesh_apply"):
        check(f"name = '{tool}'" in mesh_docs,
              f"Werkzeug {tool} ist in der MESH-Sektion dokumentiert (Doku = Argumentpruefung)")
    check("slots = @{ type = 'array'; required = $true" in mesh_docs,
          "build_mesh_model verlangt slots (Schema)")
    switch = region(source, "    function Invoke-ServerTool($sessionId, [string]$tool, $toolArgs) {", "            'get_docs' {")
    for tool in ("blender_status", "build_mesh_model", "mesh_status", "mesh_cancel", "mesh_apply_asset"):
        check(f"'{tool}'" in switch, f"{tool} wird im Handler beantwortet (kein Studio-Befehl)")
    mesh_tool = region(source, "    function Invoke-MeshServerTool(", "    function Invoke-ServerTool(")
    check("MeshToolkitText" in mesh_tool, "der Handler laedt den Toolkit-Text (eine Quelle)")
    check("BLENDER_NOT_READY" in mesh_tool and "mesh_apply" in mesh_tool,
          "build_mesh_model meldet fehlendes Blender ehrlich; mesh_apply_asset nutzt den Plugin-Befehl")
    check("Test-MeshScriptSafety" in mesh_tool,
          "build_mesh_model prueft jedes Skript, bevor Blender startet")
    check("Start-MeshJobWork" in mesh_tool, "build_mesh_model startet den Hintergrund-Job")

    # ------------------------------------------------------------------
    # 3) Skript-Sperrliste, Messung, Limits
    # ------------------------------------------------------------------
    safety = region(source, "function Test-MeshScriptSafety {", "function Get-MeshJobData {")
    for token in ("subprocess", "socket", "urllib", "ctypes", "winreg",
                  "bpy.ops.wm.", "export_scene", "__import__", "eval(", "exec("):
        check(token in safety, f"Sperrliste enthaelt {token}")
    check("200000" in safety, "Skriptgroesse ist begrenzt")
    stats = region(source, "function Get-MeshObjStats {", "function Test-MeshScriptSafety {")
    for token in ("triangles", "vertices", "bytes", "size", "limit", "overLimit"):
        check(token in stats, f"OBJ-Messung liefert {token}")
    check("[int]$Limit = 10000" in stats, "Standardgrenze sind 10.000 Dreiecke")
    job = region(source, "function Start-MeshJobWork {", "function Stop-MeshJob {")
    check("Set-MeshSlotField $Shared ([string]$slot.key) 'state' 'rejected'" in source
          and "hoechstens" in source,
          "ein Slot ueber der Dreiecksgrenze wird abgelehnt (state rejected)")
    check("MeshJobScriptText" in job and "BeginInvoke" in job,
          "der Blender-Lauf startet in einem eigenen Runspace (HTTP-Antwort sofort)")
    check("WaitForExit($timeoutSeconds" in source and "Kill()" in source,
          "der Blender-Prozess hat ein Zeitlimit und wird hart beendet")

    # ------------------------------------------------------------------
    # 4) Plugin: Geometrie einsetzen, Platzhalter, ehrliche Gates
    # ------------------------------------------------------------------
    lua = region(source, "tools.mesh_slots = function(args)", "tools.get_output = function(args)")
    check("tools.mesh_apply = function(args)" in lua, "Plugin kennt den internen Befehl mesh_apply")
    check('Instance.new("MeshPart")' in lua, "Platzhalter sind MeshParts (viereckige Box)")
    check('part:SetAttribute("ArenaMeshSlot", key)' in lua
          and 'part:SetAttribute("ArenaMeshState", "placeholder")' in lua
          and 'part:SetAttribute("ArenaPlaceholder", true)' in lua,
          "Platzhalter sind eindeutig markiert (Slot, Zustand, Platzhalter-Flag)")
    check("CreateMeshPartAsync" in lua and ":ApplyMesh(created)" in lua,
          "Geometrie kommt ueber CreateMeshPartAsync + ApplyMesh in die BESTEHENDE Instanz")
    check(re.search(r"\.MeshId\s*=\s*[^=]", lua) is None and "MeshContent" not in lua,
          "MeshId/MeshContent werden NIE direkt geschrieben (schreibgeschuetzt)")
    check("local savedSize = target.Size" in lua and "local savedCFrame = target.CFrame" in lua
          and "target:SetAttribute(\"ArenaPlaceholder\", false)" in lua,
          "Groesse/Position bleiben erhalten, das Platzhalter-Flag wird ehrlich entfernt")
    check("meshIdReadBack" in lua, "die Antwort nennt die zurueckgelesene MeshId")
    audit = region(source, "tools.model_audit = function(args)", "tools.world_audit = function(args)")
    check('part:GetAttribute("ArenaMeshSlot")' in audit and "meshSlotCount" in audit
          and "meshSlots" in audit,
          "model_audit meldet Mesh-Platzhalter getrennt")
    check("if isPlaceholder and meshKey == nil then" in audit,
          "Mesh-Platzhalter werden nicht als vergessene Platzhalter gezaehlt")
    report_start = source.index("            'report_done' {")
    # Der Fall endet mit der schliessenden Klammer auf gleicher Ebene; das
    # naechste Werkzeug im Handler ist 'clear_pending' (inline, VOR
    # Invoke-ServerTool) - deshalb hier die naechste 12er-Ebene als Grenze.
    report = source[report_start:report_start + 30000]
    check("MESH_UPLOAD_PENDING" in report and "$meshSlotCount -gt 0" in report,
          "report_done antwortet MESH_UPLOAD_PENDING, solange ein Mesh wartet")
    check("meshPlaceholders = $waitingKeys.ToArray()" in report,
          "die Meldung nennt die betroffenen Slots")
    check("meshSlotCount = $meshSlotCount" in source and "meshSlots = $meshSlots" in source,
          "Audit-Kennzahlen landen in AuditFlags (report_done liest sie)")

    # ------------------------------------------------------------------
    # 5) Fenster "Mesh-Uploads" (Fenster Nr. 3) und Menue
    # ------------------------------------------------------------------
    xaml = region(source, "function Get-MeshWindowXaml {", "function Get-MeshSlotStateText {")
    check("<!--ARENA_DIALOG_STYLES-->" in xaml,
          "das Fenster nutzt den gemeinsamen Design-Block (Anthrazit/Grau/Pink)")
    for name in ("TitleBar", "CloseButton", "BlenderBar", "InstallButton", "SkipButton",
                 "SlotList", "ApplyButton", "FolderButton", "RefreshButton", "StatusText"):
        check(f'x:Name="{name}"' in xaml, f"Fenster enthaelt {name}")
    open_win = region(source, "function Open-MeshWindow {",
                     "# ----------------------------------------------------------------------------\n# Tunnel (cloudflared)")
    check("ShowDialog" in open_win,
          "das Fenster ist modal wie die beiden anderen erlaubten Fenster")
    check("Show-Toast" not in open_win,
          "das Fenster nutzt KEINE Toasts")
    apply_handler = region(source, "$applyButton.Add_Click({", "$win.Add_Closed({")
    check("New-MeshBridgeCommand" in apply_handler and "'mesh_apply'" in apply_handler,
          "die Ids aus den Textfeldern werden als Befehl an Studio geschickt")
    check("Set-MeshSlotField $script:Shared $slotKey 'state' 'applying'" in apply_handler,
          "der Slot wird sofort als 'wird eingesetzt' markiert (kein falscher Erfolg)")
    check("Mesh-Uploads" in source and "Open-MeshWindow -SessionId" in source,
          "das Place-Menue oeffnet das Fenster")
    tick = region(source, "function Update-MeshTick {", "function Get-MeshWindowXaml {")
    check("Send-MeshPlaceholders" in tick and "Update-MeshRegistryFromApplyResult" in tick,
          "der UI-Takt legt Platzhalter an und verbucht die Einsetz-Ergebnisse")
    check("Get-MeshCommandOutcome" in tick and "TryRemove" in tick,
          "Ergebnisse interner Befehle werden abgeholt und aufgeraeumt (keine late results)")
    send = region(source, "function New-MeshBridgeCommand {", "function Get-MeshCommandOutcome {")
    check("ResultSignals" in send and "CommandPayloads" in send and "PendingCommands" in send,
          "interne Befehle laufen ueber denselben Queue-Weg wie Werkzeugaufrufe")
    check("MeshInternal" in send, "interne Befehle sind im Mesh-Takt auffindbar")

    if FAILURES:
        print(f"\nFEHLGESCHLAGEN: {len(FAILURES)} Pruefung(en) rot.")
        return 1
    print("\nOK: 7.4.0 Blender-/Mesh-Weg (Schritt 4, Messung, Platzhalter, Fenster, Gates) bestanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
