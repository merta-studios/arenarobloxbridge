#!/usr/bin/env python3
"""Verifikationstest fuer Arena Roblox Bridge 7.1.1 (Hotfix: Studio fuehrt wieder Befehle aus).

Live-Befund mit 7.1.0 (03.10.2026, Tunnel + Token): JEDES Studio-Werkzeug endete in
STUDIO_TIMEOUT, obwohl das Plugin alle 2 s pollte (poll=279, result=0,
deliveryAttempts=0, openPolls=0, revivedSessions=278 bei EINER Sitzung);
/api/status und /api/queue antworteten 500 "Die Argumenttypen stimmen nicht
ueberein.", /api/places 404, clear_pending/reset liessen 5 Befehle stehen.

Dieser Test prueft den echten Quellcode in ArenaBridge.ps1 (PowerShell +
eingebettetes Luau-Plugin) UND stellt die Ursachen in einem Modell der
PowerShell-Semantik exakt nach:

  Test 1: PowerShell-Modell - @(Funktion) mit Komma-Rueckgabe ist IMMER
          1-elementig; die 7.1.0-Poll-Schleife bricht deshalb vor dem Dequeue
          ab (0 Befehle zugestellt), die 7.1.1-Schleife liefert.
  Test 2: Quellcode - Get-SessionCancellationIds flach, Aufrufer mit @(),
          Poll-Antwort traegt sessionId.
  Test 3: Quellcode - kein @($var) um List[object]-Variablen (PowerShell-5.1-
          ArgumentException), Get-QueueSnapshot/Agent-Heartbeat repariert,
          /api/status degradiert statt 500.
  Test 4: Modell + Quellcode - Admin-Reset trifft mit @(Get-PendingCommands)
          ab 2 Befehlen keinen einzigen; 7.1.1 iteriert die echte Liste.
  Test 5: Quellcode - Plugin-statePayload() traegt sessionId/gameId,
          Update-Session loest ueber instanceGuid auf, Plugin uebernimmt die
          sessionId aus Poll-/Heartbeat-Antworten.
  Test 6: Quellcode - /api/places fuer normale Tokens, Waechter
          COMMAND_NEVER_DELIVERED, undeliveredCommands, Versionsstand 7.1.1.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PS1 = ROOT / "ArenaBridge.ps1"
VERSION = "7.1.1"


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
    pattern = re.compile(rf"function\s+{re.escape(name)}\b", re.MULTILINE)
    match = pattern.search(source)
    assert match is not None, f"PowerShell-Funktion {name} nicht gefunden"
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
                return source[match.start():idx + 1]
    raise AssertionError(f"Funktion {name} nicht geschlossen")


def extract_route(source: str, path: str, next_path: str) -> str:
    start = source.index(f"if ($path -eq '{path}') {{")
    end = source.index(f"if ($path -eq '{next_path}') {{", start)
    return source[start:end]


# ---------------------------------------------------------------------------
# PowerShell-Semantik-Modell (so verhaelt sich Windows PowerShell 5.1)
# ---------------------------------------------------------------------------
class PsList(list):
    """System.Collections.Generic.List[object] (Referenztyp, kein Array)."""


class PsArray(list):
    """object[] / string[]."""


def ps_return(value, comma: bool):
    """Modelliert `return <value>` bzw. `return , <value>` als PIPELINE-AUSGABE.

    Ohne Komma wird ein Array/eine Liste beim Schreiben in die Pipeline
    entrollt (0..n Objekte). Mit Komma wird ein 1-elementiges Array mit dem
    Array/der Liste als EINZIGEM Element geschrieben - die Pipeline entrollt
    die aeussere Huelle, uebrig bleibt das innere Objekt als EIN Element.
    """
    if comma:
        return [value]  # genau ein Pipeline-Objekt: das Array/die Liste selbst
    if isinstance(value, (PsList, PsArray)):
        return list(value)  # entrollt
    return [value]


def ps_at_call(pipeline_output: list) -> PsArray:
    """@(Befehl ...): sammelt die Pipeline-Objekte in ein object[]."""
    return PsArray(pipeline_output)


def ps_assign(pipeline_output: list):
    """$x = Befehl ...: 0 Objekte -> $null, 1 Objekt -> das Objekt, n -> object[]."""
    if len(pipeline_output) == 0:
        return None
    if len(pipeline_output) == 1:
        return pipeline_output[0]
    return PsArray(pipeline_output)


def ps_at_variable(value) -> PsArray:
    """@($var) als reiner Ausdruck - in Windows PowerShell 5.1 wirft der Binder
    fuer eine List[object] 'Die Argumenttypen stimmen nicht ueberein.'."""
    if isinstance(value, PsList):
        raise ValueError("Die Argumenttypen stimmen nicht überein.")
    if value is None:
        return PsArray()
    if isinstance(value, PsArray):
        return value
    return PsArray([value])


def ps_string(value) -> str:
    """[string]$x - Sammlungen werden mit Leerzeichen verbunden."""
    if isinstance(value, (list, tuple)):
        return " ".join(ps_string(v) for v in value)
    return str(value)


def ps_member(value, name: str):
    """$x.name - auf einer Sammlung = Member-Enumeration (Liste der Werte)."""
    if isinstance(value, (PsList, PsArray)):
        return PsArray([ps_member(v, name) for v in value])
    return value.get(name) if isinstance(value, dict) else None


# ---------------------------------------------------------------------------
# Modell der Bridge-Funktionen (nur das Verhalten, das hier entscheidend ist)
# ---------------------------------------------------------------------------
def get_session_cancellation_ids(cancel_requests: dict, sid: str, comma_bug: bool) -> list:
    items = [key.split(":", 1)[1] for key in cancel_requests if key.startswith(sid + ":")]
    if comma_bug:
        return ps_return(PsArray(items), comma=True)      # 7.1.0: return , $items.ToArray()
    if not items:
        return ps_return(PsArray(), comma=False)            # 7.1.1: return @()
    return ps_return(PsArray(items), comma=False)           # 7.1.1: return $items.ToArray()


def get_pending_commands(pending_bag: dict, sid: str) -> list:
    items = PsList(dict(commandId=cid, status=info["status"]) for cid, info in pending_bag.get(sid, {}).items())
    return ps_return(items, comma=True)                     # return , $items (unveraendert)


def poll_loop(queue: list, pending_bag: dict, cancel_requests: dict, sid: str, comma_bug: bool, max_iterations: int = 4) -> list:
    """Modell der /plugin/poll-Schleife (7.1.0 und 7.1.1 identisch bis auf die Rueckgabe)."""
    collected = []
    for _ in range(max_iterations):
        cancelled_now = ps_at_call(get_session_cancellation_ids(cancel_requests, sid, comma_bug))
        if len(cancelled_now) > 0:   # if ($resetRequested -or $cancelledNow.Count -gt 0) { break }
            break
        while len(collected) < 16 and queue:
            candidate = queue.pop(0)
            info = pending_bag.get(sid, {}).get(candidate["id"])
            if info and info["status"] == "queued":
                collected.append(candidate)
        if collected:
            break
    for command in collected:
        pending_bag[sid][command["id"]]["status"] = "delivered"
        pending_bag[sid][command["id"]]["deliveryAttempts"] = 1
    return collected


def admin_reset(pending_bag: dict, sid: str, wrap_call_in_at: bool) -> int:
    """Modell von Reset-SessionQueue/Force-FailSessionQueue."""
    if wrap_call_in_at:
        pending = ps_at_call(get_pending_commands(pending_bag, sid))      # 7.1.0: @(Get-PendingCommands $sid)
    else:
        pending = ps_assign(get_pending_commands(pending_bag, sid))       # 7.1.1: $pending = Get-PendingCommands $sid
    hit = 0
    for item in (pending if pending is not None else []):
        command_id = ps_string(ps_member(item, "commandId"))             # [string]$item.commandId
        if command_id in pending_bag[sid]:
            pending_bag[sid][command_id]["status"] = "cancelled"
            hit += 1
    return hit


def fresh_state(sid: str, count: int):
    pending_bag = {sid: {f"cmd{i}": {"status": "queued", "deliveryAttempts": 0} for i in range(1, count + 1)}}
    queue = [{"id": f"cmd{i}", "tool": "get_place_info"} for i in range(1, count + 1)]
    return pending_bag, queue


# ---------------------------------------------------------------------------
# Test 1: Komma-Rueckgabe + @() blockiert die Zustellung (7.1.0) - 7.1.1 liefert
# ---------------------------------------------------------------------------
def test_1_comma_operator_blocks_delivery() -> None:
    # Reine Semantik: @(f) mit ", $leeresArray" ist 1-elementig, ohne Komma leer.
    assert len(ps_at_call(ps_return(PsArray(), comma=True))) == 1, "Modell: @(f) mit Komma muss 1-elementig sein"
    assert len(ps_at_call(ps_return(PsArray(), comma=False))) == 0, "Modell: @(f) ohne Komma muss leer sein"
    assert ps_at_call(ps_return(PsArray(["a"]), comma=False)) == ["a"]
    assert ps_at_call(ps_return(PsArray(["a", "b"]), comma=False)) == ["a", "b"]

    sid = "17e4419543574385bf64f653c2e863bd"
    # 7.1.0: keine Stornierung offen, 5 Befehle in der Warteschlange - nichts kommt an.
    pending_bag, queue = fresh_state(sid, 5)
    delivered_710 = poll_loop(queue, pending_bag, {}, sid, comma_bug=True)
    assert delivered_710 == [], (
        f"Test 1 FEHLGESCHLAGEN: das 7.1.0-Modell haette nichts zustellen duerfen, lieferte aber {delivered_710}"
    )
    assert all(info["status"] == "queued" and info["deliveryAttempts"] == 0 for info in pending_bag[sid].values()), (
        "Test 1: im 7.1.0-Modell muessen alle Befehle queued/deliveryAttempts=0 bleiben (Live-Bild)"
    )
    # 7.1.1: dieselbe Lage - alle 5 Befehle werden im ersten Poll ausgeliefert.
    pending_bag, queue = fresh_state(sid, 5)
    delivered_711 = poll_loop(queue, pending_bag, {}, sid, comma_bug=False)
    assert [c["id"] for c in delivered_711] == ["cmd1", "cmd2", "cmd3", "cmd4", "cmd5"], (
        f"Test 1 FEHLGESCHLAGEN: 7.1.1-Modell liefert nicht alle Befehle: {delivered_711}"
    )
    assert all(info["status"] == "delivered" and info["deliveryAttempts"] == 1 for info in pending_bag[sid].values())
    # 7.1.1 mit echter Stornierung: Schleife bricht korrekt ab und meldet die ID (flach, nicht [[...]]).
    pending_bag, queue = fresh_state(sid, 1)
    cancel_requests = {f"{sid}:cmd1": 1}
    assert poll_loop(queue, pending_bag, cancel_requests, sid, comma_bug=False) == []
    ids = ps_at_call(get_session_cancellation_ids(cancel_requests, sid, comma_bug=False))
    assert list(ids) == ["cmd1"] and not isinstance(ids[0], list), "cancelledCommands muss flach ['cmd1'] sein"
    # 7.1.0 lieferte dort [[]] bzw. [['cmd1']] - genau das zeigte der Live-Poll.
    nested = ps_at_call(get_session_cancellation_ids({}, sid, comma_bug=True))
    assert len(nested) == 1 and isinstance(nested[0], list) and nested[0] == [], "Modell: 7.1.0 ergab [[]]"


# ---------------------------------------------------------------------------
# Test 2: Quellcode - Get-SessionCancellationIds flach, Aufrufer mit @()
# ---------------------------------------------------------------------------
def test_2_source_cancellation_ids_flat(source: str) -> None:
    fn = extract_ps_function(source, "Get-SessionCancellationIds")
    assert "return , $items.ToArray()" not in fn and "return ," not in fn, (
        "Test 2 FEHLGESCHLAGEN: Get-SessionCancellationIds nutzt wieder den Komma-Operator"
    )
    assert "if ($items.Count -eq 0) { return @() }" in fn and "return $items.ToArray()" in fn, (
        "Test 2 FEHLGESCHLAGEN: Get-SessionCancellationIds liefert kein flaches Array"
    )
    callers = re.findall(r"@\(Get-SessionCancellationIds \$\w+\)", source)
    assert len(callers) >= 3, f"Test 2: erwartet >= 3 @()-Aufrufer, gefunden {len(callers)}"
    assert not re.search(r"(?<!@\()Get-SessionCancellationIds \$\w+\)?\s*$", "\n".join(
        line for line in source.splitlines() if "Get-SessionCancellationIds $" in line and "@(" not in line and "function" not in line
    ), re.MULTILINE), "Test 2: ein Aufrufer benutzt Get-SessionCancellationIds ohne @()"
    poll = extract_route(source, "/plugin/poll", "/plugin/result")
    assert "$cancelledNow = @(Get-SessionCancellationIds $sid)" in poll
    assert "if ($resetRequested -or $cancelledNow.Count -gt 0) { break }" in poll
    assert "$cancelledIds = @(Get-SessionCancellationIds $sid)" in poll
    assert '"sessionId":\' + (To-Json $sid 3)' in poll, (
        "Test 2 FEHLGESCHLAGEN: /plugin/poll nennt die sessionId nicht in der Antwort"
    )


# ---------------------------------------------------------------------------
# Test 3: kein @($var) um List[object] (PowerShell-5.1-ArgumentException)
# ---------------------------------------------------------------------------
def test_3_no_at_around_list_object(source: str) -> None:
    # Modell: @($liste) wirft, .ToArray() nicht.
    sample = PsList([{"a": 1}])
    try:
        ps_at_variable(sample)
        raise AssertionError("Modell: @($List[object]) muss in 5.1 werfen")
    except ValueError as exc:
        assert "Argumenttypen" in str(exc)
    assert ps_at_variable(PsArray(sample)) == [{"a": 1}]

    snapshot = extract_ps_function(source, "Get-QueueSnapshot")
    assert "@($pending)" not in snapshot and "@($recentCommands)" not in snapshot, (
        "Test 3 FEHLGESCHLAGEN: Get-QueueSnapshot legt wieder @() um eine List[object] (500 in /api/status, /api/queue)"
    )
    assert "foreach ($item in $pending)" in snapshot and "recent = $recentCommands.ToArray()" in snapshot
    assert "commands=@($items)" not in source and "commands=$items.ToArray()" in source, (
        "Test 3 FEHLGESCHLAGEN: Agent-Heartbeat legt wieder @() um die Befehlsliste"
    )

    # Allgemeiner Waechter: jede per New-Object/::new() als List[object] angelegte
    # Variable und die List[object]-Rueckgaben (Get-PendingCommands, Take-Events,
    # Take-LateResults) duerfen nirgends als @($name) vorkommen.
    list_vars = set(re.findall(r"\$(?:script:)?(\w+)\s*=\s*New-Object\s+System\.Collections\.Generic\.List\[object\]", source))
    list_vars |= set(re.findall(r"\$(?:script:)?(\w+)\s*=\s*\[System\.Collections\.Generic\.List\[object\]\]::new\(\)", source))
    list_vars |= {"pending", "pendingItems", "events", "late"}
    offenders = sorted(name for name in list_vars if re.search(r"@\(\s*\$(?:script:)?" + re.escape(name) + r"\s*\)", source))
    assert not offenders, f"Test 3 FEHLGESCHLAGEN: @($var) um List[object]-Variablen: {offenders}"

    status = extract_route(source, "/api/status", "/api/queue")
    assert "$queueSnapshot = Get-QueueSnapshot $sessionId" in status and "queueError = $queueError" in status, (
        "Test 3 FEHLGESCHLAGEN: /api/status faengt einen Fehler des Queue-Schnappschusses nicht ab"
    )


# ---------------------------------------------------------------------------
# Test 4: Admin-Reset trifft die Befehle wirklich
# ---------------------------------------------------------------------------
def test_4_admin_reset_hits_every_command(source: str) -> None:
    sid = "s1"
    # Modell 7.1.0: @(Get-PendingCommands) -> ein Element (die Liste) -> 0 Treffer ab 2 Befehlen.
    pending_bag, _ = fresh_state(sid, 5)
    assert admin_reset(pending_bag, sid, wrap_call_in_at=True) == 0, "Modell: 7.1.0-Reset haette keinen Befehl treffen duerfen"
    assert all(info["status"] == "queued" for info in pending_bag[sid].values())
    # Mit genau EINEM Befehl funktionierte es zufaellig (Member-Enumeration einer 1er-Liste).
    pending_bag, _ = fresh_state(sid, 1)
    assert admin_reset(pending_bag, sid, wrap_call_in_at=True) == 1
    # Modell 7.1.1: alle 5 getroffen.
    pending_bag, _ = fresh_state(sid, 5)
    assert admin_reset(pending_bag, sid, wrap_call_in_at=False) == 5, "Modell: 7.1.1-Reset muss alle Befehle treffen"
    assert all(info["status"] == "cancelled" for info in pending_bag[sid].values())

    assert "@(Get-PendingCommands" not in source, (
        "Test 4 FEHLGESCHLAGEN: ein Aufrufer legt wieder @() um Get-PendingCommands"
    )
    force = extract_ps_function(source, "Force-FailSessionQueue")
    reset = extract_ps_function(source, "Reset-SessionQueue")
    assert "$pendingItems = Get-PendingCommands $sid" in force and "foreach ($item in $pendingItems)" in force
    assert "$pending = Get-PendingCommands $sid" in reset and "foreach ($item in $pending)" in reset
    assert "return $resetCount" in reset and "return $pending.Count" not in reset, (
        "Test 4 FEHLGESCHLAGEN: Reset-SessionQueue meldet nicht die echte Anzahl"
    )
    pending_fn = extract_ps_function(source, "Get-PendingCommands")
    assert "return , $items" in pending_fn, "Get-PendingCommands soll die Liste weiterhin als EIN Objekt zurueckgeben"


# ---------------------------------------------------------------------------
# Test 5: Sitzungsidentitaet (Plugin + Bridge)
# ---------------------------------------------------------------------------
def test_5_session_identity(source: str, lua: str) -> None:
    state_fn = lua[lua.index("local function statePayload()"):lua.index("local function handshake()")]
    assert "sessionId = sessionId," in state_fn, "Test 5 FEHLGESCHLAGEN: statePayload() ohne sessionId"
    assert "payload.gameId = tostring(game.GameId)" in state_fn, "Test 5 FEHLGESCHLAGEN: statePayload() ohne gameId"
    assert lua.index("local sessionId") < lua.index("local function statePayload()"), "sessionId muss vor statePayload() deklariert sein"
    assert 'if type(response.sessionId) == "string" and response.sessionId ~= "" and response.sessionId ~= sessionId then' in lua, (
        "Test 5 FEHLGESCHLAGEN: Plugin uebernimmt die sessionId aus der Poll-Antwort nicht"
    )
    hb = lua[lua.index('post("/plugin/heartbeat", statePayload())'):]
    hb = hb[:hb.index("task.wait(2)")]
    assert 'if type(response.sessionId) == "string" and response.sessionId ~= "" then' in hb and "sessionId = nil" in hb, (
        "Test 5 FEHLGESCHLAGEN: Heartbeat-Rueckfall verwirft die Sitzung, statt die genannte sessionId zu uebernehmen"
    )

    update = extract_ps_function(source, "Update-Session")
    assert "$Shared.InstanceSessions.TryGetValue($instanceGuidForUpdate, [ref]$mappedSessionId)" in update
    assert "$Shared.Sessions.ContainsKey($mappedSessionId)" in update
    assert "if ([string]::IsNullOrWhiteSpace($newGameId)) { $newGameId = [string]$entry.gameId }" in update
    heartbeat = extract_route(source, "/plugin/heartbeat", "/plugin/poll")
    assert "sessionId = [string]$entry.sessionId" in heartbeat and "$knownHeartbeatSessionId" in heartbeat, (
        "Test 5 FEHLGESCHLAGEN: /plugin/heartbeat nennt die sessionId nicht"
    )
    register = extract_ps_function(source, "Register-Session")
    assert "$reuseReason -eq 'same-instance' -and $reusableAge -le 30" in register, (
        "Test 5 FEHLGESCHLAGEN: Register-Session setzt den Lesemodus bei same-instance-Reuse wieder zurueck"
    )


# ---------------------------------------------------------------------------
# Test 6: /api/places, Waechter-Sicherheitsnetz, Versionsstand
# ---------------------------------------------------------------------------
def test_6_places_watchdog_version(source: str, lua: str) -> None:
    places = extract_route(source, "/api/places", "/api/status")
    assert "multiPlace=$false; places=$ownPlaces; count=$ownPlaces.Count" in places
    assert "targetPlace = [string]$sessionEntry.sessionId" in places
    watchdog = extract_ps_function(source, "Invoke-SessionExecutorWatchdog")
    assert "COMMAND_NEVER_DELIVERED" in watchdog and "($now - $lastSeen) -le 15 -and ($now - $queuedAt) -gt 120" in watchdog, (
        "Test 6 FEHLGESCHLAGEN: Waechter-Sicherheitsnetz fuer nie abgeholte Befehle fehlt"
    )
    health = extract_ps_function(source, "Get-StudioDeliveryHealth")
    assert "undeliveredCommands = $undelivered" in health
    # Versionsstand: Dieser Test ist der REGRESSIONSWAECHTER fuer 7.1.1 und
    # darf die laufende Version nicht festnageln (den Versionsstempel pruefen
    # test_v398_structure.py und der jeweils neueste Versionstest). Geprueft
    # wird nur, dass die Auslieferung mindestens 7.1.1 ist und dass alle
    # Versionsliterale weiterhin konsistent sind.
    header = re.search(r"# Arena Roblox Bridge  -  Version (\d+\.\d+\.\d+)", source)
    assert header, "Der Versionskopf fehlt"
    shipped = header.group(1)
    assert tuple(int(part) for part in shipped.split(".")) >= tuple(int(part) for part in VERSION.split(".")), (
        f"Die Auslieferung {shipped} liegt vor dem 7.1.1-Hotfix"
    )
    assert f'local ARENA_VERSION  = "{shipped}"' in lua
    assert f"DocsVersion     = '{shipped}'" in source
    assert source.count(f"bridgeVersion = '{shipped}'") == 3 and source.count(f"serverVersion = '{shipped}'") == 2
    version = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
    assert version["version"] == shipped, f"version.json ist nicht {shipped}"


def main() -> int:
    source = load_source()
    lua = extract_plugin_lua(source)
    tests = [
        ("Test 1: Komma-Operator + @() blockiert die Zustellung (7.1.0) / 7.1.1 liefert", lambda: test_1_comma_operator_blocks_delivery()),
        ("Test 2: Get-SessionCancellationIds flach, Aufrufer mit @(), Poll nennt sessionId", lambda: test_2_source_cancellation_ids_flat(source)),
        ("Test 3: kein @($var) um List[object] (PowerShell 5.1), /api/status degradiert", lambda: test_3_no_at_around_list_object(source)),
        ("Test 4: Admin-Reset trifft jeden Befehl", lambda: test_4_admin_reset_hits_every_command(source)),
        ("Test 5: Sitzungsidentitaet (statePayload sessionId, instanceGuid-Rueckfall)", lambda: test_5_session_identity(source, lua)),
        ("Test 6: /api/places, COMMAND_NEVER_DELIVERED, Versionsstand 7.1.1", lambda: test_6_places_watchdog_version(source, lua)),
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
    print(f"OK: alle {len(tests)} 7.1.1-Tests gruen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
