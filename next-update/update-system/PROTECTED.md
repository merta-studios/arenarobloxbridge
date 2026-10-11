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

- 2026-10-11, Knoepfe "Update-Diagnose" und "Protokoll" aus den Einstellungen entfernt
  (Version bleibt 7.8.0): Der Nutzer hat in dieser Session ausdruecklich nur das Entfernen
  dieser beiden Knoepfe im Bereich UPDATES des Einstellungsfensters beauftragt
  ("entferne den update diagnose und protokoll button in den einstellungen. mehr nicht").
  Entfernt wurden genau diese zwei Knoepfe und ihre Verdrahtung in Open-SettingsWindow.
  Unveraendert bleiben: der Knopf "Jetzt nach Updates suchen" samt Ergebnisfeld, der
  Update-Block ARENA-UPDATE-INTEGRATION, die Funktionen Show-ArenaUpdateDiagnose und
  Open-ArenaUpdateLog (das Update-Fenster nutzt das Protokoll weiterhin), der Updater,
  die Kanal-Manifeste (weiterhin deaktiviert) und alle Sicherheitspruefungen. Die beiden
  v800-Tests wurden auf den neuen Stand gezogen: der Updates-Bereich hat genau EINEN Knopf,
  und fuer Diagnose/Protokoll darf es dort keine Verdrahtung mehr geben. Betroffene
  geschuetzte Dateien: `app/ArenaBridge.ps1` (Bloecke ARENA-UPDATE-SETTINGS-UI und
  ARENA-UPDATE-SETTINGS-CODE), `developer/tests/test_v800_update_system_guard.py`,
  `developer/tests/test_v800_update_window.py`, diese Datei und die Lock-Datei.
  Bewusst NICHT mitgeaendert (Auftrag "mehr nicht"): die sichtbaren Versionshinweise in
  `app/version.json` und der Kopfkommentar der App nennen die beiden Knoepfe weiterhin.
  Der Windows-Lauf (Build, EXE-Smoke-Test, Invoke-SelfUpdateSmoke.ps1) steht aus und wird
  hier nicht behauptet; die Offline-Tests laufen gruen.

- 2026-10-11, Release-Aktivierung Version 7.8.0 (Kanal stable, Auftrag der Release-Session):
  Der Nutzer hat den privaten Windows-Test ausdruecklich bestaetigt und die Freigabe erteilt,
  einschliesslich der Meldung, dass `Invoke-SelfUpdateSmoke.ps1` auf seinem Windows-PC fuer
  diesen Build bestanden hat. Geprueft und dokumentiert: `release/ArenaBridge.exe` ist die im
  Repository liegende, vom Nutzer getestete Datei (git-Status fuer diese Datei: unveraendert),
  PE-Machine 0x8664 (Windows x64), PE-FileVersion exakt 7.8.0.0, Dateigroesse 5.897.728 Bytes,
  SHA-256 4026cff81a681d4e200503c5a072a720e598963f69ac4d252b98397b45067a7d, Repository
  oeffentlich (`gh repo view --json isPrivate` = false), Version identisch mit
  `app/version.json` und hoeher als die letzte Veroeffentlichung (7.7.0 wurde zurueckgezogen;
  die naechste sequence ist daher 2). Aktiviert wurde ausschliesslich `channels/stable.json`
  mit der kanonischen URL und `sequence` 2; `channels/beta.json` bleibt deaktiviert. Das
  Artefakt liegt unveraenderlich unter `release/ArenaBridge-7.8.0.exe` und wird nie
  ueberschrieben. Quellcode, `app/version.json`, `builder/` und die EXE selbst wurden nicht
  veraendert; es wurde nichts nachgebaut und kein Manifest von Hand geschrieben - Aktivierung,
  README-Tabelle und Rebaseline liefen ausschliesslich ueber `developer/tools/release.py
  stage --version 7.8.0 --channel stable --tested-by-user --smoke-test-passed`. Betroffene
  Dateien: `channels/stable.json`, `update-system/README.md` (Letzte veroeffentlichte
  Version: 7.8.0), `release/ArenaBridge-7.8.0.exe`, diese Datei und die Lock-Datei.
  Nicht in dieser Linux-Umgebung nachpruefbar (nur vom Nutzer auf Windows bestaetigt):
  der echte Build, der Start der EXE, das WPF-Update-Fenster und der Rauchtest.

