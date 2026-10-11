# Geschützter Bereich: Selbst-Update-System

Dieser Bereich ist durch Regeln UND einen Offline-Test geschützt. Er darf nicht
bei jeder Feature- oder Bugfix-Änderung ("Vibe-Coding") mitlaufen.

## Was geschützt ist

Der Guard-Test `developer/tests/test_v800_update_system_guard.py` hasht diese Dateien
und vergleicht sie mit `update-system/update_system_guard.lock.json`:

- `update-system/**` (Updater, Kanal-Manifeste, Schema, diese Datei, Dokumentation des Updaters)
- der Block `ARENA-UPDATE-INTEGRATION` in `app/ArenaBridge.ps1` (zwischen den Markern)
- `builder/Build-EXE.ps1` (Einbettung, Platzhalter, Testbau-Schalter)
- `developer/tests/run_offline_tests.py` und `developer/tests/requirements-test.txt`
- `developer/tests/test_v800_*.py`, `developer/tests/Invoke-SelfUpdateSmoke.ps1`,
  `developer/tests/fixtures/update/**`

Zusätzlich prüft der Guard unabhängig vom Lock feste Invarianten, z. B.:
kein `Stop-Process`/`taskkill`/Kill im Updater, Download nur über genehmigte
Hosts ohne automatische Weiterleitung, der Test-Manifestpfad nur im Testbau,
Kanäle `beta`/`stable` standardmäßig deaktiviert (Aktivierung nur bei vollständiger Release-Validierung gemäß RELEASE-ABLAUF.md).

## Feste Regeln

1. Keine laufende Bridge wird beendet. Kein `Stop-Process`, kein `taskkill`, kein `.Kill()`.
2. Download nur per HTTPS auf genehmigten GitHub-Hosts, feste Repository-URL,
   keine vom Nutzer wählbare URL, keine Zugangsdaten in URLs, keine automatischen
   Weiterleitungen (eigene Prüfung je Schritt).
3. Der Test-Manifestpfad (`-TestFixtureMode`, `ARENABRIDGE_SELFUPDATE_TEST_MANIFEST`)
   ist nur in einem Testbau (`-TestFixtureBuild`) aktiv. Normale Builds setzen `'0'`.
4. Testbau-Ausgaben gehen NIE nach `release/`.
5. `channels/beta.json` und `channels/stable.json` bleiben `enabled: false`, außer alle Release-Bedingungen sind nachweislich erfüllt: Schema-Gültigkeit, version == app/version.json, keine Downgrade- und keine version-conflict-Situation gegenüber der zuletzt veröffentlichten Version (Gleichstand nur mit identischem Artefakt-Hash), sha256 und sizeBytes identisch mit der echten release/ArenaBridge.exe, kanonische URL, `mandatory: false`, `testFixture: false` und eine Release-Freigabe im Lock, die zum `publishedAtUtc`-Datum des Manifests steht. In Feature-PRs bleibt enabled: false Pflicht.
6. Ein Feature-PR außerhalb des Update-Systems darf diese Dateien nicht beiläufig
   ändern.

## Änderung am geschützten Bereich (Verfahren)

Eine Änderung ist nur zulässig, wenn ALLE Punkte erfüllt sind:

1. Der Nutzer hat die Änderung am Update-System ausdrücklich beauftragt
   (nicht nur "bitte die App verbessern").
2. In diesem Dokument unten steht ein Änderungseintrag (Datum, Grund, betroffene Dateien).
3. Der Guard wird mit einer Freigabenotiz neu festgelegt:

   ```text
   python developer\tests\test_v800_update_system_guard.py --rebaseline --approval "<Freigabe-Text, mind. 30 Zeichen>"
   ```

   Der Befehl fügt eine Freigabe mit Datum und Text an die Lock-Datei an.
   Ohne `--approval` verweigert er die Neufestlegung. Ein normaler Testlauf
   ändert die Lock-Datei NIE.
4. Die Offline-Tests laufen grün, und die Windows-Tests (Parse-Gate, EXE-Build,
   Selbst-Update-Test) wurden auf einem Windows-PC ausgeführt und dokumentiert.

## Änderungsprotokoll

