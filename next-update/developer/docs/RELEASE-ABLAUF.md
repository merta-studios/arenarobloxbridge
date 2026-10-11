# Release-Ablauf (next-update, Stand 7.8.0)

Dieses Dokument beschreibt den verbindlichen Versions- und Release-Ablauf für die
Arena Roblox Bridge. Es gilt für jede Sitzung und Entwicklungsstufe. Das Warum steht in
`UPDATE-KONZEPT.md`.

> **HARTE REGEL:** Es wird ausschließlich im Ordner `next-update/` gearbeitet.
> Der alte Bereich im Repository-Hauptordner bleibt unverändert und wird ignoriert.

> **SEIT 7.8.0:** Manifest und Veröffentlichung werden **nicht mehr von Hand** geschrieben.
> Das Werkzeug `developer/tools/release.py` prüft, veröffentlicht und schreibt Guard-Freigabe,
> README und Manifest in einem Schritt. Handarbeit an `channels/*.json` ist verboten.

---

## 1. Die vier Phasen des Release-Zyklus

### Phase 1: Änderungs-Session (Feature / Bugfix / Doku)
1. **Auftrag:** Der Nutzer schreibt z. B. „arbeite in next-update und ändere: ...“.
2. **Bearbeitung:** Du änderst ausschließlich Dateien in `next-update/`.
3. **Versionierung:** Bei funktionalen Änderungen erhöhst du die Version in `app/version.json`
   und allen in Dokumentation und Tests verankerten Versionsstellen konsistent.
4. **Offline-Tests:** `python developer/tests/run_offline_tests.py` muss grün sein
   (Windows-Tests skippen sauber mit Exit 77).
5. **Pull Request:** Auf Wunsch erstellst du einen PR auf dem Arbeits-Branch.
6. **Schranke:** In der Änderungs-Session wird **nie** ein Manifest in `update-system/channels/`
   verändert oder aktiviert. Es wird **nichts veröffentlicht**.

### Phase 2: Privater lokaler Windows-Test durch den Nutzer
1. Der Nutzer mergt den PR und lädt das Repository-ZIP herunter.
2. Der Nutzer öffnet `next-update/` und doppelklickt **`Build-EXE.bat`**.
   - Baut standardmäßig den Kanal **`stable`** ohne Rückfrage.
   - Ergebnis: `release\ArenaBridge.exe` (privater Testbau) und lokale Diagnosedateien.
