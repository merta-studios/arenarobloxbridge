# Next Update — getrennte Vorbereitungsstruktur

`next-update/` ist eine eigenständige Arbeitskopie für die nächste Bridge-Version
und ein **separates, noch nicht aktiviertes** Beta-/Stable-Update-System. Die
Root-Bridge, der bestehende Updater und die bisherige Auslieferung bleiben
unverändert. Die spätere Umstellung des laufenden Programms auf den neuen
Updater ist ausdrücklich ein eigener Schritt in einer späteren Session.

> **Keine EXE in dieser Änderung:** Der Nutzer baut EXEs selbst. Hier liegen nur
> Quelltext, Build-Skript und Update-System-Dateien; es wird keine EXE erzeugt
> oder veröffentlicht.

## Arbeitskopie und Quellregeln

- `ArenaBridge.ps1` ist eine vollständige Kopie der Root-Datei. Änderungen in
  diesem Verzeichnis betreffen nur die Kopie.
- Die laufende Version des Projekts und der Root-Updater wurden nicht auf die
  neue Update-Infrastruktur umgestellt.
- Place- und Nutzerkonventionen haben Vorrang vor allgemeinen Empfehlungen:
  zuerst konkrete Nutzerwünsche, dann den vorhandenen Place-Stil/Workflow,
  danach die am besten passende allgemeine Lösung. Blender ist für passende
  neue Geometrie empfohlen, aber nicht verpflichtend; Parts, Polygone, Meshes,
  bestehende Skript- und GUI-Muster bleiben gültige Wege.
- Für einfache Beobachtungs-/Leseaufgaben wird Fortschritt als nicht anwendbar
  gezeigt; ohne echte Prozentmeldung gibt es keinen erfundenen 0-%-Balken.
- Im Open-Cloud-Tutorial gibt es keine IP-Einrichtung und keine Beispiel-IP;
  die vorhandene IP-Konfiguration außerhalb des Tutorials wurde nicht geändert.

## Selbst eine EXE bauen

Auf einem Windows-PC im Explorer `Build-EXE.bat` doppelklicken oder in einer
PowerShell:

```powershell
.\Build-EXE.bat beta
```

Voraussetzungen:

- Windows PowerShell 5.1 und .NET Framework/WPF, passend zur Bridge.
- Internetzugang zur Installation des `ps2exe`-PowerShell-Moduls beim ersten
  Build. Das Modul wird nur im Benutzerprofil installiert, nicht systemweit.
- Für Stable-Builds ist zusätzlich die ausdrückliche Bestätigung
  `RELEASE STABLE` erforderlich. Die Stable-Datei ist zunächst trotzdem nur
  ein lokaler Build, keine Veröffentlichung.

Der Build führt zuerst `parse-gate.ps1` mit dem echten Windows-PowerShell-5.1-
Parser auf genau der Kopie `next-update/ArenaBridge.ps1` aus. Nur wenn sie
syntaktisch sauber ist, startet `ps2exe`. Lokale Ausgaben liegen danach unter
`user-builds/beta/` oder `user-builds/stable/`; dort erscheinen außerdem
`release-metadata.json` und `ArenaBridge.exe.sha256`. Eine vorherige EXE wird
als zeitgestempeltes Backup aufgehoben. `next-update/.gitignore` hält erzeugte
EXEs, Metadaten und Release-Pakete aus Git heraus.

### Dateien und Ablageorte

- `ArenaBridge.ps1`: der Programmquelltext, den dieser Builder kompiliert.
  Für diese getrennte Vorbereitung nur diese Datei unter `next-update/`
  bearbeiten; der Build nimmt nicht die Root-Kopie.
- `version.json`: dreiteilige Quellversion plus Update-Notizen. Der Builder
  verlangt, dass der Versionskern in `-BuildVersion` genau dazu passt.
- `Build-EXE.bat`, `Build-EXE.ps1` und `parse-gate.ps1`: Startskript,
  Build/Validierung und Parserprüfung. Diese bleiben zusammen in `next-update/`.
- `user-builds/beta/ArenaBridge.exe`: Standardausgabe von `Build-EXE.bat`
  (Beta); daneben liegen Hash und `release-metadata.json`. `user-builds/stable/`
  ist ausschließlich für den später ausdrücklich bestätigten Stable-Build.
- `release-inbox/beta/` und `release-inbox/stable/`: optionale, lokale
  Sammelordner. Nach eigenem Test kannst du eine Kopie der EXE dort für deine
  manuelle Release-Vorbereitung ablegen. Das ist **kein** Upload-Ort des
  Builders; die Dateien bleiben lokal und werden nicht committet.
- `channels/beta.json` und `channels/stable.json`: spätere Download-Manifeste,
  momentan beide deaktiviert. Erst nach einem echten GitHub-Release und deiner
  Freigabe werden URL, Größe und SHA-256 des tatsächlich veröffentlichten
  Artefakts eingetragen und der betreffende Kanal aktiviert.
- `updater/Update-Bridge.ps1`: eigenständiger zukünftiger Updater. Er ist noch
  nicht in die Bridge-EXE eingebunden und wird beim Bauen nicht ausgeführt.

Der Build ist **kein** Upload: Er veröffentlicht nichts, ändert keine
Channel-Datei und startet nicht automatisch den Updater.

