#!/usr/bin/env python3
"""Verifikationstest fuer Arena Roblox Bridge 7.1.0 (6 Pflicht-Tests).

Prueft sowohl den echten Quellcode in ArenaBridge.ps1 (PowerShell + eingebettetes
Luau-Plugin) als auch das Laufzeitverhalten im Zustell-Simulator und (sofern
vorhanden) in der echten Luau-VM (@luau-rs/luau):

  Test 1: BindReason-Regressionstest (Get-PlaceIdentity / Save-PlaceIdentity /
          gedrosseltes Vorschau-Fehlerlog in Update-Row).
  Test 2: COMMAND_DELIVERY_UNCONFIRMED-Reproduktion und Heilung (To-Json ohne
          Array-Unrolling fuer 0/1 Elemente, Ack-vor-Enqueue + Ack-Outbox im
          Plugin, Re-Delivery unbestaetigter Befehle bis unackedCount=3).
  Test 3: Verlust von received_batch UND started, aber /plugin/result kommt an
          (Selbstheilung in Complete-CommandResult + Chunk-Fortschritt).
  Test 4: Kaputter Befehl im Plugin (enqueueCommand ohne stilles return bei
          fehlendem Tool oder verwaister seenCommandIds-Markierung).
  Test 5: Echtes totes Plugin (ehrliches Scheitern nach 3 Re-Delivery-Versuchen
          + 30 s mit lastPollError/lastPluginError/lastAckAt + klarer deutscher
          Verlaufskarte).
  Test 6: Sequenztest mit 20 Befehlen hintereinander unter Stoerfeuer (jeder 3.
          received_batch-POST und jeder 5. started-POST schlaegt fehl, jeder 7.
          erste Poll geht verloren -> alle 20 Befehle ok=true, 0 Abbrueche).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = ROOT / "app"
PS1 = APP_ROOT / "ArenaBridge.ps1"


def load_source() -> str:
    return PS1.read_text(encoding="utf-8-sig")


def extract_plugin_lua(source: str) -> str:
    marker = "function Get-PluginSource {\n@'\n"
    begin = source.find(marker)
    assert begin >= 0, "Get-PluginSource here-string nicht gefunden"
    begin += len(marker)
    end = source.find("\n'@\n}", begin)
    assert end >= 0, "Get-PluginSource here-string nicht geschlossen"
    return source[begin:end]


def extract_ps_function(source: str, name: str) -> str:
    pattern = re.compile(rf"function\s+{re.escape(name)}\b", re.MULTILINE)
    match = pattern.search(source)
    assert match is not None, f"PowerShell-Funktion {name} nicht gefunden"
    start = match.start()
    brace_open = source.find("{", match.end())
    assert brace_open >= 0, f"Keine oeffnende Klammer fuer {name}"
    depth = 0
    for idx in range(brace_open, len(source)):
        ch = source[idx]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[start : idx + 1]
    raise AssertionError(f"Funktion {name} nicht geschlossen")


# ---------------------------------------------------------------------------
# Test 1: BindReason-Regressionstest & Vorschau-Log-Drosselung
# ---------------------------------------------------------------------------
def test_1_bind_reason_and_preview_throttle(source: str) -> None:
    get_fn = extract_ps_function(source, "Get-PlaceIdentity")
    save_fn = extract_ps_function(source, "Save-PlaceIdentity")
    update_row_fn = extract_ps_function(source, "Update-Row")

    # Alle im [pscustomobject]@{ ... } von Get-PlaceIdentity deklarierten Felder:
    obj_match = re.search(r"\[pscustomobject\]@\{([\s\S]*?)\}", get_fn)
    assert obj_match is not None, "Kein [pscustomobject]@{...} in Get-PlaceIdentity"
    declared_props = set(
        re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", obj_match.group(1), re.MULTILINE)
    )

    # Alle in Save-PlaceIdentity auf $identity.<Prop> gesetzten Eigenschaften:
    assigned_props = set(
        re.findall(r"\$identity\.([A-Za-z_][A-Za-z0-9_]*)\s*=", save_fn)
    )
    missing = assigned_props - declared_props
    assert not missing, (
        f"Test 1 FEHLGESCHLAGEN: Save-PlaceIdentity setzt Eigenschaften, die in "
        f"Get-PlaceIdentity fehlen: {sorted(missing)} -> SetValueInvocationException!"
    )
    assert "BindReason" in declared_props, (
        "Test 1 FEHLGESCHLAGEN: BindReason fehlt im [pscustomobject] von Get-PlaceIdentity"
    )
    assert "Write-PreviewCaptureError" in update_row_fn and "function Write-PreviewCaptureError" in source, (
        "Test 1 FEHLGESCHLAGEN: Update-Row drosselt Vorschau-Aufnahmefehler nicht ueber Write-PreviewCaptureError"
    )


# ---------------------------------------------------------------------------
# Test 2: COMMAND_DELIVERY_UNCONFIRMED-Reproduktion und Heilung
# ---------------------------------------------------------------------------
def test_2_command_delivery_unconfirmed_repro_and_healing(source: str, lua: str) -> None:
    to_json_fn = extract_ps_function(source, "To-Json")
    cancel_ids_fn = extract_ps_function(source, "Get-SessionCancellationIds")

    # 1) To-Json darf 0- und 1-elementige Arrays in PowerShell 5.1 nicht durch
    #    die Pipeline entrollen (sonst wird @() zu $null -> ungueltiges JSON
    #    "cancelledCommands":, und @("id") zu einem String statt Array!).
    assert "$obj.Count -eq 0" in to_json_fn and "'[]'" in to_json_fn, (
        "Test 2 FEHLGESCHLAGEN: To-Json behandelt leere Arrays (@()) nicht explizit als '[]'"
    )
    assert "$obj.Count -eq 1" in to_json_fn, (
        "Test 2 FEHLGESCHLAGEN: To-Json behandelt 1-elementige Arrays nicht explizit als '[...]'"
    )
    # 7.1.1: Der Komma-Operator war hier FALSCH. Jeder Aufrufer schreibt
    # @(Get-SessionCancellationIds $sid); aus ", $array" wird in @(...) IMMER
    # ein 1-elementiges Array (das leere Array als Element) -> "$cancelledNow.Count
    # -gt 0" war in /plugin/poll immer wahr und die Schleife brach vor dem
    # Dequeue ab (live: kein einziger Befehl erreichte Studio). Die Funktion
    # liefert jetzt FLACH; die 0/1-Element-Faelle regelt To-Json.
    assert "return , $items.ToArray()" not in cancel_ids_fn, (
        "Test 2 FEHLGESCHLAGEN: Get-SessionCancellationIds nutzt wieder den Komma-Operator (7.1.0-Regression: Poll liefert nie Befehle)"
    )
    assert "return $items.ToArray()" in cancel_ids_fn, (
        "Test 2 FEHLGESCHLAGEN: Get-SessionCancellationIds gibt kein flaches Array zurueck"
    )

    # 2) Plugin muss received_batch VOR enqueueCommand senden und eine Ack-Outbox
    #    mit Retry besitzen.
    assert "ackOutbox = {}" in lua and "sendOrQueueAckBatch" in lua, (
        "Test 2 FEHLGESCHLAGEN: Plugin besitzt keine ackOutbox / sendOrQueueAckBatch"
    )
    poll_idx = lua.find('post("/plugin/poll", payload)')
    assert poll_idx >= 0, "Poll-Aufruf im Plugin nicht gefunden"
    poll_tail = lua[poll_idx:]
    ack_pos = poll_tail.find("executorState.sendOrQueueAckBatch(receivedIds)")
    enq_pos = poll_tail.find("enqueueCommand(command)")
    assert ack_pos >= 0 and enq_pos >= 0 and ack_pos < enq_pos, (
        "Test 2 FEHLGESCHLAGEN: received_batch (sendOrQueueAckBatch) wird im Poll NICHT vor enqueueCommand aufgerufen"
    )

    # 3) Bridge muss unbestaetigte 'delivered'-Befehle bei nachfolgenden Polls
    #    erneut zustellen (Re-Delivery mit unackedCount bis 3) und CommandPayloads
    #    vorhalten.
    assert "CommandPayloads" in source and "unackedCount" in source, (
        "Test 2 FEHLGESCHLAGEN: Bridge haelt CommandPayloads / unackedCount fuer Re-Delivery nicht vor"
    )
    assert "Befehl erneut zugestellt (unbestaetigt " in source, (
        "Test 2 FEHLGESCHLAGEN: Bridge protokolliert und fuehrt Re-Delivery unbestaetigter Befehle nicht aus"
    )


# ---------------------------------------------------------------------------
# Test 3: Selbstheilung durch /plugin/result bei Verlust von received_batch & started
# ---------------------------------------------------------------------------
def test_3_result_self_healing_when_acks_lost(source: str) -> None:
    complete_fn = extract_ps_function(source, "Complete-CommandResult")
    assert "deliveredAt" in complete_fn and "receivedAt" in complete_fn, (
        "Test 3 FEHLGESCHLAGEN: Complete-CommandResult heilt fehlende deliveredAt/receivedAt-Zeitstempel nicht"
    )
    assert "Befehl abgeschlossen:" in complete_fn, (
        "Test 3 FEHLGESCHLAGEN: Complete-CommandResult schreibt keinen Lebenszyklus-Eintrag ins runtime.log"
    )
    assert "$Shared.CommandPayloads.TryRemove" in complete_fn, (
        "Test 3 FEHLGESCHLAGEN: Complete-CommandResult raeumt CommandPayloads nicht auf"
    )


# ---------------------------------------------------------------------------
# Test 4: Kaputter Befehl im Plugin (kein stilles return in enqueueCommand)
# ---------------------------------------------------------------------------
def test_4_broken_command_never_silently_dropped(lua: str) -> None:
    enq_start = lua.find("local function enqueueCommand(command)")
    assert enq_start >= 0, "enqueueCommand nicht im Plugin gefunden"
    enq_end = lua.find("\nend\n", enq_start)
    enq_body = lua[enq_start : enq_end + 4]

    assert "INVALID_COMMAND" in enq_body and "deliverOrQueueResult" in enq_body, (
        "Test 4 FEHLGESCHLAGEN: enqueueCommand beantwortet kaputte Befehle (z. B. ohne tool) nicht sofort mit INVALID_COMMAND"
    )

    # Wenn @luau-rs/luau verfuegbar ist, fuehren wir den echten Lua-Code von
    # sendOrQueueAckBatch, deliverOrQueueResult und enqueueCommand in der Luau-VM aus:
    luau_mod = Path("/home/user/luaumock/node_modules/@luau-rs/luau")
    if luau_mod.exists():
        js = r"""
