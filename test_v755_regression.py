#!/usr/bin/env python3
"""Offline-Regressionstest fuer Arena Roblox Bridge 7.5.9 (ohne Studio, ohne Windows).

Was 7.5.9 prueft (und weiterhin die 7.5.5-Regressionswaechter):

1. /api/tool lieferte HTTP 500 fuer JEDEN Werkzeugaufruf ("Die Benennung "=" wurde
   nicht als Name eines Cmdlet erkannt"). Ursache: in Get-ArenaActivityText fehlte
   bei der Hashtable $texts das Zuweisungszeichen. Geprueft werden: die Hashtable
   ist vollstaendig und eindeutig, und kein Befehl der Datei beginnt mit einem
   Operator (tree-sitter, command_name-Knoten).
2. describe_orientation (Studio-Plugin) crashte: dirHeading indizierte die
   Himmelsrichtungen falsch ("invalid argument #2 to 'format'"). Geprueft wird
   dirHeading in Lua (lupa) ueber alle Winkel, mit Luau-artiger %s-Strenge.
3. /api/tools/parallel reichte Bridge-eigene Werkzeuge an das Studio-Plugin weiter,
   das sie nicht kennt. Geprueft wird die Umleitung ueber Invoke-ServerTool mit
   Reihenfolge der Antworten.
4. BLENDER-FIRST: build_polygon_model nur mit userRequestedPolygon=true; ohne das
   blockt die Bridge (POLYGON_BLENDER_FIRST). Mit dem Flag warnt das Plugin ab 300
   WedgeParts vor Lag und empfiehlt Blender.
5. OPEN CLOUD: StudioService:GetUserId() wird gemeldet, gespeichert und vor der
   Key-Resource als creator.userId verwendet. Die manuelle Fallback-Textbox ist weg.
6. Die Bridge zeigt Avatar und Anzeigename im Footer; Profil/Thumbnail laden
   asynchron ohne UI-Blockade.
7. Das eingebettete Studio-Plugin (Lua) muss kompilieren.

Abhaengigkeiten: tree_sitter, tree_sitter_powershell, lupa (siehe requirements-test.txt).
"""

from __future__ import annotations

import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "ArenaBridge.ps1"
VERSION = "7.6.1"
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("[GRUEN] " if condition else "[ROT]   ") + message)
    if not condition:
        FAILURES.append(message)


