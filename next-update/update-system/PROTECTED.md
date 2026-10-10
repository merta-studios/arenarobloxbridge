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
Kanäle `beta`/`stable` deaktiviert.

## Feste Regeln

1. Keine laufende Bridge wird beendet. Kein `Stop-Process`, kein `taskkill`, kein `.Kill()`.
2. Download nur per HTTPS auf genehmigten GitHub-Hosts, feste Repository-URL,
   keine vom Nutzer wählbare URL, keine Zugangsdaten in URLs, keine automatischen
   Weiterleitungen (eigene Prüfung je Schritt).
3. Der Test-Manifestpfad (`-TestFixtureMode`, `ARENABRIDGE_SELFUPDATE_TEST_MANIFEST`)
   ist nur in einem Testbau (`-TestFixtureBuild`) aktiv. Normale Builds setzen `'0'`.
4. Testbau-Ausgaben gehen NIE nach `release/`.
5. `channels/beta.json` und `channels/stable.json` bleiben in Feature-PRs `enabled: false`.
   Eine Aktivierung braucht eine eigene, ausdrücklich freigegebene Release-Session.
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
