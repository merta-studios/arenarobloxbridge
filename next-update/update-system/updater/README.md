# Eigenständiger Beta-/Stable-Updater (Vorbereitung)

`Update-Bridge.ps1` ist die zukünftige Updater-Komponente. Sie ist **noch nicht
in `app/ArenaBridge.ps1` oder in die laufende Root-Bridge eingebunden**. Sie
wird weder durch `Build-EXE.bat` noch beim Start einer aktuell gebauten Beta
aufgerufen. Bitte dieses Skript nicht als normalen App-Start verwenden.

## Sicherheitsverhalten

- Windows-only; Kanal muss explizit `beta` oder `stable` sein.
- Channel-Manifest und Artefakt werden nur über genehmigte HTTPS-GitHub-Hosts
  geladen; Credentials, Fremdports und nicht genehmigte Redirects werden
  abgelehnt.
- Größe, Versionsformat, Kanal, Mindest-Updater-Version und SHA-256 werden
  geprüft. Deaktivierte Manifeste laden nichts.
- Lokaler Update-Status wird validiert. Downgrades und ein ungültiger Status
  führen zu einem Abbruch statt zu einer ungeprüften Neuinstallation.
- Die laufende EXE wird niemals beendet. Der Updater wartet auf ein Ende,
  lädt und prüft erst im Staging-Ordner und ersetzt danach atomar mit Backup
  und Rollback-Versuch.

## Voraussetzungen für eine spätere Verwendung

Vor einer Integration müssen zuerst die Bridge-EXE und der neue Ablauf auf
einem Windows-Testkonto abgenommen werden. Danach benötigt ein freigegebener
GitHub-Release ein gültiges Channel-Manifest mit der echten Release-URL,
Dateigröße und SHA-256 des **normalen** `ArenaBridge.exe`-Artefakts. Die
Diagnose-EXE darf nicht als Update-Artefakt veröffentlicht werden.

Die Manifeste liegen unter `update-system/channels/`. Sie bleiben deaktiviert,
bis Integration und Tests ausdrücklich freigegeben werden. Überblick und
Sicherheitsgrenzen: [`../README.md`](../README.md).
