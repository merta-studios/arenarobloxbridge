# Updater 1.1.0 (Update-Bridge.ps1)

Der Helfer wird vom Builder in `ArenaBridge.exe` eingebettet (Base64 mit fester SHA-256,
geprüft vor dem Schreiben nach `%LOCALAPPDATA%\ArenaRobloxBridge\updater\`). Er ist reines
ASCII, damit Windows PowerShell 5.1 ihn unabhängig von der Codierung liest.

## Modi

- `check`: lädt das Kanal-Manifest und schreibt ein JSON-Ergebnis. Verändert keine Datei.
  Status: `update-available`, `up-to-date`, `disabled`, `downgrade-refused`, `version-conflict`, `error`.
- `install`: wartet auf das **reguläre** Beenden der laufenden EXE, lädt in Staging, prüft,
  ersetzt atomar mit Backup, schreibt den Zustand und startet die neue EXE mit
  `-UpdateStatus update-erfolgreich`.

## Sicherheitsverhalten

- **Keine Prozessbeendigung.** Der Helfer wartet nur. Läuft noch eine Instanz am Zielpfad,
  bricht er ohne jede Dateiänderung ab. Ein Prozess, dessen Pfad nicht lesbar ist, zählt als laufend.
- **Feste Quellen.** Das Manifest wird aus dem Kanal aufgebaut, nicht aus einer Nutzer-URL.
  Produktiv sind nur HTTPS-Downloads auf Standardport, Start über `raw.githubusercontent.com`
  und Weiterleitungen nur auf `objects.githubusercontent.com` und `release-assets.githubusercontent.com`,
  höchstens drei. Keine automatischen Weiterleitungen des Frameworks. Keine Zugangsdaten.
- **Limits.** Manifest höchstens 1 MiB. Artefakt 1 KiB bis 64 MiB. Deklarierte und gestreamte
  Größe müssen zum Manifest passen. Zeitlimit 180 s.
- **Prüfungen vor dem Ersetzen.** Größe, SHA-256 (muss exakt zum Manifest passen), Windows-x64-PE
  (MZ-Kopf, PE-Signatur, Maschine 0x8664).
- **Downgrade-Schutz.** Verglichen wird mit dem höheren Wert aus `update-state.json` und der
  Dateiversion der installierten EXE.
- **Rollback.** Schlägt das Ersetzen fehl, bleibt die alte EXE. Startet die neue EXE nicht
  (Exit ungleich 0 innerhalb von 5 s), wird die Sicherung zurückgeholt und die alte EXE mit
  `update-fehler` gestartet. Fehlerhafte Dateien landen in `.arena-update\rejected\`.
- **Aufbewahrung.** Die letzten drei Sicherungen und abgelehnten Dateien bleiben erhalten.
- **Sperre.** `.arena-update\update.lock`. Eine veraltete Sperre wird nur entfernt, wenn kein Handle offen ist.

## Dateien

- Installationsordner: `ArenaBridge.exe`, `update-state.json`, `update-status.json`.
- Arbeitsordner: `.arena-update\staging\`, `.arena-update\backup\`, `.arena-update\rejected\`, `.arena-update\update.lock`.
- Log: `%LOCALAPPDATA%\ArenaRobloxBridge\bin\update-helper.log` (oder `-LogPath`).

## Test-Modus (nie in normalen Builds)

`-TestFixtureMode` und `-ManifestPath` sind nur mit einem Testbau aktiv. Ein Test-Manifest muss
`testFixture: true` haben und darf nur auf `http://127.0.0.1:<Port>` zeigen (Port ab 1024).
`-TestFault after-replace` erzwingt einen Fehler nach dem Ersetzen, um den Rollback zu prüfen.

## Stand

Version 1.1.0 ist geschrieben, parst mit dem Tree-sitter-PowerShell-Parser ohne Fehler und ist
ASCII-only. Ausgeführt wurde sie auf Windows **noch nicht**. Die Testfälle stehen in
`developer/tests/Invoke-SelfUpdateSmoke.ps1`. Bis dahin ist der Updater nicht freigegeben.