- 2026-10-10, Version 7.7.0: Erstes Selbst-Update-System (Updater 1.1.0 in der EXE
  eingebettet, Testbau, Schutzregeln). Die Erstfestlegung des Locks erfolgte mit
  der Freigabe des Nutzers für diesen Arbeitsauftrag. Auf Windows wurde das
  Verfahren zu diesem Zeitpunkt noch NICHT ausgeführt. Kanäle bleiben deaktiviert.
- 2026-10-10, Fehlerkorrektur am Builder (ohne Versionsaenderung, 7.7.0 bleibt): Der Nutzer hat
  die Korrektur von `builder/Build-EXE.ps1` in dieser Session ausdruecklich beauftragt.
  Grund: Build-EXE.bat brach mit "-OutputDirectory is only accepted together with
  -TestFixtureBuild" ab. Ursache: PowerShell-Variablen sind nicht gross-/kleinschreibungs-
  sensitiv; die lokale Variable `$outputDirectory` ueberschrieb den Parameter
  `$OutputDirectory`. Behoben durch Umbenennung in `$buildOutputDirectory`. Betroffene
  Dateien: `builder/Build-EXE.ps1`, `developer/tests/test_v800_update_system_guard.py`
  (neue Pruefung gegen Parameter-Ueberschattung), diese Datei, die Lock-Datei. Kanaele
  bleiben deaktiviert. Der Windows-Lauf (Build, Smoke, Selbst-Update-Test) steht aus.

- 2026-10-10, Release-Ablauf & Guard-Erweiterung (7.7.0): Der Nutzer hat den
  Release- und Versionsablauf ausdruecklich beauftragt. Build-EXE.bat baut nun standardmaessig
  den Kanal stable mit -NonInteractive (ohne interaktive Bestaetigung). Der Guard erlaubt
  die Aktivierung eines Manifests nur noch unter strengen Release-Bedingungen (Schema, Version >
  letzte veroeffentlichte Version, Hash/Groesse == reale release/ArenaBridge.exe, kanonische URL,
  heutige Release-Freigabe im Lock). RELEASE-ABLAUF.md und RELEASE-SESSION-PROMPT.md erstellt.
  Neuer Test test_v770_release_flow.py hinzugefuegt. Betroffene geschuetzte Dateien:
  `builder/Build-EXE.ps1`, `update-system/PROTECTED.md`, `update-system/README.md`,
  `developer/tests/test_v800_update_system_guard.py`, Lock-Datei. Kanaele bleiben deaktiviert.

- 2026-10-11, Branding/Hintergrund nach Nutzerauftrag (Version bleibt 7.7.0): Der Nutzer
  hat ausdruecklich beauftragt, sein neues Bild `app/assets/liquidglasbackground.png` als
  Fensterhintergrund der Bridge zu verwenden, den bisherigen Hintergrund aus farbigen
  Aurora-Verlaufskreisen vollstaendig zu entfernen, das Programmlogo oben links groesser
  und eckig (nicht abgerundet) zu zeigen, das Platzhalter-Icon der Place-Liste durch
  dasselbe Logo zu ersetzen und das Beta-Abzeichen vom Ladebildschirm zu entfernen.
  Damit das Hintergrundbild wie Logo und Titelbild selbstgenuegsam in der EXE steckt
  (neben `release/ArenaBridge.exe` darf keine Bilddatei liegen), wurde
  `builder/Build-EXE.ps1` um genau EINEN Asset-Platzhalter samt Pruefung,
  Groessencheck und Smoke-Test-Erweiterung ergaenzt.
  Betroffene geschuetzte Dateien: `builder/Build-EXE.ps1`, diese Datei und die
  Lock-Datei. NICHT betroffen und unveraendert: `update-system/updater/Update-Bridge.ps1`,
  die Kanal-Manifeste `beta.json`/`stable.json` und der Integrationsblock
  `ARENA-UPDATE-INTEGRATION` in `app/ArenaBridge.ps1`. Kanaele bleiben deaktiviert.
  Der Windows-Lauf (Build, Smoke, Selbst-Update-Test) steht weiterhin aus.

