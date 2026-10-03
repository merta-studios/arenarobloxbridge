# Arena Roblox Bridge

Dieses Repository enthält das Programm **Arena Roblox Bridge** – die Brücke
zwischen einer KI und Roblox Studio:

- Verbindet jedes geöffnete Roblox-Studio-Fenster automatisch
- Installiert das Studio-Plugin und den Cloudflare-Tunnel vollständig
  automatisch (keine Admin-Rechte, keine Eingaben)
- Stellt für jedes Place einen Prompt (URL + Token) bereit

Die **ArenaBridge.exe** (der Starter) wird einmalig gebaut und an Freunde
weitergegeben. Sie lädt das Programm **aus diesem Repository** herunter und
hält es automatisch aktuell – deshalb muss dieses Repository **öffentlich**
sein.

## Dateien

| Datei | Zweck |
|---|---|
| `ArenaBridge.ps1` | Das komplette Programm |
| `version.json` | Aktuelle Version + Neuigkeiten (wird im Update-Fenster angezeigt) |
| `README.md` | Diese Datei |
| `test_v398_structure.py` | Python-Strukturtest (Versionen, Watchdog-/Reconnect-/Selbstauskunft-/Timeline-/Place-Zeilen-Guards, Kanal-Guards, 7.1.1-Regressionswächter gegen `@()` um `List[object]` und den Komma-Operator in `Get-SessionCancellationIds`, Lua via luaparser, XAML-XML; kein PowerShell nötig) |
| `test_v710_delivery.py` | Python-Verifikationstest 7.1.0 (BindReason, Ack-Outbox, Re-Delivery, Selbstheilung, 20-Befehle-Sequenz unter Störfeuer) |
| `test_v711_delivery.py` | Python-Modelltest 7.1.1: stellt die 7.1.0-Zustellblockade exakt nach (PowerShell-`@()`-Semantik mit Komma-Operator → Poll-Schleife bricht vor dem Dequeue ab), beweist die Reparatur, den wirksamen Admin-Reset und die Sitzungsauflösung über `instanceGuid` |
| `test_v712_toolbox.py` | Python-Modelltest 7.1.2 (Toolbox-Hotfix): gemockter Katalog + gemockter Studio-Executor. Stellt die 7.1.1-Symptome exakt nach (automatische Katalog-Wiederholung 2×20 s+1,5 s, 20 s Validierung + 55 s Studio auf **einer** HTTP-Anfrage, `delivery.state='ok'` bei `executorAlive=false`, Verlaufskarte bleibt auf „Macht gerade“, Cache-Schreibsturm) und beweist den Fix: harter Timeout, keine Wiederholung, `TOOLBOX_BUSY`/`TOOLBOX_IMPORT_IN_FLIGHT`/`TOOLBOX_IMPORT_WEDGED`, kein zweiter nativer `LoadAsset`, keine doppelte Einfügung, terminale UI-Zustände, begrenzte Caches |
| `test_queue_model_707.py` | Python-Modelltest: reproduziert den Queue-Stillstand von 7.0.4 und prüft die 7.0.5-Regeln (unabhängiger Watchdog, lateResults, Reconnect-Übergabe) **plus** 7.0.6 (Sitzungs-Identität, Fast-Fail, Zustell-Timeline) und 7.0.7 (Place-Zeile: fehlende Eigenschaft bricht den Zeilenaufbau ab) |
| `bridge_live_check.py` | Live-Abnahme gegen die laufende Bridge (URL + Token): 7.1.1-Checks (`/api/version` 7.1.1, `counters.revivedSessions` konstant, `/api/places` 200, `/api/status` 200), Status/Wächter, normaler Befehl, Hänger-Reproduktion, Regression, optional `--reset-test` (Reset mit 2 wartenden Befehlen) und `--force-fail` |
| `test-v39.ps1` | Ergänzende Windows-PowerShell-Mock-Tests für 5.2 (optional; wird NICHT vom Starter geladen) |

## So wird ein Update veröffentlicht

1. `ArenaBridge.ps1` im Repository durch die neue Version ersetzen.
2. In `version.json` die `version` erhöhen (z. B. `3.6` → `3.7`) und die
   `notes` mit den Neuigkeiten füllen – genau dieser Text erscheint den
   Nutzern nach dem Update im Update-Fenster.
3. Änderungen committen und pushen. Fertig!

Beim nächsten Start der ArenaBridge.exe wird das Update automatisch erkannt,
heruntergeladen und mit dem Hinweis-Fenster („Update installiert!“) gestartet.

## Versionsverlauf

## 7.1.2
- **MINI-HOTFIX: Toolbox-/Asset-Befehle hängen nicht mehr.** Live-Befund mit 7.1.1 (03.10.2026, Place „Place1“, Studio im Edit-Modus): nach mehreren Katalogsuchen (Katze, Hund, Fuchs, Hirsch, Kaninchen) liefen Detail-/Folgeaufrufe in Timeouts; ein `insert_asset` (assetId 14124432577, `sanitize=true`, `unpack=false`, Ziel `game.Workspace`, Name `Wildlife_Cat`) kehrte nie zurück und der POST auf `/api/tool` endete nach **ca. 125,8 s im Cloudflare-524**. Danach: `executor.alive=false` bei gleichzeitig `delivery.state='ok'`, Toolbox-Karten dauerhaft auf „Macht gerade“, Queue-Reset hing. **Es war keine einzelne Ursache – vier Stellen haben sich verstärkt, alle am Quellcode belegt:**
  1. **Unbegrenzte Katalogzeit auf der HTTP-Anfrage.** `search_assets`/`asset_details`/`validate_asset` laufen synchron im HTTP-Runspace (`Invoke-ServerTool`). `Invoke-AssetSearch` hatte eine **eigene Wiederholungsschleife** (`for ($attempt=1; $attempt -le 2)` mit `Invoke-RestMethod -TimeoutSec 20` + `Start-Sleep 1500 ms`) und danach noch einen 20-s-Detailaufruf → bis zu **61,5 s für einen Aufruf**. `Invoke-AssetDetails` fragte im 404-Fall **jede Asset-Id einzeln** mit 20 s ab (bei 20 Ids 400 s, ohne jede Grenze). Vor jedem `insert_asset` lief zusätzlich `Invoke-AssetValidation` (20 s) auf **derselben** Anfrage, bevor die 55 s Studio-Wartezeit überhaupt begannen – 20 + 55 s liegen bereits über der ~100-s-Grenze des Tunnels.
  2. **Keine Obergrenze für gleichzeitige Toolbox-Arbeit.** Der Server nimmt bis zu 32 Anfragen parallel an; parallele Suchen bedeuteten parallele Katalogaufrufe, die zusätzlich dieselbe Cache-Datei lasen und neu schrieben.
  3. **`delivery.state` log einen gesunden Zustand vor.** `Get-StudioDeliveryHealth` setzte `$state='ok'`, sobald irgendein HTTP-Kontakt jünger als 15 s war, und prüfte `executorAlive` erst ab 45 s Funkstille – genau deshalb stand `ok` neben `executorAlive=false`.
  4. **„Macht gerade“ ohne Ende.** Der `STUDIO_TIMEOUT`-Pfad in `/api/tool` ließ den Verlaufseintrag bewusst auf `phase='running'` stehen; bei totem Executor kam nie ein Ergebnis, das ihn geschlossen hätte.
- **Der Fix (klein und begrenzt):** ein einziger Weg in den Katalog (`Invoke-CatalogHttp`) mit hartem Zeitlimit (12 s, Validierung 8 s), hartem Gesamtbudget je Werkzeug (25 s), **ohne automatische Wiederholung** und mit typisierten Fehlern (`CATALOG_TIMEOUT`/`CATALOG_UNAVAILABLE`); höchstens **2 laufende Katalogaufrufe** und **genau ein aktiver Asset-Import** je Place (`Enter-ToolboxSlot`/`Enter-ToolboxImport`, Freigabe immer in `finally`, sonst sofort `TOOLBOX_BUSY`/`TOOLBOX_IMPORT_IN_FLIGHT`); `executorAlive` fließt zuerst in `delivery.state` ein (neuer, ehrlicher Zustand `executor_down`); jeder Aufruf erreicht einen Endzustand (`completed`/`failed`/`timed_out`/`cancelled`).
- **`InsertService:LoadAsset` ist nicht abbrechbar – und die Bridge tut jetzt auch nicht mehr so.** `task.cancel` beendet nur den Luau-Thread, der native Ladevorgang läuft weiter. Das Plugin hält deshalb eine ehrliche Einzelbelegung (`assetImportState`): hängt ein Import länger als 45 s, wird **kein zweiter** gestartet, der Zustand heißt `TOOLBOX_IMPORT_WEDGED`, und die Antwort nennt die sichere Erholung (Studio komplett neu starten, Place prüfen, danach prozedural bauen). Bleibt die Antwort vor der HTTP-Frist aus, kommt `TOOLBOX_IMPORT_UNCONFIRMED` und die Sperre bleibt **absichtlich** stehen.
- **Keine doppelten Einfügungen:** Idempotenz über `requestId` bzw. den Fingerabdruck aus `assetId`/`parentRef`/`name` in einem 120-s-Fenster (`idempotentReplay=true`); `allowDuplicate=true` erlaubt eine bewusste Zweitkopie.
- **Speicher/Trägheit** (passend zur Nutzerbeobachtung steigender RAM-Auslastung von ca. 70 % – **das ist eine Beobachtung aus den Studio-/Bridge-Logs, kein von der Bridge gemessener Wert**): `asset_cache.json` war unbegrenzt (die 7/30-Tage-Prüfung galt nur beim *Lesen*, gelöscht wurde nie) und `Add-CacheEntry` las und schrieb die **ganze Datei je Eintrag** – bei 20 Detail-Ids 20 vollständige Serialisierungen einer immer größeren Datei, in jedem HTTP-Runspace als PSObject-Graph. Jetzt: Sammel-Schreiben (`Add-CacheEntries`), serialisierter Zugriff (`AssetCacheLock`), harte Obergrenze 400 Einträge / 2 MB mit Verdrängung der ältesten, sofortige Freigabe großer Zwischenantworten. Zusätzlich war `Get-CacheEntry` falsch geklammert (`-not $x -contains $y` wertet `(-not $x) -contains $y` aus) und lief bei jedem Fehltreffer in eine Ausnahme statt in den Schnellausstieg.
- **Neue Dauerregel für Arena (`toolboxRules` in `Get-BridgeGuides`, erreicht jede neue Session über Sessionstart/`get_docs`/`api-docs`):** Tiere, Kreaturen, Pflanzen und organische Freiformen werden **prozedural** gebaut (`build_polygon_model`, ergänzt durch `build_assembly`/normale Parts, eigene Welds/Gelenke und eine kleine Lua-Animation für Atmung, Kopf-/Ohrenbewegung, Schwanzschwingen). Keine Toolbox-Suche als Abkürzung; reicht eine prozedurale Form nicht, wird zuerst ein begrenzter, transparenter Fallback **vorgeschlagen**.
- **Nicht geändert:** Befehlszustellung, Queue-Wächter, Sitzungsidentität, Oberfläche und alle Nicht-Toolbox-Werkzeuge.
- **Live-Abnahme 7.1.2 (kurz):** 1) Studio **komplett** schließen und neu öffnen → `GET /api/version` zeigt `deployment.version` = 7.1.2 und `pluginVersion` = 7.1.2. 2) `GET /api/status?token=…` → `toolbox.activeCatalogRequests=0`, `toolbox.activeImport=null`, `delivery.state='ok'` **nur** bei `executorAlive=true`. 3) `catalog_status` antwortet in < 8 s. 4) Ein `search_assets` antwortet in < 25 s oder mit `CATALOG_TIMEOUT` – nie länger. 5) Zwei Toolbox-Aufrufe gleichzeitig → der zweite bekommt sofort `TOOLBOX_BUSY`. 6) Keine Karte im Verlauf bleibt nach einem Timeout auf „Macht gerade“.
- **Ehrliche Einordnung:** Die vier Ursachen sind am Quellcode und am Live-Symptom belegt und in `test_v712_toolbox.py` reproduzierbar nachgestellt (7.1.1-Modell schlägt fehl, 7.1.2-Modell besteht). Offline geprüft sind Struktur, Lua-Syntax und Semantikmodell; **die Bestätigung auf Windows mit laufendem Studio steht noch aus** (insbesondere, ob ein real hängender nativer `LoadAsset` am Ende wirklich `TOOLBOX_IMPORT_WEDGED` erzeugt).

