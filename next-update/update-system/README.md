# Update-System (next-update, Stand 7.8.0 / Updater 2.0.0)

Dieser Ordner enthält das **neue** Selbst-Update-System. Er ist der einzige Ort
für Updates dieses Ablaufs. Das alte System im Repository-Hauptordner wird weder
verwendet noch verändert. Das vollständige Konzept steht in
`developer/docs/UPDATE-KONZEPT.md`.

## Was sich mit 7.8.0 geändert hat (ehrliche Kurzfassung)

Vorher war das System nicht benutzbar: `channels/stable.json` war aktiviert und
nannte Größe und SHA-256 einer Datei, die es im Repository nicht gab
(`release/ArenaBridge.exe` hatte einen anderen Inhalt als das Manifest). Jeder
Downloadversuch musste bei der Prüfung scheitern – ein Update konnte niemals
installiert werden. Zusätzlich hieß die veröffentlichte Datei immer gleich
(`ArenaBridge.exe`), sodass eine neue Veröffentlichung die alte Datei
überschrieben hätte.

Mit 7.8.0 gilt ein Vertrag, der genau diese Fehler unmöglich macht:

- Jede Veröffentlichung liegt in einer **unveränderlichen** Datei
  `release/ArenaBridge-<Version>.exe`. Dateiname und Adresse werden automatisch
  aus der Version abgeleitet; eine Sammeldatei `ArenaBridge.exe` gibt es als
  Updateziel nicht mehr.
- Der Updater prüft vor dem Ersetzen Größe, SHA-256, PE-Kopf (x64) **und** die
  eingebaute Dateiversion der neuen EXE gegen das Manifest. Ein falsches,
  fremdes oder halb hochgeladenes Artefakt wird abgelehnt, die alte Fassung
  bleibt unverändert.
- Das Manifest trägt eine `sequence`. Eine ältere Folge als der lokale Stand
  (z. B. ein veralteter Cache-Stand auf `raw.githubusercontent.com`) wird nie
  installiert.
- Deaktivierte Kanäle nennen **keine** Download-Koordinaten. Es gibt keinen
  zweiten, heimlichen Auslieferungsweg.
- Ein Update wird nie erzwungen (`mandatory` wird nicht ausgewertet) und das
  System beendet nie einen Prozess. Die Bridge schließt sich selbst; der Helfer
  wartet auf das reguläre Ende.

## Status (Stand 2026-10-11)

- Beide Kanäle sind **deaktiviert** (`enabled: false`). Der Nutzer erhält derzeit **keine**
  Update-Hinweise; das ist der sichere Ruhezustand.
- `updater/Update-Bridge.ps1` ist Version **2.0.0** und wird vom Builder als
  Base64 mit SHA-256 in `ArenaBridge.exe` eingebettet. Die App braucht keine
  separate Updater-Datei.
- Die Windows-Ergebnisse (Build, Start, Selbst-Update-Test) stammen jeweils aus
  der Aussage des Nutzers in der Release-Session. In der Linux-Umgebung können
  sie nicht nachgerechnet werden; hier wurde nichts als "bestanden" erfunden.
- Bereits installierte Kopien **ohne** eingebauten Updater (alles vor 7.8.0)
  bekommen dieses System nicht automatisch. Für sie gibt es das einmalige
  Migrationswerkzeug `../tools/ArenaBridge-Update-Holen.cmd`.
- `raw.githubusercontent.com` kann nach dem Merge bis zu 5 Minuten den alten
  Stand ausliefern. Das ist ungefährlich: Der Updater erkennt es über `sequence`
  bzw. Größe/SHA-256 und bricht ab; beim nächsten Start wird es erneut versucht.

## Letzte veröffentlichte Version

Letzte veröffentlichte Version: keine (7.7.0 wurde am 2026-10-11 zurückgezogen; die Freigabe war fehlerhaft und für Nutzer nicht installierbar)

| Version | Datum (UTC) | Kanal | Sequence | Artefakt |
|---|---|---|---|---|
| 7.7.0 | 2026-10-11 | stable | 1 | **Zurückgezogen** – Manifest nannte 5.842.432 Bytes / SHA-256 `19984c19…ec1690`, im Repository lag aber `release/ArenaBridge.exe` mit 5.835.776 Bytes / SHA-256 `21c9800f…f63f3a5c`. Kein Nutzer hat diese Version installiert. |

Vor 7.7.0 wurde nie ein Kanal-Manifest aktiviert. Die nächste Freigabe muss
höher als 7.7.0 sein und bekommt automatisch die nächste `sequence`
(Neufassung 2026-10-11: Die fehlerhafte Aktivierung vom selben Tag zählt als
Folge 1, die nächste Freigabe ist damit Folge 2).

## Bestandteile

