# Update-System (next-update, Stand 7.7.0)

Dieser Ordner enthält das **neue** Selbst-Update-System. Er ist der einzige
Ort für Updates dieses Ablaufs. Das alte System im Repository-Hauptordner wird
weder verwendet noch verändert.

**Status (ehrlich):**

- Der Updater `updater/Update-Bridge.ps1` (Version 1.1.0) ist in `app/ArenaBridge.ps1`
  integriert und wird vom Builder in die EXE eingebettet. Die EXE braucht keine
  separate Updater-Datei.
- Auf Windows wurde davon noch **nichts** ausgeführt (die Entwicklungssandbox hat kein
  PowerShell). Parse-Gate, EXE-Build, Smoke-Test und Selbst-Update-Test sind offen,
  bis sie auf einem Windows-PC gelaufen sind.
- `channels/beta.json` und `channels/stable.json` sind **deaktiviert** (`enabled: false`).
  Es gibt keine Veröffentlichung und keinen Nutzer des neuen Systems.
- Bereits installierte Kopien ohne Updater erhalten dieses System **nicht** automatisch.
  Eine einmalige manuelle Migration ist offen und wird in der Release-Session entschieden.

## Bestandteile

| Datei | Zweck |
|---|---|
| `updater/Update-Bridge.ps1` | Der Helfer: prüft Manifest, lädt in Staging, prüft Größe und SHA-256, ersetzt atomar mit Backup, startet neu oder rollt zurück. |
| `updater/README.md` | Verhalten, Grenzen und Testfälle des Updaters. |
| `channels/manifest.schema.json` | JSON-Schema (Draft 2020-12) für Kanal-Manifeste. Feste Repository-URL, Größenlimit 64 MiB, `testFixture` nur für Tests. |
| `channels/beta.json`, `channels/stable.json` | Kanal-Manifeste. Beide **deaktiviert**. |
| `PROTECTED.md` | Schutzregeln und Verfahren für Änderungen am geschützten Bereich. |
| `update_system_guard.lock.json` | Hashes des geschützten Bereichs und Freigabeprotokoll. |

## Ablauf (Ziel, nach Windows-Tests und Freigabe)

1. Ein Kanal-Manifest verweist auf genau eine Datei: `release/ArenaBridge.exe` im Repository,
   mit Version, Größe und SHA-256.
2. Die Bridge prüft im Hintergrund das Manifest und fragt nur nach Bestätigung.
3. Die Bridge beendet sich regulär. Der Helfer wartet darauf und beendet nie einen Prozess.
4. Download nur über HTTPS auf GitHub-Hosts. Größe und Hash werden geprüft, die alte EXE
   bleibt bei jedem Fehler unverändert.
5. Atomarer Austausch mit Backup, Neustart und Rückrollung bei Startfehler.

Ein Update für Nutzer entsteht erst, wenn der PR gemergt ist, das Manifest aktiviert wurde
und die Release-Session die getestete EXE bereitgestellt hat. Merge, ZIP-Download und
lokaler Build sind **keine** Veröffentlichung.

## Tests

- Offline: `developer/tests/test_v800_update_manifest.py` (Schema, Fixtures, deaktivierte Kanäle)
  und `developer/tests/test_v800_update_system_guard.py` (Schutz des geschützten Bereichs).
- Windows: `developer/tests/Invoke-SelfUpdateSmoke.ps1`, aufgerufen durch
  `test_v800_selfupdate_smoke.py`. Er baut zwei Test-EXEs und prüft Installation, Backup,
  Neustart, Downgrade, falschen Hash, Größe, deaktiviertes/ungültiges Manifest,
  Netzwerkfehler, laufende EXE und Rollback in isolierten Ordnern unter `%TEMP%`.
