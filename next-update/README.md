# Next Update — Beta bauen, testen und später veröffentlichen

`next-update/` ist eine **isolierte Arbeitskopie** für die nächste Bridge-Version
und das vorbereitete Beta-/Stable-Update-System. Der Ordner `next-update/` ist
der einzige Arbeitsbereich dieser Vorbereitung. Die Root-Bridge, der bestehende
Updater und die bisherige Auslieferung bleiben unverändert.

> **Wichtig:** In dieser Änderung wurde keine Windows-EXE gebaut oder
> veröffentlicht. Die EXE baut der Nutzer auf seinem Windows-PC mit der BAT in
> diesem Ordner. Der neue Updater ist noch nicht in die laufende Root-Bridge
> integriert; beide Channel-Manifeste sind deshalb deaktiviert.

## Schnellstart: genau eine BAT-Datei

1. Lade das Repository als ZIP herunter, entpacke es und öffne den Ordner
   `next-update`. Die Kurz-Anleitung dafür liegt zusätzlich in `START-HIER.txt`.
2. Führe **genau `Build-EXE.bat`** per Doppelklick aus. Sie baut immer die
   lokale Beta. Keine andere BAT im `next-update`-Hauptordner ist für den
   normalen Build vorgesehen. `Build-EXE.ps1` ist ein internes Skript und soll
   nicht per Doppelklick gestartet werden.
3. Warte auf `BUILD ERFOLGREICH`. Der Builder führt vor der Ablage zusätzlich
   einen echten Start der temporären EXE im isolierten Smoke-Test aus: x64,
   STA, WPF und das eingebettete Titelbild müssen funktionieren. Bei einem
   Fehler wird die neue EXE nicht als fertige Ausgabe übernommen.
4. Die normale Beta zum manuellen Test liegt anschließend exakt hier:
   `next-update/user-builds/beta/ArenaBridge.exe`. Sowohl BAT als auch
   PowerShell-Ausgabe zeigen den vollständigen PC-Pfad.
5. Schließe vor dem Test alle älteren ArenaBridge-Fenster vollständig und starte
   dann diese `ArenaBridge.exe` von Hand. Die Bridge erlaubt absichtlich nur
   eine laufende Instanz. Bei einer schon geöffneten Bridge zeigt die neue
   Beta jetzt einen Hinweis statt kommentarlos zu enden.
6. Wenn nach dem Schließen anderer Bridge-Fenster weiterhin kein Fenster
   erscheint, starte
   `next-update/user-builds/beta/Start-Diagnostic.bat`. Die Konsole bleibt
   sichtbar. Lass sie geöffnet und notiere den Fehlertext. Die erste Datei zum
   Prüfen ist `%LOCALAPPDATA%\START-CHECK.txt`; die BAT nennt auch die weiteren
   Startdateien.

### Was der Build erzeugt

Unter `next-update/user-builds/beta/` liegen nach einem erfolgreichen Build:

- `ArenaBridge.exe` — **die normale App**, die du auf deinem PC testen sollst.
- `ArenaBridge-Diagnose.exe` — lokale Konsole-Ausgabe für die Fehlersuche.
- `Start-Diagnostic.bat` — startet nur die Diagnose-EXE sichtbar.
- `release-metadata.json` und `*.sha256` — Größe und SHA-256 der beiden EXEs;
  beim späteren Release ist nur der Wert für die normale `ArenaBridge.exe`
  relevant.
- Zeitgestempelte Backups älterer lokaler Builds, falls bereits welche da sind.

Das Titelbild wird beim Build in die EXE eingebettet; die normale EXE braucht
keine zusätzliche Bilddatei neben sich. Das Programm erhält außerdem das
Anwendungssymbol aus `assets/ArenaBridge.ico`. Die Diagnose-EXE und die
Diagnose-BAT sind **nur für dich**, nicht für einen Release-Upload.

### Voraussetzungen

- 64-Bit-Windows mit Windows PowerShell 5.1, WPF und .NET Framework.
- Internetverbindung für die Installation des `ps2exe`-Moduls beim ersten
  Build. Das Modul wird nur für dein Windows-Benutzerkonto installiert, nicht
  systemweit.
