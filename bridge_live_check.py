#!/usr/bin/env python3
"""Live-Abnahme der Arena Roblox Bridge 7.1.1 (laeuft gegen die echte Bridge).

Aufruf (URL + Token aus der Place-Zeile im Bridge-Fenster):

    python bridge_live_check.py --url https://xxxx.trycloudflare.com --token DEIN_TOKEN

Geprueft wird, was in 7.0.4-7.1.0 live kaputt war (und in 7.0.5 / 7.1.1 behoben ist):

  0. 7.1.1-Hotfix         -> /api/status antwortet 200 (kein "Argumenttypen"-500),
                             /api/places antwortet 200 fuer das Place-Token,
                             counters.revivedSessions bleibt bei pollendem Studio
                             KONSTANT (Plugin schickt sessionId; kein Reconnect je Poll),
                             nach dem normalen Befehl: delivery.undeliveredCommands == 0
  1. /api/status          -> Version 7.1.1 + queue.sweep.running == true
  2. normaler Befehl      -> kommt in wenigen Sekunden mit Ergebnis zurueck
  3. Haenger-Reproduktion -> run_lua blockiert ~150 s; die Bridge muss WEIT vor
                             Cloudflares ~100-s-524 antworten (< 90 s), der
                             Befehl muss spaetestens nach budget+15 s als
                             abgebrochen erkannt werden (kein ewiges pending),
                             und danach muss ein normaler Befehl wieder laufen
  4. Reconnect-Hinweis    -> was im Studio zu tun ist (nicht automatisierbar)
  5. optional --force-fail-> Admin-Reset raeumt die Queue sofort
  6. optional --reset-test-> zwei wartende Befehle (run_lua mit task.wait) + POST /api/queue
                             action=reset -> cancelledCommands == 2 und pending leer
                             (7.1.0: reset traf ab 2 Befehlen keinen einzigen)

Das Skript schreibt nichts in den Place (nur list_jobs/status/queue) und bricht
den Haenger-Test NICHT ab - der Lua-Haenger laeuft von selbst aus.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

FAILURES: list[str] = []
EXPECTED_VERSION = "7.1.1"


def check(condition: bool, message: str) -> None:
    marker = "OK  " if condition else "FEHL"
    print(f"[{marker}] {message}")
    if not condition:
        FAILURES.append(message)


def api(url: str, path: str, payload: dict | None = None, timeout: float = 120.0) -> tuple[int, dict, float]:
    target = url.rstrip("/") + path
    data = None
    headers = {"User-Agent": "ArenaBridge-LiveCheck/" + EXPECTED_VERSION}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(target, data=data, headers=headers,
                                     method="POST" if data is not None else "GET")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
            elapsed = time.monotonic() - started
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = {"_raw": body[:400]}
            return response.status, parsed, elapsed
    except urllib.error.HTTPError as error:
        elapsed = time.monotonic() - started
        body = error.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"_raw": body[:400]}
        return error.code, parsed, elapsed
    except Exception as error:  # noqa: BLE001 - Netzfehler soll nur die Diagnose fuellen
        elapsed = time.monotonic() - started
        return 0, {"_error": f"{type(error).__name__}: {error}"}, elapsed


def tool(url: str, token: str, name: str, args: dict | None = None, **extra) -> tuple[int, dict, float]:
    payload = {"token": token, "tool": name, "args": args or {}}
    payload.update(extra)
    return api(url, "/api/tool", payload)


def status(url: str, token: str) -> dict:
    _, body, _ = api(url, f"/api/status?token={token}")
    return body


def show_late(body: dict) -> int:
    bridge = body.get("_bridge") if isinstance(body, dict) else None
    late = (bridge or {}).get("lateResults") or []
    for item in late:
        print("      lateResult:", json.dumps(item, ensure_ascii=False)[:400])
    return len(late)


def main() -> int:
    parser = argparse.ArgumentParser(description="Live-Abnahme der Arena Roblox Bridge " + EXPECTED_VERSION)
    parser.add_argument("--url", required=True, help="Tunnel-URL, z. B. https://xxx.trycloudflare.com")
    parser.add_argument("--token", required=True, help="Place-Token aus der Place-Zeile")
    parser.add_argument("--tool", default="list_jobs", help="normaler Testbefehl (Default: list_jobs)")
    parser.add_argument("--hang-seconds", type=int, default=150, help="Laenge des Lua-Haengers")
    parser.add_argument("--hang-budget", type=int, default=30, help="timeoutSeconds fuer den Haenger-Test")
    parser.add_argument("--skip-hang", action="store_true", help="Haenger-Test ueberspringen")
    parser.add_argument("--force-fail", action="store_true", help="am Ende force_fail ausfuehren")
    parser.add_argument("--reset-test", action="store_true",
                        help="zwei wartende Befehle anlegen und POST /api/queue action=reset pruefen (7.1.1)")
    args = parser.parse_args()

    print(f"Bridge: {args.url}")
    print()

    # 0) 7.1.1-Hotfix: Deployment + Sitzungsidentitaet -------------------------
    code, version_a, _ = api(args.url, "/api/version")
    deployment = (version_a.get("deployment") or {}) if isinstance(version_a, dict) else {}
    check(code == 200 and deployment.get("version") == EXPECTED_VERSION,
          f"GET /api/version: deployment.version ist {EXPECTED_VERSION} (gefunden: {deployment.get('version')}, HTTP {code})")
    telemetry_a = (version_a.get("counters") or {}) if isinstance(version_a, dict) else {}
    time.sleep(6)
    _, version_b, _ = api(args.url, "/api/version")
    telemetry_b = (version_b.get("counters") or {}) if isinstance(version_b, dict) else {}
    polls_a, polls_b = telemetry_a.get("poll"), telemetry_b.get("poll")
    revived_a, revived_b = telemetry_a.get("revivedSessions"), telemetry_b.get("revivedSessions")
    if isinstance(polls_a, int) and isinstance(polls_b, int):
        check(polls_b > polls_a, f"Studio pollt (counters.poll {polls_a} -> {polls_b})")
        check(revived_a == revived_b,
              f"revivedSessions bleibt konstant bei pollendem Studio ({revived_a} -> {revived_b}); "
              f"7.1.0 zaehlte hier +1 pro Poll (Plugin ohne sessionId)")
    code, places, _ = api(args.url, f"/api/places?token={args.token}")
    check(code == 200 and places.get("ok") is True and int(places.get("count") or 0) >= 1,
          f"GET /api/places antwortet fuer das Place-Token (HTTP {code}, count={places.get('count')}; 7.1.0: 404)")

    # 1) Status + Waechter ----------------------------------------------------
    code, body, _ = api(args.url, f"/api/status?token={args.token}")
    check(code == 200, f"GET /api/status antwortet HTTP 200 (gefunden: {code}; 7.0.6-7.1.0: 500 'Die Argumenttypen stimmen nicht ueberein.')")
    if not body.get("ok"):
        print("Antwort:", json.dumps(body, ensure_ascii=False)[:400])
        check(False, "GET /api/status liefert kein ok (Token/URL falsch? Place verbunden?)")
        return 1
    check(body.get("queueError") in (None, ""), f"Status ohne degradierten Queue-Schnappschuss (queueError={body.get('queueError')})")
    check(body.get("bridgeVersion") == EXPECTED_VERSION,
          f"bridgeVersion ist {EXPECTED_VERSION} (gefunden: {body.get('bridgeVersion')})")
    plugin_version = body.get("pluginVersion")
    check(plugin_version == EXPECTED_VERSION,
          f"Plugin-Version ist {EXPECTED_VERSION} (gefunden: {plugin_version}) - 'Studio neu starten' beachten")
    queue = body.get("queue") or {}
    sweep = queue.get("sweep") or {}
    check(sweep.get("running") is True,
          f"unabhaengiger Waechter laeuft (queue.sweep={json.dumps(sweep, ensure_ascii=False)})")

    # 2) Normaler Befehl -----------------------------------------------------
    code, body, elapsed = tool(args.url, args.token, args.tool)
    check(code == 200 and body.get("ok") is True,
          f"normaler Befehl '{args.tool}' ok in {elapsed:.1f}s (HTTP {code}, "
          f"code={body.get('code') or body.get('error') or '-'})")
    show_late(body)
    if not (code == 200 and body.get("ok")):
        print("Antwort:", json.dumps(body, ensure_ascii=False)[:600])
    after = status(args.url, args.token)
    delivery = after.get("delivery") or {}
    check(int(delivery.get("undeliveredCommands") or 0) == 0,
          f"keine nie abgeholten Befehle (delivery.undeliveredCommands={delivery.get('undeliveredCommands')}, "
          f"state={delivery.get('state')})")

    # 2b) Admin-Reset mit ZWEI wartenden Befehlen (7.1.0: traf keinen) -----------
    if args.reset_test:
        print("\nReset-Test: zwei run_lua-Befehle mit task.wait(25) (timeoutSeconds=3) anlegen...")
        for _ in range(2):
            tool(args.url, args.token, "run_lua", {"source": "task.wait(25); return 'reset-test'", "timeoutSeconds": 3})
        before = status(args.url, args.token)
        pending_before = (before.get("queue") or {}).get("pending") or []
        check(len(pending_before) >= 2, f"zwei Befehle warten vor dem Reset (pending={len(pending_before)})")
        code, body, _ = api(args.url, "/api/queue", {"token": args.token, "action": "reset"})
        check(code == 200 and body.get("ok") is True,
              f"POST /api/queue action=reset antwortet 200 (HTTP {code}, code={body.get('code') or body.get('error') or '-'})")
        cancelled = body.get("cancelledCommands")
        check(isinstance(cancelled, int) and cancelled >= 2 and cancelled >= len(pending_before),
              f"reset hat ALLE wartenden Befehle getroffen (cancelledCommands={cancelled}, vorher pending={len(pending_before)})")
        pending_after = ((body.get("queue") or {}).get("pending")) or []
        check(len(pending_after) == 0, f"nach dem Reset ist pending leer (pending={len(pending_after)})")
        time.sleep(3)

    # 3) Haenger-Reproduktion ------------------------------------------------
    if not args.skip_hang:
        source = (f"local t = os.clock(); while os.clock() - t < {args.hang_seconds} do end; "
                  f"return 'haenger beendet'")
        print(f"\nHaenger-Test: run_lua blockiert ~{args.hang_seconds}s "
              f"(timeoutSeconds={args.hang_budget}, Abbruch erwartet bei budget+15s)...")
        code, body, elapsed = tool(args.url, args.token, "run_lua",
                                   {"source": source, "timeoutSeconds": args.hang_budget})
        check(elapsed < 90, f"HTTP-Antwort kam nach {elapsed:.1f}s (muss < 90s, Cloudflare-524 ~100s)")
        check(code == 200 and body.get("ok") is False and body.get("code") == "STUDIO_TIMEOUT",
              f"Haenger endet als STUDIO_TIMEOUT ohne Verbindungsabriss (code={body.get('code')})")
        command_id = None
        bridge = body.get("_bridge") or {}
        pending = bridge.get("pendingCommands") or body.get("pendingInStudio") or []
        if isinstance(pending, list) and pending:
            command_id = (pending[0] or {}).get("commandId")
        show_late(body)

        print("   warte auf den Waechter (Sweep erkennt den Haenger spaetestens nach budget+15s)...")
        deadline = time.monotonic() + args.hang_budget + 60
        abandoned_seen = False
        last_queue = {}
        while time.monotonic() < deadline:
            time.sleep(5)
            queue = (status(args.url, args.token).get("queue") or {})
            last_queue = queue
            sweep = queue.get("sweep") or {}
            pending_ids = [item.get("commandId") for item in (queue.get("pending") or [])]
            if command_id and command_id not in pending_ids:
                abandoned_seen = True
                break
            if command_id is None and not pending_ids:
                abandoned_seen = True
                break
        check(abandoned_seen,
              f"Befehl ist aus der Warteschlange verschwunden (kein ewiges pendingInStudio); "
              f"abandonedTotal={(last_queue.get('sweep') or {}).get('abandonedTotal')}")

        # 4) Regression: danach laeuft ein normaler Befehl wieder -------------
        time.sleep(3)
        code, body, elapsed = tool(args.url, args.token, args.tool)
        check(code == 200 and body.get("ok") is True,
              f"nach dem Haenger laeuft '{args.tool}' wieder normal ({elapsed:.1f}s)")
        show_late(body)
        print("\n   Reconnect-Test (manuell): im Studio 'Plugins neu laden' bzw. Studio neu starten und "
              "danach erneut list_jobs rufen - Ergebnis muss ankommen, kein 403 COMMAND_OWNER_MISMATCH.")

    # 5) Admin-Reset ---------------------------------------------------------
    if args.force_fail:
        print()
        code, body, elapsed = api(args.url, "/api/queue",
                                  {"token": args.token, "action": "force_fail"})
        check(code == 200 and body.get("ok") is True,
              f"force_fail ok (clearedCommands={body.get('clearedCommands')}, HTTP {code})")

    print()
    if FAILURES:
        print("FEHLGESCHLAGEN:")
        for failure in FAILURES:
            print("  -", failure)
        return 1
    print(f"OK: Live-Abnahme bestanden (Bridge {EXPECTED_VERSION}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
