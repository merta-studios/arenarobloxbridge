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
- `<VERSION>`: Die dreiteilige Versionsnummer aus `app/version.json` (z. B. `7.7.0` oder `7.7.1`).
- `<KURZBESCHREIBUNG DER GEMERGTEN AENDERUNG>`: Eine prägnante deutsche Zusammenfassung der im Code-PR gemergten Änderungen.

---

### Text der Vorlage (innerhalb des Codeblocks)

```markdown
Du bist die Release-Session für Arena Roblox Bridge.
Der Nutzer hat den privaten Windows-Test von Version <VERSION> erfolgreich abgeschlossen und die Freigabe erteilt.
Gemergte Änderungen: <KURZBESCHREIBUNG DER GEMERGTEN AENDERUNG>.

Lies ZUERST die Datei next-update/developer/docs/RELEASE-ABLAUF.md sorgfältig durch.

AUFTRAG DER RELEASE-SESSION:
1. ARBEITSBEREICH: Arbeite AUSSCHLIESSLICH in next-update/ und next-update/update-system/. Das alte System im Repository-Hauptordner ist strikt verboten und wird ignoriert.
2. KEINE QUELLCODE-ÄNDERUNG: Verändere NIE Quelltexte in app/, builder/ oder version.json. Baue keine EXE still nach.
3. EXE PRÜFEN:
   - Prüfe, ob die vom Nutzer getestete EXE unter next-update/release/ArenaBridge.exe existiert.
   - Falls sie fehlt: STOPPE sofort und bitte den Nutzer um genau diese Datei.
   - Berechne SHA-256 und Dateigröße (sizeBytes) direkt aus der Datei next-update/release/ArenaBridge.exe. Raten ist verboten.
   - Prüfe die PE-FileVersion der EXE (z. B. via pefile in einem temporären venv außerhalb des Repos). Sie MUSS exakt '<VERSION>.0' lauten. Bei Abweichung: STOPPE und melde den Fehler dem Nutzer.
4. REPO-SICHTBARKEIT PRÜFEN:
   - Führe `gh repo view --json isPrivate` aus.
   - Ist das Repository privat (isPrivate != false) oder nicht prüfbar: STOPPE, aktiviere nichts und warne den Nutzer (der Updater sendet keine Zugangsdaten; privat = 404 = kein Update).
5. SMOKE-TEST-RÜCKFRAGE:
   - Prüfe, ob der Nutzer in dieser Session bereits gemeldet hat, dass `Invoke-SelfUpdateSmoke.ps1` auf Windows bestanden hat.
   - Wenn nicht gemeldet: Frage einmal ausdrücklich nach dem Ergebnis. Ohne Bestätigung oder ein ausdrückliches „trotzdem“ des Nutzers wird das Manifest NICHT aktiviert.
6. MANIFEST AKTIVIEREN:
   - Fülle next-update/update-system/channels/stable.json aus:
     * schemaVersion: 1
     * channel: "stable"
     * enabled: true
     * testFixture: false
     * version: "<VERSION>"
     * publishedAtUtc: Aktueller UTC-Zeitstempel im ISO-8601-Format (z. B. "2026-10-10T14:30:00Z")
     * minimumUpdaterVersion: "1.1.0"
     * mandatory: false
     * artifact.fileName: "ArenaBridge.exe"
     * artifact.url: "https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/next-update/release/ArenaBridge.exe"
     * artifact.sha256: Die berechnete hexadezimale SHA-256 der EXE
     * artifact.sizeBytes: Die exakte Byteanzahl der EXE
     * notes: Deutsche Nutzerhinweise zu den Neuerungen dieser Version
   - Halte beta.json auf enabled: false.
7. DOKUMENTATION & LOCK:
   - Aktualisiere in next-update/update-system/README.md den Eintrag "Letzte veröffentlichte Version" auf "<VERSION>".
   - Dokumentiere die Freigabe in next-update/update-system/PROTECTED.md.
   - Führe Rebaseline für die Lock-Datei aus (GENAU EINE Freigabe, mind. 30 Zeichen):
     python developer/tests/test_v800_update_system_guard.py --rebaseline --approval "Release-Freigabe Version <VERSION>: Kanal stable aktiviert fuer freigegebene EXE."
8. TESTS:
   - Führe die Offline-Testsuite in einem venv außerhalb des Repos aus:
     python developer/tests/run_offline_tests.py
   - Alle Tests müssen grün sein (test_v800_selfupdate_smoke.py darf auf Linux exit 77 skippen).
9. PULL REQUEST:
   - Erstelle einen Pull Request für diesen Release auf GitHub.
   - Merge den PR NICHT selbst.
   - Liste ehrlich auf, was nur der Nutzer auf Windows prüfen kann.
   - Weise den Nutzer darauf hin, dass raw.githubusercontent.com bis zu 5 Minuten Cache-Verzögerung haben kann (völlig sicher durch SHA-256-Prüfung des Updaters).
```
