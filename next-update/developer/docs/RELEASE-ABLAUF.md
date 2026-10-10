# Release-Ablauf (next-update)

Dieses Dokument beschreibt den verbindlichen Versions- und Release-Ablauf für die
Arena Roblox Bridge. Es gilt für jede Sitzung und Entwicklungsstufe.

> **HARTE REGEL:** Es wird ausschließlich im Ordner `next-update/` gearbeitet.
> Der alte Bereich im Repository-Hauptordner bleibt unverändert und wird ignoriert.

---

## 1. Die vier Phasen des Release-Zyklus

### Phase 1: Änderungs-Session (Feature / Bugfix / Doku)
1. **Auftrag:** Der Nutzer schreibt z. B. „arbeite in next-update und ändere: ...“.
2. **Bearbeitung:** Du änderst ausschließlich Dateien in `next-update/`.
3. **Versionierung:** Bei funktionalen Änderungen erhöhst du die Version in `app/version.json`
   und allen in der Dokumentation / den Tests verankerten Versionsstellen konsistent.
4. **Offline-Tests:** Du führst die Offline-Testsuite aus (`developer/tests/run_offline_tests.py`),
   sodass alle Tests grün sind (bzw. Windows-Tests sauber skippen).
5. **Pull Request:** Du erstellst auf Wunsch einen PR auf dem Arbeits-Branch.
6. **Schranke:** In der Änderungs-Session wird **nie** ein Manifest in `update-system/channels/`
   verändert oder aktiviert. Es wird **nichts veröffentlicht**.

