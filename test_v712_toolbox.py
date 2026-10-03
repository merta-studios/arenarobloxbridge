#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifikationstest fuer Arena Roblox Bridge 7.1.2 (Mini-Hotfix: haengende Toolbox-Befehle).

LIVE-BEFUND MIT 7.1.1 (03.10.2026, Place "Place1", Studio im Edit-Modus):
site_survey, world_style und style_lock liefen durch. Danach mehrere
Katalog-/Toolbox-Suchen (Katze, Hund, Fuchs, Hirsch, Kaninchen); catalog_status
meldete den Katalog als erreichbar, einzelne Detail-/Folgeaufrufe liefen in
Timeouts. Ein insert_asset (assetId 14124432577, sanitize=true, unpack=false,
Ziel game.Workspace, Name Wildlife_Cat) kehrte nie zurueck; der POST auf
/api/tool endete nach ca. 125,8 s in einem Cloudflare-HTTP-524. Ein spaeterer
bridge_status zeigte executor.alive=false, dispatcherBusy=false, queueDepth=0 -
waehrend /api/status gleichzeitig delivery.state='ok' meldete. Toolbox-Karten
blieben in der Oberflaeche dauerhaft auf "Macht gerade", ein Queue-Reset hing,
und mit zunehmenden Toolbox-Aufrufen wurde das Programm immer traeger (der vom
Nutzer berichtete RAM-Anstieg auf ca. 70 % ist eine Beobachtung aus den
Studio-/Bridge-Logs, KEIN von der Bridge gemessener Wert).

Dieser Test beweist die Ursachen in einem Modell der 7.1.1-Semantik, zeigt die
7.1.2-Semantik als Gegenprobe und prueft zusaetzlich den echten Quellcode in
ArenaBridge.ps1 (PowerShell-Server + eingebettetes Luau-Plugin). Es werden
AUSSCHLIESSLICH gemockte Katalog-/Studio-Aufrufe benutzt - keine Live-Bridge,
kein Token, kein echter Toolbox-Import.

  Test 1: schnelle erfolgreiche Suche + erfolgreicher Import
  Test 2: Katalog antwortet nie -> definierter Timeout, UI endet terminal
  Test 3: Asset-Import haengt lange -> kein zweiter Import, klare Erholung
  Test 4: Ausnahme / Abbruch / verspaetete Antwort -> Sperren frei, keine
          doppelte Einfuegung
  Test 5: zweiter paralleler Asset-Aufruf -> klarer BUSY-/Limit-Status
  Test 6: Executor-Heartbeat / Bridge-Status waehrend eines langsamen
          Toolbox-Aufrufs -> keine falsche "alive/ok"-Meldung
  Test 7: 200 wiederholte gemockte Aufrufe -> Queue, Tasks, Caches und
          Idempotenz-Speicher wachsen NICHT unbegrenzt
  Test 8: Quellcode-Abnahme (begrenzter Katalog-Client, Toolbox-Tor,
          Import-Sperre im Plugin, terminale UI-Zustaende, Cache-Grenzen,
          Versionsstand 7.1.2)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "ArenaBridge.ps1"
VERSION = "7.1.2"

# Grenzwerte, die der Fix im Quellcode setzt (werden in Test 8 gegengeprueft).
CATALOG_TIMEOUT_SEC = 12
CATALOG_BUDGET_SEC = 25
VALIDATE_TIMEOUT_SEC = 8
MAX_PENDING_PER_PLACE = 2
IMPORT_WEDGED_AFTER_SEC = 45
IDEMPOTENCY_WINDOW_SEC = 120
MAX_CACHE_ENTRIES = 400
STUDIO_HTTP_TIMEOUT_SEC = 55
CLOUDFLARE_524_SEC = 100


# ===========================================================================
# Quellcode laden
# ===========================================================================
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


