# Arena Roblox Bridge — neuer Update- und Testablauf

> **Arbeite nur in `next-update/`.** Der alte Bereich im Repository-Hauptordner
> bleibt unverändert und wird für diesen Ablauf vollständig ignoriert.
>
> **Pflichtlektüre zum Release-Ablauf:** Siehe `developer/docs/RELEASE-ABLAUF.md`.
> Die Prompt-Vorlage für die Release-Session liegt in `developer/docs/RELEASE-SESSION-PROMPT.md`.

## Lokal bauen und testen

1. Eine Änderung beschreibst du im Chat. Die KI bearbeitet ausschließlich
   `next-update/`, prüft die passenden Tests und erstellt einen Pull Request.
   **Der PR ist nur eine Code-Änderung — keine Veröffentlichung.** Die
   Kanal-Manifeste bleiben deaktiviert und es wird keine EXE an Nutzer verteilt.
2. Du mergst den PR und lädst danach das Repository-ZIP herunter.
3. Öffne darin `next-update` und doppelklicke **`Build-EXE.bat`**. Das ist der
   einzige normale Build-Knopf. `Build-EXE.bat` baut standardmäßig den Kanal **`stable`**
   (ohne interaktive Rückfrage). Der lokale Test-Build braucht 64-Bit-Windows,
   Windows PowerShell 5.1, WPF/.NET und beim ersten Build eine Internetverbindung
   für `ps2exe`.
4. Die zu testende App liegt immer hier — ohne beta/stable-Unterordner:

   ```text
   next-update\release\ArenaBridge.exe
   ```

   Starte genau diese EXE und teste sie privat. Schließe vorher ältere
   ArenaBridge-Fenster. Falls kein Fenster erscheint, schließe andere
   ArenaBridge-Prozesse und starte `next-update\release\Start-Diagnostic.bat`.
5. `release\ArenaBridge-Diagnose.exe`, Diagnose-BAT, Prüfsummen und
   `release-metadata.json` sind Hilfsdateien. Nur `release\ArenaBridge.exe`
   ist später als App-Artefakt vorgesehen.

> **Kanal-Hinweis:** Build-EXE.bat baut standardmäßig den Kanal `stable` (die EXE
> liest `stable.json`). Hinweis: Die bereits getestete 7.7.0-EXE ist ein beta-Kanal-Build
> und erhält kein Stable-Update.

Das Build-Skript prüft zuerst den Windows-PowerShell-Parser (Bridge **und** Updater).
Danach startet es die EXE in einem isolierten Smoke-Test; dabei werden x64, STA/WPF,
der EXE-Ordnerpfad, das Startbild **und das eingebettete `neueslogo.png`** geprüft.
Dieser Smoke-Test startet weder Roblox Studio noch den Bridge-Server noch einen Updater.

**Der Build bettet außerdem den Updater (Version 1.1.0) in die EXE ein.** Die EXE
braucht keine separate Updater-Datei. Die Auto-Update-Prüfung ist im Normalbau
aktiv, gilt aber nur für Kanäle, die freigegeben sind. Solange `beta.json` bzw.
`stable.json` deaktiviert sind, findet kein Update statt.

## Selbst-Update privat testen (nur Windows, nach dem ZIP-Build)

Dieser Test ist vom normalen Build getrennt und lädt nichts aus dem Internet außer
dem lokalen Fixture-Server auf `127.0.0.1`:

```powershell
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\developer\tests\Invoke-SelfUpdateSmoke.ps1
```

