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
| `test-v39.ps1` | Logik-Tests der 3.9-Features (optional, lokal ausführen; wird NICHT vom Starter geladen) |

## So wird ein Update veröffentlicht

1. `ArenaBridge.ps1` im Repository durch die neue Version ersetzen.
2. In `version.json` die `version` erhöhen (z. B. `3.6` → `3.7`) und die
   `notes` mit den Neuigkeiten füllen – genau dieser Text erscheint den
   Nutzern nach dem Update im Update-Fenster.
3. Änderungen committen und pushen. Fertig!

Beim nächsten Start der ArenaBridge.exe wird das Update automatisch erkannt,
heruntergeladen und mit dem Hinweis-Fenster („Update installiert!“) gestartet.

## Versionsverlauf

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