def extract_ps_function(source: str, name: str) -> str:
    """Schneidet eine PowerShell-Funktion ueber die geschweiften Klammern aus."""
    match = re.search(rf"function\s+{re.escape(name)}\b", source)
    assert match, f"Funktion {name} nicht gefunden"
    start = source.index("{", match.end())
    depth = 0
    for index in range(start, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[match.start():index + 1]
    raise AssertionError(f"Funktion {name} ist nicht geschlossen")


# ===========================================================================
# Gemockte Welt: Katalog-Endpunkt und Studio-Executor
# ===========================================================================
class Clock:
    """Virtuelle Uhr - der Test laeuft ohne echtes Warten."""

    def __init__(self) -> None:
        self.now = 1000.0

    def advance(self, seconds: float) -> None:
        self.now += seconds


class MockCatalog:
    """Gemockter Roblox-Katalog. `mode` steuert das Verhalten pro Aufruf."""

    def __init__(self, clock: Clock, mode: str = "fast", latency: float = 0.4) -> None:
        self.clock = clock
        self.mode = mode            # fast | never | notfound | error
        self.latency = latency
        self.calls = 0

    def get(self, url: str, timeout: float):
        """Gibt (ok, data, elapsed, timed_out, not_found) zurueck."""
        self.calls += 1
        if self.mode == "fast":
            self.clock.advance(self.latency)
            return True, {"data": [{"id": 14124432577, "name": "Cat"}], "totalResults": 1}, self.latency, False, False
        if self.mode == "notfound":
            self.clock.advance(self.latency)
            return False, None, self.latency, False, True
        if self.mode == "error":
            self.clock.advance(self.latency)
            return False, None, self.latency, False, False
        # "never": der Endpunkt antwortet nie - der Client muss selbst abbrechen.
        self.clock.advance(timeout)
        return False, None, timeout, True, False


class MockExecutor:
    """Gemockter Studio-Plugin-Executor (ein Befehl zur Zeit, eigener Lebens-Tick)."""

    def __init__(self, clock: Clock) -> None:
        self.clock = clock
        self.last_tick = clock.now
        self.running_tool = ""
        self.started_at = 0.0
        self.alive_flag = True
        # Einzelbelegung fuer den nativen InsertService:LoadAsset.
        self.import_active = False
        self.import_asset_id = None
        self.import_started_at = 0.0
        self.native_loads_started = 0
        self.inserted = []          # tatsaechlich eingefuegte Modelle

    # -- Lebenszeichen ---------------------------------------------------
    def tick(self) -> None:
        self.last_tick = self.clock.now

    @property
    def alive(self) -> bool:
        # Wie Get-SessionExecutorSnapshot: Tick darf hoechstens 12 s alt sein.
        return self.alive_flag and (self.clock.now - self.last_tick) <= 12

    def freeze(self) -> None:
        """Lua-VM blockiert: kein Tick mehr (genau der Live-Zustand)."""
        self.alive_flag = False

    # -- insert_asset ----------------------------------------------------
    def insert_asset(self, asset_id, name, hang_seconds: float, http_deadline: float):
        """Modelliert tools.insert_asset 7.1.2 inklusive Einzelbelegung."""
        if self.import_active:
            running_for = int(self.clock.now - self.import_started_at)
            if running_for >= IMPORT_WEDGED_AFTER_SEC:
                return {"ok": False, "code": "TOOLBOX_IMPORT_WEDGED",
                        "cancellable": False, "stuckForSeconds": running_for}
            return {"ok": False, "code": "TOOLBOX_IMPORT_IN_FLIGHT",
                    "runningSeconds": running_for}

        self.import_active = True
        self.import_asset_id = asset_id
        self.import_started_at = self.clock.now
        self.native_loads_started += 1

        if hang_seconds > http_deadline:
            # Der native Aufruf kehrt innerhalb der HTTP-Frist NICHT zurueck.
            # task.cancel beendet nur den Luau-Thread - import_active bleibt
            # deshalb absichtlich stehen (ehrlicher "haengt noch"-Zustand).
            self.clock.advance(http_deadline)
            return None

        self.clock.advance(hang_seconds)
        self.import_active = False
        self.import_asset_id = None
        self.import_started_at = 0.0
        self.inserted.append({"assetId": asset_id, "name": name})
        return {"ok": True, "inserted": [{"name": name}], "assetId": asset_id, "count": 1}


# ===========================================================================
# Modell der BRIDGE - 7.1.1 (kaputt) und 7.1.2 (repariert)
# ===========================================================================
class BridgeModel:
    """Gemeinsame Basis: Aktivitaetsliste (UI), Cache, Queue, Status."""

    def __init__(self, clock: Clock, catalog: MockCatalog, executor: MockExecutor) -> None:
        self.clock = clock
        self.catalog = catalog
        self.executor = executor
        self.session = "sid-place1"
        self.activities = {}            # activityId -> {"phase": ...}
        self.next_activity = 0
        self.asset_cache = {}           # key -> value (Modell von asset_cache.json)
        self.cache_writes = 0           # vollstaendige Serialisierungen der Datei
        self.pending_commands = {}      # commandId -> tool
        self.open_polls = 0
        self.last_http_contact = clock.now

    # -- UI-Aktivitaeten -------------------------------------------------
    def new_activity(self, tool: str) -> str:
        self.next_activity += 1
        activity_id = f"act{self.next_activity}"
        self.activities[activity_id] = {"tool": tool, "phase": "running"}
        return activity_id

    def complete_activity(self, activity_id: str, phase: str) -> None:
        if activity_id in self.activities:
            self.activities[activity_id]["phase"] = phase

    def running_activities(self):
        return [a for a in self.activities.values() if a["phase"] == "running"]

    # -- Cache -----------------------------------------------------------
    def cache_put_many(self, pairs: dict) -> None:
        raise NotImplementedError


class Bridge711(BridgeModel):
    """Nachbau der 7.1.1-Semantik - hier MUSS der Fehler auftreten."""

    def cache_put_many(self, pairs: dict) -> None:
        # 7.1.1: Add-CacheEntry je Eintrag -> je Eintrag die GANZE Datei neu.
        for key, value in pairs.items():
            self.asset_cache[key] = value
            self.cache_writes += 1      # keine Obergrenze, kein Sammel-Schreiben

    def search_assets(self) -> dict:
        """Invoke-AssetSearch 7.1.1: 2 Versuche a 20 s + 1,5 s Pause + 20 s Details."""
        started = self.clock.now
        result = None
        for _ in range(2):              # <-- automatische Wiederholung
            ok, data, _, _, _ = self.catalog.get("search", 20)
            if ok:
                result = data
                break
            self.clock.advance(1.5)     # Start-Sleep -Milliseconds 1500
        if result is None:
            return {"ok": False, "code": "CATALOG_UNAVAILABLE",
                    "elapsed": self.clock.now - started}
        ok, _, _, _, _ = self.catalog.get("details", 20)
        return {"ok": True, "elapsed": self.clock.now - started}

    def insert_asset(self, asset_id, name, hang_seconds) -> dict:
        """/api/tool 7.1.1: Validierung (20 s) + Studio-Wartezeit (55 s)."""
        activity_id = self.new_activity("insert_asset")
        started = self.clock.now
        self.catalog.get("validate", 20)                    # Vorpruefung, ungedrosselt
        outcome = self.executor.insert_asset(asset_id, name, hang_seconds, STUDIO_HTTP_TIMEOUT_SEC)
        elapsed = self.clock.now - started
        if outcome is None:
            # 7.1.1: Der Verlaufseintrag bleibt ABSICHTLICH auf "running".
            return {"ok": False, "code": "STUDIO_TIMEOUT", "elapsed": elapsed,
                    "activityId": activity_id}
        self.complete_activity(activity_id, "completed" if outcome["ok"] else "failed")
        return dict(outcome, elapsed=elapsed, activityId=activity_id)

    def delivery_state(self) -> dict:
        """Get-StudioDeliveryHealth 7.1.1 - executorAlive erst ab 45 s geprueft."""
        age = self.clock.now - self.last_http_contact
        waiting = len(self.pending_commands)
        state = "ok"
        if self.open_polls > 0:
            state = "ok"
        elif age <= 15:
            state = "ok"
        elif waiting > 0 and age > 25:
            state = "wedged"
        elif not self.executor.alive and age > 45:
            state = "wedged"
        elif age > 45:
            state = "quiet"
        return {"state": state, "executorAlive": self.executor.alive}


class Bridge712(BridgeModel):
    """Nachbau der 7.1.2-Semantik - der Fix."""

    def __init__(self, clock, catalog, executor):
        super().__init__(clock, catalog, executor)
        self.toolbox_slots = 0
        self.import_lock = None         # {"assetId", "startedAt", "insertKey", "unconfirmed"}
        self.insert_results = {}        # insertKey -> Ergebnis (Idempotenz)
        self.insert_at = {}             # insertKey -> Zeitstempel

    # -- Cache mit harten Grenzen ---------------------------------------
    def cache_put_many(self, pairs: dict) -> None:
        for key, value in pairs.items():
            self.asset_cache[key] = value
        # Verdraengung der aeltesten Eintraege (Limit-AssetCache).
        while len(self.asset_cache) > MAX_CACHE_ENTRIES:
            self.asset_cache.pop(next(iter(self.asset_cache)))
        self.cache_writes += 1          # EIN Schreibvorgang fuer alle Eintraege

    # -- Toolbox-Tor -----------------------------------------------------
    def _enter_slot(self):
        if self.toolbox_slots >= MAX_PENDING_PER_PLACE:
            return False, {"ok": False, "code": "TOOLBOX_BUSY",
                           "activeRequests": self.toolbox_slots,
                           "limit": MAX_PENDING_PER_PLACE}
        self.toolbox_slots += 1
        return True, None

    def _exit_slot(self):
        self.toolbox_slots = max(0, self.toolbox_slots - 1)

    # -- Katalogaufruf mit hartem Limit ----------------------------------
    def _catalog(self, what: str, timeout: float):
        ok, data, elapsed, timed_out, not_found = self.catalog.get(what, timeout)
        return ok, data, elapsed, timed_out, not_found

    def search_assets(self) -> dict:
        activity_id = self.new_activity("search_assets")
        entered, busy = self._enter_slot()
        if not entered:
            self.complete_activity(activity_id, "failed")
            return dict(busy, activityId=activity_id, elapsed=0.0)
        started = self.clock.now
        try:
            ok, data, _, timed_out, _ = self._catalog("search", CATALOG_TIMEOUT_SEC)
            if not ok:
                code = "CATALOG_TIMEOUT" if timed_out else "CATALOG_UNAVAILABLE"
                self.complete_activity(activity_id, "timed_out" if timed_out else "failed")
                return {"ok": False, "code": code, "activityId": activity_id,
                        "elapsed": self.clock.now - started}
            remaining = CATALOG_BUDGET_SEC - (self.clock.now - started)
            if remaining >= 3:
                ok2, _, _, timed2, _ = self._catalog("details", min(CATALOG_TIMEOUT_SEC, remaining))
                if ok2:
                    self.cache_put_many({f"detail|{i}": {"x": 1} for i in range(20)})
            self.complete_activity(activity_id, "completed")
            return {"ok": True, "activityId": activity_id, "elapsed": self.clock.now - started}
        finally:
            self._exit_slot()           # Freigabe IMMER - auch bei Ausnahme

    # -- Import mit Einzelbelegung + Idempotenz --------------------------
    def _insert_key(self, asset_id, parent_ref, name, request_id=None):
        if request_id:
            return f"{self.session}|rid|{request_id}"
        return f"{self.session}|fp|{asset_id}|{parent_ref}|{name}"

    def insert_asset(self, asset_id, name, hang_seconds, parent_ref="game.Workspace",
                     request_id=None, allow_duplicate=False, raise_in_studio=False) -> dict:
        activity_id = self.new_activity("insert_asset")
        key = self._insert_key(asset_id, parent_ref, name, request_id)

        # 1) Idempotenz: dieselbe Einfuegung im Fenster = Wiedergabe, kein 2. Einbau.
        if not allow_duplicate and key in self.insert_at:
            if (self.clock.now - self.insert_at[key]) <= IDEMPOTENCY_WINDOW_SEC:
                self.complete_activity(activity_id, "completed")
                return dict(self.insert_results[key], idempotentReplay=True,
                            activityId=activity_id)
            self.insert_at.pop(key)
            self.insert_results.pop(key, None)

        # 2) Einzelbelegung
        if self.import_lock is not None:
            running_for = int(self.clock.now - self.import_lock["startedAt"])
            if self.import_lock.get("unconfirmed") or running_for >= IMPORT_WEDGED_AFTER_SEC:
                self.import_lock["wedged"] = True
                self.complete_activity(activity_id, "failed")
                return {"ok": False, "code": "TOOLBOX_IMPORT_WEDGED", "cancellable": False,
                        "stuckAssetId": self.import_lock["assetId"],
                        "stuckForSeconds": running_for, "activityId": activity_id,
                        "howToFix": "Roblox Studio komplett schliessen und neu oeffnen."}
            self.complete_activity(activity_id, "failed")
            return {"ok": False, "code": "TOOLBOX_IMPORT_IN_FLIGHT",
                    "runningSeconds": running_for, "activityId": activity_id}

        self.import_lock = {"assetId": asset_id, "startedAt": self.clock.now,
                            "insertKey": key, "unconfirmed": False}
        self.pending_commands[f"cmd-{activity_id}"] = "insert_asset"
        started = self.clock.now
        try:
            # Vorpruefung laeuft durch dasselbe Tor und hat ein hartes Limit.
            entered, busy = self._enter_slot()
            if entered:
                try:
                    self._catalog("validate", VALIDATE_TIMEOUT_SEC)
                finally:
                    self._exit_slot()

            if raise_in_studio:
                raise RuntimeError("Executor-Ausnahme waehrend des Imports")

            outcome = self.executor.insert_asset(asset_id, name, hang_seconds,
                                                 STUDIO_HTTP_TIMEOUT_SEC)
            elapsed = self.clock.now - started
            if outcome is None:
                # Kein Ergebnis vor der HTTP-Frist. Die Sperre bleibt
                # ABSICHTLICH stehen (nativer Load evtl. noch aktiv), aber der
                # UI-Eintrag wird terminal und die Queue freigegeben.
                self.import_lock["unconfirmed"] = True
                self.pending_commands.pop(f"cmd-{activity_id}", None)
                self.complete_activity(activity_id, "timed_out")
                return {"ok": False, "code": "TOOLBOX_IMPORT_UNCONFIRMED",
                        "importLocked": True, "cancellable": False,
                        "elapsed": elapsed, "activityId": activity_id,
                        "howToFix": "Nicht wiederholen. Roblox Studio komplett neu starten."}

            self.import_lock = None     # Endzustand -> Sperre frei
            self.pending_commands.pop(f"cmd-{activity_id}", None)
            if outcome["ok"]:
                self.insert_results[key] = dict(outcome)
                self.insert_at[key] = self.clock.now
                self._trim_idempotency()
                self.complete_activity(activity_id, "completed")
            else:
                self.complete_activity(activity_id, "failed")
            return dict(outcome, elapsed=elapsed, activityId=activity_id)
        except RuntimeError as exc:
            # Ausnahme: Sperre UND Queue werden sauber geraeumt, UI terminal.
            self.import_lock = None
            self.pending_commands.pop(f"cmd-{activity_id}", None)
            self.complete_activity(activity_id, "failed")
            return {"ok": False, "code": "TOOLBOX_FAILED", "error": str(exc),
                    "activityId": activity_id, "elapsed": self.clock.now - started}

    def cancel_insert(self, activity_id: str) -> None:
        """Client bricht ab: Sperre und Queue muessen trotzdem sauber enden."""
        self.import_lock = None
        self.pending_commands.pop(f"cmd-{activity_id}", None)
        self.complete_activity(activity_id, "cancelled")

    def _trim_idempotency(self) -> None:
        if len(self.insert_at) > 64:
            cutoff = self.clock.now - IDEMPOTENCY_WINDOW_SEC
            for key in [k for k, at in self.insert_at.items() if at < cutoff]:
                self.insert_at.pop(key, None)
                self.insert_results.pop(key, None)
            # Reicht das Alter nicht (viele verschiedene Assets in kurzer
            # Zeit), fliegen die aeltesten Eintraege bis zur harten Grenze.
            while len(self.insert_at) > 64:
                oldest = min(self.insert_at, key=self.insert_at.get)
                self.insert_at.pop(oldest, None)
                self.insert_results.pop(oldest, None)

    # -- ehrlicher Zustellzustand ---------------------------------------
    def delivery_state(self) -> dict:
        age = self.clock.now - self.last_http_contact
        waiting = len(self.pending_commands)
        alive = self.executor.alive
        ever_reported = True
        state = "ok"
        if not alive and waiting > 0 and age > 25:
            state = "wedged"
        elif not alive and age > 45:
            state = "wedged"
        elif not alive and ever_reported:
            state = "executor_down"
        elif self.open_polls > 0 or age <= 15:
            state = "ok"
        elif waiting > 0 and age > 25:
            state = "wedged"
        elif age > 45:
            state = "quiet"
        return {"state": state, "executorAlive": alive}


def fresh(mode: str = "fast"):
    clock = Clock()
    catalog = MockCatalog(clock, mode)
    executor = MockExecutor(clock)
    return clock, catalog, executor


# ===========================================================================
# TESTS
# ===========================================================================
def test_1_fast_success():
    """Schnelle erfolgreiche Suche und erfolgreicher Import."""
    clock, catalog, executor = fresh("fast")
    bridge = Bridge712(clock, catalog, executor)

    search = bridge.search_assets()
    assert search["ok"], f"Suche muss gelingen: {search}"
    assert search["elapsed"] < 5, f"Schnelle Suche darf nicht bummeln ({search['elapsed']} s)"
    assert bridge.toolbox_slots == 0, "Der Toolbox-Slot muss nach der Suche frei sein"

    result = bridge.insert_asset(14124432577, "Wildlife_Cat", hang_seconds=1.2)
    assert result["ok"], f"Import muss gelingen: {result}"
    assert len(executor.inserted) == 1, "Genau EIN Modell darf eingefuegt sein"
    assert bridge.import_lock is None, "Die Import-Sperre muss freigegeben sein"
    assert bridge.pending_commands == {}, "Die Queue muss leer sein"
    assert not bridge.running_activities(), "Keine Karte darf auf 'Macht gerade' stehen"
    phases = {a["phase"] for a in bridge.activities.values()}
    assert phases <= {"completed", "failed", "timed_out", "cancelled"}, phases


def test_2_catalog_never_answers():
    """Katalog-Endpunkt, der nie antwortet -> definierter Timeout, UI nicht busy."""
    # --- 7.1.1: die eigene Wiederholungsschleife haelt die Anfrage fest ----
    clock, catalog, executor = fresh("never")
    legacy = Bridge711(clock, catalog, executor)
    old = legacy.search_assets()
    assert old["ok"] is False
    assert old["elapsed"] >= 41.5, (
        f"7.1.1 musste 2 x 20 s + 1,5 s warten, gemessen {old['elapsed']} s")
    assert catalog.calls == 2, "7.1.1 wiederholt nach einem Timeout automatisch"

    # --- 7.1.1 insert_asset: Validierung + Studio-Wartezeit > Cloudflare ---
    clock, catalog, executor = fresh("never")
    legacy = Bridge711(clock, catalog, executor)
    hung = legacy.insert_asset(14124432577, "Wildlife_Cat", hang_seconds=10_000)
    assert hung["code"] == "STUDIO_TIMEOUT"
    assert hung["elapsed"] >= 75, (
        f"7.1.1: 20 s Validierung + 55 s Studio = {hung['elapsed']} s auf EINER Anfrage")
    assert legacy.activities[hung["activityId"]]["phase"] == "running", (
        "BEWEIS fuer das dauerhafte 'Macht gerade': 7.1.1 laesst die Karte offen")

    # --- 7.1.2: ein Versuch, hartes Limit, typisierter Fehler, UI terminal -
    clock, catalog, executor = fresh("never")
    bridge = Bridge712(clock, catalog, executor)
    new = bridge.search_assets()
    assert new["ok"] is False
    assert new["code"] == "CATALOG_TIMEOUT", f"typisierter Fehler erwartet: {new}"
    assert new["elapsed"] <= CATALOG_TIMEOUT_SEC + 0.5, (
        f"7.1.2 muss nach {CATALOG_TIMEOUT_SEC} s abbrechen, gemessen {new['elapsed']} s")
    assert catalog.calls == 1, "KEINE automatische Wiederholung nach einem Timeout"
    assert bridge.toolbox_slots == 0, "Der Slot muss auch nach dem Timeout frei sein"
    assert not bridge.running_activities(), "Die UI darf nicht im Busy-Zustand enden"
    assert bridge.activities[new["activityId"]]["phase"] == "timed_out"


def test_3_import_hangs():
    """Asset-Import, der lange haengt -> kein zweiter paralleler Import."""
    clock, catalog, executor = fresh("fast")
    bridge = Bridge712(clock, catalog, executor)

    first = bridge.insert_asset(14124432577, "Wildlife_Cat", hang_seconds=10_000)
    assert first["code"] == "TOOLBOX_IMPORT_UNCONFIRMED", first
    assert first["cancellable"] is False, "Ein nativer LoadAsset darf NICHT als abbrechbar gelten"
    assert first["importLocked"] is True
    assert "Studio" in first["howToFix"], "Die Antwort muss die sichere Erholung nennen"
    assert bridge.activities[first["activityId"]]["phase"] == "timed_out", (
        "Auch der haengende Import muss in der UI terminal werden")
    assert executor.native_loads_started == 1

    # Zweiter Versuch waehrend des Haengers: KEIN zweiter nativer Ladevorgang.
    second = bridge.insert_asset(14124432577, "Wildlife_Cat_2", hang_seconds=10_000)
    assert second["code"] == "TOOLBOX_IMPORT_WEDGED", second
    assert second["cancellable"] is False
    assert executor.native_loads_started == 1, (
        "Es darf KEIN zweiter InsertService:LoadAsset gestartet worden sein")
    assert len(executor.inserted) == 0, "Nichts darf eingefuegt worden sein"

    # Auch ein drittes Mal: weiterhin gesperrt, keine Retry-Schleife.
    third = bridge.insert_asset(99999, "Wildlife_Dog", hang_seconds=1)
    assert third["code"] == "TOOLBOX_IMPORT_WEDGED", third
    assert executor.native_loads_started == 1
    assert not bridge.running_activities(), "Keine Karte bleibt auf 'Macht gerade'"


def test_4_exception_cancel_late_answer():
    """Ausnahme / Abbruch / verspaetete Antwort -> sauber aufgeraeumt, kein Doppeleinbau."""
    # a) Ausnahme im Studio-Pfad
    clock, catalog, executor = fresh("fast")
    bridge = Bridge712(clock, catalog, executor)
    boom = bridge.insert_asset(14124432577, "Wildlife_Cat", hang_seconds=1,
                               raise_in_studio=True)
    assert boom["ok"] is False and boom["code"] == "TOOLBOX_FAILED", boom
    assert bridge.import_lock is None, "Nach einer Ausnahme muss die Sperre frei sein"
    assert bridge.pending_commands == {}, "Nach einer Ausnahme muss die Queue leer sein"
    assert bridge.toolbox_slots == 0, "Nach einer Ausnahme muss der Slot frei sein"
    assert not bridge.running_activities()

    # b) Abbruch durch den Client
    clock, catalog, executor = fresh("fast")
    bridge = Bridge712(clock, catalog, executor)
    activity = bridge.new_activity("insert_asset")
    bridge.import_lock = {"assetId": 1, "startedAt": clock.now, "insertKey": "k",
                          "unconfirmed": False}
    bridge.pending_commands[f"cmd-{activity}"] = "insert_asset"
    bridge.cancel_insert(activity)
    assert bridge.import_lock is None and bridge.pending_commands == {}
    assert bridge.activities[activity]["phase"] == "cancelled"

    # c) Verspaetete Antwort / Wiederholung nach Client-Timeout: KEIN zweiter Einbau
    clock, catalog, executor = fresh("fast")
    bridge = Bridge712(clock, catalog, executor)
    first = bridge.insert_asset(14124432577, "Wildlife_Cat", hang_seconds=1.0)
    assert first["ok"] and len(executor.inserted) == 1
    clock.advance(5)
    retry = bridge.insert_asset(14124432577, "Wildlife_Cat", hang_seconds=1.0)
    assert retry.get("idempotentReplay") is True, f"Wiederholung muss wiedergegeben werden: {retry}"
    assert len(executor.inserted) == 1, "Das Modell darf NICHT doppelt eingefuegt werden"
    assert executor.native_loads_started == 1

    # Ausdruecklich gewollte Zweitkopie bleibt moeglich.
    again = bridge.insert_asset(14124432577, "Wildlife_Cat", hang_seconds=1.0,
                                allow_duplicate=True)
    assert again["ok"] and len(executor.inserted) == 2, (
        "allowDuplicate=true muss eine bewusste Zweitkopie weiterhin erlauben")


def test_5_parallel_call_is_busy():
    """Zweiter paralleler Asset-Aufruf -> klarer BUSY-/Limit-Status."""
    clock, catalog, executor = fresh("fast")
    bridge = Bridge712(clock, catalog, executor)

    # Das Limit wird durch bereits belegte Slots dargestellt (paralleler Lauf).
    bridge.toolbox_slots = MAX_PENDING_PER_PLACE
    busy = bridge.search_assets()
    assert busy["ok"] is False and busy["code"] == "TOOLBOX_BUSY", busy
    assert busy["limit"] == MAX_PENDING_PER_PLACE
    assert busy["elapsed"] == 0, "Ein BUSY muss SOFORT zurueckkommen, nicht warten"
    assert catalog.calls == 0, "Bei BUSY darf kein Katalogaufruf starten"
    assert not bridge.running_activities(), "Auch BUSY ist ein Endzustand"

    # Zweiter Import waehrend eines laufenden Imports -> eigener Code.
    bridge.toolbox_slots = 0
    bridge.import_lock = {"assetId": 111, "startedAt": clock.now, "insertKey": "k",
                          "unconfirmed": False}
    parallel = bridge.insert_asset(222, "Wildlife_Dog", hang_seconds=1)
    assert parallel["code"] == "TOOLBOX_IMPORT_IN_FLIGHT", parallel
    assert executor.native_loads_started == 0, "Kein zweiter nativer Ladevorgang"


def test_6_status_must_not_lie():
    """Executor-Heartbeat / Bridge-Status waehrend eines langsamen Toolbox-Aufrufs."""
    # --- 7.1.1: 'ok' trotz toten Executors (genau der Live-Widerspruch) ----
    clock, catalog, executor = fresh("fast")
    legacy = Bridge711(clock, catalog, executor)
    executor.freeze()                       # Lua-VM blockiert, kein Tick mehr
    clock.advance(20)                       # Executor ist jetzt nachweislich tot
    legacy.last_http_contact = clock.now    # aber HTTP-Kontakt (Outbox) ist frisch
    old = legacy.delivery_state()
    assert old["executorAlive"] is False
    assert old["state"] == "ok", (
        "BEWEIS: 7.1.1 meldete delivery.state='ok' bei executorAlive=false")

    # --- 7.1.2: derselbe Zustand wird ehrlich gemeldet --------------------
    clock, catalog, executor = fresh("fast")
    bridge = Bridge712(clock, catalog, executor)
    executor.freeze()
    clock.advance(20)
    bridge.last_http_contact = clock.now
    new = bridge.delivery_state()
    assert new["executorAlive"] is False
    assert new["state"] != "ok", "Ein toter Executor darf NIE als 'ok' gemeldet werden"
    assert new["state"] == "executor_down", new

    # Mit wartender Arbeit und laengerer Stille wird daraus 'wedged'.
    bridge.pending_commands["cmd-x"] = "insert_asset"
    clock.advance(30)
    wedged = bridge.delivery_state()
    assert wedged["state"] == "wedged", wedged

    # Ein LEBENDER Executor waehrend eines langsamen Aufrufs bleibt 'ok'.
    clock, catalog, executor = fresh("fast")
    bridge = Bridge712(clock, catalog, executor)
    for _ in range(10):
        clock.advance(5)
        executor.tick()                     # Heartbeat laeuft weiter
        bridge.last_http_contact = clock.now
        assert bridge.delivery_state()["state"] == "ok"


def test_7_no_unbounded_growth():
    """200 wiederholte gemockte Aufrufe -> nichts waechst unbegrenzt."""
    clock, catalog, executor = fresh("fast")
    legacy = Bridge711(clock, catalog, executor)
    for _ in range(50):
        legacy.cache_put_many({f"detail|{n}": {"payload": "x" * 64} for n in range(20)})
    assert legacy.cache_writes == 50 * 20, (
        "BEWEIS: 7.1.1 schrieb die ganze Cache-Datei JE EINTRAG "
        f"({legacy.cache_writes} Schreibvorgaenge)")
    assert len(legacy.asset_cache) == 20

    clock, catalog, executor = fresh("fast")
    bridge = Bridge712(clock, catalog, executor)
    for round_index in range(50):
        bridge.cache_put_many(
            {f"detail|{round_index}-{n}": {"payload": "x" * 64} for n in range(20)})
    assert bridge.cache_writes == 50, (
        f"7.1.2 braucht EINEN Schreibvorgang je Stapel ({bridge.cache_writes})")
    assert len(bridge.asset_cache) <= MAX_CACHE_ENTRIES, (
        f"Der Asset-Cache muss bei {MAX_CACHE_ENTRIES} Eintraegen gedeckelt sein "
        f"({len(bridge.asset_cache)})")

    # 200 Toolbox-Aufrufe am Stueck: Slots, Queue und Idempotenz bleiben klein.
    clock, catalog, executor = fresh("fast")
    bridge = Bridge712(clock, catalog, executor)
    for index in range(200):
        bridge.search_assets()
        bridge.insert_asset(index, f"Model_{index}", hang_seconds=0.2)
    assert bridge.toolbox_slots == 0, "Kein Slot darf leaken"
    assert bridge.pending_commands == {}, "Kein Queue-Eintrag darf leaken"
    assert bridge.import_lock is None, "Keine Import-Sperre darf leaken"
    assert len(bridge.insert_at) <= 64, (
        f"Der Idempotenz-Speicher muss gedeckelt sein ({len(bridge.insert_at)})")
    assert len(bridge.asset_cache) <= MAX_CACHE_ENTRIES
    assert not bridge.running_activities(), "Keine Karte bleibt auf 'Macht gerade'"
    assert len(bridge.activities) == 400
    assert all(a["phase"] in ("completed", "failed", "timed_out", "cancelled")
               for a in bridge.activities.values())


def test_8_source(source: str, lua: str):
    """Quellcode-Abnahme des Mini-Fixes in ArenaBridge.ps1."""
    # -- 1) EIN begrenzter Katalog-Client, keine Wiederholungen ------------
    assert "function Invoke-CatalogHttp" in source, "Invoke-CatalogHttp fehlt"
    catalog_http = extract_ps_function(source, "Invoke-CatalogHttp")
    assert "-TimeoutSec $timeoutSeconds" in catalog_http
    assert "[Math]::Min(20, $timeoutSeconds)" in catalog_http
    search = extract_ps_function(source, "Invoke-AssetSearch")
    assert "for ($attempt = 1; $attempt -le 2" not in search, (
        "Die automatische Wiederholungsschleife muss weg sein")
    assert "Start-Sleep" not in search, "Kein Start-Sleep mehr im Katalogpfad"
    assert "Invoke-RestMethod" not in search, (
        "Invoke-AssetSearch darf nicht mehr direkt Invoke-RestMethod aufrufen")
    details = extract_ps_function(source, "Invoke-AssetDetails")
    assert "Invoke-RestMethod" not in details, (
        "Invoke-AssetDetails darf nicht mehr direkt Invoke-RestMethod aufrufen")
    assert "MaxDetailIdsPerCall" in details, "Die Id-Obergrenze fehlt"
    assert "CatalogBudgetSec" in details, "Das Gesamtbudget im 404-Pfad fehlt"
    validation = extract_ps_function(source, "Invoke-AssetValidation")
    assert "Invoke-CatalogHttp" in validation and "Invoke-RestMethod" not in validation
    status_tool = extract_ps_function(source, "Invoke-CatalogStatus")
    assert "Invoke-CatalogHttp" in status_tool and "Invoke-RestMethod" not in status_tool
    assert "CATALOG_TIMEOUT" in source, "Der typisierte Timeout-Fehler fehlt"

    # -- 2) Grenzwerte ------------------------------------------------------
    limits = source[source.index("ToolboxLimits = [hashtable]"):][:1200]
    for name, value in (("MaxPendingPerPlace", MAX_PENDING_PER_PLACE),
                        ("CatalogTimeoutSec", CATALOG_TIMEOUT_SEC),
                        ("CatalogBudgetSec", CATALOG_BUDGET_SEC),
                        ("ImportWedgedAfterSec", IMPORT_WEDGED_AFTER_SEC),
                        ("IdempotencyWindowSec", IDEMPOTENCY_WINDOW_SEC),
                        ("MaxCacheEntries", MAX_CACHE_ENTRIES)):
        assert re.search(rf"{name}\s*=\s*{value}\b", limits), f"{name} = {value} fehlt"
    assert CATALOG_TIMEOUT_SEC + STUDIO_HTTP_TIMEOUT_SEC < CLOUDFLARE_524_SEC, (
        "Katalogzeit + Studio-Wartezeit muessen unter der 524-Grenze bleiben")
    assert VALIDATE_TIMEOUT_SEC + STUDIO_HTTP_TIMEOUT_SEC < CLOUDFLARE_524_SEC

    # -- 3) Toolbox-Tor mit garantierter Freigabe ---------------------------
    gate = extract_ps_function(source, "Invoke-ToolboxServerTool")
    assert "Enter-ToolboxSlot" in gate and "Exit-ToolboxSlot $slot.sessionKey" in gate
    assert "} finally {" in gate, "Der Slot muss in finally freigegeben werden"
    assert "TOOLBOX_FAILED" in gate, "Eine Ausnahme muss einen Endzustand liefern"
    server_tool = extract_ps_function(source, "Invoke-ServerTool")
    for tool in ("search_assets", "asset_details", "validate_asset", "catalog_status"):
        assert re.search(rf"'{tool}'\s+\{{ return \(Invoke-ToolboxServerTool", server_tool), (
            f"{tool} laeuft nicht durch das Toolbox-Tor")
    assert "TOOLBOX_BUSY" in extract_ps_function(source, "Enter-ToolboxSlot")

    # -- 4) Import: Einzelbelegung, Idempotenz, ehrlich nicht abbrechbar ----
    enter_import = extract_ps_function(source, "Enter-ToolboxImport")
    assert "TOOLBOX_IMPORT_WEDGED" in enter_import
    assert "TOOLBOX_IMPORT_IN_FLIGHT" in enter_import
    assert "cancellable = $false" in enter_import, (
        "Die Bridge darf keinen Abbruch vortaeuschen")
    assert "close Roblox Studio COMPLETELY" in enter_import, "Die Erholung fehlt"
    assert "function Get-ToolboxInsertKey" in source
    assert "function Save-ToolboxInsertResult" in source
    assert "idempotentReplay" in source, "Der Idempotenz-Schutz fehlt"
    assert "Set-ToolboxImportUnconfirmed" in source
    assert "TOOLBOX_IMPORT_UNCONFIRMED" in source
    trim = extract_ps_function(source, "Save-ToolboxInsertResult")
    assert "ToolboxInsertAt.Count -gt 64" in trim, (
        "Der Idempotenz-Speicher muss begrenzt werden")

    # -- 5) delivery.state darf nicht mehr luegen ---------------------------
    health = extract_ps_function(source, "Get-StudioDeliveryHealth")
    assert "$executorAlive = [bool]$executor.alive" in health
    assert "executor_down" in health, "Der ehrliche Zustand 'executor_down' fehlt"
    assert health.index("-not $executorAlive") < health.index("$openPolls -gt 0 -or $age -le 15"), (
        "executorAlive muss VOR dem reinen Lebenszeichen geprueft werden")
    assert "stateReason" in health

    # -- 6) Terminale UI-Zustaende -----------------------------------------
    complete = extract_ps_function(source, "Complete-ArenaActivity")
    assert "[string]$terminalPhase = ''" in complete
    assert "$phase = $terminalPhase" in complete
    kind = extract_ps_function(source, "Get-ArenaActivityKind")
    assert "$phase -eq 'timed_out' -or $phase -eq 'cancelled'" in kind
    assert "$toolArgs (To-Json $timeoutBody 12) 'timed_out'" in source, (
        "Der STUDIO_TIMEOUT-Pfad muss den Verlaufseintrag terminal machen")

    # -- 7) Cache-Grenzen und Sammel-Schreiben ------------------------------
    assert "function Limit-AssetCache" in source
    save_cache = extract_ps_function(source, "Save-AssetCache")
    assert "Limit-AssetCache $cache" in save_cache
    assert "MaxCacheBytes" in save_cache
    add_many = extract_ps_function(source, "Add-CacheEntries")
    assert "Monitor]::Enter($Shared.AssetCacheLock)" in add_many
    assert "} finally {" in add_many, "Das Cache-Schloss muss in finally fallen"
    get_entry = extract_ps_function(source, "Get-CacheEntry")
    assert "if (-not ($cache.PSObject.Properties.Name -contains $key))" in get_entry, (
        "Die falsche Klammerung in Get-CacheEntry ist nicht repariert")
    assert "Add-CacheEntries $detailPairs" in source, (
        "Die Detail-Eintraege muessen in EINEM Zug gecacht werden")

    # -- 8) Aufraeumen beim Sitzungsende ------------------------------------
    assert "$script:Shared.ToolboxSlots.TryRemove($SessionId" in source
    assert "$script:Shared.ToolboxImportLocks.TryRemove($SessionId" in source

    # -- 9) Plugin: nativer LoadAsset ist nicht abbrechbar -------------------
    assert "local assetImportState" in lua, "Die Einzelbelegung im Plugin fehlt"
    assert "ASSET_IMPORT_WEDGED_AFTER = 45" in lua
    assert "local function runAssetImport(args, assetId, parent)" in lua
    assert lua.count("InsertService:LoadAsset(assetId)") == 1, (
        "Es darf genau EINE Stelle geben, die den nativen Load startet")
    insert_tool = lua[lua.index("tools.insert_asset = function(args)"):]
    insert_tool = insert_tool[:insert_tool.index("tools.apply_asset")]
    assert "if assetImportState.active then" in insert_tool
    assert "TOOLBOX_IMPORT_WEDGED" in insert_tool
    assert "TOOLBOX_IMPORT_IN_FLIGHT" in insert_tool
    assert "cancellable = false" in insert_tool
    assert insert_tool.index("if assetImportState.active then") < insert_tool.index(
        "assetImportState.active = true"), "Die Pruefung muss VOR dem Laden stehen"

    # -- 10) Versionsstand ---------------------------------------------------
    assert f'local ARENA_VERSION  = "{VERSION}"' in lua
    assert f"DocsVersion     = '{VERSION}'" in source
    assert source.count(f"bridgeVersion = '{VERSION}'") == 3
    assert source.count(f"serverVersion = '{VERSION}'") == 2
    assert f"# Arena Roblox Bridge  -  Version {VERSION}" in source
    version = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    assert version["version"] == VERSION, f"version.json ist nicht {VERSION}"
    notes = "\n".join(str(note) for note in version["notes"])
    for needle in ("insert_asset", "CATALOG_TIMEOUT", "TOOLBOX_BUSY",
                   "InsertService:LoadAsset", "executorAlive"):
        assert needle in notes, f"version.json erklaert '{needle}' nicht"


def main() -> int:
    source = load_source()
    lua = extract_plugin_lua(source)
    tests = [
        ("Test 1: schnelle Suche + erfolgreicher Import", lambda: test_1_fast_success()),
        ("Test 2: Katalog antwortet nie -> definierter Timeout, UI terminal", lambda: test_2_catalog_never_answers()),
        ("Test 3: haengender Import -> kein zweiter Import, klare Erholung", lambda: test_3_import_hangs()),
        ("Test 4: Ausnahme/Abbruch/verspaetete Antwort -> keine doppelte Einfuegung", lambda: test_4_exception_cancel_late_answer()),
        ("Test 5: zweiter paralleler Asset-Aufruf -> BUSY/Limit", lambda: test_5_parallel_call_is_busy()),
        ("Test 6: Status luegt nicht (kein 'ok' bei totem Executor)", lambda: test_6_status_must_not_lie()),
        ("Test 7: 200 Aufrufe -> Queue/Tasks/Caches wachsen nicht unbegrenzt", lambda: test_7_no_unbounded_growth()),
        ("Test 8: Quellcode-Abnahme 7.1.2", lambda: test_8_source(source, lua)),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL  {name}\n      {exc}")
    if failed:
        print(f"{failed} von {len(tests)} Tests fehlgeschlagen")
        return 1
    print(f"OK: alle {len(tests)} 7.1.2-Toolbox-Tests gruen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