- 2026-10-11, Wiederherstellung der Gleichstand-Regel in den drei Release-Gates
  (Version bleibt 7.8.0; Auftrag der Release-Session nach Rueckfrage - der Nutzer hat die
  Entscheidung ausdruecklich an die Session uebertragen, mit dem Ziel "am Ende sehen dass
  es klappt"): Ursache war ein echter Befund direkt nach dem Veroeffentlichen. Alle drei
  Gates (`test_v770_release_flow.py`, `test_v800_update_manifest.py`,
  `test_v800_update_system_guard.py`) lesen die Zeile "Letzte veröffentlichte Version" aus
  `update-system/README.md`. Genau diese Zeile schreibt `release.py stage` beim
  Veroeffentlichen auf die neue Version, wodurch das Manifest anschliessend auf Gleichstand
  mit der letzten Veroeffentlichung steht und pauschal als Fehler galt - das Release fiel
  auf sich selbst herein. Die Regel war fuer Release 7.7.0 (PR #89) bereits genau so
  eingebaut und wurde beim Neuschreiben der Tests in PR #92 versehentlich entfernt.
  Wiederhergestellt wird nur der hier und in RELEASE-ABLAUF.md Regel 4 dokumentierte
  Stand: Gleichstand ist ausschliesslich mit genau demselben Artefakt erlaubt (gleicher
  SHA-256 der echten Datei in `release/`); ein anderer Hash bleibt `version-conflict`, ein
  Downgrade bleibt ein Fehler. Neu ist ein Negativtest im Guard, der genau dieses
  Aushebeln (gleiche Version, fremder Hash) abfaengt. Nicht geaendert wurden
  `update-system/updater/Update-Bridge.ps1`, die Kanal-Schemas, der Integrationsblock
  `ARENA-UPDATE-INTEGRATION` in `app/ArenaBridge.ps1`, `builder/Build-EXE.ps1` und
  `developer/tools/release.py`. Betroffene geschuetzte Dateien: die drei Testdateien,
  diese Datei und die Lock-Datei.

- 2026-10-11, Komplettueberarbeitung des Update-Systems auf Updater 3.0.0 (App-Version bleibt
  7.8.0; eine neue Version braucht ein eigenes Release ueber release.py):
  Der Nutzer hat die Ueberarbeitung des Update-Systems ausdruecklich beauftragt. Anlass sind
  drei gemeldete Fehler aus dem Betrieb von 7.8.0: (1) "neue Version 7.8.0 / alte Version 7.8.0"
  bei gleicher Versionsnummer, (2) Fortschrittsanzeige bleibt stehen und die Installation
  haengt nach "Warte auf das regulaere Beenden", (3) Bedienbarkeit der Bridge waehrend der
  Pruefung. Gewuenscht war: kein "Spaeter", kein "Diese Version ueberspringen", kein Abbruch,
  keine Update-Suche in den Einstellungen, automatische Pruefung bei jedem Programmstart,
  Bridge waehrend des Updates nicht bedienbar, Installation zwingend.
  Geaenderte geschuetzte Dateien und Inhalte:
  - `update-system/updater/Update-Bridge.ps1` (3.0.0): gleiche Version = up-to-date; nur
    hoehere Version wird installiert (zusaetzlicher Schutz im Helfer); Fortschritt wird direkt
    geschrieben (kein File.Replace mehr, Schreibfehler werden protokolliert); RunId je Lauf;
    keine Abbruchdatei; Wartezeit auf das Ende der Bridge 60 s statt 180 s.
  - `app/ArenaBridge.ps1`, Block ARENA-UPDATE-INTEGRATION: ersetzt durch das Pflicht-Gate
    (modales Fenster ohne Schliessen-Knopf, vor Studio/Plugin/Server/Tunnel; die Bridge beendet
    sich selbst nach geprueftem Download; Neustart mit "Update erfolgreich").
  - `app/ArenaBridge.ps1`, Einstellungsfenster: Updates-Bereich (Ueberschrift, Knopf "Jetzt nach
    Updates suchen", Ergebnisfeld, Verdrahtung und die Update-Info) komplett entfernt.
    Die Markierungen ARENA-UPDATE-SETTINGS-UI und -CODE entfallen damit.
  - `developer/tools/release.py`: Fallback zum Lesen der Dateiversion ohne `pefile` (UTF-16-Suche
    war fehlerhaft und las nur 4 MB); die Datei wird jetzt vollstaendig gelesen.
  - `developer/tests/requirements-test.txt`: `pefile` als Testabhaengigkeit.
  - Tests: `test_v800_update_window.py` (Pflicht-Fenster statt Hinweisfenster),
    `test_v800_update_system_guard.py` (neue Invarianten), `test_v765_release_workflow.py`
    (neue Namen), `Invoke-SelfUpdateSmoke.ps1` (S13 ohne Abbruch, S16 gleiche Version, S17
    Fortschritt aus frueherem Lauf).
  - `update-system/README.md`: Ursachen, neuer Ablauf, korrigierter Kanalstatus (stable aktiv,
    beta deaktiviert; der Satz "beide Kanaele deaktiviert" war falsch).
  Unveraendert: Kanal-Manifeste (stable bleibt freigegeben mit 7.8.0), Builder, Release-Artefakte
  in release/, Sicherheitsregeln (kein Prozessabbruch, HTTPS-Hosts, Testmodus nur im Testbau).
  Bekannte Grenzen: (a) Die alte 7.8.0-EXE mit Updater 2.0.0 traegt den Fehler weiter; sie muss
  einmal manuell durch die Fassung mit Updater 3.0.0 ersetzt werden. (b) Ein Task-Manager-Kill
  ist technisch nicht verhindern. (c) Der Windows-Lauf (Build, Start, Invoke-SelfUpdateSmoke.ps1)
  ist in der Linux-Umgebung NICHT ausgefuehrt worden und steht aus. PowerShell-Verhalten ist nur
  durch den Tree-sitter-Parser und die Quelltext-Pruefungen belegt.