| Datei | Zweck |
|---|---|
| `updater/Update-Bridge.ps1` | Der Helfer (2.0.0): Modi `check`, `install`, `doctor`. Lädt HTTPS von GitHub, prüft Größe/SHA-256/PE/Dateiversion, wartet auf das reguläre Ende der Bridge, ersetzt atomar mit Backup, schreibt Status/Fortschritt/Verlauf, startet neu oder rollt zurück. |
| `updater/README.md` | Verhalten, Grenzen und Testfälle des Updaters. |
| `channels/manifest.schema.json` | JSON-Schema (Draft 2020-12) für Kanal-Manifeste, Version 2. Unbekannte Felder sind verboten. |
| `channels/beta.json`, `channels/stable.json` | Kanal-Manifeste. Beide **deaktiviert**; Aktivierung nur über `developer/tools/release.py stage`. |
| `PROTECTED.md` | Schutzregeln und Verfahren für Änderungen am geschützten Bereich. |
| `update_system_guard.lock.json` | Hashes des geschützten Bereichs und Freigabeprotokoll. |
| `../developer/tools/release.py` | Release-Doctor: `status`, `check`, `stage`, `disable`, `prune`. Prüft und veröffentlicht nur nach ausdrücklicher Nutzerfreigabe. |
| `../developer/tests/Invoke-SelfUpdateSmoke.ps1` | Windows-Test: baut zwei Test-EXEs und prüft in isolierten Ordnern alle Update-Fälle. |
| `../tools/ArenaBridge-Update-Holen.ps1` / `.cmd` | Einmalige Migration für Altinstallationen ohne eingebauten Updater. |

## Wie ein Update beim Nutzer abläuft

1. Beim Start prüft die Bridge im Hintergrund den Kanal (nur wenn der Kanal
   aktiviert ist). Ein Hinweisfenster nennt Version, Größe, Neuerungen und
   Fortschritt; „Später“ und „Diese Version überspringen“ ändern nichts.
2. Nach „Jetzt aktualisieren“ lädt der Helfer die neue EXE in einen
   Staging-Ordner und prüft Größe, SHA-256, x64-Kopf und Dateiversion.
3. Die Bridge schließt sich selbst. Der Helfer wartet nur und beendet nie einen
   Prozess.
4. Die neue EXE wird atomar ersetzt (die alte bleibt als Backup unter
   `.arena-update\backup`), Status, Fortschritt und Verlauf werden geschrieben,
   die neue Version startet mit „Update erfolgreich“ und zeigt die Neuerungen.
5. Schlägt irgendein Schritt fehl, wird die alte Fassung wiederhergestellt; eine
   abgelehnte Datei wird nur unter `.arena-update\rejected` abgelegt.

Ort der Dateien in der Installation: `update-state.json` (installierte Version),
`update-status.json` (letzter Lauf), `update-history.json` (bis zu 12 Einträge),
`.arena-update\update-progress.json` (Fortschritt), `.arena-update\update.log`
(Protokoll). Ein Abbruch ist ohne Prozesseingriff möglich
(`.arena-update\cancel.request`).

## Wie man veröffentlicht (nur Release-Session, ausdrückliche Freigabe nötig)

1. Änderung im Branch, exakter Release-Plan: siehe `developer/docs/RELEASE-ABLAUF.md`.
2. Nutzer baut privat mit `builder/Build-EXE.bat`, startet die EXE und lässt
   `Invoke-SelfUpdateSmoke.ps1` laufen. Erst danach ist eine Freigabe möglich.
3. `python developer/tools/release.py check --require-test-build` (Prüfbericht).
4. `python developer/tools/release.py stage --version <VERSION> --channel stable
   --tested-by-user (--smoke-test-passed|--smoke-test-skipped)` – kopiert die
   getestete EXE nach `release/ArenaBridge-<VERSION>.exe`, schreibt Manifest,
   README-Tabelle und das Guard-Rebaseline. Eine veröffentlichte Datei wird nie
   überschrieben.
5. Merge des Release-PRs. Erst dann liefert `raw.githubusercontent.com` aus.

`--dry-run` zeigt alles ohne zu schreiben. `disable --channel <name>` deaktiviert
einen Kanal sofort wieder; `prune --keep N` räumt alte Artefakte auf, ohne die
letzte(n) zu löschen.

## Tests

- Offline: `developer/tests/run_offline_tests.py`
  - `test_v800_update_manifest.py` – Schema 2, alle Fixtures, Kanalzustand,
    abgeleitete Dateinamen, Freigabe-Gates.
  - `test_v800_update_system_guard.py` – Schutz des geschützten Bereichs
    (Absicht der Regeln, zweite Implementierung der Freigabeprüfung).
  - `test_v800_update_window.py` – prüft die XAML-Oberfläche des
    Update-Hinweisfensters (keine geteilten Fensterressourcen, erwartete Knöpfe).
- Windows: `developer/tests/Invoke-SelfUpdateSmoke.ps1` (Aufruf über
  `test_v800_selfupdate_smoke.py`). Es baut zwei Test-EXEs mit dem echten Builder
  und prüft in isolierten Ordnern unter `%TEMP%`: Installation, Backup, Neustart,
  Downgrade, falscher SHA-256, Größe, deaktiviertes/ungültiges Manifest,
  Netzwerkfehler, laufende EXE, Rollback, falsche Dateiversion, veraltete
  `sequence`, Abbruch, Diagnose und Fortschritt. Er verändert niemals
  `release\` oder die Kanal-Dateien.