## 7.1.1
- **HOTFIX: Studio führt wieder Befehle aus (live belegt am 03.10.2026).** Mit 7.1.0 endete **jedes** Studio-Werkzeug in `STUDIO_TIMEOUT`, obwohl das Plugin alle 2 s pollte: `GET /api/version` zeigte `poll=279, result=0`, die Befehle blieben `queued` mit `deliveryAttempts=0`, `openPolls=0`. **Ursache (am Quellcode und am Live-Symptom bewiesen):** `Get-SessionCancellationIds` gab in 7.1.0 `, $items.ToArray()` zurück; alle Aufrufer schreiben `@(Get-SessionCancellationIds $sid)`. In PowerShell ergibt `@(f)` bei einem Komma-Rückgabewert **immer** ein 1-elementiges Array (das – auch leere – Array als Element). Damit war `$cancelledNow.Count -gt 0` in `/plugin/poll` immer wahr, die Schleife brach **vor** dem Dequeue ab und `cancelledCommands` war `[[]]`. Die Funktion liefert jetzt ein flaches Array (0..n Strings).
- **`/api/status` und `/api/queue` antworten wieder** (seit 7.0.6: 500 „Die Argumenttypen stimmen nicht überein.“). Windows PowerShell 5.1 wirft diesen Fehler für `@($var)`, wenn `$var` eine `System.Collections.Generic.List[object]` hält (leer oder gefüllt). `Get-QueueSnapshot` (`foreach ($item in @($pending))`, `recent = @($recentCommands)`) und der Agent-Heartbeat (`commands=@($items)`) tun das nicht mehr. **Regel ab jetzt:** nie `@()` um eine `List[object]`-Variable – `.ToArray()` oder `[object[]]`. Der Strukturtest wacht darüber. `/api/status` degradiert bei einem Diagnosefehler (`queueError`) statt mit 500 zu scheitern.
- **Admin-Reset wirkt wirklich.** `Force-FailSessionQueue`/`Reset-SessionQueue` iterierten über `@(Get-PendingCommands $sid)`; `Get-PendingCommands` gibt `, $liste` zurück, `@()` machte daraus **ein** Element. Ab zwei offenen Befehlen traf `clear_pending`/`reset`/`force_fail` keinen einzigen (live: 5 Befehle überlebten jeden Reset). Beide iterieren jetzt die echte Liste; `reset` meldet die echte Anzahl.
- **Sitzungsidentität repariert.** Das Plugin schickte seit 7.0.0 keine `sessionId` im Poll-/Heartbeat-Payload (`statePayload()`). Jeder Poll scheiterte deshalb in `Update-Session` und lief durch `Register-Session` (`reconnects+1`, `revivedSessions` im Sekundentakt, Lesemodus still auf `readwrite` zurückgesetzt); der Ersatz-Heartbeat meldete „Die Bridge kennt diese Sitzung nicht mehr“ → Plugin verwarf die Sitzung, re-hello, „Bridge connected“-Sturm. Jetzt: `statePayload()` trägt wieder `sessionId` und `gameId`; die Bridge löst Polls/Heartbeats ohne (oder mit veralteter) `sessionId` über die `instanceGuid` auf, nennt in jeder Poll-/Heartbeat-Antwort die gültige `sessionId`, das Plugin übernimmt sie. Ein noch laufendes 7.1.0-Plugin funktioniert damit ebenfalls wieder (Studio-Neustart bleibt empfohlen, `pluginOutdated` zeigt es an).
- **`GET /api/places` auch für ein normales Place-Token** (vorher 404, obwohl die Root-Dokumentation die Route nennt): das eigene Place als einziger Eintrag, gleiche Form wie beim Alle-Places-Token.
- **Wächter-Sicherheitsnetz:** ein Befehl, der trotz nachweislich pollendem Plugin 120 s nie abgeholt wurde (`deliveryAttempts=0`), endet mit `COMMAND_NEVER_DELIVERED` statt 30 Minuten als Zombie zu stehen; `delivery.undeliveredCommands` zeigt solche Fälle im Status.
- **Live-Abnahme 7.1.1 (kurz):** 1) `GET /api/version` → `deployment.version` = 7.1.1, `counters.revivedSessions` bleibt bei laufendem Studio **konstant** (nicht mehr +1 pro Poll). 2) `GET /api/status?token=…` → 200 mit `queue.timeline`. 3) `GET /api/places?token=…` → 200, `count=1`. 4) Normaler Befehl (`get_place_info`) kommt in < 5 s; `timeline.deliveryAttempts` ≥ 1. 5) `POST /api/queue {action:"reset"}` bei 2+ offenen Befehlen → `cancelledCommands` = echte Anzahl, danach `pending=[]`. 6) Studio einmal komplett neu starten → `pluginVersion` = 7.1.1.
- **Ehrliche Einordnung:** Die vier Ursachen sind am Quellcode (PowerShell-Semantik von `@()`/Komma-Operator, dokumentierter PowerShell-5.1-Binderfehler für `@($List[object])`) und am Live-Symptom belegt; offline ist 7.1.1 strukturell geprüft (`test_v398_structure.py`, `test_v710_delivery.py`, `test_v711_delivery.py` mit einem Modell, das die 7.1.0-Blockade exakt nachstellt). Die Bestätigung liefert die laufende Bridge.

## 7.1.0
- Zuverlässige Befehlszustellung (Ack-Outbox + `received_batch` vor dem Einreihen, Re-Delivery unbestätigter Befehle bis 3×, Selbstheilung bei verlorenen Zwischen-Acks), `To-Json` serialisiert leere/1-elementige Arrays immer als JSON-Array, BindReason-Vorschaufehler behoben, Watchdog-Abbrüche mit Plugin-Diagnose. **Enthielt die in 7.1.1 behobene Regression** (Komma-Operator in `Get-SessionCancellationIds` → keine Befehlszustellung).

## 7.0.8
- Vier im 7.0.x-Plugin fehlende Lua-Namen (`findByPath`, `resolveGroups`, `runSolidOperation`, `firstNonEmpty`) wieder vorhanden, `tplName`-Scope in `fill_region` repariert, Poll-Schleife fehlerfest (`xpcall`, sichtbarer `ARENA-PLUGIN-FEHLER`).

## 7.0.7
- **HOTFIX: Place-Liste ist wieder da (live belegter Fehler aus 7.0.6).** 7.0.6 ist beim Nutzer nachweislich gelaufen – Titelzeile: „Bridge 7.0.6 · SHA 91389fc3 · Wächter aktiv (vor 1 s) · neue Sitzungen (60 s): 2“, also **zwei lebende Sitzungen** –, aber die Liste blieb leer: „Place-Liste wird repariert / Die Liste ist noch unvollständig“. Genau dieses Bild entsteht, wenn **beide** Zeilen-Bauer (`New-Row` **und** der Minimal-Fallback) mit einer Ausnahme abbrechen: dann wird keine einzige Zeile angehängt, obwohl Sitzungen vorhanden sind.
- **Ursache:** In beiden Bauern setzte 7.0.6 `$row.CommandCancelButton = …`, aber die Eigenschaft fehlte im `[pscustomobject]`-Initialisierer. Das ist die **einzige** nicht deklarierte Zeilen-Eigenschaft im ganzen Skript (alle 27 anderen stehen im Initialisierer). In Windows PowerShell wirft diese Zuweisung („property cannot be found on this object“) und riss den kompletten Zeilenaufbau mit – inklusive des Minimal-Fallbacks, der dieselbe Zeile enthält.
- **Fix:** Die Eigenschaft ist in **beiden** Initialisierern deklariert, und der optionale Knopf wird zusätzlich in `try/catch` gebaut – ein Extra darf nie den Aufbau der ganzen Zeile kosten.
- **Abbrechen in der Place-Zeile funktioniert jetzt wirklich.** Der Knopf rief zuvor `Get-DeliverySession`/`Request-CommandCancel` auf – beide existieren nur im Server-Runspace, die UI läuft in einem anderen; er tat also nichts. Jetzt läuft der Abbruch direkt über den gemeinsamen Zustand: Abbruchwunsch merken (`CancelRequests`), Befehl aus der FIFO nehmen, den wartenden Aufrufer **sofort** mit `COMMAND_CANCELLED` beantworten und den Long-Poll wecken.
- **Klartext statt Raterei:** Die Reparatur-Anzeige nennt den **echten** Grund (letzter Zeilenfehler) direkt im Fenster – ein Screenshot genügt als Beweis, ohne die große `runtime.log`.
- **Klarerer Plugin-Hinweis:** „⚠ Studio einmal komplett schließen und neu öffnen – lädt Plugin 7.0.7 (läuft noch 7.0.5)“. Ein laufendes Studio behält das alte Plugin im Speicher; das ist der erwartete, einmalige Schritt.
- **Live-Abnahme 7.0.7 (kurz):** 1) Titelzeile zeigt **„Bridge 7.0.7 · SHA … · Wächter aktiv“**. 2) Die Place-Liste zeigt die verbundenen Fenster wieder als Zeilen (kein „Place-Liste wird repariert“ mehr). 3) `GET /api/version` → `deployment.version` = 7.0.7, `deployment.sha256` passt zur Datei. 4) `verdict.pluginOutdated` = false (sonst Studio komplett neu starten). 5) Normaler Befehl kommt in < 5 s; `/api/queue` zeigt die Timeline. 6) Bleibt die Liste doch leer, steht der **echte Grund** jetzt direkt in der Reparatur-Anzeige.
- **Update installieren (Test vor dem Merge):** `%LOCALAPPDATA%\ArenaRobloxBridge\update-config.json` mit `{ "branch": "<Session-Branch>" }` anlegen und die Bridge/den Starter neu starten; danach die Datei wieder entfernen bzw. auf `main` stellen.
- **Ehrliche Einordnung:** Ursache und Fix sind am Code und am Live-Symptom belegt; offline ist 7.0.7 strukturell geprüft (`test_v398_structure.py`, `test_queue_model_707.py` – inklusive eines Modelltests, der den 7.0.6-Absturz nachstellt). Die Bestätigung liefert die laufende Bridge.

## 7.0.6
- **Selbstauskunft statt Vermutung.** `GET /api/version` (bewusst **ohne Token**, damit sie auch bei ungültigem Token hilft) beantwortet in EINER Anfrage: laufende Version, Datei-Pfad, **SHA-256 der laufenden Datei**, Startzeit, Sprachmodus, die immer mitlaufenden Zähler (`hello`/`poll`/`result`/`tool`, neue Sitzungen der letzten 60 s, Wiederbelebungen, unbekannte Polls, Sturm-Warnungen, Fast-Fails, Zeilen-Abbrüche) und den Wächterstand (`running`, `secondsSinceSweep`, `abandonedTotal`) sowie je Sitzung `pluginVersion`/`pluginOutdated`, offene Polls und wartende Befehle. Die Kopfzeile des Hauptfensters zeigt dauerhaft **„Bridge 7.0.6 · SHA \<8\> · Wächter aktiv (vor N s)“** (gelb, sobald das Studio-Plugin veraltet ist). Damit ist ohne Log-Datei entscheidbar, ob 7.0.6 überhaupt läuft (H1) und ob das Plugin pollt (H2/H5).
- **Sitzungs-Identität beendet den „Bridge connected“-Sturm.** Eine Plugin-Instanz (`instanceGuid`) behält **immer** dieselbe `sessionId` und denselben Token – auch nach Cleanup, Reconnect oder einem Zustand, der von außen „tot“ aussieht. `/plugin/hello` und `/plugin/poll` beleben die bekannte Sitzung wieder (kein neuer Token, keine verwaisten Befehle), und das Plugin **übernimmt** eine vom Server genannte `sessionId`, statt seine Sitzung zu verwerfen. Mehr als sechs neue Sitzungen in 60 s werden als Sturm gezählt (`Telemetry.StormWarnings`, `newSessionsLast60s`) und im Log gewarnt.
- **Keine 55-Sekunden-Timeouts mehr bei toten oder belegten Executors.** `Get-StudioDeliveryHealth` prüft **vor** jedem Einreihen: Ist der Executor nachweislich stumm (kein offener Poll, kein Lebenszeichen, Arbeit wartet), antwortet die Bridge **sofort** mit `STUDIO_UNREACHABLE` samt klarer Handlungsanweisung („Studio einmal komplett schließen und neu öffnen“ – ein blockiertes Lua gibt nur der Studio-Neustart frei) und reiht **nichts** ein. Ist er belegt und die FIFO nicht leer, kommt **sofort** `STUDIO_BUSY` mit laufendem Tool und Laufzeit; `args.asJob=true` umgeht das. Zähler: `fastFailWedged`/`fastFailBusy`.
- **Zustell-Timeline pro Befehl.** `GET /api/queue` liefert `timeline[]` mit `queuedAt → deliveredAt → receivedAt → startedAt → heartbeatAt → runningSeconds → budgetSeconds → lastError` und `recent[]` (die letzten 12 abgeschlossenen Befehle mit Code). In EINER Antwort ist sichtbar, wo es klemmt: fehlt `deliveredAt`, hat das Plugin den Befehl nie abgeholt; fehlt `startedAt`, wurde er nie gestartet; steht `heartbeatAt` still, meldet der Executor nicht mehr. `GET /api/status` liefert denselben Zustell-Zustand kompakt als `delivery { state: ok|busy|quiet|wedged, secondsSinceLastSign, runningTool, runningSeconds }`.
- **`get_bridge_log`.** Neues Tool: die KI liest `runtime.log` und `performance.txt` selbst (10–500 Zeilen wählbar) – jede Antwort enthält Laufzeit-Identität, Wächterstand und Zustell-Zustand des Places.
- **Plugin sichtbar.** Das Studio-Widget zeigt „Poll: läuft (letzte Antwort vor X s) – Befehle: n – läuft/zuletzt: \<tool\>“; Poll-/Handshake-Fehler und ein veraltetes Plugin erscheinen klar markiert als `ARENA-PLUGIN-FEHLER: …` im Studio-Output (höchstens eine Meldung je 60 s).
- **Befehl sichtbar und abbrechbar in der Place-Zeile.** Die Zeile zeigt den echten offenen Befehl („Befehl: \<tool\> – \<status\> seit N s“) mit **Abbrechen**-Knopf; der Abbruch läuft über denselben Pfad wie der KI-Abbruch (`Request-CommandCancel`) und gibt die serielle Studio-Queue sofort frei (`rowCancels` im Zähler).
- **Vorschau ehrlich.** `GET /api/version` enthält `preview.mode`, `preview.modeReason`, `preview.lastOutcome` und die Pfade von `preview-diagnose.txt` / `preview-cache`. Ist das Studio-Fenster schwarz/leer oder antwortet nicht, steht der konkrete Grund in `preview-diagnose.txt`, im `runtime.log` und in `/api/version`; die Aufnahme läuft mit hartem Zeitlimit (10 s) statt endlos zu drehen.
- **Live-Abnahme (Ziel-PC, Bridge läuft, Studio verbunden)** – erst danach gilt 7.0.6 als belegt:
  1. `GET /api/version` **ohne Token** → `deployment.version` = 7.0.6, `deployment.file` + `deployment.sha256` notieren und mit `git show origin/main:ArenaBridge.ps1 | sha256sum` vergleichen (Beweis, dass die neue Datei läuft). `verdict.storm` muss `false` sein.
  2. Titelzeile des Fensters: „Bridge 7.0.6 · SHA … · Wächter aktiv“. `verdict.pluginOutdated` muss `false` sein (sonst Studio einmal komplett neu starten).
  3. Normaler Befehl (`get_tree`, `list_jobs`, `get_place_info`) kommt in < 5 s zurück; `GET /api/queue` zeigt die vollständige `timeline` bis `finishedAt`.
  4. **Hänger reproduzieren:** `run_lua` mit einem **nicht** kooperativen Hänger, z. B. `args = { source: "local t = os.clock(); while os.clock() - t < 150 do end; return 'done'", timeoutSeconds: 30 }`. Erwartung: Der Aufruf endet nach 30 s mit `STUDIO_TIMEOUT`; danach antwortet `get_place_info` **sofort** mit `STUDIO_UNREACHABLE` (kein 55-s-Warten mehr) und `/api/version` zeigt `counters.fastFailWedged > 0`. Nach einem Studio-Neustart läuft der nächste Befehl wieder normal, **ohne** neue Sitzung und ohne „Bridge connected“-Sturm (`counters.newSessionsLast60s` bleibt klein).
  5. `get_bridge_log` (120 Zeilen) liefert die Laufzeit-Identität und den Wächterstand zurück.
  6. Vorschau: `GET /api/version` → `preview.lastOutcome` (ok + Pixelgröße/Methode oder der genaue Grund) und `preview-diagnose.txt` prüfen.