def region(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    stop = source.index(end, begin)
    return source[begin:stop]


def load_source() -> tuple[bytes, str]:
    raw = PS1.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf"), "ArenaBridge.ps1 muss mit UTF-8-BOM beginnen"
    assert b"\r\n" not in raw, "ArenaBridge.ps1 darf keine CRLF-Zeilenenden haben"
    return raw, raw.decode("utf-8-sig")


def plugin_lua(source: str) -> str:
    match = re.search(r"function Get-PluginSource \{\n@'\n(.*?)\n'@", source, re.S)
    assert match, "Get-PluginSource-Here-String nicht gefunden"
    return match.group(1)


# ----------------------------------------------------------------------
# 1) /api/tool-500: $texts und Operator-Befehle
# ----------------------------------------------------------------------
def check_texts_and_commands(raw: bytes, source: str) -> None:
    from tree_sitter import Language, Parser
    import tree_sitter_powershell as tsp

    lines = source.split("\n")
    starts = [i for i, line in enumerate(lines) if line == "        $texts = @{"]
    check(len(starts) == 1, "Hashtable $texts ist genau einmal vorhanden (Ursache des /api/tool-500)")
    if len(starts) == 1:
        start = starts[0]
        end = next(i for i in range(start + 1, len(lines)) if lines[i] == "        }")
        keys: list[str] = []
        malformed: list[str] = []
        for line in lines[start + 1:end]:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*'", stripped)
            if match:
                keys.append(match.group(1))
            else:
                malformed.append(stripped[:60])
        check(not malformed, f"jede Zeile in $texts ist ein Schluessel = 'Satz' (Fehler: {malformed[:3]})")
        check(len(keys) == 145, f"$texts enthaelt genau 145 Aktions-Texte (gezaehlt: {len(keys)})")
        check(len(keys) == len(set(keys)), "$texts hat keine doppelten Schluessel")
        # PowerShell-Hashtables vergleichen Schluessel OHNE Gross-/Kleinschreibung.
        check(len({k.lower() for k in keys}) == len(keys), "$texts hat keine Schluessel, die sich nur in Gross-/Kleinschreibung unterscheiden")
        docs = region(source, "function Get-ToolDocs {", "function Get-BridgeGuides {")
        catalog = re.findall(r"\$t\.Add\(\@\{\s*name\s*=\s*'([a-z][a-z0-9_]*)'", docs)
        check(len(catalog) == 145, f"Werkzeugkatalog enthaelt 145 Aktionen (gezaehlt: {len(catalog)})")
        check(set(keys) == set(catalog), f"$texts deckt exakt den Werkzeugkatalog ab (fehlend: {sorted(set(catalog)-set(keys))}, extra: {sorted(set(keys)-set(catalog))})")

    # Die Operator-Pruefung laeuft IMMER (auch wenn $texts fehlt): sie ist der eigentliche Schutz.
    tree = Parser(Language(tsp.language())).parse(raw)
    operators = {"=", "+=", "-=", "*=", "/=", "%=", "-eq", "-ne", "-and", "-or", "-f",
                 "-lt", "-gt", "-like", "-match", "-contains", "-not"}
    found: list[tuple[int, str]] = []

    def walk(node) -> None:
        if node.type == "command_name":
            text = raw[node.start_byte:node.end_byte].decode("utf-8", "replace").strip()
            if text.lower() in operators:
                found.append((raw.count(b"\n", 0, node.start_byte) + 1, text))
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    check(not found, f"kein Befehl beginnt mit einem Operator (gefunden: {found[:5]})")


# ----------------------------------------------------------------------
# 2) Activity copy and Arena-Verlauf progress UI
# ----------------------------------------------------------------------
def check_activity_history_progress(source: str) -> None:
    activity = region(source, "function Get-ArenaActivityText", "function Get-ArenaActivityKind")
    tool_texts = re.findall(r"^\s{12}([A-Za-z_][A-Za-z0-9_]*)\s*=\s*'([^']*)'", activity, re.M)
    tool_texts = [(key, text) for key, text in tool_texts if key not in {"read", "running"}]
    check(len(tool_texts) == 145 and len({key for key, _ in tool_texts}) == 145,
          f"alle 145 Toolschluessel besitzen genau einen festen deutschen Text (gezaehlt: {len(tool_texts)})")
    texts = "\n".join(text for _, text in tool_texts).casefold()
    check("ein objekt" not in texts and "tool_hier" not in texts and "hat tool" not in texts,
          "keine generischen Objekt-/TOOL-Platzhalter im deutschen Aktionskatalog")
    check("$tool +" not in activity and "+ $tool" not in activity,
          "unbekannte Aktionen werden nicht mit dem rohen Tool-Schluessel angezeigt")

    search = region(source, "function Get-ActivitySearchDescription", "function Add-ActivityDetailPart")
    check("@('query','name')" in search and "@('className','class')" in search and "@('tag')" in search,
          "Explorer-Suche benennt Suchbegriff, Klasse und Tag statt eines generischen Objekts")
    check("Get-ActivitySearchDescription $args $false" in activity
          and "@('rootRef')" in activity and "exakte Namen" in activity,
          "Explorer-Verlauf enthaelt Suchbereich und exakte/Teiltreffer-Art")
    check("Get-ActivityActionDetailText" in activity
          and "Get-ResultNumber" in activity
          and "Get-ActivityArgument" in activity,
          "Verlaufstexte koennen echte Argumente und Ergebniszahlen aufnehmen")

    labels_match = re.search(r"ActivityToolLabels = @\{(.*?)^    \}", source, re.S | re.M)
    labels = re.findall(r"^\s{8}([A-Za-z_][A-Za-z0-9_]*)\s*=\s*'([^']*)'", labels_match.group(1), re.M) if labels_match else []
    check(len(labels) == 145 and len({key for key, _ in labels}) == 145,
          f"Fortschrittsanzeige hat 145 verstaendliche Aktionsnamen (gezaehlt: {len(labels)})")
    check("function Get-ArenaActivityDisplayLabel" in source
          and "return 'Bridge-Aktion'" in source,
          "Fortschrittsanzeige faellt bei unbekannten Tools auf einen freundlichen Namen zurueck")

    progress = region(source, "function Get-ArenaHistoryProgressTargets", "function Add-ArenaHistoryCard {")
    window = region(source, "function Open-ArenaHistoryWindow {", "function Copy-Prompt {")
    history_update = region(source, "function Update-ArenaHistoryWindow {", "function New-HistoryButton {")
    card = region(source, "function Add-ArenaHistoryCard {", "function Update-ArenaHistoryWindow {")
    place_progress = region(source, "function Update-PlaceProgressVisual {", "function Get-ProgressDiagnoseLines {")
    check("ProgressBar" in progress and "PercentKnown" in progress and "0 %" in progress,
          "Verlaufsfenster zeichnet einen ehrlichen Balken samt Prozentstatus")
    check("ProgressHost" in window and "ProgressScroll" in window and "ProgressCards=@{}" in window,
          "Arena-Verlauf besitzt einen separaten, je Place aktualisierten Fortschrittsbereich")
    check("Update-ArenaHistoryProgress $State $entries" in history_update,
          "Fortschritt aktualisiert sich unabhaengig von neuen Verlaufskarten")
    check("$main.FontSize=14" in card and "$main.TextWrapping='Wrap'" in card,
          "Aktionskarten sind groesser und umbrechen lesbar")
    check("Get-ArenaActivityDisplayLabel" in place_progress
          and "Get-PendingCommandStatusLabel" in place_progress
          and "[string]$openCmd.tool + ' - ' + $status" not in place_progress,
          "Place-Fortschritt zeigt deutsche Toolnamen statt rohe Werkzeug-Schluessel")
    check("$progressText.FontSize = 13" in source
          and "$progressText.TextWrapping = 'Wrap'" in source
          and "$progressRow.Orientation = 'Vertical'" in source,
          "Place-Status unter dem Namen ist groesser, mehrzeilig und zeigt den Balken darunter")


# ----------------------------------------------------------------------
# 3) describe_orientation: dirHeading in Lua (lupa)
# ----------------------------------------------------------------------
HARNESS = r'''
local realFormat = string.format
string.format = function(fmt, ...)
  local args = table.pack(...)
  local i = 0
  for spec in string.gmatch(fmt, "%%.-([a-zA-Z%%])") do
    if spec ~= "%" then
      i = i + 1
      if spec == "s" and type(args[i]) ~= "string" then
        error("invalid argument #" .. (i + 1) .. " to 'format' (string expected, got " .. type(args[i]) .. ")", 0)
      end
    end
  end
  return realFormat(fmt, ...)
end
local V = {}
V.__index = V
local function vec(x, y, z)
  return setmetatable({X = x, Y = y, Z = z, Magnitude = math.sqrt(x*x + y*y + z*z)}, V)
end
Vector3 = { new = vec }
math.atan2 = function(y, x) return math.atan(y, x) end
'''


def check_dir_heading(source: str) -> None:
    try:
        from lupa import LuaRuntime
    except ImportError:
        check(False, "lupa ist installiert (pip install lupa, siehe requirements-test.txt)")
        return
    lua_src = plugin_lua(source)
    start = lua_src.index("local function dirHeading(v)")
    end = lua_src.index("\nend\n", start) + len("\nend\n")
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(HARNESS)
    lua.execute(lua_src[start:end] + "\n__dh = dirHeading\n")
    dir_heading = lua.eval("__dh")
    make = lua.eval("function(x, y, z) return Vector3.new(x, y, z) end")

    failures = []
    for deg in list(range(0, 360)) + [0.0001, 22.4, 22.5, 359.9, 359.99]:
        rad = math.radians(deg)
        try:
            dir_heading(make(math.sin(rad), 0.0, -math.cos(rad)))
        except Exception as error:  # noqa: BLE001 - jede Lua-Ausnahme ist ein Fehler
            failures.append((deg, str(error)[:100]))
    check(not failures, f"dirHeading wirft fuer keinen Winkel 0-359 Grad einen Fehler (Fehler: {failures[:3]})")

    expected = {
        0: "north (away",
        30: "north-east",
        90: "east (toward +X)",
        180: "south (toward",
        270: "west (toward -X)",
        350: "north (away",
    }
    for deg, prefix in expected.items():
        rad = math.radians(deg)
        try:
            text = str(dir_heading(make(math.sin(rad), 0.0, -math.cos(rad))))
        except Exception as error:  # noqa: BLE001
            check(False, f"dirHeading({deg}) laeuft durch (Lua-Fehler: {str(error)[:80]})")
            continue
        check(text.startswith(prefix), f"dirHeading({deg}) beginnt mit '{prefix}' (Ist: {text[:40]})")


# ----------------------------------------------------------------------
# 4) /api/tools/parallel: Bridge-Werkzeuge ueber Invoke-ServerTool
# ----------------------------------------------------------------------
def check_parallel_routing(source: str) -> None:
    block = region(source, "if ($path -eq '/api/tools/parallel') {", "if ($path -eq '/api/tool') {")
    check("$serverOut = Invoke-ServerTool $sessionId $callTool $callArgs" in block,
          "/api/tools/parallel fragt jeden Aufruf zuerst bei Invoke-ServerTool an")
    check("$pluginCalls.Add($call)" in block and "Invoke-PluginToolsParallel $sessionId $pluginCalls.ToArray()" in block,
          "nur Aufrufe, die die Bridge nicht selbst bedient, gehen ans Studio-Plugin")
    check(block.index("Invoke-ServerTool $sessionId $callTool $callArgs")
          < block.index("Invoke-PluginToolsParallel $sessionId $pluginCalls.ToArray()"),
          "Serverwerkzeuge werden vor dem Plugin-Aufruf ausgefuehrt")
    check("for ($pos = 0; $pos -lt $callPosition; $pos++)" in block and "$serverParts.ContainsKey($pos)" in block,
          "Antworten werden in der Reihenfolge der calls zusammengefuehrt")
    check("Get-OrganicBuildGuardResult $candidateTool $candidateArgs -ParallelCall" in block,
          "das Organik-/Polygon-Gate gilt auch fuer /api/tools/parallel")
    check("Complete-ArenaActivity $sessionId $serverActivity $callTool $callArgs $serverJson" in block,
          "Serverwerkzeuge in parallel schreiben ihre Aktivitaet ins Protokoll")


# ----------------------------------------------------------------------
# 5) Blender-first: build_polygon_model nur auf ausdruecklichen Wunsch
# ----------------------------------------------------------------------
def check_blender_first(source: str) -> None:
    check("function Test-PolygonBuildWithoutRequest" in source,
          "Gate Test-PolygonBuildWithoutRequest ist definiert")
    guard_start = source.index("function Get-OrganicBuildGuardResult")
    guard_block = source[guard_start:guard_start + 2000]
    check("if (Test-PolygonBuildWithoutRequest $tool $toolArgs) {" in guard_block,
          "Get-OrganicBuildGuardResult blockt Polygon-Bau ohne userRequestedPolygon")
    check("POLYGON_BLENDER_FIRST" in source, "Fehlercode POLYGON_BLENDER_FIRST ist vorhanden")
    check("userRequestedPolygon=@{type='bool'" in source,
          "build_polygon_model fuehrt den Parameter userRequestedPolygon im Katalog")
    lua = plugin_lua(source)
    check("wedgeCount>=300" in lua and "LAG-WARNUNG (7.5.5)" in lua,
          "das Plugin warnt ab 300 WedgeParts vor Lag und empfiehlt Blender")
    guides = source[source.index("function Get-BridgeGuides"):source.index("function Get-SessionStartPackage")]
    check("BLENDER-FIRST (Version 7.5.5)" in guides,
          "die Leitregeln sagen Blender-first (Version 7.5.5)")
    check("polygonPreference = 'BLENDER-FIRST (Version 7.5.5)" in guides,
          "modelBuildRules.polygonPreference ist Blender-first")
    check("GLOBALER 3D-BAUSTANDARD" not in guides,
          "der alte Polygon-Standard ('GLOBALER 3D-BAUSTANDARD') steht nicht mehr in den Leitregeln")


# ----------------------------------------------------------------------
# 6) Open Cloud: Studio-Login ist der Upload-Ersteller, kein manuelles Feld
# ----------------------------------------------------------------------
def check_open_cloud(source: str) -> None:
    resolver = region(source, "function Resolve-OpenCloudCreatorForUpload {", "function Invoke-OpenCloudUpload {")
    studio_pos = resolver.find("Get-OpenCloudStudioDeveloper -SessionId $SessionId")
    key_pos = resolver.find("Resolve-OpenCloudCreatorFromKey -Shared $Shared")
    early_return_pos = resolver.find("if ($null -ne $studio) { return $studio }")
    check(studio_pos >= 0 and key_pos >= 0 and early_return_pos >= 0
          and studio_pos < key_pos and early_return_pos < key_pos,
          "Upload-Reihenfolge: angemeldeter Studio-Nutzer zuerst, Key-Resource nur als Rueckfall")
    check("return $fromKey" in resolver,
          "wenn Studio keine ID liefert, bleibt der automatische Key-Introspect-Rueckfall")

    studio = region(source, "function Get-OpenCloudStudioDeveloper {", "function Resolve-OpenCloudCreatorForUpload {")
    check("Get-SessionEntry $SessionId" in studio and "$entry.editorUserId" in studio,
          "die Upload-ID kommt aus editorUserId der verbundenen Sitzung (nicht game.CreatorId)")
    check("creatorKind = 'user'" in studio and "-notmatch '^\\d+$'" in studio,
          "nur eine gueltige numerische Studio-User-ID wird als user creator verwendet")

    upload_start = source.index("function Invoke-OpenCloudUpload {")
    upload_head = source[upload_start:upload_start + 1200]
    check("[string]$SessionId = ''" in upload_head,
          "Invoke-OpenCloudUpload bekommt die Sitzung (SessionId)")
    check("Invoke-OpenCloudUpload -Shared $Shared -SessionId $sessionId" in source,
          "der Aufrufer reicht die Sitzung weiter")
    check("$creatorFound = Resolve-OpenCloudCreatorForUpload -Shared $Shared -SessionId $SessionId" in source,
          "jeder Upload ermittelt den aktuellen Creator aus der Sitzung")
    check("$creator['userId'] = [string]$config.creatorId" in source,
          "die Studio-ID landet als creationContext.creator.userId in Open Cloud")

    lua = plugin_lua(source)
    state_payload = region(lua, "local function statePayload()", "local function handshake()")
    check("StudioService:GetUserId()" in state_payload
          and 'payload.editorUserId = "0"' in state_payload
          and "payload.editorUserId = tostring(math.floor(signedInUserId))" in state_payload,
          "das Studio-Plugin meldet GetUserId() (0 = nicht angemeldet) getrennt vom Place-Creator")
    check("payload.creatorId = tostring(game.CreatorId)" in state_payload
          and "payload.creatorType = game.CreatorType.Name" in state_payload,
          "der Eigentumer des Places bleibt als getrennte Information erhalten")
    check(source.count("editorUserId = [string]$body.editorUserId") >= 3,
          "alle drei Session-Registrierungspfade speichern die Studio-ID")
    check("$newEditorUserId = [string]$body.editorUserId" in source
          and "editorUserId  = $newEditorUserId" in source,
          "Session-Updates uebernehmen/loeschen die aktuelle ID (0 = abgemeldet)")

    obsolete = ("openCloudDeveloperId", "openCloudDeveloperName", "Resolve-OpenCloudDeveloperName",
                "CloudDeveloperBox", "CloudDeveloperButton", "CloudDeveloperPanel", "CloudDeveloperStatus")
    for marker in obsolete:
        check(marker not in source, f"manueller Entwickler-Fallback entfernt: {marker}")


def check_studio_profile_ui(source: str) -> None:
    for marker in ("x:Name=\"StudioEditorProfile\"", "x:Name=\"StudioEditorAvatarImage\"",
                   "x:Name=\"StudioEditorNameText\"", "StudioEditorCaptionText"):
        check(marker in source, f"Footer-Profilkarte enthaelt {marker}")
    check('x:Name="StudioEditorProfile" Orientation="Horizontal" HorizontalAlignment="Left"' in source,
          "die Studio-Profilkarte bleibt unten links im Footer")
    check('x:Name="ArenaAiButton" Width="178" Height="40" HorizontalAlignment="Right"' in source
          and 'Text="Arena AI öffnen"' in source,
          "der bestehende Arena-AI-Button bleibt unten rechts erhalten")
    check("https://users.roblox.com/v1/users/" in source
          and "https://thumbnails.roblox.com/v1/users/avatar-headshot" in source,
          "Anzeigename und Roblox-Headshot werden ueber die offiziellen oeffentlichen Endpunkte geladen")
    check("function Start-StudioProfileLookup" in source and ".BeginInvoke()" in source
          and ".EndInvoke($lookup.Handle)" in source,
          "Profilabfrage laeuft in einem Hintergrund-Runspace und wird erst fertig ausgewertet")
    check("-TimeoutSec 10" in source and "$request.Timeout = 10000" in source,
          "Profil- und Avatar-Netzwerkzugriffe haben Zeitlimits")
    check("Update-StudioEditorProfile $activeStudios" in source
          and "editorUserId" in source[source.index("function Update-StudioEditorProfile"):source.index("function Refresh-Ui {")],
          "der UI-Takt zeigt das Profil der aktuell verbundenen Studio-Anmeldung")
    check("$StudioEditorProfile.Visibility = 'Collapsed'" in source,
          "ohne angemeldeten Studio-Nutzer bleibt die Profilkarte verborgen")


# ----------------------------------------------------------------------
# 7) Studio-Plugin kompiliert
# ----------------------------------------------------------------------
def check_plugin_compiles(source: str) -> None:
    from lupa import LuaRuntime

    lua = LuaRuntime(unpack_returned_tuples=True)
    chunk = lua.eval("function(s) return load(s) end")(plugin_lua(source))
    check(chunk is not None and callable(chunk), "das eingebettete Studio-Plugin (Lua) kompiliert")


# ----------------------------------------------------------------------
# Versionen
# ----------------------------------------------------------------------
def check_versions(source: str) -> None:
    import json

    data = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    check(data.get("version") == VERSION, f"version.json steht auf {VERSION}")
    check(str(data.get("notes", [""])[0]).startswith(f"• {VERSION}"),
          f"version.json: die erste Neuigkeit ist die {VERSION}-Notiz")
    check(f"# Arena Roblox Bridge  -  Version {VERSION}" in source,
          f"Kopfzeile von ArenaBridge.ps1 nennt {VERSION}")


def run_group(name: str, function, *args) -> None:
    # Jede Pruefgruppe laeuft fuer sich: eine Ausnahme macht nur diese Gruppe rot.
    try:
        function(*args)
    except Exception as error:  # noqa: BLE001
        check(False, f"{name}: Ausnahme {type(error).__name__}: {str(error)[:120]}")


def main() -> int:
    raw, source = load_source()
    run_group("texts/Befehle", check_texts_and_commands, raw, source)
    run_group("Aktivitäten/Verlauf", check_activity_history_progress, source)
    run_group("dirHeading", check_dir_heading, source)
    run_group("parallel", check_parallel_routing, source)
    run_group("Blender-first", check_blender_first, source)
    run_group("Open Cloud", check_open_cloud, source)
    run_group("Studio-Profil UI", check_studio_profile_ui, source)
    run_group("Plugin", check_plugin_compiles, source)
    run_group("Versionen", check_versions, source)

    if FAILURES:
        print(f"\nFEHLGESCHLAGEN: {len(FAILURES)} Pruefung(en) rot.")
        for item in FAILURES:
            print("  - " + item)
        return 1
    print(f"\nOK: 7.5.9 Regressionstest bestanden (145 Tooltexte, Verlauf/Fortschritt, describe_orientation, "
          f"/api/tools/parallel, Blender-first, Studio-Identitaet, Profilkarte, Plugin-Kompilierung).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