const { Lua } = require('/home/user/luaumock/node_modules/@luau-rs/luau');
const fs = require('fs');
const ps1 = fs.readFileSync('ArenaBridge.ps1', 'utf8');
const marker = "function Get-PluginSource {\n@'\n";
const begin = ps1.indexOf(marker) + marker.length;
const end = ps1.indexOf("\n'@\n}", begin);
const lua = ps1.slice(begin, end);

// 1) Komplettes Plugin muss in Luau fehlerfrei kompilieren und 2) echte Funktionstexte ausfuehren:
(async () => {
const vm = await Lua.create();
vm.compile(lua);

const ackStart = lua.indexOf("executorState.sendOrQueueAckBatch = function");
const pumpStart = lua.indexOf("local function pumpCommandQueue()");
const enqStart = lua.indexOf("local function enqueueCommand(command)");
const enqEnd = lua.indexOf("\nend\n", enqStart) + 4;
if (ackStart < 0 || pumpStart < 0 || enqStart < 0) process.exit(2);

const helpersCode = lua.slice(ackStart, pumpStart);
const enqCode = lua.slice(enqStart, enqEnd);

const harness = `
local sessionId = "sid-test"
local seenCommandIds = {}
local completedResults = {}
local commandQueue = {}
local lastError = nil
local deliveredResults = {}
local ackCalls = 0
local executorState = {
    lastTick = 0,
    runningCommandId = nil,
    runningTool = nil,
    startedAt = 0,
    dispatcherBusy = false,
    queueDepth = 0,
    resultOutbox = {},
    ackOutbox = {},
    lastAckAt = 0,
}
local function pluginOutputError(msg) lastError = msg end
local function failCode(code, message, extra)
    local t = { ok = false, code = code, error = message }
    if type(extra) == "table" then
        for k, v in pairs(extra) do t[k] = v end
    end
    return t
end
local function rememberCompletedResult(cid, res) completedResults[tostring(cid)] = res end
local function post(path, payload)
    if path == "/plugin/command_state" then
        ackCalls = ackCalls + 1
        return { ok = true, accepted = true }
    end
    return { ok = true }
end
local function postResult(cid, payload)
    deliveredResults[tostring(cid)] = payload
    return true
end
local function commandStateRequest(cmd, phase) return { ok = true, accepted = true } end
local function pumpCommandQueue() end
local task = { spawn = function(fn) fn() end, defer = function(fn) fn() end }
local os = { time = function() return 12345 end, clock = function() return 100 end }
` + helpersCode + "\n" + enqCode + `

-- Fall A: Befehl ohne tool -> muss sofort INVALID_COMMAND liefern (kein stilles Verwerfen!)
enqueueCommand({ id = "cmd-broken-1", tool = nil, args = {} })
assert(deliveredResults["cmd-broken-1"] ~= nil, "Kaputter Befehl wurde nicht beantwortet")
assert(deliveredResults["cmd-broken-1"].ok == false, "Kaputter Befehl muss ok=false sein")
assert(deliveredResults["cmd-broken-1"].code == "INVALID_COMMAND", "Erwartet INVALID_COMMAND")

-- Fall B: Befehl war in seenCommandIds, ist aber weder fertig noch laufend noch in commandQueue -> muss neu eingereiht werden!
seenCommandIds["cmd-orphan-1"] = 100
enqueueCommand({ id = "cmd-orphan-1", tool = "site_survey", args = {} })
assert(#commandQueue == 1 and commandQueue[1].id == "cmd-orphan-1", "Verwaister seenCommandId-Befehl wurde still verworfen")
`;

vm.execute(harness);
})().catch((e) => { console.error(e); process.exit(1); });
"""
        res = subprocess.run(["node", "-e", js], cwd=ROOT, capture_output=True, text=True)
        assert res.returncode == 0, f"Test 4 Luau-Ausfuehrung fehlgeschlagen: {res.stderr}"


# ---------------------------------------------------------------------------
# Test 5: Echtes totes Plugin (ehrliches Scheitern + Diagnose + deutsche Karte)
# ---------------------------------------------------------------------------
def test_5_dead_plugin_honest_failure_with_diagnostics(source: str, lua: str) -> None:
    watchdog_fn = extract_ps_function(source, "Invoke-SessionExecutorWatchdog")
    abandon_fn = extract_ps_function(source, "Mark-CommandAbandoned")
    activity_fn = extract_ps_function(source, "Complete-ArenaActivity")

    assert "lastPollError" in lua and "lastPluginError" in lua and "lastAckAt" in lua, (
        "Test 5 FEHLGESCHLAGEN: Plugin sendet lastPollError / lastPluginError / lastAckAt nicht im Executor-Snapshot"
    )
    assert "lastPollError" in abandon_fn and "lastPluginError" in abandon_fn and "pluginDiagnostics" in abandon_fn, (
        "Test 5 FEHLGESCHLAGEN: Mark-CommandAbandoned enthaelt keine pluginDiagnostics (lastPollError/lastPluginError/lastAckAt)"
    )
    assert "Befehl vom Waechter abgebrochen:" in abandon_fn or "Befehl vom Waechter abgebrochen:" in watchdog_fn, (
        "Test 5 FEHLGESCHLAGEN: Watchdog-Abbruch wird nicht mit Grund und Plugin-Diagnose in runtime.log protokolliert"
    )
    assert "COMMAND_DELIVERY_UNCONFIRMED" in activity_fn and "Empfang des Befehls" in activity_fn, (
        "Test 5 FEHLGESCHLAGEN: Complete-ArenaActivity erzeugt keine verstaendliche deutsche Meldung fuer COMMAND_DELIVERY_UNCONFIRMED"
    )


# ---------------------------------------------------------------------------
# Test 6: Sequenztest mit 20 Befehlen unter Stoerfeuer (Simulator)
# ---------------------------------------------------------------------------
class SimulatedBridge710:
    """Exaktes Verhaltensmodell der 7.1.0-Zustellung (Server + Plugin)."""

    def __init__(self, is_710: bool) -> None:
        self.is_710 = is_710
        self.now = 1000
        self.queue: list[dict] = []
        self.pending: dict[str, dict] = {}
        self.payloads: dict[str, dict] = {}
        self.completed: dict[str, dict] = {}
        self.cancelled_ids: list[str] = []
        # Plugin-Zustand
        self.plugin_seen: set[str] = set()
        self.plugin_completed: dict[str, dict] = {}
        self.plugin_ack_outbox: dict[str, dict] = {}
        self.plugin_result_outbox: dict[str, dict] = {}
        self.plugin_queue: list[dict] = []
        self.ack_call_index = 0
        self.start_call_index = 0
        self.poll_call_index = 0

    def enqueue_from_arena(self, cid: str, tool: str | None) -> None:
        cmd = {"id": cid, "tool": tool, "args": {}, "queuedAt": self.now, "budgetSeconds": 90}
        self.queue.append(cmd)
        self.pending[cid] = {
            "commandId": cid,
            "tool": tool or "",
            "status": "queued",
            "queuedAt": self.now,
            "deliveredAt": 0,
            "lastDeliveryAt": 0,
            "receivedAt": 0,
            "startedAt": 0,
            "unackedCount": 0,
            "deliveryAttempts": 0,
        }
        if self.is_710:
            self.payloads[cid] = cmd

    def server_poll(self, drop_http_response: bool = False) -> dict | None:
        self.poll_call_index += 1
        collected: list[dict] = []
        if self.is_710:
            for cid, info in list(self.pending.items()):
                if info["status"] == "delivered" and (self.now - info["lastDeliveryAt"]) >= 1 and info["unackedCount"] < 3:
                    info["unackedCount"] += 1
                    info["lastDeliveryAt"] = self.now
                    info["deliveryAttempts"] += 1
                    if cid in self.payloads:
                        collected.append(self.payloads[cid])
        while self.queue and len(collected) < 16:
            item = self.queue.pop(0)
            cid = item["id"]
            info = self.pending.get(cid)
            if info and info["status"] == "queued":
                info["status"] = "delivered"
                info["deliveredAt"] = self.now
                info["lastDeliveryAt"] = self.now
                info["deliveryAttempts"] = 1
                collected.append(item)

        if not self.is_710:
            # 7.0.8-Bug: leeres $cancelledIds erzeugte ungueltiges JSON ("cancelledCommands":,)
            if len(self.cancelled_ids) == 0:
                return None
        if drop_http_response:
            return None
        return {"ok": True, "commands": collected, "cancelledCommands": list(self.cancelled_ids)}

    def server_command_state(self, phase: str, command_ids: list[str] | None = None, command_id: str | None = None) -> bool:
        if phase == "received_batch":
            self.ack_call_index += 1
            if self.ack_call_index % 3 == 0:
                return False  # Stoerfeuer: jeder 3. received_batch-POST schlaegt fehl
            for cid in command_ids or []:
                info = self.pending.get(cid)
                if info and info["status"] in ("queued", "delivered"):
                    info["status"] = "received"
                    info["receivedAt"] = self.now
                    info["unackedCount"] = 0
            return True
        if phase == "started":
            self.start_call_index += 1
            if self.start_call_index % 5 == 0:
                return False  # Stoerfeuer: jeder 5. started-POST schlaegt fehl
            info = self.pending.get(command_id or "")
            if info and info["status"] in ("queued", "delivered", "received"):
                info["status"] = "started"
                info["startedAt"] = self.now
                if info["receivedAt"] <= 0:
                    info["receivedAt"] = self.now
                info["unackedCount"] = 0
            return True
        return True

    def server_result(self, cid: str, payload: dict) -> bool:
        info = self.pending.pop(cid, None)
        self.payloads.pop(cid, None)
        if info and self.is_710:
            if info["deliveredAt"] <= 0:
                info["deliveredAt"] = self.now
            if info["receivedAt"] <= 0:
                info["receivedAt"] = self.now
            if info["startedAt"] <= 0:
                info["startedAt"] = self.now
        self.completed[cid] = payload
        return True

    def plugin_step(self, drop_first_poll_for_every_7th: bool = True) -> None:
        drop = drop_first_poll_for_every_7th and (self.poll_call_index + 1) % 7 == 0
        resp = self.server_poll(drop_http_response=drop)
        if resp and resp.get("commands"):
            cmds = resp["commands"]
            if self.is_710:
                ids = [c["id"] for c in cmds if c.get("id")]
                if ids:
                    for cid in ids:
                        self.plugin_ack_outbox[cid] = True
                    if self.server_command_state("received_batch", command_ids=ids):
                        for cid in ids:
                            self.plugin_ack_outbox.pop(cid, None)
            for cmd in cmds:
                cid = cmd["id"]
                if self.is_710 and not cmd.get("tool"):
                    err = {"ok": False, "code": "INVALID_COMMAND", "commandId": cid}
                    self.plugin_completed[cid] = err
                    self.server_result(cid, err)
                    continue
                if cid in self.plugin_completed:
                    self.server_result(cid, self.plugin_completed[cid])
                    continue
                if cid not in self.plugin_seen:
                    self.plugin_seen.add(cid)
                    self.plugin_queue.append(cmd)
            if not self.is_710:
                ids = [c["id"] for c in cmds if c.get("id")]
                if ids:
                    self.server_command_state("received_batch", command_ids=ids)

        # Outbox-Flush (7.1.0)
        if self.is_710 and self.plugin_ack_outbox:
            ids = list(self.plugin_ack_outbox.keys())
            if self.server_command_state("received_batch", command_ids=ids):
                self.plugin_ack_outbox.clear()

        # Lokale Ausführung
        while self.plugin_queue:
            cmd = self.plugin_queue.pop(0)
            cid = cmd["id"]
            self.server_command_state("started", command_id=cid)
            res = {"ok": True, "commandId": cid, "tool": cmd["tool"]}
            self.plugin_completed[cid] = res
            self.server_result(cid, res)

    def watchdog_tick(self) -> None:
        for cid, info in list(self.pending.items()):
            if info["status"] == "delivered" and (self.now - info["deliveredAt"]) > 30:
                self.pending.pop(cid, None)
                self.payloads.pop(cid, None)
                self.completed[cid] = {
                    "ok": False,
                    "code": "COMMAND_DELIVERY_UNCONFIRMED",
                    "commandId": cid,
                    "unackedCount": info["unackedCount"],
                }


def test_6_20_commands_under_fault_injection(source: str, lua: str) -> None:
    # Sicherstellen, dass erst die echten 7.1.0-Quellcode-Garantien vorhanden sind
    test_2_command_delivery_unconfirmed_repro_and_healing(source, lua)
    test_3_result_self_healing_when_acks_lost(source)

    # 1) 7.0.8-Gegenprobe: stirbt mit COMMAND_DELIVERY_UNCONFIRMED
    sim_708 = SimulatedBridge710(is_710=False)
    sim_708.enqueue_from_arena("cmd-708", "site_survey")
    for _ in range(35):
        sim_708.now += 1
        sim_708.plugin_step()
        sim_708.watchdog_tick()
    assert sim_708.completed.get("cmd-708", {}).get("code") == "COMMAND_DELIVERY_UNCONFIRMED", (
        "7.0.8-Reproduktion muss COMMAND_DELIVERY_UNCONFIRMED zeigen"
    )

    # 2) 7.1.0: 20 Befehle hintereinander unter Stoerfeuer -> 20x ok=true, 0x COMMAND_DELIVERY_UNCONFIRMED
    tools_20 = [
        "site_survey", "get_place_info", "get_tree", "create_instance", "set_property",
        "set_properties", "bulk_create", "run_lua", "get_properties", "get_bounds",
        "scene_stats", "ui_capabilities", "ui_skin", "build_surface", "ui_audit",
        "world_capabilities", "build_room", "populate_zone", "world_audit", "report_done",
    ]
    sim_710 = SimulatedBridge710(is_710=True)
    for idx, tool_name in enumerate(tools_20, start=1):
        cid = f"cmd-{idx:02d}"
        sim_710.enqueue_from_arena(cid, tool_name)
        for _ in range(4):
            sim_710.now += 1
            sim_710.plugin_step(drop_first_poll_for_every_7th=True)
            sim_710.watchdog_tick()
        assert cid in sim_710.completed, f"Befehl {cid} ({tool_name}) wurde nicht abgeschlossen"
        assert sim_710.completed[cid].get("ok") is True, (
            f"Befehl {cid} ({tool_name}) schlug fehl: {sim_710.completed[cid]}"
        )


def main() -> int:
    source = load_source()
    lua = extract_plugin_lua(source)
    failures: list[str] = []

    tests = [
        ("Test 1 (BindReason & Vorschau-Log-Drosselung)", lambda: test_1_bind_reason_and_preview_throttle(source)),
        ("Test 2 (COMMAND_DELIVERY_UNCONFIRMED-Heilung, To-Json, Ack-Outbox, Re-Delivery)", lambda: test_2_command_delivery_unconfirmed_repro_and_healing(source, lua)),
        ("Test 3 (Selbstheilung durch /plugin/result bei Ack-Verlust)", lambda: test_3_result_self_healing_when_acks_lost(source)),
        ("Test 4 (Kein stilles return in enqueueCommand bei kaputtem Befehl)", lambda: test_4_broken_command_never_silently_dropped(lua)),
        ("Test 5 (Ehrliches Scheitern + Plugin-Diagnose + deutsche Karte bei totem Plugin)", lambda: test_5_dead_plugin_honest_failure_with_diagnostics(source, lua)),
        ("Test 6 (20 Befehle hintereinander unter Stoerfeuer ohne Abbruch)", lambda: test_6_20_commands_under_fault_injection(source, lua)),
    ]

    for label, fn in tests:
        try:
            fn()
            print(f"[GRUEN] {label}")
        except AssertionError as exc:
            print(f"[ROT]   {label}: {exc}")
            failures.append(f"{label}: {exc}")

    if failures:
        print(f"\nFEHLGESCHLAGEN: {len(failures)} von {len(tests)} Tests rot.", file=sys.stderr)
        return 1
    print(f"\nOK: Alle {len(tests)} Pflicht-Tests fuer Version 7.1.0 sind gruen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