- **Update installieren (Live-Test vor dem Merge):** In `%LOCALAPPDATA%\ArenaRobloxBridge\update-config.json` `{ "branch": "arena/01a0fe46-arenarobloxbridge" }` eintragen und die Bridge (bzw. den Starter) neu starten – sie lädt 7.0.6 direkt vom Session-Branch. Danach die Datei wieder entfernen (oder auf `main` stellen), sobald gemergt ist.
- **Ehrliche Einordnung.** Offline ist diese Version nur strukturell geprüft (`test_v398_structure.py`, `test_queue_model_707.py`) – **nicht** auf Windows gemessen. Erst die Live-Abnahme oben entscheidet über den Erfolg. (Nachtrag: Die Live-Abnahme zeigte in 7.0.6 den Place-Listen-Fehler – behoben in 7.0.7.)

## 7.0.5
- **Hängende Befehle: der Watchdog läuft jetzt unabhängig.** In 7.0.4 lief die Ausfallerkennung ausschließlich in der `/plugin/poll`-Anfrage. Genau dann, wenn ein Befehl die Lua-VM des Plugins blockiert (kein `yield`) oder die Verbindung abreißt, kommt aber kein Poll mehr – der Watchdog lief deshalb nie, der Befehl blieb für immer in `pendingInStudio`, `lateResults` kam nie an und die strikt serielle Queue blockierte alles (real: zwei hängende `list_jobs` = 15 Minuten Stillstand). Jetzt läuft ein **eigener Sweep-Runspace** neben dem Server: alle 2 s prüft er alle offenen Befehle und beendet tote/stumme Ausführungen mit klarem Code (`STUDIO_ABANDONED`, `EXECUTOR_UNRESPONSIVE`, `EXECUTOR_UNAVAILABLE`, `EXECUTOR_DROPPED_COMMAND`, `COMMAND_DELIVERY_UNCONFIRMED`, `QUEUE_EXPIRED`). Er weckt einen noch wartenden HTTP-Aufrufer oder legt das Ergebnis als `lateResults` der **Anrufer-Sitzung** ab und lässt die Queue weiterlaufen. `GET /api/queue` zeigt mit `queue.sweep.running` / `secondsSinceSweep` / `abandonedTotal` live, dass er arbeitet.
- **Reconnect-sicher: kein doppeltes Ausführen, kein Verlieren.** Ergebnisse werden über die `commandId` **und** die Plugin-`instanceGuid` zugeordnet, nicht mehr über die zufällige Session-Id. Ein Plugin-Neustart verwirft die Warteschlange nicht mehr: nie zugestellte Befehle gehen auf die neue Session über (`SessionSuccessors` + `Get-DeliverySession`), die aufrufende Sitzung behält Token und `lateResults` (`CommandOrigins`), und ein bereits ausgeführter `commandId` wird im Plugin mit dem **gespeicherten Ergebnis** erneut zugestellt statt ein zweites Mal ausgeführt. Bereits laufende Befehle einer toten Instanz werden nie blind wiederholt, sondern mit ehrlichem Fehler und `partialChangesPossible` abgeschlossen.
- **Cloudflare-Schutz.** Tool-Antworten enden nach **55 s** (maximal **85 s**, auch mit `timeoutSeconds`) – deutlich unter dem ~100-s-524 des Tunnels. Längere Studio-Arbeit läuft weiter und kommt über `_bridge.lateResults` zurück oder wird von Anfang an mit `asJob=true` als Job gestartet.
- **Admin-Reset ohne Studio-Neustart.** Neu: `force_fail` und `clear_pending` (als Tool und als `POST /api/queue { action: "force_fail" | "clear_pending" }`). Jeder offene Befehl erhält sofort ein endgültiges `FORCE_CLEARED`-Ergebnis (Waiter oder `lateResults`), die Warteschlange wird geleert und Studio wird gebeten, seine lokale Queue zu verwerfen. Ein blockiertes Lua im Plugin kann weiterhin einen Studio-Neustart brauchen – die Antwort zeigt dann `executor.alive=false`.
- **Place-Liste wieder mittig und kompakt.** Die blaue Arbeits-/Fortschrittszeile lag seit 7.0.4 in der **Vorschau-Spalte** (Grid-Spalte 0), zog die Zeile in die Höhe und riss die Mitte auseinander; der Inhalt war zusätzlich auf `Top` gestellt. Jetzt läuft die Vorschau über beide Zeilen und ist zentriert, die Arbeitszeile sitzt unter dem Place-Namen, die Zeile hat symmetrisches Innen-Padding.
- **Nach dem Update Roblox Studio einmal neu starten**, damit Plugin **7.0.5** geladen wird.
- **Live-Abnahme** (Ziel-PC, Bridge läuft, Studio verbunden):
  1. `GET /api/status` → `pluginVersion`/`docsVersion` = 7.0.5, kein `versionMismatch`.
  2. `GET /api/queue` → `queue.sweep.running: true`, `secondsSinceSweep` ≤ ~5.
  3. Normaler Befehl (`get_tree`, `list_jobs`) kommt in < 5 s mit Ergebnis zurück.
  4. **Hänger reproduzieren:** `run_lua` mit einem kooperativen Hänger, z. B. `args = { source: "local t = os.clock(); while os.clock() - t < 120 do end; return 'done'", timeoutSeconds: 30 }` (blockiert die Lua-VM ~120 s). Erwartung: die Bridge antwortet nach 30 s mit `STUDIO_TIMEOUT`, `GET /api/queue` zeigt den Befehl als `running`, nach ca. 45 s erscheint er als abgebrochen (`EXECUTOR_UNRESPONSIVE`/`STUDIO_ABANDONED`) und `abandonedTotal` steigt; nach dem Ende des Hängers läuft der nächste Befehl (`get_tree`) wieder normal. Kein Studio-Neustart nötig, solange das Lua irgendwann endet.
  5. **Reconnect:** Studio-Plugin neu laden (oder kurz Verbindung trennen) und danach `list_jobs` rufen – Ergebnis muss ankommen, `queue_followed`-Event im Log, kein `403 COMMAND_OWNER_MISMATCH`.
  6. **Admin-Reset:** `POST /api/queue { token, action: "force_fail" }` → `clearedCommands` > 0, alle offenen Befehle erhalten `FORCE_CLEARED`, danach läuft ein neuer Befehl sofort.
- **Offline-Prüfung:** `python -m pip install luaparser` und `python test_v398_structure.py`; zusätzlich `python test_queue_model_707.py` (Modelltest, kein PowerShell/Studio nötig).

## 7.0.4
- **Executor und Queue erholen sich nach Ausfällen.** Jeder Studio-Befehl erhält eine eindeutige `commandId`, wird mit geschützter Fehlerbehandlung/Traceback und einem festen Zeitbudget ausgeführt und sendet Start-/Liveness-Heartbeats. Ein Plugin-Watchdog markiert hängende Befehle als `STUDIO_ABANDONED`; der Server-Watchdog erkennt fehlende Heartbeats, nicht bestätigte Zustellung und verlorene Executor-Einträge. Abgebrochene Schreibbefehle können Teiländerungen hinterlassen – vor einem Retry den Place prüfen.
- **Ergebniszustellung ist idempotent.** Resultate und Chunk-Antworten gehören zu ihrer `commandId`; Wiederholungen werden dedupliziert, nicht zugestellte Ergebnisse bleiben in einer Retry-Outbox. Argumente und erforderliche Felder werden vor dem Queueing geprüft, und die Studio-Queue ist begrenzt.
- **Diagnose und kontrollierte Wiederherstellung.** `GET /api/queue?token=...` zeigt Queue, pending commandIds, Plugin-/Executor-Liveness und Zeitpunkte. `POST /api/queue` mit `{ action: "cancel", commandId: "..." }` bricht einen Befehl best-effort ab; `{ action: "reset" }` markiert offene Befehle und fordert einen lokalen Executor-Reset an. Beide Aktionen können Teiländerungen hinterlassen.
- **Spatial-/Boden-Tools repariert und begrenzt.** Schema und Handler stimmen für `ground_height`, `measure_height`, `snap_to_ground`, `verify_measurable`, `raycast_many` und weitere räumliche Abfragen wieder überein. Bodenraster und `probe_world` werden vor dem Queueing und erneut im Plugin auf maximal 4.000 Messpunkte begrenzt; große Durchläufe yielden regelmäßig und unterstützen Jobfortschritt/Abbruch. Einzel-Refs und dokumentierte Aliase werden vor der Ausführung korrekt akzeptiert.
- **Place-Liste und Einstellungen.** Der Place-Name steht etwas höher; darunter erscheinen bei aktiver Arena-Arbeit der blaue Text „Arena arbeitet gerade...“, eine blaue Fortschrittsleiste und Prozent. Die Mitteilungen-Kategorie wurde aus den Einstellungen entfernt; die Place-Zeile zeigt nur die Fortschrittsanzeige, ohne Zusatzlabel.
- **Nach dem Update Roblox Studio einmal neu starten**, damit Plugin **7.0.4** geladen wird.

## 7.0.3
- **Die Ursache des Dauer-Lags, nicht die Frequenz.** 7.0.2 hat nur die Oberfläche beruhigt (Deko-Animationen, 1,8-s-Abgleich, minimiertes Fenster, Handoff-Prüfung) und deshalb nichts geändert. Der Befund liegt im Studio-Kanal: Das Plugin hielt ab dem ersten verbundenen Place **dauerhaft** eine HTTP-Anfrage offen. Der Long-Poll fragte 12 Sekunden an und startete unmittelbar danach die nächste Anfrage – ohne jede Pause (100 % Belegung eines HTTP-Platzes), plus ein eigener Heartbeat alle 5 Sekunden als zweiter Dauerkanal.
- **Warum das Lag erzeugt.** Roblox Studio führt nur **drei HTTP-Anfragen gleichzeitig** aus (DevForum-Bericht „HttpService only allows 3 in-flight requests at a time“, von Roblox bestätigt), und Roblox schreibt selbst: *„If certain plugins or game scripts are making requests that utilize long polling, or generally requests that by nature take a long time, this can currently stall next requests.“* Genau dieser Dauerzustand begann mit dem ersten verbundenen Place und lief im Leerlauf unverändert weiter – unabhängig von Vorschau, Place-Liste und UI-Takt. Die Vorschauaufnahme war nie die Ursache.
- **Zweiter Fund.** Jede HTTP-Anfrage erzeugte in der Bridge ein neues PowerShell-Objekt und **parste den 337-KB-Handler (~4300 Zeilen) neu**. Diese Kosten liefen exakt mit den Plugin-Anfragen an. Der Handler wird jetzt einmal als ScriptBlock erzeugt und im Runspace-Pool nur noch aufgerufen (Mini-Wrapper).
- **Kleinste belastbare Korrektur.** Jede Anfrage ist kurz (4 s aktiv / 6 s Ruhemodus) und nach **jeder** Anfrage liegt eine Pflichtpause (0,3 s aktiv / 2,0 s ruhig) – der HTTP-Platz ist garantiert zeitweise frei. Ruhemodus erst nach drei leeren Polls; ein Befehl schaltet sofort auf aktiv zurück (Arena-Aufrufe bleiben schnell, Befehle kommen weiterhin über das Poll-Signal sofort an). Der 5-s-Heartbeat ist jetzt reiner Rückfall und läuft erst, wenn 20 s kein Poll mehr durchkam; der Poll frischt Sitzung und Anzeige ohnehin bei jeder Anfrage auf. Die Bridge begrenzt die Wartezeit serverseitig auf höchstens 8 s (schützt auch gegen ein altes Plugin im Studio-Ordner).
- **Abschaltbare Leistungsdiagnose (Standard AUS).** Einstellungen → „DIAGNOSE“ → „Leistungsdiagnose aufzeichnen“. Sie schreibt höchstens alle 30 Sekunden **eine** Zeile ins Protokoll und einen kompakten Bericht nach `%LOCALAPPDATA%\ArenaRobloxBridge\performance.txt`: HTTP-Anfragen der Bridge, Handler-Dauer (Ø/Max), UI-Tick-Zeit (Ø/Max) und je Place „Anfragen/Minute“, „Poll-Dauer Ø“, „HTTP-Platz belegt %“ und „Pause Ø“. Kein Logging pro Tick, keine zusätzliche Anfrage. Ein Place, das auffällig häufig pollt (> 30 Anfragen/60 s), wird einmal pro 5 Minuten im Protokoll gemeldet.
- **Nach dem Update Roblox Studio einmal neu starten**, damit Plugin **7.0.3** geladen wird. Ohne Neustart läuft im Studio weiterhin die alte Poll-Regel.
- **Ehrliche Einordnung.** Diese Änderung beseitigt eine im Code belegte Dauerbelegung (und den doppelten Kanal), gestützt auf die Roblox-Aussagen unten. Sie ist hier **nicht** auf Windows gemessen worden – deshalb ist die Leistungsdiagnose absichtlich eingebaut. Erst wenn `performance.txt` auf dem Zielsystem „HTTP-Platz belegt“ deutlich unter 100 % und wenige Anfragen pro Minute zeigt **und** das Lag verschwindet, ist der Fall abgeschlossen.
- **Mehrere Places waren der Extremfall:** Jedes verbundene Fenster hielt vorher seinen eigenen Dauer-Kanal (Long-Poll + 5-s-Heartbeat). Bei drei oder mehr Places war der Plugin-Anteil des Studio-HTTP-Kontingents damit praktisch vollständig dauerbelegt – weitere Plugins/Anfragen mussten warten. Mit Pflichtpause und Rückfall-Heartbeat ist pro Place immer ein Platz frei.