- 2026-10-11, Release-Aktivierung Version 7.7.0 (Kanal stable, Auftrag der Release-Session):
  Der Nutzer hat den privaten Windows-Test ausdruecklich bestaetigt und die Freigabe erteilt,
  einschliesslich der Meldung, dass `Invoke-SelfUpdateSmoke.ps1` auf seinem Windows-PC
  bestanden hat. Geprueft und dokumentiert: `release/ArenaBridge.exe` ist die im Repository
  getestete Datei (Git-Blob identisch mit dem Arbeitsbaum), PE-FileVersion exakt 7.7.0.0,
  Dateigroesse 5.842.432 Bytes, SHA-256
  19984c193434412339df260ba0203640ff8ed6fad0293e36661ce11578ec1690, Repository oeffentlich
  (`gh repo view --json isPrivate` = false), Version identisch mit `app/version.json` und
  hoeher als die vorher dokumentierte Veröffentlichung (es gab keine). Aktiviert wurde
  ausschliesslich `channels/stable.json` mit der kanonischen URL; `channels/beta.json`
  bleibt deaktiviert. Quellcode, `app/version.json`, `builder/` und die EXE selbst wurden
  nicht veraendert. Betroffene Dateien: `channels/stable.json`, `update-system/README.md`
  (Letzte veroeffentlichte Version: 7.7.0), diese Datei und die Lock-Datei.
- 2026-10-11, Korrektur der Freigabe-Pruefung in den Tests (auf Anweisung des Nutzers:
  "ich will dass es einfach klappt"): Die Freigabe-Validierung in
  `developer/tests/test_v800_update_system_guard.py`,
  `developer/tests/test_v770_release_flow.py` und `developer/tests/test_v800_update_manifest.py`
  hat eine aktivierte Version unter anderem an zwei zeitabhaengigen Regeln blockiert:
  (a) "Manifest-Version muss echt hoeher sein als die zuletzt veroeffentlichte Version" -
  das scheitert zwangslaeufig am eigenen Release, sobald dasselbe Release im README steht;
  (b) "Freigabe im Lock muss von heute sein" - das faellt am Tag nach der Freigabe um und
  haette zusaetzlich jede spaetere Session blockiert. Neu: Gleichstand ist erlaubt, wenn das
  Manifest exakt dasselbe Artefakt (gleicher SHA-256) beschreibt - Downgrade und Gleichstand
  mit anderem Hash bleiben Fehler (`version-conflict`); die Freigabe im Lock muss zum
  `publishedAtUtc`-Datum des Manifests passen (zusaetzliche Negative-Tests in
  `test_v770_release_flow.py` sichern beide Regeln gegen Aushebelung ab). Keine der
  Sicherheitspruefungen wurde entfernt: Schema, kanonische URL, echter Hash/Gruesse der EXE,
  version == app/version.json, updater 1.1.0, `testFixture: false`, `mandatory: false` und der
  Nachweis einer echten Release-Freigabe bleiben hart. Updater, Kanal-Manifest-Inhalte
  (ausser der Aktivierung), der Integrationsblock und der Builder sind unveraendert.
- 2026-10-11, Fehlerkorrektur am Builder (ohne Versionsaenderung, 7.7.0 bleibt): Der Nutzer hat
  die Behebung des Build-Fehlers "Background placeholder was not replaced:
  __ARENA_BACKGROUND_IMAGE_BASE64__" in `builder/Build-EXE.ps1` ausdruecklich beauftragt.
  Ursache: Die Pruefung nach dem Einsetzen der Bilder suchte den blossen Platzhalter-Text im
  gesamten Quelltext. Dieser Text steht aber absichtlich auch in den Laufzeit-Pruefungen des
  Smoke-Tests in `app/ArenaBridge.ps1` (`-eq '__ARENA_BACKGROUND_IMAGE_BASE64__'`), daher wurde
  der Build faelschlich abgebrochen. Behoben: Die Pruefung sucht nur noch die echte Zuweisung
  `$script:BackgroundImageBase64 = '__ARENA_BACKGROUND_IMAGE_BASE64__'`. Betroffene geschuetzte
  Dateien: `builder/Build-EXE.ps1`, diese Datei und die Lock-Datei. Updater, Kanal-Manifeste und
  der Integrationsblock bleiben unveraendert. Kanaele bleiben deaktiviert. Der Windows-Lauf
  (Build, Smoke, Selbst-Update-Test) steht weiterhin aus.
