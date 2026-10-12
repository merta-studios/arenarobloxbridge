# Release-Ablauf (next-update, Version 7.9.3)

Kurzfassung: Siehe `next-update/README.md`. Hier die Details für Entwicklung und Prüfung.

## Phasen

1. **Änderungs-Session:** Code, Tests und Doku in `next-update/` ändern. Version in
   `app/version.json` erhöhen, wenn die EXE veröffentlicht werden soll, und die
   Nutzer-Notiz als kurze Stichpunkte schreiben (Stichpunkt-Regel in
   `docs/GANZ WICHTIG LESEN VOR JEDER BEARBEITUNG`). Tests laufen lassen:
   `python developer/tests/run_offline_tests.py`. Dann "mach Pull Request".
2. **Merge und Build:** Der Nutzer mergt den PR, lädt das ZIP, startet `Build-EXE.bat`.
   Ergebnis: `release/ArenaRobloxBridge.exe` (lokal).
3. **Privater Test:** Der Nutzer testet die EXE auf seinem Windows-PC (Checkliste in
   `UPDATE-SYSTEM.md`, Abschnitt "Tests").
4. **Veröffentlichung:** Nur bei gutem Stand die getestete `ArenaRobloxBridge.exe` nach
   `next-update/release/ArenaRobloxBridge.exe` hochladen und auf `main` speichern. Der Workflow
   erzeugt `latest.json` automatisch. Niemand schreibt `latest.json` von Hand.

## Regeln

- Die Version muss bei jeder Veröffentlichung höher sein. Gleiche Version mit anderer
  EXE wird abgelehnt (Nutzer mit dieser Version bekämen sonst nie das Update).
- Jede EXE bleibt in der Git-Historie (ca. 6 MB pro Version). Es wird keine zweite Kopie
  mit Versionsnamen abgelegt.
- Testbauten gehören nicht in `release/`, sondern bleiben lokal.
- Erst nach Freigabe durch den Nutzer veröffentlichen.

## Werkzeuge

- `developer/tools/publish_latest.py` — Prüfung und Erzeugung von `latest.json`.
  Lokal testen (ohne Schreiben): `python next-update/developer/tools/publish_latest.py --commit <40-stelliger SHA> --dry-run`
- `.github/workflows/publish-bridge.yml` — startet das Werkzeug auf `main`.
