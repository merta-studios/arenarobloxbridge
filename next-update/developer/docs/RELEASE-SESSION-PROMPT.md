# Prompt-Vorlage für die Release-Session

Dieses Dokument enthält die verbindliche Textvorlage, die eine **Änderungs-Session**
ausgibt, sobald der Nutzer nach erfolgreichem privatem Windows-Test signalisiert:
„perfekt, als neue Version und Update rausbringen“.

> **PFLICHT FÜR DIE ÄNDERUNGS-SESSION:**  
> Die Änderungs-Session antwortet auf diese Freigabe **AUSSCHLIESSLICH** mit einem einzigen
> Codeblock, der den unten stehenden Text mit ausgefüllten Platzhaltern enthält.
> Außerhalb des Codeblocks darf **kein einziges Zeichen Begleittext** ausgegeben werden.

---

### Auszufüllende Platzhalter
- `<VERSION>`: Die dreiteilige Versionsnummer aus `app/version.json` (z. B. `7.8.0`).
- `<KURZBESCHREIBUNG DER GEMERGTEN AENDERUNG>`: Eine prägnante deutsche Zusammenfassung der im Code-PR gemergten Änderungen.

---

### Text der Vorlage (innerhalb des Codeblocks)

```markdown
Du bist die Release-Session für Arena Roblox Bridge.
Der Nutzer hat den privaten Windows-Test von Version <VERSION> erfolgreich abgeschlossen und die Freigabe erteilt.
Gemergte Änderungen: <KURZBESCHREIBUNG DER GEMERGTEN AENDERUNG>.

Lies ZUERST next-update/developer/docs/RELEASE-ABLAUF.md und next-update/developer/docs/UPDATE-KONZEPT.md sorgfältig durch.

AUFTRAG DER RELEASE-SESSION:
1. ARBEITSBEREICH: Arbeite AUSSCHLIESSLICH in next-update/. Das alte System im Repository-Hauptordner ist strikt verboten und wird ignoriert.
2. KEINE QUELLCODE-ÄNDERUNG: Verändere NIE Quelltexte in app/, builder/ oder version.json. Baue keine EXE still nach. Aktiviere kein Manifest von Hand – dafür ist ausschließlich developer/tools/release.py zuständig.
3. ZUSTAND PRÜFEN:
   - Führe `python developer/tools/release.py status` aus und lies das Ergebnis vollständig.
   - Führe `python developer/tools/release.py check --require-test-build` aus.
   - Prüfe, ob die vom Nutzer getestete EXE unter next-update/release/ArenaBridge.exe liegt, und ob die PE-FileVersion exakt '<VERSION>.0' lautet (Werkzeug prüft das mit; hilfsweise pefile in einem temporären venv außerhalb des Repos).
   - Wenn Datei fehlt, Version nicht zu app/version.json passt oder die Dateiversion abweicht: STOPPE und melde den Fehler dem Nutzer. Rate niemals SHA-256, Größe oder Version.
4. REPO-SICHTBARKEIT PRÜFEN:
   - Führe `gh repo view --json isPrivate` aus.
   - Ist das Repository privat (isPrivate != false) oder nicht prüfbar: STOPPE, veröffentliche nichts und warne den Nutzer (der Updater sendet keine Zugangsdaten; privat = 404 = kein Update).
5. SMOKE-TEST-RÜCKFRAGE:
   - Prüfe, ob der Nutzer in dieser Session bereits gemeldet hat, dass `Invoke-SelfUpdateSmoke.ps1` auf Windows bestanden hat.
   - Wenn nicht gemeldet: Frage einmal ausdrücklich nach dem Ergebnis. Ohne Bestätigung oder ein ausdrückliches „trotzdem“ des Nutzers wird NICHT veröffentlicht (dann `--smoke-test-skipped`, ehrlich im PR vermerken).
6. VERÖFFENTLICHEN (nur mit dem Werkzeug):
   - Erst Probelauf: `python developer/tools/release.py stage --version <VERSION> --channel stable --tested-by-user --smoke-test-passed --dry-run`
   - Dann echt: gleicher Befehl ohne `--dry-run` (bzw. `--smoke-test-skipped`, falls der Nutzer den Test ausdrücklich übersprungen hat).
   - Das Werkzeug kopiert die getestete EXE nach release/ArenaBridge-<VERSION>.exe (unveränderlich), schreibt stable.json im Schema 2 mit fortlaufender sequence, aktualisiert die README-Tabelle und führt das Guard-Rebaseline (`--rebaseline`) mit der Release-Freigabe aus. Handarbeit an den JSON-Dateien ist verboten.
   - Lasse beta.json unverändert auf enabled: false.
7. DOKUMENTATION:
   - Prüfe, dass in next-update/update-system/README.md die Zeile "Letzte veröffentlichte Version" auf "<VERSION>" steht und die Tabelle die neue Zeile mit Sequence enthält (schreibt das Werkzeug).
   - Ergänze in next-update/update-system/PROTECTED.md eine kurze Freigabenotiz zur Veröffentlichung, falls noch nicht vorhanden.
8. TESTS:
   - Führe in einem venv außerhalb des Repos aus: `python developer/tests/run_offline_tests.py`
   - Alle Tests müssen grün sein (test_v800_selfupdate_smoke.py darf auf Linux mit Exit 77 skippen).
9. PULL REQUEST:
   - Erstelle einen Pull Request für diesen Release auf GitHub (nur Kanal, README, Lock, ggf. PROTECTED.md).
   - Merge den PR NICHT selbst.
   - Liste ehrlich auf, was nur der Nutzer auf Windows prüfen kann.
   - Weise den Nutzer darauf hin, dass raw.githubusercontent.com bis zu 5 Minuten Cache-Verzögerung haben kann (ungefährlich: Cache-Brecher, sequence-Prüfung und SHA-256-Prüfung im Updater).
   - Nenne als Rücknahme-Weg: `python developer/tools/release.py disable --channel stable`.
```
