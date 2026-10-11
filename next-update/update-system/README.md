# Update-System (next-update, Stand 7.7.0)

Dieser Ordner enthält das **neue** Selbst-Update-System. Er ist der einzige
Ort für Updates dieses Ablaufs. Das alte System im Repository-Hauptordner wird
weder verwendet noch verändert.

**Status (ehrlich):**

- Der Updater `updater/Update-Bridge.ps1` (Version 1.1.0) ist in `app/ArenaBridge.ps1`
  integriert und wird vom Builder in die EXE eingebettet. Die EXE braucht keine
  separate Updater-Datei.
- `channels/stable.json` ist **aktiviert** (`enabled: true`) und verweist auf genau die
  EXE, die der Nutzer privat auf Windows gebaut, gestartet und getestet hat
  (`release/ArenaBridge.exe`, Version 7.7.0, PE-FileVersion 7.7.0.0).
- Die Windows-Ergebnisse stammen aus der Aussage des Nutzers in der Release-Session
  (EXE-Build über `Build-EXE.bat`, Start der EXE, `Invoke-SelfUpdateSmoke.ps1` bestanden).
  In der Linux-Sandbox können sie nicht nachgerechnet werden; hier wurde nichts als
  "bestanden" erfunden.
- `channels/beta.json` bleibt **deaktiviert** (`enabled: false`). Es gibt keinen zweiten,
  heimlichen Auslieferungsweg.
- Nach dem Merge des Release-PRs erhält jede EXE mit eingebautem Updater und Kanal
  `stable` beim Start einen freiwilligen Ja/Nein-Hinweis. Ein Update wird nie erzwungen
  (`mandatory: false` wird vom Updater nicht ausgewertet).
- Bereits installierte Kopien ohne Updater erhalten dieses System **nicht** automatisch.
  Für sie bleibt der einmalige manuelle Austausch noetig; eine automatische Migration
  gibt es in 7.7.0 nicht.
- `raw.githubusercontent.com` kann nach dem Merge einige Minuten den alten Stand ausliefern.
  Das ist sicher: Der Updater vergleicht vor dem Ersetzen zwingend Größe und SHA-256 und
  bricht ohne Änderung ab, wenn etwas nicht passt (neuer Versuch beim nächsten Start).

## Letzte veröffentlichte Version

Letzte veröffentlichte Version: 7.7.0 (freigegeben am 2026-10-11, Kanal stable)

| Version | Datum (UTC) | Kanal | Artefakt |
|---|---|---|---|
| 7.7.0 | 2026-10-11 | stable | `release/ArenaBridge.exe`, 5.842.432 Bytes, SHA-256 `19984c193434412339df260ba0203640ff8ed6fad0293e36661ce11578ec1690` |

Vor 7.7.0 wurde nie ein Kanal-Manifest aktiviert, es gibt also keine ältere
veröffentlichte Version dieses Systems. Die nächste Freigabe muss eine höhere Version als
7.7.0 tragen; Gleichstand mit anderem Hash oder ein Downgrade ist ein Fehler
(`version-conflict`) und blockiert die Aktivierung.

## Bestandteile

| Datei | Zweck |
|---|---|
| `updater/Update-Bridge.ps1` | Der Helfer: prüft Manifest, lädt in Staging, prüft Größe und SHA-256, ersetzt atomar mit Backup, startet neu oder rollt zurück. |
| `updater/README.md` | Verhalten, Grenzen und Testfälle des Updaters. |
| `channels/manifest.schema.json` | JSON-Schema (Draft 2020-12) für Kanal-Manifeste. Feste Repository-URL, Größenlimit 64 MiB, `testFixture` nur für Tests. |
| `channels/beta.json`, `channels/stable.json` | Kanal-Manifeste. `stable` aktiviert (7.7.0), `beta` deaktiviert. |
| `PROTECTED.md` | Schutzregeln und Verfahren für Änderungen am geschützten Bereich. |
| `update_system_guard.lock.json` | Hashes des geschützten Bereichs und Freigabeprotokoll. |

## Ablauf (mit 7.7.0 in Kraft)

1. Ein Kanal-Manifest verweist auf genau eine Datei: `release/ArenaBridge.exe` im Repository,
   mit Version, Größe und SHA-256.
2. Die Bridge prüft im Hintergrund das Manifest und fragt nur nach Bestätigung.
3. Die Bridge beendet sich regulär. Der Helfer wartet darauf und beendet nie einen Prozess.
4. Download nur über HTTPS auf GitHub-Hosts. Größe und Hash werden geprüft, die alte EXE
   bleibt bei jedem Fehler unverändert.
5. Atomarer Austausch mit Backup, Neustart und Rückrollung bei Startfehler.

Ein Update für Nutzer entsteht erst, wenn der Release-PR gemergt ist, das Manifest
aktiviert wurde und die getestete EXE genau unter `release/ArenaBridge.exe` im
Repository liegt. Merge, ZIP-Download und lokaler Build sind für sich allein **keine**
Veröffentlichung; erst dieser Merge liefert aus.

## Tests

- Offline: `developer/tests/test_v800_update_manifest.py` (Schema, Fixtures, Kanalzustand:
  deaktivierte Kanäle ohne Artefakt-Koordinaten, aktivierte Kanäle nur bei erfüllten
  Release-Gates)
  und `developer/tests/test_v800_update_system_guard.py` (Schutz des geschützten Bereichs).
- Windows: `developer/tests/Invoke-SelfUpdateSmoke.ps1`, aufgerufen durch
  `test_v800_selfupdate_smoke.py`. Er baut zwei Test-EXEs und prüft Installation, Backup,
  Neustart, Downgrade, falschen Hash, Größe, deaktiviertes/ungültiges Manifest,
  Netzwerkfehler, laufende EXE und Rollback in isolierten Ordnern unter `%TEMP%`.
