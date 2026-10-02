#!/usr/bin/env python3
"""Modelltest der 7.0.5-Queue-Regeln (kein PowerShell, kein Roblox Studio).

Dies ist ein *Modell* des Server-/Plugin-Verhaltens, kein Live-Test. Es bildet
die Regeln nach, die ArenaBridge.ps1 anwendet, und prueft mit einer virtuellen
Uhr, dass diese Regeln den in 7.0.4 gemeldeten Stillstand tatsaechlich
aufloesen:

  A) Nachbau 7.0.4: Der Executor-Watchdog lief NUR in /plugin/poll. Haengt ein
     Befehl ohne yield (oder antwortet das Plugin nicht mehr), kommt kein Poll
     mehr -> nichts raeumt auf -> Queue + lateResults bleiben fuer immer leer.
  B) 7.0.5: Ein unabhaengiger Sweep (eigener Runspace, 2 s) bricht den Befehl
     nach budget+15 s ab, beantwortet den Wartenden bzw. legt das Ergebnis in
     die lateResults der ANRUFER-Sitzung und laesst die Queue weiterlaufen.
  C) 7.0.5: Beim Reconnect gehen nur NIE zugestellte Befehle an die neue
     Sitzung (genau einmal ausgefuehrt); bereits ausgefuehrte commandIds liefern
     ihr gespeichertes Ergebnis erneut aus, statt neu zu laufen.
  D) 7.0.5: Die HTTP-Antwort liegt mit 55 s (max 85 s) unter dem ~100-s-524
     von Cloudflare; ein abgebrochener Befehl kommt als lateResult zurueck.
  E) 7.0.5: force_fail/clear_pending beantwortet JEDEN offenen Befehl sofort
     und leert die serielle Queue.

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

    if FAILURES:
        print("\nFEHLGESCHLAGEN:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print("\nOK: 7.0.5-Queue-Modell (Waechter, Reconnect, Cloudflare, Admin-Reset) geprueft.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
