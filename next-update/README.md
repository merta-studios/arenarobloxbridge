# Arena Roblox Bridge — neuer Update- und Testablauf

> **Arbeite nur in `next-update/`.** Der alte Bereich im Repository-Hauptordner
> bleibt unverändert und wird für diesen Ablauf vollständig ignoriert.

## Lokal bauen und testen

1. Eine Änderung beschreibst du im Chat. Die KI bearbeitet ausschließlich
   `next-update/`, prüft die passenden Tests und erstellt einen Pull Request.
   **Der PR ist nur eine Code-Änderung — keine Veröffentlichung.** Das Stable-
   Manifest bleibt deaktiviert und es wird keine EXE an Nutzer verteilt.
2. Du mergst den PR und lädst danach das Repository-ZIP herunter.
3. Öffne darin `next-update` und doppelklicke **`Build-EXE.bat`**. Das ist der
   einzige normale Build-Knopf. Der lokale Test-Build braucht 64-Bit-Windows,
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

Das Build-Skript prüft zuerst den Windows-PowerShell-Parser. Danach startet es
beide EXE-Kopien in einem isolierten Smoke-Test; dabei werden x64, STA/WPF,
der EXE-Ordnerpfad, das Startbild **und das eingebettete `neueslogo.png`**
geprüft. Dieser Smoke-Test startet weder Roblox Studio noch den Bridge-Server
oder einen Updater. In dieser Sandbox wurde keine Windows-EXE gebaut.

## Wenn der Test fehlschlägt oder dir die Änderung nicht gefällt

- Lade die Test-EXE **nicht** in das Repository hoch und fordere keine
  öffentliche Freigabe an.
- Starte einfach einen neuen Chat und beschreibe, was korrigiert werden soll.
  Die KI erstellt einen neuen PR in `next-update/`; nach dessen Merge lädst du
  wieder ein ZIP herunter, baust erneut und testest erneut.
- Frühere Test-PRs oder lokale Builds lösen kein Update bei Nutzern aus. Die
  Channel-Manifeste werden in dieser Phase nicht aktiviert. Nutzer merken von
  deinen privaten Tests nichts.

## Wenn du den getesteten Stand ausdrücklich freigibst

1. Schreibe **im Chat, in dem der Änderungs-PR bereits gemergt wurde**, dass
   dir der Test gefällt und du die Version für alle freigibst.
2. In genau diesem Chat darf die KI **nicht veröffentlichen und nichts weiter
   erklären**. Sie muss als Antwort ausschließlich **eine kopierbare Textbox
   (einen Codeblock) mit einem vollständigen Prompt für die nächste Session**
   ausgeben. Der Prompt nennt die gemergte Änderung/Version, fordert die
   nächste Session auf, ausschließlich `next-update/` und das neue
   `update-system/` zu verwenden, und verbietet ausdrücklich das alte System.
3. In der Release-Session wird die **bereits getestete** EXE verwendet — keine
   unbemerkte Neu-Kompilierung und kein anderer Build. Nach deiner ausdrücklichen
   Freigabe kommt genau diese Datei an diesen einen Repository-Pfad:

   ```text
   next-update/release/ArenaBridge.exe
   ```

   Wenn sie der Release-Session nicht vorliegt, muss die KI dich bitten, genau
   diese getestete Datei dort hochzuladen oder anzuhängen. Sie darf nicht raten
   oder einen ungeprüften Ersatz verwenden.
4. Die öffentliche Auslieferung läuft ausschließlich über
   `next-update/update-system/`. **Wichtige Freigabeschranke:** Der neue
   `Update-Bridge.ps1` ist aktuell noch nicht in die Bridge-EXE integriert.
   Die Release-Session muss die Integration, den echten Start-/Update-Pfad und
   einen Bootstrap für bereits installierte Versionen zuerst prüfen und auf
   Windows absichern. Solange das nicht funktioniert, bleibt Stable deaktiviert
   und es darf nicht behauptet werden, alle Nutzer würden automatisch
   aktualisiert.
5. Erst nachdem Integration, Bootstrap, getestete EXE, Versionsnummer,
   Dateigröße und SHA-256 stimmen, darf die Release-Session den Stable-Kanal
   über das neue System vorbereiten. Das Stable-Manifest muss auf genau die
   geprüfte `release/ArenaBridge.exe` im Repository zeigen. Erforderliche
   Quell-/Manifeständerungen gehen wieder als PR durch den Merge-Prozess. Kein
   Update darf allein durch einen normalen Code-PR oder einen privaten Build
   aktiviert werden.

Damit gilt die klare Trennung: **Merge + ZIP + lokaler Build = Test.** Nur die
spätere ausdrückliche Freigabe und der abgeschlossene Release-Schritt über den
neuen Updater können ein Update für Nutzer bereitstellen.

## Ordnerübersicht

| Pfad | Zweck |
|---|---|
| `Build-EXE.bat` | Einziger normaler Klick für den lokalen Test-Build. |
| `START-HIER.txt` | Kurzanleitung für Bauen, Testen und Freigeben. |
| `app/` | Bridge-Quelle, Version, Assets und Open-Cloud-Daten. |
| `app/assets/neueslogo.png` | Verbindliches Logo für EXE und Programmfenster. |
| `builder/` | Interner PowerShell-Builder und Parser — nicht separat starten. |
| `release/` | Einziger Ausgabeordner; hier liegt `ArenaBridge.exe`. |
| `update-system/` | Neues Manifest-/Updater-System für eine spätere, freigegebene Verteilung. |
| `developer/tests/` | Offline-Regressionstests; für den normalen EXE-Build nicht nötig. |
| `developer/docs/` | Arbeitsregeln, technische Verträge und Hintergründe. |
| `developer/ci/`, `developer/tools/` | Wartungs- und Prüfwerkzeuge. |

Es gibt in `next-update/` **keinen** `release-inbox/`-Ordner und **keinen**
`user-builds/`-Ordner. Beta-/Stable-Kanäle sind keine Build-Unterordner. Die
lokale EXE und Diagnose-Hilfsdateien liegen gemeinsam in `release/`.

## Offline-Tests (nur Wartung/Entwicklung)

Im Ordner `next-update`:

```powershell
python -m pip install -r developer\tests\requirements-test.txt
python developer\tests\run_offline_tests.py
```

Für Windows-spezifische Parser-/Open-Cloud-Prüfungen zusätzlich:

```powershell
.\builder\parse-gate.ps1 -Path .\app\ArenaBridge.ps1
.\developer\tests\test_v762_runtime.ps1
```

Ein Offline-Test ist keine Roblox-Studio-Live-Abnahme. Auch der lokale
EXE-Smoke-Test ersetzt nicht deinen anschließenden privaten Test der normalen
`release\ArenaBridge.exe`.
