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
| `test_v398_structure.py` | Python-Strukturtest für 5.2 (Versionen, Lua via luaparser, XAML-XML; kein PowerShell nötig) |
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
  Windows-Benachrichtigung (z. B. „Ich bin fertig“)
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