Quellen für den Befund (Roblox Developer Forum):
- Roblox-Staff zum Stallen durch Long-Polling: <https://devforum.roblox.com/t/httpservice-extremely-sluggish-in-studio/2658364>
- „HttpService only allows 3 in-flight requests at a time“ (Plugin-Queue, nur Studio-Neustart leert sie): <https://devforum.roblox.com/t/httpservice-only-allows-3-in-flight-requests-at-a-time/2673475>
- „Update HttpService wiki page to indicate 3 concurrent connection limit“ (Long-Poll-Plugin gegen lokalen Server; Roblox: Long-Polling ist ein Hack und nicht offiziell unterstützt): <https://devforum.roblox.com/t/update-httpservice-wiki-page-to-indicate-3-concurrent-connection-limit/243099>

### Windows-Messanleitung (5 Minuten, liefert den Beweis)
1. Bridge starten, **Einstellungen → DIAGNOSE → „Leistungsdiagnose aufzeichnen“ einschalten** (Vorschau kann aus bleiben). Roblox Studio neu starten, ein Place öffnen und **nichts** tun.
2. Zwei Minuten warten. Danach `%LOCALAPPDATA%\ArenaRobloxBridge\performance.txt` öffnen (Windows-Taste + R, Pfad einfügen).
3. Erwarteter Sollwert im Ruhezustand: „HTTP-Platz belegt“ **unter 80 %** und „Anfragen/Minute“ zwischen **7 und 16** je Place; ohne verbundenes Place dürfen die Plugin-Zeilen fehlen.
4. Zum Vergleich: Task-Manager → Details → `RobloxStudioBeta.exe` und `powershell.exe`/`ArenaBridge.exe` bei „CPU“ beobachten – jeweils im Leerlauf mit verbundenem Place und danach mit geschlossenem Studio.
5. Gegenprobe „mehrere Places“: zwei Places öffnen und die Zeilen in `performance.txt` vergleichen (je Place eine eigene Zeile).
6. Ist „HTTP-Platz belegt“ weiterhin ~100 %, läuft noch ein **altes Plugin** (Studio nicht neu gestartet) – die Datei nennt das in der Zeile „BEWERTUNG“.

## 7.0.2
- **Weniger Leerlauf-Rendering.** Die dauerhaft wiederholten Deko-Animationen im transparenten Hauptfenster wurden entfernt. Farbverläufe, Fensteraufbau sowie kurze Hover- und Einblend-Effekte bleiben erhalten; die Oberfläche muss im Leerlauf aber keine Aurora-/Glanz-Bewegungen mehr pro Frame neu zeichnen.
- **Place-Liste mit weniger Hintergrundarbeit.** Der sichtbare UI-Abgleich läuft alle 1,8 statt 0,9 Sekunden. Im minimierten Zustand wird nur die Tunnel-Ausgabe geleert; Place-Sitzungen und WPF-Zeilen werden bis zum Wiederherstellen nicht durchsucht/aktualisiert. HTTP-Server, Tunnel und Plugin-Verbindungen laufen unabhängig weiter; beim Wiederherstellen wird sofort aktualisiert.
- **Vorschau AUS ist jetzt wirklich ruhig.** Der per-Place Spinner läuft nur, solange die Vorschau aktiv und noch kein Bild/Fallback da ist; Ausschalten, Bild-Erfolg und Platzhalter stoppen seine WPF-Animationsuhr. Der visuelle Selbsttest wird übersprungen, wenn die Vorschau ausgeschaltet ist.
- **Weniger doppelte Prüfungen.** Arena-Übergaben werden einmal je UI-Aktualisierung statt für jede einzelne Place-Zeile geprüft. Der Studio-Leerlaufwächter prüft Zustand/Kamera alle 1,5 statt 0,5 Sekunden; Auswahländerungen werden weiterhin direkt über ihr Ereignis gemeldet.
- Nach dem Update Roblox Studio einmal neu starten, damit Plugin **7.0.2** geladen wird.

## 7.0.1
- **Mehr Platz in den Einstellungen und klare Schalterzustände.** Das Einstellungs-Inhaltsraster hat gleichmäßiges Innen-Padding. Beim Öffnen werden alle vier verbleibenden Schalter mit ihrem gespeicherten Wert initialisiert und ihre sichtbare AN/AUS-Position wird nach dem Laden nochmals synchronisiert.
- **Arena AI sitzt im Hauptfenster.** „Arena AI öffnen“ steht nicht mehr in den Einstellungen, sondern als grüner Button unten rechts unter der Place-Liste – im Stil von „Prompt kopieren“.
- **Verbundene Places bleiben sichtbar.** Scheitert der Aufbau einer aufwendigen Zeile, zeigt die Bridge eine sichere Minimal-Zeile mit Place-Name und „Prompt kopieren“. Fehler beim Erstellen, Aktualisieren oder Einhängen werden mit Session-ID und Stacktrace in `runtime.log` erfasst. Fehlt eine Zeile, zeigt die UI einen Reparaturstatus, ohne bereits sichtbare Zeilen zu verdecken, und protokolliert die fehlenden Session-IDs.
- **Simulation ehrlich eingeordnet und deaktiviert.** Der bisherige Mechanismus `StudioTestService:ExecuteRunModeAsync()` ist die offizielle Studio-Run-Simulation im selben Fenster; Studio verlässt dabei Edit Mode (`EditModeActive=false`). Die dokumentierte Roblox-API bietet keinen unterstützten Weg, Physik und Skripte bei aktivem Edit Mode (`EditModeActive=true`) laufen zu lassen. Deshalb ist `sim_start` jetzt mit `SIM_DISABLED` gesperrt – direkt, parallel und auch innerhalb von Batch-/Job-Aufrufen. `sim_status` unterscheidet Studio Run von Play/F5 (oder meldet `unknown`, wenn Studio es nicht sicher klassifizieren kann); `sim_stop` beendet nur bestätigte bridge-eigene Sessions. `compile_check`, `run_lua` und alle Bau-/Lesewerkzeuge bleiben verfügbar. Der irreführende Start-Schalter wurde aus den Einstellungen entfernt.
- Nach dem Update Roblox Studio einmal neu starten, damit Plugin **7.0.1** geladen wird.

## 7.0.0
- **Der Schnitt: kein Playtest mehr.** `play_start`, `play_stop`, `play_pause`, `play_resume`, `play_status`, `session_diag`, `character_state`, `move_character`, `teleport_character`, `respawn_character`, `gui_dump`, `gui_check`, `gui_click`, `gui_set_text`, `send_input`, `client_action` und `set_camera` sind entfernt – samt Reporter-Injektion, Session-Agent, SharedTable-Befehlskanal, Play-Here-Heuristik und Client-Agent. Die Bridge baut wieder, statt getrennte DataModels, Cross-DM-Kanäle und Zombie-Sweeps zu reparieren.
- **Studio-Run-Simulation statt Playtest (kein echter Edit-Modus).** `sim_start` nutzt `StudioTestService:ExecuteRunModeAsync()` und startet damit die offizielle Server-Simulation im selben Studio-Fenster. Dabei laufen Physik und Server-Skripte ohne Spieler, Charakter, Client-Skripte oder Play/F5-Test; Studio verlässt jedoch den Edit-Modus (`EditModeActive=false`). Eine unterstützte Physik-/Skript-Ausführung bei weiterhin aktivem Edit-Modus (`EditModeActive=true`) ist laut verfügbarer Roblox-API nicht möglich. `sim_stop` beendet die Session; `sim_status` liest den echten Zustand. Während der Simulation blockiert `SIM_RUNNING` dauerhafte Änderungen; `allowInSimMode=true` bleibt für bewusste Wegwerf-Änderungen.
- **Einstellung für den Studio-Run (7.0.0).** Sie blockierte ausschließlich `sim_start` (`SIM_DISABLED`, severity notice); Bauen, GUIs, Assets, Jobs, `compile_check` und `run_lua` blieben unberührt. In 7.0.1 wurde der Start-Schalter entfernt und `sim_start` bis zu einer unterstützten echten Edit-Modus-Simulation gesperrt. Einen vom **Nutzer** gestarteten Playtest blockiert die Bridge weiterhin (`USER_PLAYTEST_ACTIVE`) und bittet darum, selbst zu stoppen (Shift+F5) – sie kann und will ihn nicht fernsteuern.
- **UI Engine 2.0.** `ui_glow` baut Glow (nie mehr handgemachte Transparenz-Ketten), `ui_texture` liefert das Rezept „echte Textur zuerst“ (`TEXTURE_ASSET_MISSING` ist eine Warnung, kein Fehler), `ui_radial` baut Radialmenüs aus **einer** Bild-Id mit Ring- und Aktivfarbe aus der Engine (`RADIAL_ASSET_MISSING`, wenn keine Id vorliegt). `ui_audit` zählt Glow-Stapel, echte Texturbilder und Radials und nennt die Engine-Version.
- **Welt-Engine 1.0.** `world_style`/`style_lock` (Palette, Materialien, Dichte, Wetter, Seed), `site_survey` (gemessene Höhen, Materialien, Wasser, freier Raum, bestehende Teile), `variation` (deterministisch statt `math.random`), `prop_place`/`prop_save`/`prop_list` (wiederverwendbare Props mit Boden-Snap), `world_glow` (eine Engine-Lampe statt Glow-Bastelei), `refine` (messbarer Feinschliff) und `model_audit`/`world_audit` (Platzhalter, Blockouts, Phase, Stil-Treue – genau die Zahlen, die `HANDOFF_REQUIRED` liest).
- **Fortschrittsvertrag und Übergabe.** Jeder Aufruf trägt `progress={percent,message}`; ein fehlendes Prozentfeld gilt als 0 % und blockiert **nie** einen Bau. Die Place-Zeile färbt blau (arbeitet), grün (nach `report_done`), grau (keine Rückmeldung) und rot (Fehler), zeigt Nachricht und Tooltip und schreibt alles in Verlauf und `places-diagnose.txt`. `handoff { scope="game", ... }` ist nur für komplette Spiele oder Mehrsystem-Verbünde erlaubt (`HANDOFF_NOT_ALLOWED`/`HANDOFF_INCOMPLETE`) und wird der nächsten Sitzung desselben Places automatisch vorgelegt.
- **Fenster- und Place-Identität über stabile Schlüssel.** Die Zuordnung nutzt Fensterhandle, Prozess-Id und Place-Id statt Anzeigenamen; ein veraltetes Plugin steht rot unter dem Place-Namen und sperrt die Kopier-Buttons, statt still zu wirken.
- Keine Änderung an den bestehenden Bau-, Polygon-, Asset- und Job-Werkzeugen. Nach dem Update Roblox Studio einmal neu starten, damit Plugin **7.0.0** geladen wird.

## 6.2.0
- **UI Engine 1.0 – die Bridge kann endlich GUIs bauen.** Bis 6.1.5 gab es kein einziges GUI-Bauwerkzeug: `gui_dump`, `gui_check`, `gui_click` und `gui_set_text` sind ausnahmslos Test-Funktionen. Jede Oberfläche entstand freihändig über `create_instance`/`run_lua` – also im selben Zustand, in dem der Polygon-Bau vor 6.1.0 war. Die Folge waren reproduzierbar dieselben Fehler: `AnchorPoint` 0,0 zusammen mit `UIScale` (das Element wächst nach unten rechts statt aus der Mitte), Offset statt Scale (Handy-GUI verrutscht oder wird riesig), Inhalt über zu großen Eckenradien, `CanvasGroup` statt `Frame` ohne Grund, `UIGradient` immer auf dem Frame und nie auf einem `UIStroke`, keine Textur, kein Schatten – und farblich immer dasselbe dunkle Dashboard.
- **Die eine Idee: kein Frame ist je nur ein Frame.** Eine Oberfläche ist ein kompilierter Schichtstapel – Schattenstapel, Füllung, Füllgradient, gekachelte Raster-Textur, Konturstapel mit `UIGradient` **im** `UIStroke`, Glanzkante, Eckenprofil und ein Inhaltsschacht – eingefasst in einen Transform-Wrapper. Das ist das 2D-Gegenstück zur Polygonregel, dass jede Fläche aus Dreiecken dünner Wedges besteht.
- **Design-Raum statt UDim2.** Arena liefert Rechtecke in 0…100 des Elternteils; die Bridge kompiliert daraus reines Scale-`UDim2`, leitet den `AnchorPoint` aus der Ausrichtung ab und sichert Proportionen mit `UIAspectRatioConstraint`. Offset ist strukturell nicht erreichbar; jede Rückgabe enthält `offsetUsed = 0`. Layout-Kinder bekommen automatisch einen äußeren Slot, damit `UIListLayout`/`UIGridLayout` die Position steuert und die Skalierungsanimation trotzdem mittig bleibt.
- **Fünf neue Werkzeuge.** `ui_capabilities` probt mit `Instance.new`/`pcall` in genau dieser Studio-Version, ob `UIShadow`, einzelne `UICorner`-Radien, `UIStroke.StrokeSizingMode.ScaledSize`, `BorderOffset`, mehrere `UIStroke`s, `UIFlexItem`, `UIDragDetector`, `Path2D`, `StyleSheet`, `CanvasGroup` und `FontFace` existieren – kein Code mehr aus veraltetem Trainingswissen, und für jede fehlende Fähigkeit nennt die Antwort den automatischen Fallback. `build_surface` baut eine komposite Oberfläche, `build_interface` ein komplettes GUI samt mitgeliefertem Bewegungs-`LocalScript` in einem Call, `ui_skin` wählt eine von zwölf Kunstrichtungen oder liest den Stil vorhandener GUIs aus, `ui_audit` misst das Ergebnis.
- **Anti-Generik ist eingebaut.** Die Palette wird aus **einer** Markenfarbe harmonisch abgeleitet, mit Mindestsättigung – auch ein dunkler Skin bleibt farbig statt neutral-anthrazit. Entsättigtes Dunkelblaugrau wird mit `STYLE_TOO_GENERIC` abgelehnt (bewusster Opt-out: `allowGeneric=true`). Textfarben werden gegen den tatsächlichen Hintergrund auf Kontrast geprüft und notfalls korrigiert.
- **„Den Stil der anderen GUIs bitte“ wird messbar.** `ui_skin { action = "extract" }` liest ein bestehendes GUI und meldet dominante Farben, wahrscheinliche Markenfarbe, Eckenradien, Schriften und ob dort überhaupt Strokes, Gradients, Schatten oder Texturen verwendet werden. Diese Werte gehen direkt in den nächsten `build_interface`-Aufruf.
- **Ehrliche Messung statt Hoffnung.** `ui_audit` rechnet die effektiven Pixelgrößen für Phone/Tablet/Desktop/Ultrawide aus der Scale-Kette aus – ohne Screenshot und ohne Playtest – und meldet `offsetRatio`, Anker-Fehler, Ecken-Überlauf, Textkontrast, zu kleine Touch-Ziele, verschachtelte `CanvasGroup`s, das Stroke-Budget und einen `blandnessScore`, bei dem 1.0 exakt das generische dunkle Dashboard ist.
- **Dauerhafte Session-Regel.** `Get-BridgeGuides` liefert `uiEngineRules` mit acht harten Regeln und geprüftem Referenz-Lua in jeder Session – genau wie `polygonEngineRules` seit 6.1.4. Damit greift die Regel auch dann, wenn Arena bewusst eigenen GUI-Code über `run_lua` schreibt.
- Bestehende Werkzeuge bleiben unverändert. Nach dem Update Roblox Studio einmal neu starten, damit Plugin **6.2.0** geladen wird.