Der Test baut zwei Test-EXEs (7.7.0 und 7.7.1) mit `-TestFixtureBuild` in einen
Ordner unter `%TEMP%` — **nie** nach `release\`. Er prüft isoliert: check,
Installation einer gestoppten EXE mit Backup und Neustart, Downgrade-Ablehnung,
falschen Hash, Größenlimit, deaktiviertes und ungültiges Manifest,
Netzwerkfehler, laufende EXE (wird nicht beendet) und Rollback. Die Channel-Dateien
werden dabei nicht verändert. Bei Fehlern bleibt der Arbeitsordner für die Analyse erhalten.

**Ehrlicher Stand:** Dieser Test wurde in der Entwicklungssandbox NICHT ausgeführt
(dort gibt es kein Windows/PowerShell). Er gilt erst als bestanden, wenn er auf einem
Windows-PC gelaufen ist und das Ergebnis dokumentiert wurde.

## Wenn der Test fehlschlägt oder dir die Änderung nicht gefällt

- Lade die Test-EXE **nicht** in das Repository hoch und fordere keine
  öffentliche Freigabe an.
- Starte einfach einen neuen Chat und beschreibe, was korrigiert werden soll.
  Die KI erstellt einen neuen PR in `next-update/`; nach dessen Merge lädst du
  wieder ein ZIP herunter, baust erneut und testest erneut.
- Frühere Test-PRs oder lokale Builds lösen kein Update bei Nutzern aus. Die
  Kanal-Manifeste werden in dieser Phase nicht aktiviert. Nutzer merken von
  deinen privaten Tests nichts.

## Wenn du den getesteten Stand ausdrücklich freigibst

1. Schreibe **im Chat, in dem der Änderungs-PR bereits gemergt wurde**, dass
   dir der Test gefällt und du die Version für alle freigibst („perfekt, als neue Version und Update rausbringen“).
2. In genau diesem Chat darf die KI **nicht veröffentlichen und nichts weiter
   erklären**. Sie muss als Antwort ausschließlich **eine kopierbare Textbox
   (einen Codeblock) mit einem vollständigen Prompt für die nächste Session**
   ausgeben (Vorlage: `developer/docs/RELEASE-SESSION-PROMPT.md`).
3. In der Release-Session wird die **bereits getestete** EXE verwendet — keine
   unbemerkte Neu-Kompilierung und kein anderer Build. Nach deiner ausdrücklichen
   Freigabe kommt genau diese Datei an diesen einen Repository-Pfad:

   ```text
   next-update/release/ArenaBridge.exe
   ```

   Wenn sie der Release-Session nicht vorliegt, muss die KI dich bitten, genau
   diese getestete Datei dort hochzuladen oder anzuhängen. Sie darf nicht raten
   oder einen ungeprüften Ersatz verwenden.
4. Die öffentliche Auslieferung läuft ausschließlich über `next-update/update-system/`.
   **Offene Freigabeschranken:** (a) Ein Windows-Lauf von Parse-Gate, EXE-Build und
   Selbst-Update-Test ist noch nicht dokumentiert. (b) Bereits installierte Kopien
   ohne Updater werden vom System **nicht automatisch** erreicht; eine einmalige
   Migration ist offen. Solange diese Punkte offen sind, bleibt Stable deaktiviert,
   und es darf nicht behauptet werden, alle Nutzer würden automatisch aktualisiert.
5. Erst nachdem Integration, Bootstrap, getestete EXE, Versionsnummer,
   Dateigröße und SHA-256 stimmen, darf die Release-Session den Stable-Kanal
   über das neue System vorbereiten. Das Stable-Manifest muss auf genau die
   geprüfte `release/ArenaBridge.exe` im Repository zeigen. Erforderliche
   Quell-/Manifeständerungen gehen wieder als PR durch den Merge-Prozess. Kein
   Update darf allein durch einen normalen Code-PR oder einen privaten Build
   aktiviert werden.

Damit gilt die klare Trennung: **Merge + ZIP + lokaler Build = Test.** Nur die
spätere ausdrückliche Freigabe und der abgeschlossene Release-Schritt über den
neuen Updater können ein Update für Nutzer bereitstellen. Details: `developer/docs/RELEASE-ABLAUF.md`.

## Schutz des Update-Systems

`update-system/`, der Updater-Block in `app/ArenaBridge.ps1`, die Update-Teile des
Builders und die Update-Tests sind **geschützt**. Änderungen daran brauchen eine
ausdrückliche Freigabe und ein dokumentiertes Verfahren; siehe `update-system/PROTECTED.md`.
Der Guard-Test schlägt bei jeder ungeprüften Änderung fehl.

## Ordnerübersicht

| Pfad | Zweck |
|---|---|
| `Build-EXE.bat` | Einziger normaler Klick für den lokalen Test-Build. |
| `START-HIER.txt` | Kurzanleitung für Bauen, Testen und Freigeben. |
| `app/` | Bridge-Quelle, Version, Assets und Open-Cloud-Daten. |
| `app/assets/neueslogo.png` | Verbindliches Logo für EXE und Programmfenster. |
| `builder/` | Interner PowerShell-Builder und Parser — nicht separat starten. |
| `release/` | Einziger Ausgabeordner; hier liegt `ArenaBridge.exe` (nach dem Build). |
| `update-system/` | Neues Manifest-/Updater-System (geschützt, Kanäle deaktiviert). |
| `developer/tests/` | Offline-Regressionstests; für den normalen EXE-Build nicht nötig. |
| `developer/docs/` | Arbeitsregeln, technische Verträge und Hintergründe (`RELEASE-ABLAUF.md`). |
| `developer/ci/`, `developer/tools/` | Wartungs- und Prüfwerkzeuge. |

Es gibt in `next-update/` **keinen** `release-inbox/`-Ordner und **keinen**
`user-builds/`-Ordner. Beta-/Stable-Kanäle sind keine Build-Unterordner. Die
lokale EXE und Diagnose-Hilfsdateien liegen gemeinsam in `release/`.

## Offline-Tests (nur Wartung/Entwicklung)

Im Ordner `next-update`:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r developer\tests\requirements-test.txt
.\.venv\Scripts\python developer\tests\run_offline_tests.py
```

Der Runner führt alle `test_*.py` aus. Ein Test mit Exit-Code 77 gilt als
übersprungen (z. B. der Windows-Selbst-Update-Test auf Linux).

Für Windows-spezifische Prüfungen zusätzlich:

```powershell
.\builder\parse-gate.ps1 -Path .\app\ArenaBridge.ps1
.\builder\parse-gate.ps1 -Path .\update-system\updater\Update-Bridge.ps1
.\developer\tests\test_v762_runtime.ps1
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\developer\tests\Invoke-SelfUpdateSmoke.ps1
```

Ein Offline-Test ist keine Roblox-Studio-Live-Abnahme. Auch der lokale
EXE-Smoke-Test ersetzt nicht deinen anschließenden privaten Test der normalen
`release\ArenaBridge.exe`.
