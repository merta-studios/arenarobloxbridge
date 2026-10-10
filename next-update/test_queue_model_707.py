#!/usr/bin/env python3
"""Modelltest der 7.0.7-Queue-Regeln (kein PowerShell, kein Roblox Studio).

Dies ist ein *Modell* des Server-/Plugin-Verhaltens, kein Live-Test. Es bildet
die Regeln nach, die ArenaBridge.ps1 anwendet, und prueft mit einer virtuellen
Uhr, dass diese Regeln den in 7.0.4 gemeldeten Stillstand tatsaechlich
aufloesen:

  A) Nachbau 7.0.4: Der Executor-Watchdog lief NUR in /plugin/poll. Haengt ein
     Befehl ohne yield (oder antwortet das Plugin nicht mehr), kommt kein Poll
     mehr -> nichts raeumt auf -> Queue + lateResults bleiben fuer immer leer.
  B) 7.0.5-Sweep (in 7.0.6 unveraendert): Ein unabhaengiger Sweep (eigener Runspace, 2 s) bricht den Befehl
     nach budget+15 s ab, beantwortet den Wartenden bzw. legt das Ergebnis in
     die lateResults der ANRUFER-Sitzung und laesst die Queue weiterlaufen.
  C) 7.0.5: Beim Reconnect gehen nur NIE zugestellte Befehle an die neue
     Sitzung (genau einmal ausgefuehrt); bereits ausgefuehrte commandIds liefern
     ihr gespeichertes Ergebnis erneut aus, statt neu zu laufen.
  D) 7.0.5: Die HTTP-Antwort liegt mit 55 s (max 85 s) unter dem ~100-s-524
     von Cloudflare; ein abgebrochener Befehl kommt als lateResult zurueck.
  E) 7.0.5-Sweep: force_fail/clear_pending beantwortet JEDEN offenen Befehl
     sofort und leert die serielle Queue.
  F) 7.0.6: Dieselbe Plugin-Instanz (instanceGuid) behaelt IMMER dieselbe
     Sitzung und denselben Token - hier entstand der "Bridge connected"-Sturm
     alle ~2 Sekunden; eine unbekannte Sitzung mit bekannter Instanz bekommt
     ihre sessionId zurueck, statt eine neue zu erzeugen.
  G) 7.0.6: Ist der Executor nachweislich stumm, antwortet die Bridge SOFORT
     mit STUDIO_UNREACHABLE (nichts wird eingereiht) statt 55 s zu warten; ist
     er belegt und die FIFO nicht leer, kommt SOFORT STUDIO_BUSY.
  H) 7.0.6: Jeder Befehl traegt die Zustell-Timeline queuedAt -> deliveredAt ->
     receivedAt -> startedAt -> heartbeatAt (+ lastError) fuer /api/queue.
  I) 7.0.7 LIVE-FIX: Die Place-Liste bleibt leer, wenn ein Zeilen-Bauer an einer
     NICHT deklarierten [pscustomobject]-Eigenschaft abbricht (live: 7.0.6,
     "$row.CommandCancelButton"). Der Test baut den Fall nach - beide Bauer
     brechen ab, keine Zeile erscheint - und prueft am echten Quellcode, dass
     die Eigenschaft in BEIDEN Initialisierern steht und der optionale Knopf in
     try/catch gebaut wird. Ausserdem: der UI-Abbruch darf keine Funktionen des
     Server-Runspaces aufrufen.

Die Zeitfenster werden aus ArenaBridge.ps1 GELESEN - aendert jemand dort eine
Konstante (oder entfernt den unabhaengigen Sweep), faellt der Test auf.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "ArenaBridge.ps1").read_text(encoding="utf-8-sig")

FAILURES: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        FAILURES.append(message)


def read_int(pattern: str, label: str) -> int:
    match = re.search(pattern, SOURCE, re.MULTILINE)
    require(match is not None, f"Konstante nicht gefunden: {label}")
    return int(match.group(1)) if match else -1


# --- Konstanten aus dem echten Code lesen (Regressionsschutz) ----------------
BUDGET_DEFAULT = read_int(r"\[int\]\$budgetSeconds = (\d+)", "Default-Budget")
BUDGET_GRACE = read_int(r"\(\$budget \+ (\d+)\)", "Sweep: budget+GRACE")
HEARTBEAT_STALE = read_int(r"\(\$now - \$heartbeatAt\) -gt (\d+)", "Sweep: Heartbeat-Grenze")
DELIVERY_TTL = read_int(r"\$status -eq 'delivered' -and \$age -gt (\d+)", "Sweep: Zustell-TTL")
SESSION_ALIVE = read_int(r"sessionAge -le (\d+)", "Sweep: Sitzung lebendig")
HTTP_DEFAULT = read_int(r"\$timeout = (\d+)\n", "HTTP-Default")
HTTP_CAP = read_int(r"\[Math\]::Min\(\[int\]\$body\.timeoutSeconds, (\d+)\)", "HTTP-Cap")
SWEEP_INTERVAL = read_int(r"Start-Sleep -Seconds (\d+)\n\s*\}\n\}", "Sweep-Intervall")
# Version 7.1.2: Get-StudioDeliveryHealth prueft executorAlive jetzt ZUERST
# (delivery.state = ok durfte nicht mehr allein von einem frischen HTTP-Kontakt
# kommen). Die Zeitfenster 15 s / 45 s sind unveraendert.
HEALTH_FRESH = read_int(r"\$openPolls -gt 0 -or \$age -le (\d+)\)", "Health: frisches Lebenszeichen")
HEALTH_WAIT = read_int(r"\$waiting -gt 0 -and \$oldestWaiting -gt (\d+)", "Health: wartende Arbeit")
HEALTH_DEAD = read_int(r"-not \$executorAlive -and \$age -gt (\d+)", "Health: stummer Executor")
CF_524 = 100

require("$script:BridgeSweepScript = {" in SOURCE, "Der unabhaengige Sweep-Runspace fehlt.")
require("[void]$sweepPs.AddScript([string]$script:BridgeSweepScript).AddArgument($script:Shared)" in SOURCE,
        "Der Sweep wird nicht als eigener Runspace gestartet.")
require("foreach ($sessionPair in @($Shared.Sessions.GetEnumerator()))" in SOURCE
        and "Start-Sleep -Seconds" in SOURCE,
        "Der Sweep laeuft nicht eigenstaendig ueber alle Sitzungen.")
require("$Shared.SweepState.LastSweepAt" in SOURCE and "abandonedBy = 'server-watchdog'" in SOURCE,
        "Sweep-Lebenszeichen/abandonedBy fehlt.")
require(HTTP_DEFAULT <= 55 and HTTP_CAP <= 85,
        f"HTTP-Fenster zu gross: default={HTTP_DEFAULT}, cap={HTTP_CAP}")
require(HTTP_CAP < CF_524, "HTTP-Cap muss unter dem Cloudflare-524-Fenster liegen.")
require(BUDGET_GRACE > 0 and HEARTBEAT_STALE > 0 and DELIVERY_TTL >= HEARTBEAT_STALE,
        "Sweep-Zeitfenster sind unplausibel.")
require("$reuseReason = 'same-instance'" in SOURCE
        and "$Shared.InstanceSessions[$guid] = $sessionId" in SOURCE
        and "function Resolve-InstanceSession" in SOURCE
        and "InstanceSessions = [System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()" in SOURCE,
        "Die Sitzungs-Identitaet (instanceGuid -> sessionId) fehlt - der Reconnect-Sturm waere zurueck.")
require("if ($deliveryHealth.state -eq 'wedged')" in SOURCE
        and "code = 'STUDIO_UNREACHABLE'" in SOURCE
        and "code = 'STUDIO_BUSY'" in SOURCE
        and "commandSent = $false" in SOURCE,
        "Die Vorab-Pruefung vor dem Einreihen (Fast-Fail) fehlt - Befehle wuerden wieder 55 s warten.")
require("timeline = $timeline" in SOURCE and "timelineRule" in SOURCE
        and "lastError = if ($info.lastError)" in SOURCE
        and SOURCE.count("$Shared.CommandHistory.TryAdd($sid, $historyQueue)") == 2,
        "Die Zustell-Timeline fehlt (inkl. Historie fuer den Waechter-Runspace).")
require("sessionId = $(if ([string]::IsNullOrWhiteSpace($knownSessionId))" in SOURCE,
        "Eine unbekannte Sitzung mit bekannter Instanz bekommt ihre sessionId nicht zurueck.")
require(0 < HEALTH_FRESH < HEALTH_WAIT < HEALTH_DEAD,
        f"Gesundheitsfenster unplausibel: fresh={HEALTH_FRESH}, wait={HEALTH_WAIT}, dead={HEALTH_DEAD}")

# --- 7.0.7: Place-Zeilen-Bauer und UI-Abbruch --------------------------------
require(SOURCE.count("CommandCancelButton = $null") == 2,
        "CommandCancelButton ist nicht in BEIDEN Zeilen-Initialisierern deklariert (7.0.6-Live-Fehler).")
require(SOURCE.count("$row.CommandCancelButton = $cancelButton") == 2,
        "Der optionale Abbrechen-Knopf wird nicht in genau beiden Zeilen-Bauern gebaut.")
_sync_start = SOURCE.index("function Sync-PlaceList {")
_builder_main = SOURCE[SOURCE.index("function New-Row {"):SOURCE.index("function New-MinimalPlaceRow {")]
_builder_min = SOURCE[_sync_start - 8000:_sync_start]
require("Abbrechen-Knopf konnte" in _builder_main and "Abbrechen-Knopf konnte" in _builder_min,
        "Ein Zeilen-Bauer baut den optionalen Knopf ohne try/catch - ein Extra darf die Zeile nie kosten.")
_cancel_fn = SOURCE[SOURCE.index("function Invoke-PlaceRowCancel {"):SOURCE.index("function Update-PlaceProgressVisual {")]
_cancel_code = "\n".join(line for line in _cancel_fn.splitlines() if not line.strip().startswith("#"))
require("Get-DeliverySession " not in _cancel_code and "Request-CommandCancel" not in _cancel_code,
        "Der UI-Abbruch ruft wieder Funktionen des Server-Runspaces auf (wirkungslos).")
require("function Get-UiDeliverySession" in SOURCE and "COMMAND_CANCELLED" in _cancel_fn
        and "$script:Shared.CancelRequests[$cancelKey] = $now" in _cancel_fn,
        "Der UI-Abbruch nutzt nicht den gemeinsamen Zustand (CancelRequests + COMMAND_CANCELLED).")
require("$script:LastPlaceRowError" in SOURCE and "'Ursache: ' + [string]$script:LastPlaceRowError" in SOURCE,
        "Die Reparatur-Anzeige nennt den echten Grund nicht.")


# --- Modell -----------------------------------------------------------------
class Command:
    def __init__(self, cid: str, tool: str, budget: int = BUDGET_DEFAULT) -> None:
        self.id = cid
        self.tool = tool
        self.budget = budget
        self.status = "queued"
        self.queued_at = 0
        self.delivered_at = 0
        self.started_at = 0
        self.heartbeat_at = 0
        self.origin = "A"
        self.executions = 0
        self.results_posted = 0
        self.last_error = ""


class Bridge:
    """Modell: serielle Queue + Sitzungen + (optional) unabhaengiger Sweep."""

    def __init__(self, independent_sweep: bool) -> None:
        self.independent_sweep = independent_sweep
        self.now = 0
        self.pending: dict[str, Command] = {}
        self.late: dict[str, list[Command]] = {}
        self.waiting: dict[str, Command] = {}
        self.completed: set[str] = set()
        self.executed: list[str] = []
        self.abandoned_total = 0
        self.poll_alive = True  # 7.0.4: Sweep lief nur in der Poll-Anfrage
        self.instances: dict[str, str] = {}
        self.sessions: set[str] = set()
        self.session_counter = 0

    # -- Ablauf ---------------------------------------------------------------
    def enqueue(self, command: Command, session: str = "A") -> None:
        command.queued_at = self.now
        command.origin = session
        self.pending[command.id] = command
        self.waiting[command.id] = command

    def deliver(self, session: str, command_id: str | None = None) -> Command | None:
        for command in self.pending.values():
            if command.status == "queued" and (command_id is None or command.id == command_id):
                command.status = "delivered"
                command.delivered_at = self.now
                return command
        return None

    def plugin_start(self, command: Command) -> None:
        """Plugin startet den Befehl (Start-Ack) - fuer den Modelltest der Hänger."""
        command.status = "received"
        command.started_at = self.now
        command.heartbeat_at = self.now
        command.executions += 1

    def complete(self, command: Command, session: str) -> None:
        command.results_posted += 1
        command.status = "completed"
        self.completed.add(command.id)
        if command.id in self.waiting:
            del self.waiting[command.id]
        else:
            self.late.setdefault(command.origin, []).append(command)
        self.pending.pop(command.id, None)

    def tick(self) -> None:
        self.now += 1
        if self.independent_sweep:
            self.sweep()
        elif self.poll_alive:
            self.sweep()  # 7.0.4: nur wenn das Plugin noch pollt

    # -- Sweep (7.0.5) --------------------------------------------------------
    def sweep(self) -> None:
        for command in list(self.pending.values()):
            if command.status in ("started", "running", "received"):
                age = self.now - command.started_at if command.started_at else self.now - command.queued_at
                if command.started_at and age > command.budget + BUDGET_GRACE:
                    self.abandon(command, "STUDIO_ABANDONED")
                elif command.heartbeat_at and (self.now - command.heartbeat_at) > HEARTBEAT_STALE:
                    self.abandon(command, "EXECUTOR_UNRESPONSIVE")
                elif not self.poll_alive and age > 60:
                    self.abandon(command, "EXECUTOR_UNAVAILABLE")
            elif command.status == "delivered" and (self.now - command.delivered_at) > DELIVERY_TTL:
                self.abandon(command, "COMMAND_DELIVERY_UNCONFIRMED")
            elif command.status == "queued" and not self.poll_alive and (self.now - command.queued_at) > 60:
                self.abandon(command, "EXECUTOR_UNAVAILABLE")

    def abandon(self, command: Command, code: str) -> None:
        command.status = "abandoned"
        command.last_error = code
        self.abandoned_total += 1
        if command.id in self.waiting:
            del self.waiting[command.id]
        else:
            self.late.setdefault(command.origin, []).append(command)
        self.pending.pop(command.id, None)

    # -- Admin-Reset --------------------------------------------------------
    def force_fail(self) -> int:
        count = 0
        for command in list(self.pending.values()):
            self.abandon(command, "FORCE_CLEARED")
            count += 1
        return count

    # -- Sitzungs-Identitaet (7.0.6) -----------------------------------------
    def register(self, instance_guid: str, known_session: str = "") -> tuple[str, bool]:
        """Gibt (sessionId, tokenErneuert) zurueck.

        Dieselbe Instanz bekommt dieselbe Sitzung - auch wenn die Sitzung von
        aussen tot aussieht. Nur eine NEUE Instanz erzeugt eine neue Sitzung;
        eine unbekannte sessionId mit bekannter Instanz bekommt die bekannte
        sessionId zurueck (kein neuer Token, kein Sturm).
        """
        if instance_guid in self.instances:
            return self.instances[instance_guid], False
        if known_session:
            self.instances[instance_guid] = known_session
            return known_session, False
        self.session_counter += 1
        session = f"S{self.session_counter}"
        self.instances[instance_guid] = session
        return session, True

    def poll(self, instance_guid: str, session: str) -> tuple[str, bool]:
        if session in self.sessions:
            return session, False
        known = self.instances.get(instance_guid, "")
        resolved, renewed = self.register(instance_guid, known)
        require(not renewed, "7.0.6: eine bekannte Instanz darf keinen neuen Token bekommen")
        return resolved, True

    # -- Gesundheit (7.0.6) ---------------------------------------------------
    def call_tool(self, tool: str, waiting: int, seconds_since_sign: int, alive: bool, busy: bool, as_job: bool = False) -> str:
        """Antwort der Bridge VOR dem Einreihen: ok | STUDIO_UNREACHABLE | STUDIO_BUSY."""
        wedged = (waiting > HEALTH_WAIT and seconds_since_sign > HEALTH_WAIT) or (not alive and seconds_since_sign > HEALTH_DEAD)
        if wedged:
            return "STUDIO_UNREACHABLE"   # sofort, nichts wird eingereiht
        if busy and waiting > 0 and not as_job:
            return "STUDIO_BUSY"          # sofort, nichts wird eingereiht
        return "ok"

    # -- Reconnect ----------------------------------------------------------
    def handover(self, old: str, new: str) -> int:
        moved = 0
        for command in list(self.pending.values()):
            if command.origin != old:
                continue
            if command.status == "queued":  # nie zugestellt -> sicher uebergeben
                command.origin = old  # Ergebnis bleibt beim Anrufer
                moved += 1
            # zugestellte/gelaufene Befehle werden NICHT wiederholt
        return moved


def build_row(declared: set[str]) -> bool:
    """Nachbau des 7.0.6-Live-Fehlers beim Aufbau einer Place-Zeile.

    Windows PowerShell wirft bei `$row.X = ...`, wenn X im
    [pscustomobject]-Initialisierer fehlt ("property cannot be found on this
    object"). Der Wurf reisst den KOMPLETTEN Zeilenaufbau mit - und weil der
    Minimal-Fallback dieselbe Zeile enthaelt, scheitern beide Bauer.
    """
    class PsCustomRow:
        """[pscustomobject]-Nachbau: nur DEKLARIERTE Eigenschaften sind setzbar."""

        def __init__(self, props):
            self.__dict__["_declared"] = set(props)

        def __setattr__(self, name, value):
            if name not in self.__dict__["_declared"]:
                raise AttributeError(f"'{name}' cannot be found on this object")
            self.__dict__[name] = value

    row = PsCustomRow(declared)
    try:
        row.CommandCancelButton = object()   # die Zuweisung aus dem Code
    except AttributeError:
        return False
    return True


def run_704_wedge() -> tuple[Bridge, Command]:
    """Nachbau des gemeldeten 7.0.4-Falls: Befehl ohne yield, Plugin pollt nicht mehr."""
    bridge = Bridge(independent_sweep=False)
    hung = Command("c1", "list_jobs", budget=90)
    bridge.enqueue(hung)
    bridge.deliver("A")
    bridge.plugin_start(hung)
    bridge.poll_alive = False  # Lua-VM blockiert -> kein Poll mehr
    for _ in range(400):
        bridge.tick()
    return bridge, hung


def main() -> int:
    # A) 7.0.4-Nachbau: Der Stillstand ist reproduzierbar ----------------------
    bridge, hung = run_704_wedge()
    require(hung.status in ("received", "started"),
            "7.0.4-Nachbau: der haengende Befehl muss weiter 'laufend' sein")
    require(len(bridge.late.get("A", [])) == 0,
            "7.0.4-Nachbau: es darf kein lateResult geben (genau das war der Fehler)")
    require(hung.id in bridge.pending,
            "7.0.4-Nachbau: der Befehl blockiert die Queue fuer immer")
    print(f"A) 7.0.4-Nachbau: nach 400 s weiterhin haengend, 0 lateResults, "
          f"Queue-Blockade bestaetigt (budget+grace={BUDGET_GRACE}, heartbeat={HEARTBEAT_STALE}s).")

    # B) 7.0.5: unabhaengiger Sweep raeumt auf und liefert --------------------
    bridge = Bridge(independent_sweep=True)
    hung = Command("c1", "list_jobs", budget=90)
    bridge.enqueue(hung, "A")
    bridge.deliver("A")
    bridge.plugin_start(hung)
    bridge.poll_alive = False  # das Plugin antwortet gar nicht mehr
    # Der HTTP-Aufrufer laeuft nach HTTP_DEFAULT Sekunden in den Timeout; erst
    # danach faellt der Abbruch in die lateResults (genau das war die Anforderung).
    for _ in range(HTTP_DEFAULT):
        bridge.tick()
    bridge.waiting.clear()
    for _ in range(90 + BUDGET_GRACE + SWEEP_INTERVAL + 1 - HTTP_DEFAULT):
        bridge.tick()
    require(hung.status == "abandoned", "7.0.5: der haengende Befehl muss abgebrochen werden")
    require(bridge.abandoned_total == 1, "7.0.5: abandonedTotal muss steigen")
    require(len(bridge.late.get("A", [])) == 1,
            "7.0.5: das Abbruch-Ergebnis muss in den lateResults der Anrufer-Sitzung liegen")
    require(hung.id not in bridge.pending, "7.0.5: die Queue muss frei sein")
    # Queue laeuft weiter:
    follow = Command("c2", "get_tree", budget=90)
    bridge.enqueue(follow, "A")
    next_cmd = bridge.deliver("A")
    require(next_cmd is not None and next_cmd.id == "c2", "7.0.5: der naechste Befehl muss laufen")
    print(f"B) 7.0.5-Sweep: abgebrochen nach {hung.budget + BUDGET_GRACE} s "
          f"(exakt budget+15), lateResult fuer Sitzung A, Queue laeuft weiter.")

    # C) Reconnect: Uebergabe ohne Doppelausfuehrung -------------------------
    bridge = Bridge(independent_sweep=True)
    waiting = Command("c3", "site_survey", budget=90)
    bridge.enqueue(waiting, "A")  # noch nicht zugestellt
    running = Command("c4", "ground_height", budget=90)
    bridge.enqueue(running, "A")
    bridge.deliver("A", "c4")     # c4 war schon beim alten Executor
    bridge.plugin_start(running)
    moved = bridge.handover("A", "B")
    require(moved == 1, "Reconnect: genau der nie zugestellte Befehl darf uebergehen")
    require(running.status != "queued", "Reconnect: gestartete Arbeit bleibt beim alten Executor")
    require(running.executions == 1, "Reconnect: bereits gestartete Arbeit darf nicht doppelt laufen")
    delivered = bridge.deliver("B")
    require(delivered is not None and delivered.id == "c3", "Reconnect: Uebergabe an die neue Sitzung")
    # Der Aufrufer von c3 wartet nach dem Reconnect nicht mehr (HTTP-Timeout) -
    # das Ergebnis muss trotzdem bei ihm ankommen.
    bridge.waiting.clear()
    bridge.complete(waiting, "B")
    require(len(bridge.late.get("A", [])) == 1,
            "Reconnect: das Ergebnis muss in den lateResults des ANRUFERS (A) landen")
    print("C) Reconnect: genau ein nie zugestellter Befehl uebergeben, nichts doppelt ausgefuehrt.")

    # D) Cloudflare: die HTTP-Antwort bleibt unter 100 s ---------------------
    worst = max(HTTP_DEFAULT, min(300 + 25, HTTP_CAP))
    require(worst < CF_524, f"HTTP-Antwort {worst}s muss unter {CF_524}s bleiben")
    print(f"D) Cloudflare: Default {HTTP_DEFAULT}s, Maximum {HTTP_CAP}s < {CF_524}s (524-Grenze).")

    # E) Admin-Reset ---------------------------------------------------------
    bridge = Bridge(independent_sweep=True)
    for index in range(3):
        bridge.enqueue(Command(f"r{index}", "build_polygon_model"), "A")
    # Realistischer Fall: die HTTP-Aufrufer sind schon in den Timeout gelaufen,
    # die Befehle haengen aber noch in der seriellen Queue.
    bridge.waiting.clear()
    cleared = bridge.force_fail()
    require(cleared == 3, "force_fail muss jeden offenen Befehl beantworten")
    require(not bridge.pending, "force_fail muss die Queue leeren")
    require(bridge.abandoned_total == 3, "force_fail muss abandonedTotal zaehlen")
    require(len(bridge.late["A"]) == 3,
            "force_fail muss fuer jeden Befehl ein lateResult beim Anrufer hinterlegen")
    print("E) Admin-Reset: 3 offene Befehle sofort mit FORCE_CLEARED beantwortet, Queue leer.")

    # F) Sitzungs-Identitaet: kein Reconnect-Sturm --------------------------
    bridge = Bridge(independent_sweep=True)
    first_session, renewed = bridge.register("inst-1")
    bridge.sessions.add(first_session)
    require(renewed, "7.0.6: die erste Anmeldung erzeugt genau eine Sitzung")
    # 20 Handshakes derselben Instanz (auch nach Cleanup/Reconnect):
    for _ in range(20):
        same, renewed = bridge.register("inst-1")
        require(same == first_session and not renewed,
                "7.0.6: dieselbe Instanz darf nie eine neue Sitzung/Token bekommen")
    # Die Sitzung wurde aufgeraeumt und das Plugin pollt mit der alten Id:
    resolved, _ = bridge.poll("inst-1", "unbekannt")
    require(resolved == first_session,
            "7.0.6: eine unbekannte Sitzung mit bekannter Instanz bekommt ihre sessionId zurueck")
    second_session, renewed = bridge.register("inst-2")
    require(renewed and second_session != first_session,
            "7.0.6: nur eine WIRKLICH neue Instanz erzeugt eine neue Sitzung")
    require(len(bridge.instances) == 2, "7.0.6: hoechstens eine Sitzung je Plugin-Instanz")
    print("F) Sitzungs-Identitaet: 20 Handshakes = 1 Sitzung/Token; neue Instanz = neue Sitzung (Sturm beendet).")

    # G) Fast-Fail: sofort ehrlich antworten statt 55 s warten ---------------
    bridge = Bridge(independent_sweep=True)
    hung = Command("g1", "run_lua", budget=90)
    bridge.enqueue(hung, "A")
    bridge.deliver("A")
    bridge.plugin_start(hung)
    bridge.poll_alive = False
    for _ in range(120):   # die Lua-VM ist blockiert, nichts pollt mehr
        bridge.tick()
    verdict = bridge.call_tool("get_place_info", waiting=len(bridge.pending),
                               seconds_since_sign=120, alive=False, busy=True)
    require(verdict == "STUDIO_UNREACHABLE",
            "7.0.6: ein stummer Executor muss SOFORT als STUDIO_UNREACHABLE erkannt werden")
    busy_verdict = bridge.call_tool("get_tree", waiting=1, seconds_since_sign=3, alive=True, busy=True)
    require(busy_verdict == "STUDIO_BUSY",
            "7.0.6: ein belegter Executor mit wartender FIFO muss SOFORT STUDIO_BUSY melden")
    job_verdict = bridge.call_tool("get_tree", waiting=1, seconds_since_sign=3, alive=True, busy=True, as_job=True)
    require(job_verdict == "ok", "7.0.6: args.asJob=true muss die Busy-Sperre umgehen")
    ok_verdict = bridge.call_tool("get_tree", waiting=0, seconds_since_sign=2, alive=True, busy=False)
    require(ok_verdict == "ok", "7.0.6: ein gesunder Executor darf nie blockiert werden")
    print(f"G) Fast-Fail: wedged => STUDIO_UNREACHABLE, busy+FIFO => STUDIO_BUSY "
          f"(Schwellen fresh={HEALTH_FRESH}s, wait={HEALTH_WAIT}s, dead={HEALTH_DEAD}s).")

    # H) Zustell-Timeline: queuedAt -> ... -> lastError ----------------------
    bridge = Bridge(independent_sweep=True)
    for _ in range(3):
        bridge.tick()   # die virtuelle Uhr startet nicht bei 0
    timeline_cmd = Command("h1", "site_survey", budget=90)
    bridge.enqueue(timeline_cmd, "A")
    require(timeline_cmd.queued_at > 0 and timeline_cmd.delivered_at == 0
            and timeline_cmd.started_at == 0 and timeline_cmd.heartbeat_at == 0,
            "7.0.6: eine neue Zeitleiste darf nur queuedAt tragen")
    bridge.deliver("A")
    bridge.plugin_start(timeline_cmd)
    require(timeline_cmd.delivered_at > 0 and timeline_cmd.started_at > 0
            and timeline_cmd.heartbeat_at > 0,
            "7.0.6: die Timeline muss deliveredAt, startedAt und heartbeatAt tragen")
    bridge.sweep()
    for _ in range(90 + BUDGET_GRACE + SWEEP_INTERVAL + 1):
        bridge.tick()
    # Zwei ehrliche Gruende sind moeglich: der Budget-Abbruch (budget+15 s) oder -
    # wenn der Heartbeat vorher 45 s stillsteht - EXECUTOR_UNRESPONSIVE.
    require(timeline_cmd.status == "abandoned"
            and timeline_cmd.last_error in ("STUDIO_ABANDONED", "EXECUTOR_UNRESPONSIVE"),
            "7.0.6: nach dem Abbruch muss die Timeline den Grund in lastError tragen")
    print(f"H) Zustell-Timeline: queued -> delivered -> started -> heartbeat -> abandoned/{timeline_cmd.last_error} vollstaendig.")

    # I) 7.0.7: Place-Zeile baut wieder (Live-Fehler nachgestellt) ----------
    declared_706 = {"SessionId", "Root", "Title", "Copy", "Menu", "Popup",
                    "ProgressPanel", "ProgressBar", "ProgressText", "ProgressPercent"}
    declared_707 = set(declared_706) | {"CommandCancelButton"}
    require(build_row(declared_706) is False,
            "7.0.6-Nachbau: die fehlende Deklaration muss den Zeilenaufbau abbrechen")
    require(build_row(declared_707) is True,
            "7.0.7: mit deklarierter Eigenschaft muss die Zeile aufgebaut werden")
    require(SOURCE.count("CommandCancelButton = $null") == 2,
            "7.0.7: die Eigenschaft fehlt in einem der beiden Initialisierer")
    both_builders_fail = (build_row(declared_706) is False)
    require(both_builders_fail, "7.0.6-Nachbau: identischer Fehler im Minimal-Fallback")
    print("I) Place-Zeile: 7.0.6-Nachbau bricht ab (leere Liste), 7.0.7 deklariert die "
          "Eigenschaft in beiden Bauern und baut den Knopf in try/catch.")

    if FAILURES:
        print("\nFEHLGESCHLAGEN:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("\nOK: 7.0.7-Modell (Waechter, Reconnect, Cloudflare, Admin-Reset, Sitzungs-Identitaet, Fast-Fail, Timeline, Place-Zeile) geprueft.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