## 6.1.5
- **Polygone bleiben als ein Objekt verbunden.** `build_polygon_model` verschweißt jedes Polygon-Untermodell jetzt standardmäßig per `WeldConstraint`. Das behebt den konkreten Laufzeitfehler, bei dem unanchored Wedges zwar an der richtigen Position entstanden, in der Physiksimulation aber als unabhängige Teile auseinanderfielen und kreuz und quer rotierten. Nur ein bewusstes `autoWeld=false` schaltet die Verbindung ab.
- **Berechnete Rotation kann nicht mehr überschrieben werden.** Freie `style.properties` wurden bisher nach dem berechneten `Size`/`CFrame` angewandt. Dadurch konnten `Position`, `Orientation`, `Rotation`, `CFrame`, `Size` oder `PivotOffset` die korrekte Dreiecksgeometrie zerstören. Diese Builder-eigenen Felder werden nun gefiltert; `Size` und `CFrame` werden garantiert zuletzt gesetzt.
- **Messbare Diagnose statt Vermutung.** Die Rückgabe enthält `autoWeldDefault=true`, `weldedSubmodels`, `ignoredGeometryProperties` und `geometryInvariant`. Die Session-Regel routet Polygon-/Freiformflächen verbindlich über `build_polygon_model`, sofern nicht ausdrücklich Low-Level-Wedges verlangt werden.
- Bestehende Aufrufe bleiben kompatibel. Farben, Materialien, Kollision und andere normale Part-Eigenschaften bleiben erhalten; `autoWeld=false` ist der explizite Opt-out. Nach dem Update Roblox Studio einmal neu starten, damit Plugin **6.1.5** geladen wird.

## 6.1.4
- **Polygon Engine 2.0 – dauerhafte KI-Regel gegen 90°-Drehfehler & Nahtspalten.** `build_polygon_model` trianguliert Dreiecke seit 6.1.3 korrekt (siehe unten), aber die richtige `WedgePart`-Achsenkonvention war nirgends als feste, sitzungsübergreifende Regel für die KI hinterlegt. Schrieb Arena statt des Tools eigenen Lua-Code für Polygone/Wedges (z. B. über `run_lua`), konnte sie versehentlich Dicke, Höhe und Basiskante auf die falschen lokalen Achsen legen – genau das erzeugt die gemeldeten 90°-Drehfehler und klaffenden Nahtstellen.
- **Harte Achsen-Regel jetzt Teil jeder Session.** `Get-BridgeGuides` liefert automatisch bei Sessionstart, `get_docs` und `/api/docs` die unverletzliche Regel (lokal X = Dicke/Flächennormale, lokal Y = Höhe/Orthogonale zur Basiskante, lokal Z = Basiskanten-Richtung, `CFrame.fromMatrix(position, normal, up, dir)`) sowie eine fertige, geprüfte Referenz-Lua-Funktion `drawSeamlessTriangle` (längste Kante als Basis, Lotfußpunkt-Teilung in zwei rechtwinklige Keile, nach innen versetzter Skin-Offset gegen Nahtspalten).
- **Kein Verhaltenswechsel an `build_polygon_model` selbst.** Das Tool bleibt unverändert die stark empfohlene erste Wahl für Polygon-Modelle inklusive Retry/Fallback-Triangulierung und Vertex-Welding; die neue Regel greift nur, wenn Arena bewusst eigene Wedge-/Dreieck-Logik über `run_lua` schreibt.
- Nach dem Update Roblox Studio einmal neu starten, damit das Plugin **6.1.4** geladen wird.

## 6.1.3
- **Polygon-Builder: sichtbare Lücken geschlossen.** `build_polygon_model` hat einzelne Flächen kommentarlos weggelassen – besonders bei Bäumen, Stämmen, Tieren und anderen runden oder organischen Formen. Ursache war ein Punktreihenfolge-Bug in `MASTER_BUILD.triangleWedges`: Beim internen Umsortieren (längste Kante nach unten) wurden nur zwei der drei Dreieckspunkte neu gesetzt, sodass zwei Ecken auf denselben Punkt zeigten und ein völlig korrektes Dreieck als „entartet“ verworfen wurde. Ob eine Fläche entstand, hing damit allein von der zufälligen Reihenfolge der gelieferten Punkte ab – bei einem achteckigen Stamm fielen so alle 16 Wedges aus.
- **Offene Nähte werden wieder verschweißt.** `MASTER_BUILD.pointKey` erzeugte aus winzigen negativen Rundungsresten (z. B. `sin(2*pi)`) den Schlüssel `-0.00000` statt `0.00000`. Derselbe Punkt bekam dadurch zwei verschiedene Schlüssel, und runde Querschnitte konnten ihre eigene Anfangs-/End-Naht nicht schließen. Negative Null wird jetzt normalisiert.
- **Robustere Triangulierung mit Retry und Fallback.** `cleanPolygonPoints` entfernt vorab Beinahe-Duplikate und exakt kollineare Zwischenpunkte; scheitert eine Fläche trotzdem, versucht `triangulate` es mit gelockerter Toleranz, danach mit umgekehrter Orientierung und zuletzt mit einer Fan-Triangulierung. `weldEntryVertices` verschweißt praktisch identische Vertices eines Untermodells, bevor `closeOpenings` die Ränder sucht.
- **Ehrliche Diagnose statt stiller Lücken.** `build_polygon_model` liefert jetzt `facesTotal`, `facesBuilt`, `facesSkipped`, `incomplete` und einen lesbaren `warnings`-Text. Ein Modell mit übersprungenen Flächen sieht nicht mehr wie ein voller Erfolg aus; jeder Eintrag in `skipped` und `fallbackFaces` nennt Untermodell, Polygonname und Grund. Bestehende Felder bleiben unverändert.
- Nach dem Update Roblox Studio einmal neu starten, damit das Plugin **6.1.3** geladen wird.

## 6.1.2
- **Kritischer Start-Hotfix.** Die 6.1.1-Datei enthielt nach dem vorgesehenen letzten `Exit(0)` versehentlich sieben beschädigte Textfragmente, darunter eine alleinstehende schließende Klammer. Windows PowerShell parst das gesamte Skript vor dem ersten Fenster; deshalb konnte die Bridge nach dem funktionierenden EXE-Updater gar nicht mehr starten.
- **Behebung ohne Funktionsrückbau.** Der fehlerhafte Dateianhang ist entfernt. Oberfläche, Update-Hinweis und alle 6.1.1-Funktionen bleiben erhalten.
- **Dauerhafter Regressionstest.** `test_v398_structure.py` prüft jetzt die feste, beabsichtigte Schlusssequenz der PowerShell-Datei. Jede angehängte Zeile – ob unvollständig oder nicht – lässt den Release-Test fehlschlagen.

## 6.1.1
- **Polygon-Modelling wie in Blender – ausdrücklich stark empfohlen.** `build_polygon_model` kann jetzt in einem Call sehr große, vollständig untergeordnete Modelle aus mehreren Foldern/Untermodellen erstellen. Ein Baum kann etwa aus Stamm und drei Kronen bestehen; jedes Untermodell erhält eigene Farbe, Material-, Kollisions-, Transparenz- und normale Part-Eigenschaften. Auto-Welds halten jedes Untermodell zusammen (seit 6.1.5 standardmäßig aktiv), klassische benannte Haupt-Welds verbinden sie animierbar miteinander.
- **Nahtlose Wedge-Haut.** Die Dicke wird standardmäßig von der sichtbaren Polygonseite nach innen aufgebaut statt um die Flächenmitte. Dadurch bleiben die gelieferten Polygonpunkte die exakte Außenhaut und stark gegeneinander gedrehte Flächen erzeugen keine wachsenden Rillen mehr; die Innenseiten überlappen sauber. `thicknessPlacement=center` erhält bei Bedarf das alte Verhalten.
- **Offene Modelle automatisch schließen.** `closeOpenings=true` erkennt offene Rand-Loops eines Untermodells und erzeugt triangulierte `AutoCap`-Flächen – etwa wenn an einem Baumstamm die Oberseite vergessen wurde.
- **Toolbox-Säuberung vor dem Einfügen.** `insert_asset { sanitize=true }` entfernt bereits im noch nicht untergeordneten Asset alle Lua-Skripte, Remote-/Bindable-Events und Functions. So kann Arena Modelle bewusst als reine Geometrie ohne Skripte oder typischen Viren-Müll einsetzen.
- **Editor-Vorschau-Icons abschaltbar.** Ein neuer dauerhafter Schalter in den Einstellungen blendet die Live-Vorschau-Icons aus und stoppt sofort alle weiteren Fensteraufnahmen, um Leistung zu sparen.

