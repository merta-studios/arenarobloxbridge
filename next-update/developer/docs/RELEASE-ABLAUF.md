# Release-Ablauf (next-update, Version 7.9.1)

Kurzfassung: Siehe `next-update/README.md`. Hier die Details fuer Entwicklung und Pruefung.

## Phasen

1. **Aenderungs-Session:** Code, Tests und Doku in `next-update/` aendern. Version in
   `app/version.json` erhoehen, wenn die EXE veroeffentlicht werden soll. Tests laufen lassen:
   `python developer/tests/run_offline_tests.py`. Dann "mach Pull Request".
2. **Merge und Build:** Der Nutzer mergt den PR, laedt das ZIP, startet `Build-EXE.bat`.
   Ergebnis: `release/ArenaBridge.exe` (lokal).
3. **Privater Test:** Der Nutzer testet die EXE auf seinem Windows-PC (Checkliste in
   `UPDATE-SYSTEM.md`, Abschnitt "Tests").
4. **Veroeffentlichung:** Nur bei gutem Stand die getestete `ArenaBridge.exe` nach
   `next-update/release/ArenaBridge.exe` hochladen und auf `main` speichern. Der Workflow
   erzeugt `latest.json` automatisch. Niemand schreibt `latest.json` von Hand.

## Regeln

- Die Version muss bei jeder Veroeffentlichung hoeher sein. Gleiche Version mit anderer
  EXE wird abgelehnt (Nutzer mit dieser Version bekaemen sonst nie das Update).
- Jede EXE bleibt in der Git-Historie (ca. 6 MB pro Version). Es wird keine zweite Kopie
  mit Versionsnamen abgelegt.
- Testbauten gehoeren nicht in `release/`, sondern bleiben lokal.
- Erst nach Freigabe durch den Nutzer veroeffentlichen.

## Werkzeuge

- `developer/tools/publish_latest.py` — Pruefung und Erzeugung von `latest.json`.
  Lokal testen (ohne Schreiben): `python next-update/developer/tools/publish_latest.py --commit <40-stelliger SHA> --dry-run`
- `.github/workflows/publish-bridge.yml` — startet das Werkzeug auf `main`.
