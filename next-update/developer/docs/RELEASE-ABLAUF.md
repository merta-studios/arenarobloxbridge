# Release-Ablauf (next-update, Version 7.9.4)

Kurzfassung: Siehe `next-update/README.md`. Hier die Details für Entwicklung und Prüfung.

## Phasen

1. **Änderungs-Session:** Code, Tests und Doku in `next-update/` ändern. Version in
   `app/version.json` erhöhen, wenn die EXE veröffentlicht werden soll, und die
   Nutzer-Notiz als kurze Stichpunkte schreiben (Stichpunkt-Regel in
   `docs/GANZ WICHTIG LESEN VOR JEDER BEARBEITUNG`). Tests laufen lassen:
   `python developer/tests/run_offline_tests.py`. Dann "mach Pull Request".
2. **Merge und Build:** Der Nutzer mergt den PR, lädt das ZIP, startet `Build-EXE.bat`.
   Ergebnis: genau eine Datei, `release/ArenaRobloxBridge.exe` (lokal). Alte
   Diagnose-Dateien und Sicherungskopien entfernt der Builder dabei selbst.
3. **Privater Test:** Der Nutzer testet die EXE auf seinem Windows-PC (Checkliste in
   `UPDATE-SYSTEM.md`, Abschnitt "Tests").
4. **Veröffentlichung:** Nur bei gutem Stand die getestete `ArenaRobloxBridge.exe` nach
   `next-update/release/ArenaRobloxBridge.exe` hochladen und auf `main` speichern. Der Workflow
   erzeugt `latest.json` automatisch. Niemand schreibt `latest.json` von Hand.

## Release-Kandidat vs. Release-EXE

- `next-update/beta-release/ArenaRobloxBridge.exe` wird von `exe-builder.yml`
  automatisch mit **`-Channel rc`** gebaut, sobald sich `app/` oder `builder/`
  auf `main` ändert. Der Kandidat trägt **exakt** die Version aus
  `app/version.json` (z. B. `8.0.5`, kein `-beta.1`) und die Dateiversion
  `<Version>.0`. Er ist damit 1:1 die spätere Release-Datei.
- Der Workflow prüft nach dem Bauen die Dateiversion und dass die Version höher
  ist als `release/latest.json`. Passt etwas nicht, bricht der Lauf ab, statt
  einen unbrauchbaren Kandidaten abzulegen.
- Veröffentlichen: Datei testen, nach `next-update/release/` kopieren
  (ersetzen), auf `main` speichern. Oder den Workflow **„Release freigeben
  (Kandidat → release)"** per `workflow_dispatch` starten: Er prüft den
  Kandidaten mit `publish_latest.py --dry-run`, übernimmt ihn und startet
  `publish-bridge.yml`. `latest.json` schreibt weiterhin nur der Publish-Lauf.
- Nichts veröffentlicht von selbst: `beta-release/` ist kein Release-Ordner,
  und Commits mit dem `GITHUB_TOKEN` lösen keine Folgeläufe aus — deshalb
  startet der Freigabe-Workflow `publish-bridge.yml` ausdrücklich selbst.
- Eine veraltete EXE kann nicht versehentlich veröffentlicht werden:
  `publish_latest.py` vergleicht die Dateiversion der EXE mit
  `app/version.json` und bricht bei Abweichung ab. Eine 8.0.3-EXE in
  `release/` führt also zu einem Fehler im Workflow, nicht zu einem Update
  für Nutzer; `latest.json` bleibt unverändert.
- `-Channel beta` gibt es weiterhin für private Testbauten mit `-beta.1`; solche
  Builds sind bewusst **nicht** veröffentlichbar.

## Regeln

- Die Version muss bei jeder Veröffentlichung höher sein. Gleiche Version mit anderer
  EXE wird abgelehnt (Nutzer mit dieser Version bekämen sonst nie das Update).
- Jede EXE bleibt in der Git-Historie (ca. 6 MB pro Version). Es wird keine zweite Kopie
  mit Versionsnamen abgelegt — und seit 7.9.4 gibt es auch keine zweite Programmdatei
  (Diagnose-EXE/BAT) mehr.
- Nutzer installieren über die Download-Seite <https://arena-rblx-bridge.netlify.app/>;
  die Bridge selbst prüft nur das Repository-Manifest.
- Testbauten gehören nicht in `release/`, sondern bleiben lokal.
- Erst nach Freigabe durch den Nutzer veröffentlichen.

## Werkzeuge

- `developer/tools/publish_latest.py` — Prüfung und Erzeugung von `latest.json`.
  Lokal testen (ohne Schreiben): `python next-update/developer/tools/publish_latest.py --commit <40-stelliger SHA> --dry-run`
- `.github/workflows/publish-bridge.yml` — startet das Werkzeug auf `main`.
