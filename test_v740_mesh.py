#!/usr/bin/env python3
"""Offline-Abnahme fuer den 7.4.1-Blender-/Mesh-Weg (ohne Windows/PowerShell).

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
VERSION = "7.4.1"
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
    check(metadata.get("version") == VERSION, "version.json ist 7.4.1")
    for phrase in ("7.4.0", "Blender", "MESH_UPLOAD_PENDING", "Mesh-Uploads",
                   "CreateMeshPartAsync"):
        check(phrase in notes, f"Release-Notiz nennt {phrase}")

    # ------------------------------------------------------------------
    # 0) BOM-Hotfix 7.4.1 (Live-Befund: "SyntaxError: invalid
    #    non-printable character U+FEFF" in check.py Zeile 1)
    #    PowerShell 5.1 schreibt Set-Content -Encoding UTF8 MIT BOM.
    # ------------------------------------------------------------------
    mesh_path = region(source, "# Version 7.4.0: BLENDER (Schritt 4 des Starts) + MESH-BAU",
                       "# Tunnel (cloudflared)")
    bom_writers = [line.strip() for line in mesh_path.splitlines()
                   if not line.strip().startswith("#")
                   and ("Set-Content" in line or "Out-File" in line or "-Encoding UTF8" in line)]
    check(not bom_writers,
          "kein Set-Content/Out-File/-Encoding UTF8 mehr auf dem Mesh-Pfad (BOM-Falle)")
    check(mesh_path.count("[System.IO.File]::WriteAllText(") >= 4,
          "die erzeugten Skript- und Statusdateien werden mit WriteAllText BOM-frei geschrieben")
    check("(New-Object System.Text.UTF8Encoding($false))" in mesh_path,
          "WriteAllText benutzt den UTF8-Encoder OHNE BOM")
    check('encoding="utf-8-sig"' in mesh_path and 'if source.startswith("\\ufeff")' in mesh_path
          and 'source = source[1:]' in mesh_path,
          "der Runner liest Modellskripte BOM-tolerant (utf-8-sig + \\ufeff-Strip)")
    job_write = region(source, "function Start-MeshJobWork {", "function Stop-MeshJob {")
    job_writers = [line.strip() for line in job_write.splitlines()
                   if not line.strip().startswith("#") and "Set-Content" in line]
    check(not job_writers and job_write.count("::WriteAllText(") >= 2,
          "Job-Runner UND Slot-Skript werden BOM-frei geschrieben (kein Set-Content)")

    # ------------------------------------------------------------------
    # 1) Schritt 4 (7.4.1): EIN Hintergrund-Runspace, EINE Hilfs-Quelle, EINE
    #    Probe, ready NUR nach bestandener Messung, kein Startblocker.
    #    7.4.0 fror hier ein (Suche+Version im UI-Thread) und meldete beim
    #    Nutzer state="ready" bei probe="failed".
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
    gate = region(source, "function Start-BlenderStartupGate {", "function Complete-BlenderStartupGate {")
    check("$script:BlenderGatePending = $true" in gate and "AddMinutes(12)" in gate,
          "der Blender-Schritt hat ein hartes Gesamt-Gate (12 min) und setzt den Warte-Zustand")
    check("Start-BlenderStepRunspace -Shared $script:Shared" in gate,
          "Suche + Version + Probe starten in EINEM Hintergrund-Runspace (kein Einfrieren)")
    complete = region(source, "function Complete-BlenderStartupGate {", "function Update-BlenderSplashRow {")
    check("Start-CloudflareTunnel" in complete and "$script:BlenderGatePending = $false" in complete,
          "der UI-Takt loest den Tunnel nach dem Schritt aus")
    refresh = region(source, "function Refresh-Ui {", "$line = $null")
    check("Complete-BlenderStartupGate" in refresh and "Update-BlenderSplashRow $null" in refresh
          and "Update-MeshTick" in refresh,
          "Refresh-Ui fuehrt Gate, Splash-Zeile und Mesh-Takt aus")
    splash = region(source, "function Update-BlenderSplashRow {",
                    "# ============================================================================\n# Version 7.4.0: MESH-BAU")
    for mode in ("'ready'", "'failed'", "'skipped'", "'installing'", "'searching'", "'probing'"):
        check(mode in splash, f"Zeile 4 kennt den Zustand {mode}")
    check("$SplashBlenderDot" in source and "$SplashBlenderState" in source,
          "Zeile 4 des Startbildschirms existiert (XAML + FindName)")
    click = region(source, "$SplashBlenderState = $window.FindName('SplashBlenderState')",
                   "$SplashTunnelDot    = $window.FindName('SplashTunnelDot')")
    check("Add_MouseLeftButtonUp" in click and "Start-BlenderRecheck" in click,
          '"Blender pruefen" (Zeile 4) startet die Pruefung neu')
    recheck = region(source, "    function Start-BlenderRecheck {", "    function Get-BlenderReport {")
    check("Start-BlenderStepRunspace" in recheck and "Install-BlenderPortableZip" not in recheck,
          '"Blender pruefen" startet denselben Runspace (echte Probe, kein reines Versionslesen)')
    check("'searching'" in recheck and "return $false" in recheck,
          "eine laufende Pruefung wird nicht doppelt gestartet")

    # EINE Hilfs-Quelle fuer Hauptprogramm UND Runspaces (7.4.0 hatte im
    # Runspace Phantom-Funktionen - die Probe scheiterte lautlos).
    tools = region(source, "$script:BridgeBlenderTools = {",
                   "try { . ([scriptblock]::Create([string]$script:BridgeBlenderTools)) }")
    for helper in ("Write-BridgeBomFreeFile", "Write-BridgeLog", "Set-BlenderState", "Get-BlenderPath",
                   "Invoke-BlenderProcess", "Test-BlenderQuick", "Get-BlenderDownloadCandidates",
                   "Test-BlenderZipHash", "Install-BlenderPortableZip", "Get-BlenderReport",
                   "Start-BlenderStepRunspace", "Start-BlenderRecheck"):
        check(f"function {helper}" in tools, f"die eine Hilfs-Quelle enthaelt {helper}")
    check(". ([scriptblock]::Create([string]$script:BridgeBlenderTools))" in source,
          "das Hauptprogramm laedt genau diese Quelle")
    check("BlenderToolsText = [string]$script:BridgeBlenderTools" in source,
          "die Quelle liegt in Shared fuer die Runspaces bereit")
    step = region(source, "$script:BridgeBlenderStepScript = {", "$script:BridgeBlenderProbeScript = {")
    check("BlenderToolsText" in step, "der Schritt-Runspace laedt genau diese Quelle (keine Phantom-Funktionen)")
    check("BlenderProbeScriptText" in step, "der Schritt-Runspace faehrt die EINE Probe")
    check("TotalSeconds -gt 180" in step, "Zeitlimit Suchen/Pruefen: 180 s")
    check("-State 'probing'" in step and "Install-BlenderPortableZip" in step,
          "auch der Installationsweg endet in der echten Probe")
    check("-State 'ready'" not in step and "portable" in step.lower(),
          "der Such-/Installationsweg setzt NIE selbst ready (portables ZIP, kein Admin)")

    # NUR EINE Probe; ready gibt es nur hier - nach bestandener Messung.
    probe = region(source, "$script:BridgeBlenderProbeScript = {",
                   "# ----------------------------------------------------------------------------\n# Der Mesh-Job-Worker")
    check("ARENA_MESH_STATS" in probe and "$marker.Length -ne 17" in probe,
          "die Probe prueft die Markerlaenge EXAKT (kein Zeichenversatz)")
    check("$markerIndex + $marker.Length" in probe and "$markerIndex + 18" not in source,
          "die Messzeile wird exakt hinter dem Marker gelesen")
    check("Write-BridgeBomFreeFile" in probe and "Write-BridgeLog" in probe,
          "die Probe schreibt BOM-frei UND protokolliert selbst in die runtime.log")
    check("$null -eq $stats" in probe and "-Probe 'failed'" in probe,
          "eine unlesbare Messzeile faellt GESCHLOSSEN durch (kein falscher Erfolg)")
    check(source.count("-State 'ready'") == 1 and "-State 'ready'" in probe,
          "ready setzt AUSSCHLIESSLICH die bestandene Faehigkeitsprobe")
    dead = [ln for ln in source.splitlines() if "Test-BlenderCapability" in ln and not ln.strip().startswith("#")]
    check(not dead, "die tote zweite Probe ist geloescht (0 Aufrufer)")
    check("BridgeBlenderInstallScript" not in source,
          "der alte Installer-Runspace ist im Schritt-Runspace aufgegangen")

    # blender-status.json: EINE Funktion, BOM-frei, Gate-Endstand sichtbar.
    state_fn = region(source, "    function Set-BlenderState {", "    function Get-BlenderExeInFolder {")
    check("BlenderStatusFile" in state_fn and "Write-BridgeBomFreeFile" in state_fn,
          "blender-status.json wird aus EINER Funktion BOM-frei geschrieben (auch aus Runspaces)")
    for field in ("state", "path", "version", "detail", "message", "percent", "source",
                  "enabled", "gateResolved", "probe"):
        check(field in state_fn, f"der Zustandsbericht enthaelt {field}")
    check("GateResolved $true" in source and "GateResolved $false" in source,
          "der Gate-Endstand wird ausdruecklich gesetzt (ready/failed zuerst)")
    failed_paths = probe.count("-State 'failed'")
    check(failed_paths >= 4, "jeder Fehlerweg der Probe endet ehrlich als failed (kein stiller Ausgang)")
    check("$state.Foreground = Get-Brush '#FF8AA0'" in splash,
          "failed wird in Zeile 4 ROT gemeldet")

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
    # 5) Automatisches Mesh-Fenster (7.4.1): neue Namen, alte Knoepfe weg,
    #    modellos per Show(), Auto-Oeffnen nur bei geaenderter Wartemenge,
    #    "Fertig" (nur Ziffern) mit Aufraeumen, "Stornieren" mit Rueckfrage.
    # ------------------------------------------------------------------
    xaml = region(source, "function Get-MeshWindowXaml {", "function Get-MeshSlotStateText {")
    check("<!--ARENA_DIALOG_STYLES-->" in xaml,
          "das Fenster nutzt den gemeinsamen Design-Block (Anthrazit/Grau/Pink)")
    check('WindowStyle="None"' in xaml and 'AllowsTransparency="True"' in xaml,
          "das Fenster ist randlos/transparent wie die uebrigen DIALOG-Fenster")
    for name in ("TitleBar", "PlaceNameText", "CloseButton", "FolderButton", "SlotList", "StatusText"):
        check(f'x:Name="{name}"' in xaml, f"Fenster enthaelt {name}")
    for gone in ("ApplyButton", "RefreshButton", "InstallButton", "SkipButton",
                 "BlenderBar", "BlenderText", "Blender jetzt installieren",
                 "Ids einsetzen", "Schritt überspringen", "Aktualisieren"):
        check(gone not in xaml, f"alter Fensterteil ist ENTFERNT: {gone}")
    check("Mesh-Uploads (Blender)" not in source and "$meshItem" not in source,
          "die Place-Liste hat KEINEN Mesh-Menueeintrag mehr")
    check("Open-MeshWindow -SessionId" not in source,
          "das Fenster wird nicht mehr aus dem Menue geoeffnet")
    open_win = region(source, "function Open-MeshWindow {",
                      "# ----------------------------------------------------------------------------\n# Tunnel (cloudflared)")
    check("ShowDialog(" not in open_win, "das Fenster ist MODELLOS (kein ShowDialog-Aufruf)")
    check("$win.Show() | Out-Null" in open_win, "das Fenster wird mit Show() angezeigt")
    check("Get-MeshWaitingSignature" in open_win and "$win.Add_Closed" in open_win,
          "beim Schliessen merkt sich die Bridge die Wartemenge (sortierte Slot-Keys)")
    auto = region(source, "function Update-MeshAutoWindow {", "function Open-MeshWindow {")
    check("MeshAutoClosedSignature" in auto and "signature -eq [string]$script:MeshAutoClosedSignature" in auto,
          "Auto-Oeffnen nur, wenn sich die Wartemenge geaendert hat (keine Schleife)")
    waiting = region(source, "function Get-MeshWaitingUploadKeys {", "function Get-MeshWaitingSignature {")
    check("MeshRegistry" in waiting and "'obj'" in waiting,
          "die Wartemenge kommt aus dem ECHTEN Register (state obj)")
    refresh = region(source, "function Refresh-Ui {", "$line = $null")
    check("Update-MeshTick" in refresh and "Update-MeshAutoWindow" in refresh
          and "Update-MeshWindow" in refresh,
          "der UI-Takt faehrt Mesh-Takt, offenes Fenster und Auto-Oeffnen")
    send = region(source, "function New-MeshBridgeCommand {", "function Get-MeshCommandOutcome {")
    check("ResultSignals" in send and "CommandPayloads" in send and "PendingCommands" in send,
          "interne Befehle laufen ueber denselben Queue-Weg wie Werkzeugaufrufe")
    check("MeshInternal" in send, "interne Befehle sind im Mesh-Takt auffindbar")
    row = region(source, "function New-MeshRow {", "function Update-MeshWindow {")
    for text in ("'Fertig'", "'Stornieren'", "'Ja, stornieren'", "'Abbrechen'", "Wirklich stornieren?"):
        check(text in row, f"die Zeile enthaelt {text}")
    check("ArenaTextField" in row and "ArenaPrimaryButton" in row and "ArenaDangerButton" in row,
          "die Zeile nutzt die geteilten Styles (Id-Feld, Fertig, Stornieren)")
    check("'Collapsed'" in row and "'Visible'" in row,
          "die Rueckfrage erscheint IN der Zeile (Aktionsknopfpaar wird ausgetauscht)")
    apply_fn = region(source, "function Invoke-MeshRowApply {", "function Invoke-MeshRowDrop {")
    check("notmatch '^\\d+$'" in apply_fn, '"Fertig" prueft die Id streng: NUR Ziffern')
    check("'applying'" in apply_fn and "'mesh_apply'" in apply_fn and "('apply:' + $jobId)" in apply_fn,
          '"Fertig" setzt applying und schickt den internen Befehl mesh_apply (Tag apply:<jobId>)')
    drop_fn = region(source, "function Invoke-MeshRowDrop {", "function Update-MeshWindow {")
    check("'dropping'" in drop_fn and "'mesh_drop'" in drop_fn and "('drop:' + $jobId)" in drop_fn,
          '"Stornieren" schickt den internen Befehl mesh_drop (Tag drop:<jobId>)')
    check("NICHT wiederhergestellt" in drop_fn or "NICHT zurueck" in drop_fn,
          'die Rueckfrage/Statuszeile sagt ehrlich, dass ein eingesetztes Mesh nicht zurueckkommt')
    tick = region(source, "function Update-MeshTick {", "function Get-MeshWindowPlaceLabel {")
    check("Send-MeshPlaceholders" in tick and "Update-MeshRegistryFromApplyResult" in tick,
          "der UI-Takt legt Platzhalter an und verbucht die Einsetz-Ergebnisse")
    check("'drop:'" in tick and "Update-MeshRegistryFromDropResult" in tick,
          "der UI-Takt verbucht auch die Stornieren-Ergebnisse (done/error)")
    check("Remove-MeshAppliedFileSets" in tick and "Eingesetzte Mesh-Dateien geloescht" in tick,
          'nach "Fertig" raeumt der Takt Dateien auf und protokolliert das wortgleich')
    check("apply_failed" in tick and "drop_failed" in tick,
          "Fehlschlaege werden ehrlich als apply_failed/drop_failed gesetzt")
    check("Mesh-Slot storniert" in tick, 'das Stornieren wird als "Mesh-Slot storniert" protokolliert')
    cleanup = region(source, "function Remove-MeshSlotFiles {", "function Remove-MeshAppliedFileSets {")
    check("MeshRegistry.TryRemove" in cleanup and "Remove-Item -LiteralPath $folder -Recurse" in cleanup,
          "aufraeumen: Slot + Dateien; der Job-Ordner nur, wenn nichts mehr wartet")
    check("'obj', 'applying', 'dropping'" in cleanup,
          "der Ordner bleibt stehen, solange noch ein Slot wartet (weniger Datenmuell, kein Verlust)")
    check("MeshSlotsBySession" in source and "placeholder" in source.lower(),
          "Register/Platzhalter bleiben die Quelle (nichts wird behauptet)")

    # ------------------------------------------------------------------
    # 6) mesh_drop: Lua-Werkzeug + Registrierung als schreibendes Werkzeug
    # ------------------------------------------------------------------
    lua_drop = region(source, "tools.mesh_drop = function(args)", "tools.get_output = function(args)")
    check('inst:IsA("MeshPart") and inst:GetAttribute("ArenaMeshSlot") == key' in lua_drop,
          "mesh_drop loescht genau die MeshParts mit ArenaMeshSlot = key")
    check("inst:Destroy()" in lua_drop and "hadAppliedMesh" in lua_drop,
          "mesh_drop entfernt die Instanz und meldet, ob schon ein Mesh eingesetzt war")
    check("NICHT wiederhergestellt" in lua_drop,
          "mesh_drop sagt im note ehrlich, dass ein eingesetztes Mesh nicht zurueckkommt")
    check("mesh_drop = true" in region(source, "local PERSISTENT_WRITE_TOOLS = {", "local WRITE_TOOLS = {}"),
          "mesh_drop ist in PERSISTENT_WRITE_TOOLS registriert (Testmodus-Schutz)")
    check("'mesh_drop'" in region(source, "    function Get-ActivityToolSets {", "    function Get-ArenaActivityText"),
          "mesh_drop steht in der writeTools-Liste")
    check("name = 'mesh_drop'" in region(source, "# ---------------- MESH / BLENDER", "# ---------------- JOBS ----------------"),
          "mesh_drop hat einen Doku-Eintrag (Kategorie mesh)")
    check("mesh_drop = 'Hat einen Mesh-Slot storniert" in source,
          "mesh_drop hat einen Aktivitaetstext fuer die Place-Zeile")

    if FAILURES:
        print(f"\nFEHLGESCHLAGEN: {len(FAILURES)} Pruefung(en) rot.")
        return 1
    print("\nOK: 7.4.1 Blender-/Mesh-Weg (Schritt 4, Messung, Platzhalter, Fenster, Gates) bestanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