3. Der Nutzer testet `release\ArenaBridge.exe` privat auf seinem Windows-PC.
4. **Optional, empfohlen:** Selbst-Update isoliert prüfen:
   ```powershell
   powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\developer\tests\Invoke-SelfUpdateSmoke.ps1
   ```
   (baut zwei Test-EXEs, prüft 15 Update-Fälle in `%TEMP%`, ändert nie `release\` oder die Kanäle)
5. **Gefällt es nicht / Fehler:** EXE **nicht** hochladen. Neuer Chat, neuer Zyklus.
6. **Gefällt es:** Der Nutzer lädt die exakt getestete EXE nach `next-update/release/ArenaBridge.exe`
   hoch (ersetzt die vorhandene EXE). Das ist die **Quelle** für die Veröffentlichung.

### Phase 3: Freigabe in der Änderungs-Session
1. Wenn alles funktioniert, schreibt der Nutzer in der Änderungs-Session (deren PR bereits gemergt ist)
   sinngemäß: **„perfekt, als neue Version und Update rausbringen“**.
2. Die Änderungs-Session antwortet **AUSSCHLIESSLICH mit einem einzigen Codeblock**, der den
   vollständigen, vorbereiteten Prompt für die Release-Session enthält (Vorlage:
   `developer/docs/RELEASE-SESSION-PROMPT.md`).
3. **Kein Begleittext, keine Höflichkeitsfloskeln, keine Erklärung außerhalb des Codeblocks.**

### Phase 4: Release-Session
1. Der Nutzer fügt den Prompt in eine **neue Session** mit leerem Gedächtnis ein.
2. Die Release-Session arbeitet **ausschließlich mit `release.py`**:
   - `python developer/tools/release.py status` – Zustand (Quellversion, eingebetteter Updater,
     letzte Veröffentlichung, lokale Test-EXE mit Dateiversion, Kanäle).
   - `python developer/tools/release.py check --require-test-build` – Prüfbericht: PE-x64-Kopf,
     Dateiversion, Größe, Quellversion, letzte Veröffentlichung.
   - `python developer/tools/release.py stage --version <VERSION> --channel stable --tested-by-user
     (--smoke-test-passed|--smoke-test-skipped)` – kopiert die getestete EXE nach
     `release/ArenaBridge-<VERSION>.exe` (unveränderlich, wird nie überschrieben), schreibt das
     Kanal-Manifest (Schema 2, `sequence` = höchste bisherige + 1), aktualisiert
     `update-system/README.md` und führt das Guard-Rebaseline mit der Release-Freigabe aus.
   - `--dry-run` zeigt alles ohne zu schreiben.
3. **Rückfrage zum Selbst-Update-Test:** Hat der Nutzer `Invoke-SelfUpdateSmoke.ps1` nicht gemeldet,
   fragt die Release-Session **einmal** nach. Ohne Bestätigung oder ausdrückliches „trotzdem“ wird
   nicht veröffentlicht (dann `--smoke-test-skipped`, ehrlich im PR vermerkt).
4. **Public-Repo-Gate:** `gh repo view --json isPrivate` muss `false` ergeben, sonst STOP
   (der Updater sendet keine Zugangsdaten; privat = 404 = kein Update).
5. Die Release-Session ändert **NUR** Kanal-Manifest, README-Tabelle, Guard-Lock (durch das
   Rebaseline von `stage`) und ggf. `PROTECTED.md`. Sie ändert **NIE** Quellcode, `version.json`
   oder die hochgeladene EXE und baut nichts nach.
6. Nach dem Merge des Release-PRs ist die Version live: Jede EXE mit eingebautem Updater und
   Kanal `stable` bietet beim Start das Update an (Fenster mit Jetzt/Später/Überspringen).
   Alte EXEs ohne Updater werden nicht gestört.

---

## 2. Harte Regeln für Änderungs- und Release-Sessions

1. **Kein Manifest in Änderungs-Sessions:**
   Eine Änderungs-Session fasst `update-system/channels/*` **nie** an. Manifeste bleiben dort
   immer `enabled: false`. Aktiviert wird ausschließlich in der Release-Session über `release.py stage`.
2. **Keine Spekulation bei Artefakt-Daten:**
   Version, SHA-256 und Größe liest ausschließlich `release.py` aus der tatsächlich hochgeladenen
   Datei. Werte werden niemals geraten, geschätzt oder von Hand eingetragen.
3. **Unveränderliche Artefakte:**
   Veröffentlicht wird `release/ArenaBridge-<VERSION>.exe`. Dateiname und `artifact.url` werden aus
   der Version abgeleitet. Eine vorhandene Zieldatei wird **nie** überschrieben (`stage` bricht ab;
   Abhilfe ist eine höhere Version, nicht `--force` als Gewohnheit).
4. **Strenge Versionsprüfung (kein Versions-Konflikt):**
   Die Version muss echt höher sein als die zuletzt veröffentlichte Version (README-Zeile
   „Letzte veröffentlichte Version“). Gleichstand mit anderem Hash oder ein Downgrade ist ein
   schwerer Fehler (`version-conflict`) und blockiert. Zusätzlich gilt: `version` ==
   `app/version.json`, und die PE-Dateiversion der EXE muss `<VERSION>.0` sein.
5. **Feste kanonische URL:**
   `https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/next-update/release/ArenaBridge-<VERSION>.exe`
   Keine alternative URL, kein fremder Host, keine dynamischen Pfade, kein HTTP.
6. **Ehrlichkeit bei Windows-Ergebnissen:**
   Windows-Ergebnisse (Build, Start, WPF, `Invoke-SelfUpdateSmoke.ps1`) sind in der Linux-Sandbox
   nicht ausführbar. Sie werden **niemals** als bestanden behauptet, sondern nur übernommen, wenn
   der Nutzer sie gemeldet hat. `stage` verlangt `--tested-by-user` und
   `--smoke-test-passed|--smoke-test-skipped`.
7. **Transparenz über den GitHub-Raw-Cache:**
   Nach dem Merge kann `raw.githubusercontent.com` bis zu 5 Minuten den alten Stand liefern. Das ist
   sicher: Der Updater bringt einen Cache-Brecher mit, prüft `sequence` und bricht bei Größe/Hash
   ohne Änderung ab; beim nächsten Start versucht er es erneut. Ein „halbes“ Update kann es nicht
   geben, weil jede Veröffentlichung eine eigene, unveränderliche Datei mit festem SHA-256 ist.
8. **Sichtbarkeitsprüfung (Public Repo Gate) und kein erzwungenes Update:**
   `gh repo view --json isPrivate` muss `false` ergeben. Ein Feld `mandatory` gibt es in Schema 2
   nicht; Updates sind immer eine freiwillige Nutzerentscheidung.
9. **Rücknahme:**
   `python developer/tools/release.py disable --channel stable` deaktiviert den Kanal sofort (kein
   Nutzer erhält danach Hinweise). `prune --keep N` räumt alte Artefakte auf, nie die neueste.
10. **Schutz:** `update-system/**`, der App-Block `ARENA-UPDATE-INTEGRATION`, der Builder und die
    v800-Tests sind per SHA-256 geschützt. Jede Änderung dort braucht die dokumentierte
    Nutzerfreigabe und ein Rebaseline (siehe `update-system/PROTECTED.md`).