- Falls Windows SmartScreen bei einer selbst gebauten/unsignierten Beta warnt,
  veröffentliche oder starte die Datei nur, wenn du dieser lokalen Build-Quelle
  vertraust. Der Builder signiert die EXE nicht.

Der Builder prüft `next-update/ArenaBridge.ps1` zuerst mit dem echten
Windows-PowerShell-5.1-Parser. Er kompiliert ausschließlich diese Kopie — nie
die Root-Datei. Das Beta-Build-Skript veröffentlicht nichts und ändert keine
Channel-Datei.

## Für alle Nutzer bereitstellen — erst nach deinem PC-Test

**Nicht** `ArenaBridge.exe` in Git committen, nicht in `user-builds/beta/`
liegen lassen und nicht als Quelltext-Datei ins Repository legen. Der
`user-builds`-Ordner wird absichtlich von Git ignoriert und ist nur dein lokaler
Build-/Testordner.

Nach einem erfolgreichen Test und deiner ausdrücklichen Freigabe ist der
öffentliche Ablageort ein **GitHub-Release** im Repository
`merta-studios/arenarobloxbridge`:

1. Erstelle für die geprüfte Beta einen eigenen Release-Tag, beispielsweise
   `v7.6.3-beta.1` (bei späteren Builds jeweils eine neue Beta-Nummer).
2. Hänge als einziges App-Artefakt `ArenaBridge.exe` aus
   `next-update/user-builds/beta/` an den Release an.
3. Vergleiche Dateigröße und SHA-256 mit `release-metadata.json` bzw.
   `ArenaBridge.exe.sha256`. Lade nicht `ArenaBridge-Diagnose.exe`, die
   Diagnose-BAT, den lokalen Metadatenordner oder eine alte Backup-EXE hoch.

Ein Release macht die EXE öffentlich herunterladbar, aber **aktiviert nicht
automatisch den neuen Updater**. `channels/beta.json` und
`channels/stable.json` bleiben absichtlich `enabled: false`, bis der Updater in
einem eigenen, ausdrücklich freigegebenen Schritt in die laufende Bridge
integriert und auf Windows abgenommen ist. Bitte die Manifeste jetzt nicht
manuell aktivieren. Stable bleibt bis nach erfolgreichem Beta-Test und
separater Freigabe deaktiviert.

## Ordnerkarte: was ist für dich wichtig?

| Pfad | Zweck | Was tun? |
|---|---|---|
| `START-HIER.txt` | Kurze Nutzer-Anleitung | Lesen, falls du nur bauen/testen willst. |
| `Build-EXE.bat` | Einziger normaler Build-Klick | Doppelklicken; baut nur Beta. |
| `ArenaBridge.ps1` | Bridge-Quelltext der nächsten Version | Änderungen werden ausschließlich hier vorbereitet. |
| `Build-EXE.ps1` / `parse-gate.ps1` | Interner Build und Parserprüfung | Nicht separat zum normalen Bauen starten. |
| `assets/` | Eingebettetes Titelbild und EXE-Symbol | Wird vom Builder verwendet; neben der EXE nicht nötig. |
| `user-builds/beta/` | Lokale Beta- und Diagnose-Ausgaben | EXE testen; nicht committen. |
| `user-builds/stable/` | Lokaler Stable-Build, derzeit gesperrt | Nicht verwenden, bis Stable ausdrücklich freigegeben ist. |
| `release-inbox/` | Optionaler lokaler Ablage-/Prüfbereich | Kein Git- oder Upload-Ziel. |
| `channels/*.json` | Spätere Beta-/Stable-Manifeste | Beide aus; jetzt nicht aktivieren. |
| `updater/Update-Bridge.ps1` | Separater zukünftiger Updater | Noch nicht integriert; nicht als App starten. |
| `test_*.py`, `run_offline_tests.py` | Offline-Regressionsprüfungen | Für Wartung/Entwicklung, nicht für den EXE-Build nötig. |
| `*_CONTRACT.md`, weitere Versionsdokumente | Entwicklungs-/Funktionsverträge | Kontext für spätere Änderungen. |