## 6.1.0
- **Kurze, lebendige Windows-Mitteilungen.** `report_done` besitzt jetzt getrennte Felder für einen von Arena formulierten Titel (maximal 70 Zeichen) und Inhalt (maximal 140 Zeichen). Die Bridge validiert diese konservativen Windows-11-Anzeigebudgets, damit Toasts nicht zu langen Änderungslisten werden. Microsoft setzt bei adaptiven Toast-Textfeldern keine feste Zeichenzahl pro Feld; die Darstellung hängt von Layout, Breite und Skalierung ab (Titel bis zu 2 Zeilen, Beschreibungen zusammen bis zu 4 Zeilen). Deshalb verwendet die Bridge bewusst feste Vollanzeige-Budgets. Quellen: [Microsoft – App notification content](https://learn.microsoft.com/en-us/windows/apps/develop/notifications/app-notifications/adaptive-interactive-toasts) und [Notifications Visualizer](https://learn.microsoft.com/en-us/windows/apps/develop/notifications/notifications-visualizer) (5-KB-Payloadlimit).
- **Live-Vorschauen alle drei Sekunden.** Solange das Bridge-Fenster geöffnet und nicht minimiert ist, werden alle Place-Vorschauen weiter aktualisiert. Ein minimiertes Roblox-Studio-Fenster wird nicht mehr durch `IsIconic` vorab ausgeschlossen; die direkten `PrintWindow`-Aufnahmewege dürfen es weiterhin rendern.
- **Toolbox vollständig geöffnet.** Arena kann nach 3D-Modellen, Models, Meshes/MeshParts, Plugins, Fonts, Audio, Bildern/Decals, Video und Animation suchen. Der frühere `allowModels`-Freigabeschalter ist aus Vertrag und Anleitung entfernt. Typ-, Rechte- und Skriptprüfungen beim tatsächlichen Einfügen bleiben als transparente Rückmeldung erhalten.
- **Arena-Verlauf repariert.** Die History-Funktion gab alle Einträge durch ein überflüssiges unäres Komma als ein verschachteltes Array zurück. Die UI erhält nun eine flache Liste; Aktionen erscheinen wieder pro Place und in „Alle Places“.
- **Neue Meister-Bautools.** `build_assembly` erstellt bis zu 2.000 Instanzen einschließlich linearer oder radialer Wiederholungen direkt in einem Model. `build_polygon_model` akzeptiert Punktlisten oder kompakte `POLYGON … END`-Skripte. Die Bridge berechnet Newell-Normale, 3D-Projektion, Orientierung, Ear-Clipping für konkave Polygone, Triangulation und Wedge-CFrames. Jede Fläche wird ausschließlich aus ultradünnen WedgeParts gebaut (zwei pro Dreieck) und strukturiert gruppiert.
- **Freier arbeitende Arena.** Die lange Vorschriftenliste der Sitzungsdokumentation wurde durch eine kurze Fähigkeitenübersicht ersetzt. Arena kann Bau-, Asset-, Skript-, Batch- und Testwerkzeuge passend zur Aufgabe kombinieren. Dedizierte Bautools werden klar angeboten; `run_lua` bleibt für echte Speziallogik verfügbar.

## 6.0.6
- **Laufzeitursache aus 6.0.5 nachgewiesen.** Die ausgelieferte Datei lief mit
  Version `6.0.5`, SHA-256
  `7433925B060FDD21A699936B3B8267E899EF1BB80A1673119D1DDFFB9B20E588`,
  `LanguageMode=FullLanguage` und geladenem C#-Helfer. Trotzdem brach
  `New-PlacePreviewVisual` schon beim UI-Aufbau mit
  `MethodException: Für "new" und die folgende Argumenteanzahl kann keine
  Überladung gefunden werden: "1"` ab (Laufzeitzeile 16101). Der nachfolgende
  Selbsttest belegte die direkte Folge:
  `IMAGE_ASSIGN_SKIPPED ... grund=Zeile/IconImage fehlt`.
- **Gezielte Änderung in `New-PlacePreviewVisual`.** Der belegte
  Ein-Argument-Aufruf
  `[System.Windows.Media.DoubleCollection]::new(@(4.0, 8.0))` wurde ersetzt:
  parameterlos konstruieren, `4.0` und `8.0` einzeln per `Add` eintragen, dann
  erst `StrokeDashArray` zuweisen. Damit wird das von Windows PowerShell 5.1
  nicht bindbare `object[]` vermieden. Kein UI-Umbau und keine Änderung an
  Fensterzuordnung oder Aufnahmewegen.
- **Regressionstest erweitert.** `test_v398_structure.py` verbietet genau den
  fehlgeschlagenen Konstruktoraufruf, prüft die Reihenfolge
  Konstruktor → `Add(4.0)` → `Add(8.0)` → Zuweisung und kontrolliert alle
  funktionalen Versionsliterale mit exakten Anzahlen.
- **Live-Abnahme offen.** Die Änderung ist statisch geprüft, aber noch nicht
  auf dem Nutzer-PC bestätigt. Maßgeblich sind erst eine 6.0.6-Identität und
  `PREVIEW_UI_VERIFY`/`PREVIEW_UI_SELFTEST_OK` sowie danach die `cap-N`- und
  PNG-Nachweise. Keine Erfolgsmeldung vor diesen Laufzeitbelegen.

## 6.0.5
- **Fenster-Vorschau: zugewiesen, aber unsichtbar – Einblendung repariert.**
  Zwei Messbefunde vom Nutzer-PC haben die Ursache eingekreist:
  (1) Die Einstellungen zeigten „Version 6.0.4“, es lief also tatsächlich die
  neue Fassung – der Verdacht „Updater liefert nie aus“ ist damit widerlegt.
  (2) Die pinke Selbsttest-Kachel aus 6.0.4 erschien nie. Da ein einmal
  gesetztes Vorschaubild im Programm durch nichts mehr entfernt werden kann
  (`PreviewHasFrame = $true` sperrt das Platzhalter-Symbol, und
  `IconImage.Source` wird nirgends zurückgesetzt), hätte das Testbild dauerhaft
  stehen bleiben müssen. Es war also nie sichtbar – der Fehler lag im
  Anzeigepfad, nicht in der Fensteraufnahme.
- **Ursache und Fix (`Set-PlacePreviewImage`).** Das erste Bild einer Zeile
  wurde mit `Opacity = 0` eingesetzt; sichtbar wurde es ausschließlich durch
  eine `DoubleAnimation` (0 → 1). Läuft diese Animation nicht an, bleibt die
  Kachel dauerhaft leer, obwohl Bildquelle, `Visibility` und Layout korrekt
  sind. Genau dieser Ausfall ist in diesem Programm für die Place-Zeile selbst
  belegt – sie hat deshalb seit 5.0.2 einen Einblend-Wächter
  („Einblend-Animation kam nie an“); das Vorschaubild hatte keinen. Jetzt ist
  der Grundwert sofort `Opacity = 1`, die Animation ist nur noch Verzierung
  (`FillBehavior = Stop`), und ein Wächter korrigiert eine hängende
  Einblendung nach 400 ms hart (`PREVIEW_OPACITY_RESCUE`).
- **Ehrliches Selbsttest-Urteil.** `PREVIEW_UI_SELFTEST_OK` wurde bisher
  geschrieben, sobald das Zuweisen nicht geworfen hat – auch bei Deckkraft 0.
  Das Urteil fällt jetzt erst 1,5 s später und nur, wenn das Bild wirklich
  sichtbar ist (im Baum sichtbar, effektive Deckkraft > 0,05, Fläche > 0,
  Bildquelle gesetzt); sonst `PREVIEW_UI_SELFTEST_FAILED` mit konkretem Grund.
- **Neue Station `PREVIEW_UI_VERIFY`.** Misst Bild, Rahmen und Zeile
  (Visibility/Opacity/ActualSize/Source) und rechnet die effektive Deckkraft
  der Kette aus. Fehlt die Zeile ganz, laufen im Prozess weder
  Dispatcher-Timer noch Animationen – auch das wäre damit bewiesen.
- **Kleiner Kurzbericht zum Weitergeben:**
  `%LOCALAPPDATA%\ArenaRobloxBridge\preview-diagnose.txt` mit
  Laufzeit-Identität (Version/SHA-256), Aufnahme-Modus, Selbsttest-Urteil,
  Inhalt der PNG-Ablage und den letzten Vorschau-Stationen.
- Aufnahmewege, Fensterzuordnung, Design, Bedienung, Einstellungen, Server und
  Plugin-Protokolle bleiben unverändert. Keine Toast-/Popup-Meldungen.

## 6.0.4
- **Ende des Ratens: Laufzeit-Diagnose für die Fenster-Vorschau.** In den
  Place-Zeilen erschien trotz 6.0.1–6.0.3 weiterhin kein Vorschaubild – ohne
  dass ein einziger Aufnahmeversuch im Log belegt gewesen wäre. Jeder Versuch
  trägt jetzt eine kompakte Ablauf-ID und protokolliert die Stationen
  `CAPTURE_START` → `WINDOWS_ENUMERATED` → `HANDLE_RESOLVED` → `WORKER_STARTED`
  → `WORKER_COMPLETED` → `RESULT_RECEIVED` → `PNG_DECODED` → `IMAGE_ASSIGNED`
  → `IMAGE_VISIBLE` – jeweils mit Sitzung, Prozess-ID, Fensterhandle
  (HWND), Fenstertitel, Datentyp, Byte-Anzahl, Bildgröße und Fehlertext.
  Kein `catch`-Block im Vorschaupfad bleibt mehr still.
- **Sichtbarer UI-Selbsttest.** Beim ersten Place wird ein im Speicher
  gezeichnetes, unverwechselbar pink-limettenfarbenes Testbild durch exakt
  denselben `Set-PlacePreviewImage`-Pfad in die Kachel geschickt
  (`PREVIEW_UI_SELFTEST_OK`/`PREVIEW_UI_SELFTEST_FAILED` im Log). Erscheint
  das Testbild nicht, liegt der Fehler in WPF/UI; erscheint es, aber kein
  echtes Fensterbild, blockiert allein die Fensteraufnahme – und das Log
  nennt den blockierten Weg.
- **Robuste Bilddaten-Übergabe.** Die Aufnahme läuft über den kompilierten
  C#-Helfer `Arena.PreviewCapture` direkt im Hauptprozess. Das Ergebnis ist
  ein unveränderliches `byte[]` und durchquert keine PowerShell-Runspace-
  Grenze mehr (bei Kompilier-Fehlern, z. B. Sprachmodus ConstrainedLanguage,
  greift begründet geloggt der 6.0.3-Runspace-Fallback). Die UI-Zuweisung
  läuft ausschließlich über den WPF-Dispatcher.
- **Vier Aufnahmewege für GPU-/verdeckte Fenster.** `PrintWindow` mit
  `PW_RENDERFULLCONTENT` → `PrintWindow` ohne Flag → `WindowDcBitBlt`
  (DWM-Umleitfläche) → `CopyFromScreen` als letzter Fallback. Ein Weg gilt
  nur als erfolgreich, wenn die Bitmap nicht schwarz/transparent ist – der
  benutzte Weg und jeder Zwischenbefund stehen im Log. Jede Aufnahme liegt
  zusätzlich atomar als `%LOCALAPPDATA%\ArenaRobloxBridge\preview-cache\
  <sid>.png` vor (mit SHA-256-Kurzhash im Log, eindeutig prüfbar).
- **Laufzeit-Identität.** Beim Start protokolliert das Programm Version,
  absoluten Pfad und SHA-256 der wirklich laufenden Datei sowie den
  PowerShell-Sprachmodus – der Beleg, ob der Starter tatsächlich 6.0.4
  installiert hat oder weiter eine alte Kopie startet.
- **Keine neuen Blocker.** Kein synchroner Netzwerkzugriff im UI-Thread,
  kein `Worker.Stop`/`Dispose` auf dem UI-Thread (Task-Jobs werden bei
  Zeitüberschreitung nur fallengelassen). Design, Bedienung, Einstellungen,
  Server und Plugin-Protokolle bleiben unverändert.

## 6.0.3
- **Mehrfenster-Vorschau wirklich repariert.** Die Fensterliste wurde durch ein
  überflüssiges PowerShell-Komma als verschachteltes Array zurückgegeben. Bei
  mehreren Studio-Fenstern versuchte die Bridge deshalb, ein ganzes
  Handle-Array als einzelnes Fenster zu behandeln; die Aufnahme startete nie.
  Fenster- und Titellisten werden jetzt garantiert flach zurückgegeben.
- **Direkte Fensteraufnahme statt Bildschirmfoto.** `PrintWindow` mit
  `PW_RENDERFULLCONTENT` rendert das zugeordnete Studio-Fenster auch dann, wenn
  die Bridge oder ein anderes Fenster davor liegt. `CopyFromScreen` bleibt als
  automatischer Fallback für Systeme, die `PrintWindow` ablehnen.
- **Sofortiger Start ohne Web-Blockade.** Die synchrone Roblox-Thumbnail-
  Abfrage wurde aus dem WPF-Thread entfernt. Die Kachel ist wieder
  ausschließlich eine echte Studio-Fenster-Vorschau.
- **Selbstheilung und Diagnose.** Blockierte Aufnahme-Worker werden nach zehn
  Sekunden beendet und neu versucht. Auch eine bereits vor dem Worker
  gescheiterte Fensterzuordnung steht nun mit Ursache in `runtime.log`.

## 6.0.2
- **Spiel-Icon-/Vorschau-System repariert (der lang ersehnte Fix).** In 6.0.1
  blieb bei *jedem* gescheiterten Aufnahmeversuch des Studio-Fensters (z. B.
  Studio minimiert, Fenster mehreren Zeilen nicht eindeutig zuordbar, Fehler
  beim Aufnehmen) der Ladekreis endlos stehen – nie ein Bild, nie eine
  Fehlermeldung. Jetzt: Nach 3 gescheiterten Versuchen erscheint das
  Platzhalter-Symbol, die Aufnahmen laufen im Hintergrund weiter, und sobald
  eine klappt, blendet die Live-Vorschau ein. Jede fehlgeschlagene Aufnahme
  wird außerdem mit Grund in `runtime.log` protokolliert (gedrosselt), und
  die erste erfolgreiche Aufnahme je Sitzung wird einmalig bestätigt.
- **Zuordnung bei mehreren Studio-Fenstern robuster.** Der Zeilentitel musste
  bisher exakt dem bereinigten Fenstertitel entsprechen – der angehängte
  Hinweis „Studio neu starten (Plugin veraltet)“ oder Leerraum-/Groß-/Klein-
  Schreibabweichungen brachen die Zuordnung. Jetzt: exakter Treffer, danach
  toleranter Treffer (Leerraum, Groß-/Kleinschreibung, Anfangs-
  Übereinstimmung), danach der zuletzt bekannte Handle.
- **Null- und Type-Sicherheit.** Ein nicht auflösbarer Fenster-Handle kann
  nicht mehr still bis zur Aufnahme durchreichen; der Aufnahme-Worker bringt
  zudem seinen eigenen ScreenHelper-Fallback mit (Add-Type im Worker), falls
  der Typ im Haupt-Runspace nicht geladen werden konnte.
- **Update-Sicherheitsnetz (wichtigster Fix).** Startet der Starter (EXE) das
  Programm mit einem Status, der nicht beweist, dass er gerade frisch
  installiert hat („kein Update“, „keine Verbindung“, „Update-Fehler“,
  „Update-Suche-Fehler“), prüft das Programm jetzt selbst kurz gegen
  `version.json` im Repository und zieht ein Update notfalls direkt (kurzes
  Zeitlimit, stilles Scheitern, Neustart mit Hinweisfenster). Grund: Ein
  hängender oder defekter Starter ließ sonst jedes im Repository
  veröffentlichte Fix für immer beim Nutzer nicht ankommen – die plausibelste
  Erklärung dafür, dass mehrere Icon-Reparaturen der letzten Versionen beim
  Nutzer „nie ankamen“.
- Alles Weitere bleibt wie 6.0/6.0.1 (Design, Bedienung, Einstellungen,
  Server, Plugin-Protokolle).

## 6.0.1
- **Spiel-Icons ersetzt durch eine Live-Vorschau.** Statt eines von Roblox
  heruntergeladenen Spiel-Icons (das bei unveröffentlichten Places nie ein
  echtes Bild zeigen konnte, weil `game.GameId` dort 0 ist) macht die Bridge
  jetzt direkt einen Live-Screenshot des jeweiligen Roblox-Studio-Fensters –
  ohne Internetverbindung zu Roblox und unabhängig davon, ob das Place
  veröffentlicht ist. Aufnahmen laufen im Hintergrund (nie auf dem UI-Thread),
  sind pro Sitzung auf höchstens eine alle ~2,5 s gedrosselt und werden sofort
  auf Kachelgröße verkleinert. Ist das Studio-Fenster minimiert, wird die
  Vorschau bewusst nicht aktualisiert – das zuletzt gezeigte Bild bleibt
  stehen. Die „Alle Places“-Sammelzeile zeigt bewusst keine Vorschau.

## 6.0
- **Komplett neues Design: „Liquid Glass“.** Die gesamte Oberfläche ist nach
  dem Entwurf (grafik.png) neu gestaltet: ein tiefblau-violettes Fenster mit
  langsam driftenden Farblichtern (Aurora) hinter durchscheinendem Glas.
  Place-Zeilen sind Teal-Glaskarten, „Prompt kopieren“ und der
  Einstellungs-Knopf sind grüne Glas-Knöpfe, das „…“-Menü ist ein violettes
  Glas-Panel, Minimieren/Schließen sind runde Crimson-Knöpfe. Ein echter
  Rundungs-Beschchnitt sorgt dafür, dass die Farblichter nie über die
  Fensterecken hinausragen.
- **Animationen überall.** Das Fenster wächst beim Öffnen sanft auf;
  Place-Zeilen blenden ein (der bewährte Fade samt Watchdog aus 5.0.2 bleibt),
  heben sich beim Hover um 2 Pixel an und leuchten auf; das „…“-Menü blendet
  ein und gleitet hoch; alle Knöpfe tragen einen weichen Glas-Schein, der beim
  Hover aufleuchtet, und ziehen sich beim Drücken sanft zusammen; Spiel-Icons
  blenden weich ein; die Kopier-Bestätigung gleitet nach oben; An/Aus-Schalter
  (Einstellungen und „…“-Menü) gleiten weich; Verlaufs-Karten blenden ein; der
  Leerzustand schwebt leicht.
- **Auch die weiteren Fenster im neuen Design:** Einstellungen, Update-Hinweis
  und Arena-Verlauf tragen dasselbe Glas-Design mit Aurora-Lichtern und weicher
  Fenster-Einblendung. Der Startbildschirm ist halbtransparent geworden, sodass
  die Farblichter während des Starts hindurchscheinen.
- **Nichts Funktionales hat sich geändert.** Gleiche Knöpfe, gleiches Verhalten
  („…“-Toggle, „Nur Lesezugriff“ lässt das Menü offen, rot/grün-Schalter in den
  Einstellungen, keine Popups unten rechts). Server, Plugin, Tools und alle
  Protokolle sind nicht angefasst.
- Nach dem Update Roblox Studio einmal neu starten, damit das Plugin **6.0**
  geladen wird.

## 5.2
- **„Alle Places“ aufgeräumt.** Die Zeile zeigt jetzt wie alle anderen nur noch „Prompt kopieren“ und „…“. „Token zurücksetzen“ und der Sammelschalter „Nur Lesezugriff“ (wirkt auf alle verbundenen Places) bleiben im „…“-Menü erreichbar.
- **Spiel-Icons repariert.** Die bisherige Adresse des Studio-Ersatzbildes war tot (HTTP-Fehler), Fehlversuche wurden nie wiederholt, und als „Icon“ gecachte Fehlerseiten vergifteten den Cache dauerhaft – deshalb blieben die Rahmen leer. Jetzt: PNG-Signaturprüfung für jeden Download, kaputte Cache-Reste werden verworfen, Fehlversuche wiederholen sich mit ansteigender Pause (45 s …), nach dem dritten Versuch wird ein Ersatz-Icon lokal gezeichnet, und jeder Ladevorgang samt Fehlergrund steht in `runtime.log`. Das „Alle Places“-Mosaik wird nur noch bei echten Änderungen neu gebaut.
- **Arena-Verlauf überarbeitet.** Löschen- und Schließen-Knopf tragen das normale Titelleisten-Design (vorher ungestyltes Windows-Grau). Das Fenster lässt sich an Titelzeile und Hintergrund frei über den Bildschirm schieben; der Verlauf wird währenddessen nicht mehr neu aufgebaut und bei unverändertem Inhalt gar nicht mehr neu gerendert. Jede Aktionskarte ist deutlich flacher. Alle „[PLATZHALTER]“-Stellen zeigen jetzt echte Werte aus den Werkzeug-Ergebnissen (Zeilenzahlen, Kopien, Objekte), und jedes einzelne Werkzeug hat einen eigenen verständlichen deutschen Text. Dazu liefert das Plugin bei `set_script_source` jetzt auch `previousLines` mit.
- **Einstellungen schlanker.** Der Abschnitt „Letzte Arena-Meldung“ ist entfernt; die Fertig-Benachrichtigung (wenn eingeschaltet) bleibt unverändert.
- **„Alle Places“-Prompt kürzer.** Die Zeilen `MODE=ALLE_PLACES` und `HINWEIS=…` sind entfernt – die Mehr-Place-Anleitung bekommt Arena automatisch von der Bridge: Die erste Anfrage mit dem Sammel-Token beantwortet der Server direkt mit Place-Liste und Anleitung (`MULTI_PLACE_SELECTION_REQUIRED`).
- **Place-Liste räumt schneller auf – ohne Geister.** Geschlossene Places verschwinden nach ca. 15 statt 25 Sekunden (sauber abgemeldete nach ca. 4). „Geister-Places“, die unendlich hängen blieben, sind ausgeschlossen: Die Sichtbarkeit hängt nur noch am Presence-Lebenszeichen des Edit-Plugins (vorher reichte ein verklemmter Session-Reporter, der `lastSeen` weiterfütterte). Nach 120 Sekunden ohne Lebenszeichen wird eine Sitzung samt Token und allem Nebenzustand restlos entfernt (vorher 600 s).
- Nach dem Update Roblox Studio einmal neu starten, damit das Plugin **5.2** geladen wird.

## 5.0.2
- **Diagnose statt Rätselraten: Die Place-Liste wird hart überwacht.** Der Bug aus 5.0.0/5.0.1 (Anzahl oben stimmte, darunter blieb die Liste leer) wird nicht mehr geraten, sondern gemessen: Jeder catch-Block der Place-Liste schreibt jetzt Exception-Typ, Meldung, Skriptzeile und Stacktrace in `runtime.log` – vorher stand dort nur die nackte Meldung, die Ursache war damit praktisch verschluckt.
- **Nach jeder eingefügten Zeile misst das Programm den echten Fensterzustand** (Anzahl Kinder, Größe der Liste, Visibility/IsVisible/Höhe/Opacity der Zeile) und protokolliert ihn. Der Log trennt damit sauber die drei Fehlerbilder „Zeile nie gebaut“, „Zeile gebaut aber unsichtbar“ und „Layout ohne Platz“.
- **Sicherheitsnetz:** Icon, Auswahlmenü, Arena-Verlauf und die Einblend-Animation einer Zeile sind einzeln in try/catch gekapselt. Schlägt eines davon fehl, erscheint die Zeile trotzdem mindestens mit Name und „Prompt kopieren“-Knopf. Schlägt die Animation fehl oder startet sie nie, wird die Zeile hart auf sichtbar gestellt (Watchdog nach 1,5 s).
- Auch der Neu-Anordnungs-Block von `Sync-PlaceList` (`Children.Clear()` + neu anordnen) ist gekapselt und loggt Fehler – ein Fehler dort konnte die Liste zuvor spurlos leeren.
- Nach dem Update Roblox Studio einmal neu starten, damit das Plugin **5.0.2** geladen wird.

## 5.0.1
- **Spieleliste wird wieder angezeigt.** Die Anzahl der verbundenen Places oben stimmte, darunter blieb die Liste jedoch immer leer. Grund: `New-PlaceIconVisual` (und das Verlaufsfenster) legten ihr Panel in der Variablen `$host` ab – das ist in PowerShell die schreibgeschützte automatische Host-Variable. Die Zuweisung warf „Cannot overwrite variable Host because it is read-only or constant“, der Fehler wurde von `Sync-PlaceList` abgefangen und geloggt, und keine Zeile wurde je hinzugefügt. Die Panels heißen jetzt `$iconHost`, `$historyHost` bzw. der Parameter `$HostPanel`.
- Dadurch öffnet auch der Arena-Verlauf (pro Place und „Alle Places“) wieder zuverlässig.
- Nach dem Update Roblox Studio einmal neu starten, damit das Plugin **5.0.1** geladen wird.

## 5.0.0
- **Playtest-Steuerung erneut gehärtet.** Vor jedem Test registriert das Edit-Plugin den frischen, kurzlebigen Sitzungsschlüssel bei der Bridge. Ein Schlüssel aus einem älteren Playtest kann `move_character` oder `play_stop` damit nicht mehr mit einer 403-Antwort blockieren.
- **Bewegung und Stop funktionieren über die komplette Sitzung.** Die Session-Reporter senden `Humanoid:Move` über jeden Heartbeat während der gewünschten Dauer statt nur für einen Frame. `play_stop` wartet länger auf `StudioTestService:EndTest` und legt einen erneuten Reporter-Versuch ein, bevor der sichere Edit-Fallback greift.
- **„Alle Places“ ab zwei Verbindungen.** Der Sammel-Prompt besitzt einen pro Programmstart stabilen Token; Place-Zugänge kommen und gehen, ohne ihn zu ändern. Arena ruft `GET /api/places` auf und gibt anschließend für jeden Tool-Aufruf einen eindeutigen `targetPlace` an. Ohne Auswahl verweigert die Bridge die Aktion bewusst, statt ein falsches Spiel zu verändern.
- **Place-Icons und Verlauf.** Die Liste lädt abgerundete Roblox-Game-Icons mit einer Halbkreis-Ladeanimation und einem Roblox-Studio-Fallback für unveröffentlichte Places. Im neuen Verlauf sieht man laufende Aktionen blau, fertige Abfragen grau, Änderungen grün, Konsolenläufe gelb und Fehler mit Warnung rot. Der Verlauf ist pro Place oder gesammelt einsehbar und temporär.
- **Temporärer Lesezugriff.** „Nur Lesezugriff“ ist jetzt ein echter An/Aus-Schalter im Optionsmenü. Die Einstellung wird nicht gespeichert; jede Place-Registrierung beginnt wieder mit Lese- und Schreibzugriff.
- Nach dem Update Roblox Studio einmal neu starten, damit das Plugin **5.0.0** geladen wird.

## 4.0.5
- **Playtest-Stop repariert (echte Ursache, live gemessen).** Ein gestarteter
  Test liess sich nicht mehr automatisch beenden: `play_stop` und
  `move_character` meldeten `REPORTER_NOT_CONNECTED`, obwohl der Testspieler
  samt Charakter sichtbar war, und die Befehle stauten sich in Studio.
- **Der Fehler lag im Bridge-Server, nicht in Roblox.** Verräterischer
  Messwert: `reporterLoopCount` 501 bei `reporterPostFailCount` 500 – die
  Reporter-Schleife lief also einwandfrei, aber nur der allererste Heartbeat
  wurde je beantwortet. Grund: Der Heartbeat-Zustand kommt als
  `PSCustomObject` aus `ConvertFrom-Json`; `Update-PlayStateTracking` wies
  darauf `$newState.userPlaytestActive = …` zu. Auf einem `PSCustomObject`
  wirft das, sobald die Eigenschaft noch nicht existiert – jeder weitere
  Heartbeat endete im 500er-Handler. Dadurch enthielt die Antwort nie das
  Feld `commands`, und der Session-Reporter bekam `end_test` schlicht nie zu
  sehen.
- **Vier Absicherungen:** (1) neuer Setter `Set-StateField` beherrscht
  Hashtable *und* PSCustomObject; (2) der Heartbeat-Handler kapselt die
  Zustands-Übernahme in `try/catch` – Befehle werden ab jetzt **immer**
  zugestellt; (3) `sessionChannelCommand` nutzt den Session-Kanal, sobald ein
  Sitzungsschlüssel existiert (ein veraltetes `agentMode` sperrte vorher den
  einzigen funktionierenden Stop aus); (4) `play_stop` legt als letzte Stufe
  `end_test` fire-and-forget in die Warteschlange – der Reporter muss den
  Befehl nur noch abholen, nicht rechtzeitig beantworten.
- Der Session-Reporter sendet in seinem Snapshot jetzt `running=true` /
  `editModeActive=false` mit, damit der Server einen laufenden Test nicht aus
  einem unvollständigen Heartbeat als beendet verbucht.
- `PLAY_STOP_NEEDS_USER` („Bitte Shift+F5 drücken“) ist damit wieder der
  echte Ausnahmefall statt der Normalzustand.
- Nach diesem Update Roblox Studio einmal neu starten, damit das Plugin 4.0.5
  geladen wird.

## 4.0.4
- Live-Fehleranalyse: Nach dem Stop wurden alte Session-Reporter-Daten im Edit-Status weitergereicht. Aktive Sessions sind jetzt die Voraussetzung für Reporter-Snapshot, Spielerzahl und Agent-Status; EditModeActive=true zeigt wieder zuverlässig einen sauberen Edit-Zustand.
- `reporterSeenInOutput` zählt nur echte `#ARENA#`-Zeilen aus LogService. Der funktionierende Session-Plugin-Kanal wird separat diagnostiziert, statt Output-Zeilen vorzutäuschen.
- Der injizierte No-HTTP-Reporter hat eine fehlertolerante, überwachte Schleife und unterstützt `move_character` als Fallback im Session-DataModel.
- Nach diesem Update Roblox Studio einmal neu starten, damit das Plugin 4.0.4 geladen wird.


## 4.0.0
- Playtest-Rückkanal repariert: Das Plugin verwendet jetzt Roblox `SharedTableRegistry` korrekt und liest Reporter-Snapshots direkt aus der isolierten Test-Session. Dadurch funktionieren Play, `character_state`, Bewegung und Stop auch bei `HttpEnabled=false`, ohne sich auf eine Cross-DataModel-`MessageOut`-Brücke zu verlassen.
- `play_start` meldet erst Erfolg, wenn der Session-Reporter mit Spieler/Charakter erreichbar ist. `play_stop` nutzt bevorzugt `StudioTestService:EndTest` im Session-DataModel und räumt die temporären Reporter zombie-frei auf.
- UI komplett auf Tech-Dark umgestellt: Deep Slate, Neon-Cyan, Indigo und subtile Glassmorphism-Flächen. Einstellungen sind kompakt und enthalten keine langen Switch-Beschreibungen mehr.


> ⚠️ **Nach JEDEM Programm-Update Roblox Studio einmal neu starten**, damit
> das neue Studio-Plugin geladen wird. Die Bridge erkennt veraltete Plugins
> selbst (`pluginVersion` ≠ Programmversion) und meldet es in der
> Programm-Oberfläche sowie über `/api/status` als `versionMismatch`.

### 3.9.8
- **Kritischer Fix – das Autostart-Selbst-Update lud seit 3.9 nie etwas
  herunter.** `Get-RawGitHubText` rief immer
  `[System.Text.Encoding]::UTF8.GetString($response.Content)` auf – aber
  `raw.githubusercontent.com` liefert `text/plain; charset=utf-8`, sodass
  `Invoke-WebRequest` `.Content` bereits als String dekodiert. `GetString()`
  akzeptiert nur Bytes, der Aufruf landete still im `catch` → Rückgabe
  `$null` → „Branch nicht erreichbar“ → es startete immer die lokale
  Fassung (nur im Runtime-Log sichtbar). `Get-RawGitHubText` verarbeitet
  jetzt **beide Rückgabetypen** (Bytes und String) und entfernt ein
  mitdekodiertes BOM-Zeichen (U+FEFF), bevor die Datei mit UTF-8-BOM neu
  geschrieben wird – das verhindert ein doppeltes BOM am Dateianfang.
- **Der Rest der Update-Kette war bereits korrekt und wurde verifiziert:**
  Autostart-Registrierung (HKCU `Run`), Erkennung „Start ohne
  `-UpdateStatus`“, TLS 1.2, Branch-Kette (`update-config.json` → `main` →
  `master`), `[version]`-Vergleich, atomarer `.new`/`.old`-Tausch mit
  Rück-Sicherung, Hinweisfenster mit den Neuigkeiten aus
  `update-status.json` und kein Update-Loop (der neue Prozess bekommt
  `-UpdateStatus update-erfolgreich`).

### 3.9.7
- **Der Playtest-Reporter kommt jetzt garantiert IN der Test-Session an**
  (Live-Befund B1 aus 3.9.6: `reporterActive:false`, null `#ARENA#`-Zeilen –
  die Archivable-false-Injektion plus Sofort-Löschung im Edit-DataModel war
  ein Lösch-Race, der Reporter existierte in der Session nie). Ab jetzt wird
  als **normales, klon-sicheres Script** injiziert (`reporterVariant=2`,
  Standard); die Edit-Kopien werden erst gelöscht, **nachdem**
  `editModeActive=false` den Snapshot bewiesen hat (+1,5 s), plus
  Sicherheits-Sweeps bei `play_stop` und Plugin-Unload – im gespeicherten
  Place landet weiterhin nichts. Variante 1 (Archivable=false-Probe) bleibt
  per `play_start { reporterVariant=1 }` zum empirischen Gegentest erhalten.
- **Injektions-Beweis in Echtzeit.** Der Server-Reporter druckt sofort
  `#ARENA# hello`, der Client-Reporter ebenfalls. `startDiagnostics` enthält
  jetzt `reporterInjected` und `reporterSeenInOutput`; `play_status` zeigt
  die Reporter-Frische (`reporterLastKind`, `reporterLastAgeSeconds`,
  `arenaLineCount`, `reporterVariantUsed`).
- **Stop-Leiter statt Sackgasse** (Live-Befund B2: Sessions aus
  `ExecutePlayModeAsync` ließen sich aus dem Edit-DataModel weder per
  `RunService:Stop()` noch per Shift+F5/VirtualInputManager beenden;
  `StudioTestService:EndTest` funktioniert nur im Session-Server-DataModel).
  `play_stop` versucht jetzt geordnet: **(1)** `end_test`-Befehl an den
  Reporter über den Befehlskanal (s. u.), der die Session selbst per
  `EndTest("stopped_by_arena_bridge")` beendet; **(2)** Fallback
  `RunService:Stop()` aus dem Edit-DataModel; **(3)** sauberer Fehler
  **`PLAY_STOP_NEEDS_USER`** mit deutscher `userMessage` („Bitte in Studio
  Stop drücken (Shift+F5)“) statt Endlosschleife. Nach jedem erfolgreichen
  Stop wird zombie-frei aufgeräumt – ein sofortiger zweiter `play_start`
  klappt wieder.
- **Befehlskanal in die Session – ohne irgendwelche Einstellungen.**
  Priorität: (1) optionaler HTTP-Agent (nur bei `HttpEnabled=true`);
  (2) **SharedTableRegistry** als Cross-DM-Speicher zwischen Edit-Plugin und
  Session-Reporter (volle Argumente + echte Antworten; `session_diag`
  prüft per Live-Echo-Probe, ob die Tabelle wirklich über beide DataModels
  reicht); (3) **VirtualInputManager-Kombos** Strg+Alt+Umschalt+E/R/P auf dem
  Client-Reporter (antwortfrei, für `end_test`/Respawn/Zustand); (4)
  `GetTestArgs` beim (Neu-)Start (`arenaSpawn`). `teleport_character`,
  `respawn_character` und `set_camera` nutzen zur Laufzeit denselben Kanal;
  `move_character`/`gui_click` bleiben echte VIM-Eingaben aus dem Edit-DM.
- **Neues Diagnose-Werkzeug `session_diag`** (read-only): Reporter-Status
  (aktiv, letzte `#ARENA#`-Zeile + Alter, Injektions-Variante in der
  Session), Kanal-Status inkl. SharedTable-Cross-DM-Live-Probe mit Echo,
  Output-Cursor und Fehler-/Warnungszähler. Bei jedem Playtest-Problem zuerst
  `session_diag` und danach `get_output` mit Filter `ARENA` lesen.
- **Alle Play-Werkzeug-Guards kennen jetzt den Sessions-Zustand** (B3/B4):
  gültig bei `editModeActive=false` **oder** `IsRunning()`. Aktive Session
  ohne Reporter beantworten sie mit **`REPORTER_NOT_CONNECTED`** samt
  `sessionDiag`-Daten statt des falschen „No test running“. Auch dauerhafte
  Bearbeitungen werden jetzt bei getrennter Session korrekt blockiert.
- **UTF-8-GET-Dekodierung verifiziert** (Umlaute/Pfeile per GET bleiben
  korrekt, explizite UTF-8-Dekodierung der Roh-Query).

### 3.9.6
- **Playtest ohne Konfiguration – auch bei `HttpEnabled=false`.** Vor jedem
  `play_start` injiziert das Plugin einen temporären Server-Reporter in
  `ServerScriptService` sowie einen Client-Reporter in
  `StarterPlayerScripts`. Beide werden in den Test-Snapshot übernommen,
  sofort wieder aus dem Edit-DataModel entfernt und speichern somit nichts im
  Place. Sie drucken strukturierte `#ARENA#`-JSON-Zeilen über `LogService`:
  echte Spielerzahl, Charakterposition, Gesundheit, Humanoid-Zustand sowie
  GUI-Baum, Bildschirmkoordinaten und Klickziele. Das Edit-Plugin empfängt
  diese Zeilen auch dann, wenn die Test-Session keinerlei HTTP-Fähigkeit hat.
- **Getrennte DataModels richtig erkannt.** In aktuellem Studio bleiben
  `RunService:IsRunning()` und `Players` im Edit-DataModel leer, obwohl eine
  Session läuft. Der einzige Start-/Lauf-Orakel ist deshalb
  `StudioTestService.EditModeActive`: `true → false` innerhalb von 20 Sekunden
  ist Erfolg. Der Service-Fehler „previous one is still in progress“ bedeutet
  bei `EditModeActive=false`, dass eine vorhandene Session weiterverwendet
  wird – nicht, dass der Start fehlgeschlagen ist.
- **Steuerung ohne HTTP.** `character_state` und `play_status` verwenden den
  letzten LogStream-Snapshot (`agentMode: "logStream"`, echte
  `sessionPlayers`). `move_character` sendet echte W/A/S/D-/Shift-Tasten über
  `VirtualInputManager`, `gui_click` echte Mausereignisse an die vom
  Client-Reporter gemeldeten Koordinaten. Teleportieren erfolgt nur vor dem
  Spawn über `play_start { arenaSpawn={x,y,z} }` und `GetTestArgs`; das ersetzt
  den alten Laufzeit-Teleport/Play-Here-Sonderweg.
- **Stop ist kein HTTP-Sonderfall mehr.** `play_stop` ruft standardmäßig
  `RunService:Stop()` aus dem Edit-DataModel auf und wartet auf
  `EditModeActive=true`. Das beendet auch vom Nutzer gestartete getrennte
  Sessions. `PLAY_SERVICE_STUCK` entsteht nur nach einem echten
  Service-Fehler, `EditModeActive=false`, `IsRunning=false` und einem
  erfolglosen Stop-/3-Sekunden-Wiederherstellungsversuch.
- **Belegbare Diagnose und Protokollreparaturen.** `startDiagnostics` bei
  Start/Stop enthält `editModeActiveBefore/After`, den wörtlichen
  Service-Fehler, Pfad, `sessionPlayers`, `reporterActive`, `agentMode` und
  `httpEnabled`. Pending-Befehle nutzen Unix-Zeitstempel, verspätete Ergebnisse
  werden zuverlässig zugestellt, GET-Parameter werden explizit als UTF-8
  dekodiert und gleiche Play-Start/Stop-Retries innerhalb von drei Sekunden
  werden dedupliziert.
- **Versionsschutz.** Bei Plugin-/Bridge-Mismatch zeigt die UI „Studio neu
  starten“, `/api/status` meldet die Abweichung, und der KI-Umschlag enthält
  `plugin outdated - Tests warten`. HTTP bleibt bei aktiviertem HttpEnabled als
  schneller Zusatzpfad erhalten, ist aber niemals eine Voraussetzung.


### 3.9
- **Komplette Steuerung per HTTP GET (wichtigste Neuerung).** Die Bridge lässt
  sich jetzt vollständig über ganz normale GET-Anfragen bedienen – exakt
  gleichwertig zu POST. Hintergrund: Manche KI-Umgebungen dürfen keine direkte
  Verbindung zu `trycloudflare.com` aufbauen und erreichen den Tunnel nur über
  ihren Web-Abruf-Dienst, der ausschließlich GET ohne Datenkörper kann. Neu:
  - `GET /api/tool?token=…&tool=NAME&args=<URL-kodiertes JSON>&timeoutSeconds=N`
  - `GET /api/tools/parallel?token=…&calls=<URL-kodiertes JSON-Array>`
  - `GET /api/upload?token=…&uploadId=…&chunkIndex=N&chunkCount=M&text=<URL-kodiert>`

  Der Server baut aus den Abfrage-Parametern denselben Körper, den ein POST
  geschickt hätte, und schickt ihn durch **denselben Programmpfad**. Dadurch
  sind `_bridge`-Umschlag, `_sessionStart`, Stückelung/Blobs, die
  `SELF_TEST_DISABLED`-Sperre, Play-Absichten und `report_done` identisch.
  Dokumentation, Manifest (Endpunkt-Liste) und die Sitzungsstart-Hinweise sagen
  Arena ausdrücklich, dass sie **ausschließlich über GET** arbeiten kann
- **Kopier-Bestätigung**: Nach „Prompt kopieren“ im „…“-Menü erscheint ein
  dezenter Hinweis im Fenster („Prompt wurde in die Zwischenablage kopiert“),
  der nach wenigen Sekunden von allein ausblendet – kein Popup
- **Autostart sucht selbst nach Updates**: Ist „Beim PC-Start automatisch
  öffnen“ aktiv, startet Windows das Skript ohne den Starter. Die Bridge prüft
  deshalb jetzt selbst: `version.json` von GitHub laden (Branch-Kette
  konfiguriert → `main` → `master`), bei neuerer Version `ArenaBridge.ps1`
  herunterladen, sauber austauschen (`.new`-Datei, alte Instanzen beenden),
  neu starten und das Update-Hinweisfenster zeigen. Netzprobleme blockieren den
  Start **nie** – kurze Zeitlimits, im Zweifel still weiter mit der lokalen
  Fassung

### 3.8
- Große eigenes Einstellungsfenster: alle An/Aus-Optionen sind jetzt echte
  Schalter mit **rot = aus** und **grün = an** statt Kontrollkästchen
- **Alle Einstellungen werden dauerhaft gespeichert** (settings.json):
  Autostart, Selbst-Tests, Fertig-Meldung und auch „Nur Lesezugriff“ je Place
- Neue Einstellung **„Arena darf sich selbst testen“** (Standard: an). Aus:
  Run, Play und Play Here sind für Arena gesperrt – nur die Editor-
  Simulationen bleiben. Arena wird in Doku/Manifest/jeder Antwort informiert,
  dass der Nutzer das bewusst ausgeschaltet hat (SELF_TEST_DISABLED) – es
  hält die Bridge nicht für kaputt
- Neue Einstellung **„Benachrichtigung, wenn Arena fertig ist“** (Standard:
  aus). An: Arena ruft am Ende seiner Arbeit den neuen Befehl `report_done`
  mit einer eigenen deutschen Meldung – der Nutzer bekommt eine echte
  Windows-Benachrichtigung mit eigenem Titel und kurzem Inhalt
- Playtests deutlich zuverlässiger: Start/Stop über den offiziellen
  StudioTestService (neue Studio-API), gestaffelte Stop-Versuche, und der
  alte fehlerhafte Run-Fallback („kein Charakter spawnt“) ist entfernt
- Der Server verfolgt selbst, wer einen Test gestartet hat – merkt sich also
  auch zuverlässig, wenn der **Nutzer** einen Playtest startet/stoppt (selbst
  wenn das Plugin währenddessen neu lädt). Arena sieht bei jedem Aufruf,
  dass ein Test läuft, und kann ihn beenden (play_stop) oder seine Antwort
  beenden und um Ruhe bitten
- Neuer Modus **play_here** (Play Here = Charakter spawnt an der Edit-
  Kamera): wird erkannt und kann von Arena gestartet werden; Run / Play /
  Play Here / Editor-Simulation sind klar in der Doku getrennt
- Nutzer-Aktivität im Studio (Auswahl, Kamera) erreicht Arena als
  user_active-Ereignisse + userWorking-Hinweis

### 3.7
- Neue Anthrazit-/Grau-/Pink-Oberfläche mit stärkeren Kontrasten
- Update-/Willkommensfenster bleibt ohne Zeitlimit offen und startet das
  eigentliche Programm erst nach einem bewussten Klick auf OK
- Aktiver Play-/Run-Test blockiert dauerhafte Bearbeitungen schon in der
  Bridge; Arena erhält eine kritische Stop-Anweisung und bittet den Nutzer,
  den Playtest selbst zu beenden

### 3.6
- Automatische Updates über GitHub (Starter prüft bei jedem Start)
- Update-Fenster mit Neuigkeiten nach jedem Update, Willkommens-Fenster beim
  ersten Start
- Rote „1“ am Einstellungs-Button, wenn die Update-Suche oder das Update
  fehlschlug (Details stehen dann in den Einstellungen)
- Popup-Nachrichten unten rechts entfernt
- Auswahlmenü „…“: erneuter Klick schließt es wieder; „Nur Lesezugriff“
  lässt es offen

### 3.5
- Port-Freigabe repariert (http.sys/PID 4, deutsches netstat)
- Startbildschirm blieb bei abgebrochenem Start unsichtbar – behoben

### 3.4
- Kompletter Startbildschirm mit Ladekreisel und Fortschritts-Anzeige
- Belegten Port automatisch freigeben
- Kreuz oben rechts beendet das Programm garantiert komplett
- Eigenes EXE-Symbol (Logo)

### 3.3
- cloudflared wird vollautomatisch installiert (Download von GitHub,
  Fallback winget)
- EXE-fähig (ps2exe)

### 3.2 / 3.1 / 3.0
- Siehe Kommentarblock am Anfang von `ArenaBridge.ps1`.