### Phase 2: Privater lokaler Windows-Test durch den Nutzer
1. Der Nutzer mergt den PR und lädt das Repository-ZIP herunter.
2. Der Nutzer öffnet `next-update/` und doppelklickt **`Build-EXE.bat`**.
   - `Build-EXE.bat` baut standardmäßig den Kanal **`stable`** ohne interaktive Rückfrage.
   - Der Build legt `release\ArenaBridge.exe` und lokale Diagnosedateien im Ordner `release\` ab.
3. Der Nutzer testet `release\ArenaBridge.exe` privat auf seinem Windows-PC.
4. **Optional:** Der Nutzer prüft das Selbst-Update isoliert mit:
   ```powershell
   powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\developer\tests\Invoke-SelfUpdateSmoke.ps1
   ```
5. **Gefällt es nicht / Fehler:** Der Nutzer lädt die EXE **nicht** hoch. Neuer Chat, neuer Zyklus.
6. **Gefällt es:** Der Nutzer lädt die exakt getestete EXE nach `next-update/release/ArenaBridge.exe`
   ins Repository hoch (ersetzt die vorhandene EXE).

### Phase 3: Freigabe in der Änderungs-Session
1. Wenn alles funktioniert, schreibt der Nutzer in der Änderungs-Session (dessen PR bereits gemergt ist)
   sinngemäß: **„perfekt, als neue Version und Update rausbringen“**.
2. Die Änderungs-Session antwortet **AUSSCHLIESSLICH mit einem einzigen Codeblock**, der den
   vollständigen, vorbereiteten Prompt für die Release-Session enthält (Vorlage:
   `developer/docs/RELEASE-SESSION-PROMPT.md`).
3. **Kein Begleittext, keine Höflichkeitsfloskeln, keine Erklärung außerhalb des Codeblocks.**

### Phase 4: Release-Session
1. Der Nutzer fügt den Prompt in eine **neue Session** mit leerem Gedächtnis ein.
2. Die Release-Session prüft:
   - Die getestete EXE existiert unter `next-update/release/ArenaBridge.exe`.
   - Die PE-FileVersion der EXE entspricht `<VERSION>.0`.
   - Das Repository ist öffentlich (`gh repo view --json isPrivate` ergibt `false`).
   - Ob der Nutzer den Selbst-Update-Test (`Invoke-SelfUpdateSmoke.ps1`) bestätigt hat.
3. Die Release-Session berechnet SHA-256 und Dateigröße der echten Datei selbst (niemals raten).
4. Die Release-Session ändert **NUR** das Kanal-Manifest (`update-system/channels/stable.json`),
   die Lock-Datei (`update_system_guard.lock.json` per Rebaseline) und die Release-Dokumentation.
   Sie ändert **NIE** den Quellcode, `version.json` oder die EXE selbst.
5. Nach dem Merge des Release-PRs durch den Nutzer ist die Version live: Jede EXE mit
   eingebautem Updater und Kanal `stable` bietet beim Start das Update an (Ja/Nein-Dialog).
   Alte EXEs ohne Updater werden ignoriert und nicht gestört.

---

## 2. Harte Regeln für Änderungs- und Release-Sessions

1. **Kein Manifest in Änderungs-Sessions:**
   Eine Änderungs-Session fasst `update-system/channels/*` **nie** an. Manifeste bleiben dort
   immer `enabled: false`.
2. **Keine Spekulation bei Artefakt-Daten:**
   Die Release-Session liest Version, SHA-256 und Dateigröße ausschließlich aus der tatsächlich
   hochgeladenen `next-update/release/ArenaBridge.exe`. Werte werden niemals geraten oder geschätzt.
3. **Strenge Versionsprüfung (Kein Versions-Konflikt):**
   Die Version im Manifest muss **echt höher** sein als die zuletzt veröffentlichte Version
   (dokumentiert in `update-system/README.md` unter „Letzte veröffentlichte Version“).
   Ein Gleichstand mit anderem Hash oder ein Downgrade gilt als schwerer Fehler (`version-conflict`)
   und führt zum Abbruch.
4. **Feste kanonische Artefakt-URL:**
   Die `artifact.url` im Manifest ist fest und unveränderlich:
   `https://raw.githubusercontent.com/merta-studios/arenarobloxbridge/main/next-update/release/ArenaBridge.exe`
   Keine alternative URL, kein fremder Host, keine dynamischen Pfade.
5. **Ehrlichkeit bei Windows-Ergebnissen:**
   Windows-Ergebnisse (EXE-Build, WPF-Smoke, `Invoke-SelfUpdateSmoke.ps1`) können in der Linux-Sandbox
   nicht ausgeführt werden. Sie werden **niemals** als bestanden behauptet, sondern nur übernommen,
   wenn der Nutzer sie ausdrücklich gemeldet hat. Vor der Aktivierung fragt die Release-Session
   einmalig, ob `Invoke-SelfUpdateSmoke.ps1` bestanden hat; ohne ausdrückliches „trotzdem“ des
   Nutzers wird nicht aktiviert.
6. **Transparenz über den GitHub Raw-Cache:**
   Nach dem Upload und Merge liefert `raw.githubusercontent.com` unter Umständen für wenige Minuten
   noch den alten Stand (HTTP-Cache). Das ist vollkommen sicher: Der Updater prüft vor dem
   Ersetzen strikt die SHA-256-Prüfsumme. Stimmt der Hash nicht, bricht der Updater ohne Änderung ab;
   beim nächsten Programmstart versucht er es erneut. Dies wird dem Nutzer ehrlich mitgeteilt.
7. **Sichtbarkeitsprüfung des Repositorys (Public Repo Gate):**
   Der Updater sendet beim Abruf keine Authentifizierungs-Token (er nutzt reines, anonymes HTTPS).
   Ist das Repository privat, liefert GitHub einen HTTP 404-Fehler und kein Nutzer erhält Updates.
   Die Release-Session führt vor der Aktivierung folgenden Befehl aus:
   ```bash
   gh repo view --json isPrivate
   ```
   Ergibt `isPrivate` nicht `false` (z. B. `true` oder nicht prüfbar), darf das Manifest **nicht**
   aktiviert werden. Der Nutzer muss gewarnt werden.
8. **Kein erzwungenes Update („mandatory“ ist wirkungslos):**
   Das Manifestfeld `mandatory` wird vom eingebetteten Updater **nicht** ausgewertet. Ein Update
   wird dem Nutzer immer als freiwillige Ja/Nein-Entscheidung angeboten. Zwingende Updates dürfen
   dem Nutzer nicht versprochen werden.