## Was bei einem späteren Update zu tun ist

Ich arbeite auch bei späteren Änderungen nur in `next-update/` und schreibe dir
bei jeder Beta konkret dazu:

- welche Versionsnummer und welche Dateien geändert wurden;
- dass du wieder ausschließlich `Build-EXE.bat` im `next-update`-Ordner
  ausführen sollst;
- den exakten Pfad der neu gebauten Test-EXE;
- was du auf deinem Windows-PC testen sollst;
- erst nach deiner Freigabe: welcher GitHub-Release-Tag und welche Datei
  veröffentlicht werden sollen.

Du musst keine EXE hochladen, keine Stable-Fassung erstellen und kein Manifest
aktivieren, bevor ich es ausdrücklich als nächsten Schritt beschreibe und du
zustimmst.

## Beta vor Stable und Manifest-Status

`channels/beta.json` und `channels/stable.json` sind momentan absichtlich
`enabled: false`; beide enthalten keine Download-URL und keinen Hash. Das
Schema liegt in `channels/manifest.schema.json`. Es gibt weder einen
automatischen Upload noch ein automatisches Umschalten auf Stable.

Geplante Reihenfolge: lokaler Beta-Build → PC-Test → deine Freigabe →
GitHub-Release-Asset → späterer, separater Updater-Handoff/Windows-Test → erst
danach gegebenenfalls Beta-Manifest. Stable folgt nur nach eigenem Beta-Test
und ausdrücklicher Freigabe.

## Separater Updater — vorbereitet, nicht integriert

`updater/Update-Bridge.ps1` ist ein eigenständiger Windows-Updater. Er wird
nicht von `Build-EXE.bat` ausgeführt und ist noch nicht in `ArenaBridge.ps1`
eingebunden. Details und Sicherheitsgrenzen stehen in
[`updater/README.md`](updater/README.md).

Der vorbereitete Ablauf:

- akzeptiert nur den angeforderten Kanal und verweigert deaktivierte oder
  widersprüchliche Manifeste;
- verlangt HTTPS auf GitHub/GitHubusercontent ohne Zugangsdaten oder fremden
  Port und prüft jedes Redirect-Ziel erneut;
- begrenzt Manifeste, Dateigröße, Redirects und Downloadzeit;
- verlangt exakt `ArenaBridge.exe`, prüft Dateigröße und SHA-256 und verweigert
  Downgrades oder ungültigen lokalen Update-Status;
- wartet auf die beendete Ziel-EXE, beendet sie aber niemals selbst;
- lädt erst in ein Staging-Verzeichnis, verifiziert vor dem Austausch, nutzt
  `File.Replace`, bewahrt ein Backup und versucht bei Fehlern einen Rollback.

Ein Live-Rollout darf erst nach Integration in die Bridge und einem echten
Windows-Testkonto beginnen. Der aktuelle Arbeitsstand legt das Fundament,
verknüpft es aber absichtlich nicht mit dem alten Updater.

## Offline-Tests und Grenzen

Die Offline-Regressions- und Strukturtests sind eigenständige Skripte (keine
`unittest`-`TestCase`-Klassen). Im Ordner `next-update/` installierst du bei
Bedarf die Test-Extras und startest dann den Runner:

```powershell
python -m pip install -r requirements-test.txt
python run_offline_tests.py
```

Der Runner führt alle `test_*.py`-Skripte nacheinander aus und liefert einen
Fehlerstatus zurück, sobald ein Test fehlschlägt. `parse-gate.ps1` sowie
`test_v762_runtime.ps1` benötigen zusätzlich Windows PowerShell; letzterer ist
ein isolierter Open-Cloud-Laufzeittest ohne Live-Netzwerk. Ein erfolgreicher
Offline-Test belegt weder eine echte Roblox-Studio-Abnahme noch eine
Kompilierung auf dem Windows-PC des Nutzers. Der lokale Build-Smoke-Test belegt
nur das Starten der EXE im PS2EXE/WPF-Host, nicht die vollständige Roblox-
Studio-Funktion.