Direkter Aufruf des PowerShell-Builders, falls ein Beta-Suffix gesetzt werden
soll. Der dreiteilige Versionskern muss mit `version.json` übereinstimmen;
Beta-Versionen können danach ein Suffix wie `-beta.2` tragen:

```powershell
.\Build-EXE.ps1 -Channel beta -BuildVersion 7.6.3-beta.2
```

Der Build ist **kein** Upload: Er veröffentlicht nichts, ändert keine
Channel-Datei und startet nicht automatisch den Updater.

## Beta vor Stable

Die Channel-Dateien `channels/beta.json` und `channels/stable.json` sind beide
absichtlich `enabled: false`. Damit ist noch kein Release verfügbar. Das
Manifest-Schema liegt daneben in `channels/manifest.schema.json`.

Vorgesehene Reihenfolge:

1. Der Nutzer baut selbst eine Beta-EXE und testet sie zunächst lokal.
2. Erst nach seiner Freigabe wird ein Beta-Artefakt über einen GitHub-Release
   bereitgestellt. Version, Download-URL, Dateigröße und SHA-256 werden aus
   dem geprüften Artefakt in `channels/beta.json` übernommen; erst dann wird
   `enabled` manuell auf `true` gesetzt.
3. Beta-Probleme werden behoben und erneut als Beta getestet. Stable bleibt
   deaktiviert.
4. Nach erfolgreichem Beta-Test und ausdrücklicher Freigabe erhält Stable
   einen eigenen Release-Stand und eine eigene Datei in `channels/stable.json`.
   Stable-Manifeste dürfen keine Prerelease-Version verwenden.

Es gibt weder einen automatischen Upload noch ein automatisches Umschalten von
Beta auf Stable. `release-inbox/` dient nur als lokaler Ablageplatz; seine
Inhalte werden nicht committet.

## Sicherer Austausch der laufenden EXE — vorbereitet, nicht integriert

`updater/Update-Bridge.ps1` ist ein eigenständiger Windows-Updater für die
spätere Integration. Er ist noch nicht in `ArenaBridge.ps1` eingebunden und
wird nicht durch `Build-EXE.bat` gestartet.

Der vorbereitete Ablauf:

- liest nur den angeforderten Kanal und verweigert deaktivierte oder
  widersprüchliche Manifeste;
- verlangt HTTPS auf GitHub/GitHubusercontent ohne eingebettete Zugangsdaten
  oder abweichenden Port und prüft auch jedes Redirect-Ziel erneut;
- begrenzt Channel-Manifeste auf 1 MiB und streamt EXE-Downloads mit fester
  Größen- und Zeitgrenze, bevor Größe und SHA-256 weiter geprüft werden;
- verlangt die exakte Datei `ArenaBridge.exe` und einen SHA-256-Wert;
- vergleicht Versionsstände, verweigert Downgrades und bricht bei ungültigem
  lokalem Update-Status ab, statt die Versionsprüfung zu überspringen;
- wartet auf die beendete Ziel-EXE, **beendet sie aber niemals selbst**;
- lädt zuerst in ein Staging-Verzeichnis auf demselben Laufwerk herunter und
  verifiziert Größe und Hash, bevor die Installation angefasst wird;
- ersetzt die EXE mit `File.Replace`, behält die vorige Datei als Backup und
  versucht bei einem Ersetzungsfehler einen Rollback;
- schreibt den installierten Kanal/Versionsstand erst nach erfolgreicher
  Ersetzung.

Beispiel für einen späteren Beta-Aufruf (erst nach dem geplanten Updater-Handoff
und dem Veröffentlichen eines gültigen Manifests):

```powershell
.\updater\Update-Bridge.ps1 `
  -Channel beta `
  -ManifestUrl 'https://raw.githubusercontent.com/OWNER/REPO/BRANCH/channels/beta.json' `
  -InstallDirectory "$env:LOCALAPPDATA\ArenaRobloxBridge\app" `
  -WaitForProcessId 1234 `
  -StartAfterUpdate
```

Die Beispielwerte `OWNER`, `REPO`, `BRANCH` und PID müssen später mit echten
Werten ersetzt werden. Vor einem Live-Rollout sind der Updater und der
GitHub-Release-Ablauf auf einem Windows-Testkonto abzunehmen. Die aktuelle
Session legt das Fundament, verknüpft es aber absichtlich noch nicht mit dem
alten Updater.

## Tests und Grenzen

Die Offline-Regressions- und Strukturtests sind eigenständige Skripte (keine
`unittest`-TestCase-Klassen). Im Ordner `next-update/` zuerst die Test-Extras
installieren und dann den Runner starten:

```powershell
python -m pip install -r requirements-test.txt
python run_offline_tests.py
```

Der Runner führt alle `test_*.py`-Skripte nacheinander aus und liefert einen
Fehlerstatus zurück, sobald ein Test fehlschlägt. `parse-gate.ps1` sowie
`test_v762_runtime.ps1` benötigen zusätzlich Windows PowerShell; letzterer ist
ein isolierter Open-Cloud-Laufzeittest ohne Live-Netzwerk. Ein erfolgreicher
Offline-Test belegt weder eine echte Roblox-Studio-Abnahme noch eine
Windows-EXE-Kompilierung.
