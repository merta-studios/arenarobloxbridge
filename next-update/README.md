# Arena Roblox Bridge — Beta bauen und testen

## Wenn du nur die EXE starten willst

1. Öffne den Ordner **`next-update`**.
2. Doppelklicke **`Build-EXE.bat`** — das ist der einzige normale Startknopf.
3. Warte auf **`BUILD ERFOLGREICH`**. Die fertige Test-App liegt danach genau hier:

   ```text
   next-update\user-builds\beta\ArenaBridge.exe
   ```

   Die BAT und der Builder zeigen zusätzlich den vollständigen Pfad auf deinem
   PC. Starte anschließend diese `ArenaBridge.exe` per Doppelklick. Schließe
   vorher andere bereits laufende ArenaBridge-Fenster.

4. Falls Windows beim Start keinen Bridge-Bildschirm zeigt, starte nach dem
   Schließen anderer Bridge-Fenster:

   ```text
   next-update\user-builds\beta\Start-Diagnostic.bat
   ```

   Das Konsolenfenster bleibt offen. Die Diagnose nennt auch die Datei
   `%LOCALAPPDATA%\START-CHECK.txt`.

**Nicht** `builder\Build-EXE.ps1` oder den vorbereiteten Updater starten. Der
Build lädt nichts hoch und ändert keine Update-Manifeste.

## Eigenes Logo für die EXE

Du musst das mitgelieferte Logo nicht überschreiben. Kopiere dein eigenes
Windows-Symbol als **`ArenaBridge.custom.ico`** hierhin:

```text
next-update\app\assets\ArenaBridge.custom.ico
```

Beim nächsten Doppelklick auf `Build-EXE.bat` wird diese Datei automatisch
statt `ArenaBridge.ico` in die EXE eingebaut. Der Builder prüft, ob es eine
gültige `.ico`-Datei ist. Eine PNG- oder JPG-Datei funktioniert nicht direkt;
wandle sie zuerst in ein Windows-ICO um. Empfohlen sind transparente Icons mit
mehreren Größen bis 256 × 256 Pixel. Die eigene `ArenaBridge.custom.ico` wird
lokal ignoriert und nicht in Git aufgenommen. Lösche sie, um wieder das
mitgelieferte Standard-Logo zu verwenden.

Für einen einmaligen Build mit einer ICO-Datei an einem anderen Ort kann der
interne Builder auch direkt aufgerufen werden:

```powershell
.\builder\Build-EXE.ps1 -Channel beta -CustomIconPath "C:\Pfad\MeinLogo.ico"
```

Im normalen Ablauf genügt die `ArenaBridge.custom.ico` neben dem Standard-Icon.

## Was der Build prüft und erzeugt

- Voraussetzungen: **64-Bit-Windows**, Windows PowerShell 5.1, WPF/.NET
  Framework und beim ersten Build eine Internetverbindung für das
  `ps2exe`-Modul. Eine Administratorinstallation ist nicht nötig.
- Vor der Kompilierung prüft der echte Windows-PowerShell-Parser
  `app\ArenaBridge.ps1` und die eingebettete Build-Kopie.
- Vor der Ablage startet der Builder die neu kompilierte EXE im isolierten
  Smoke-Test. Er prüft den ausführbaren Ordnerpfad (der in einer EXE statt
  eines Skriptpfads verwendet werden muss), x64, STA/WPF und das eingebettete
  Titelbild. Dabei werden weder Roblox Studio noch Bridge-Server, Netzwerk,
  Nutzereinstellungen oder Updater gestartet.
- Der behobene Startfehler entstand, weil das kompilierte Programm keinen
  `$script:ScriptPath` besitzt, beim Einrichten von `AppFolder` aber trotzdem
  `Split-Path` mit diesem leeren Wert aufgerufen wurde. Die Bridge nimmt nun
  den Verzeichnisnamen der gestarteten EXE; derselbe Resolver wird im
  Build-Smoke-Test geprüft.
- Nach erfolgreichem Build liegen unter `user-builds\beta\` die normale
  `ArenaBridge.exe`, eine separate `ArenaBridge-Diagnose.exe`,
  `Start-Diagnostic.bat`, Prüfsummen und lokale Build-Metadaten. Für einen
  späteren öffentlichen Release ist ausschließlich die normale
  `ArenaBridge.exe` vorgesehen.

Die EXE ist unsigniert. Falls SmartScreen warnt, starte sie nur, wenn du dieser
lokalen Build-Quelle vertraust.

## Ordnerübersicht

| Pfad | Zweck |
|---|---|
| `Build-EXE.bat` | Einziger Klick zum lokalen Beta-Build. |
| `START-HIER.txt` | Kurzanleitung für Bauen, Pfad und Start. |
| `app\` | Programmquelle, Version, Startbild, EXE-Icons und Open-Cloud-Daten. |
| `builder\` | Interner PowerShell-Builder und Parser — nicht separat starten. |
| `user-builds\beta\` | Hier erscheint nach dem Build die zu testende EXE. |
| `user-builds\stable\` | Für den normalen Ablauf gesperrt; erst nach Beta-Test und Freigabe. |
| `update-system\` | Vorbereitete Channel-Manifeste und separater, noch nicht integrierter Updater. |
| `developer\tests\` | Offline-Regressionstests und ihre Python-Anforderungen. Für den EXE-Build nicht nötig. |
| `developer\docs\` | Entwicklungsverträge und Hintergrunddokumente. |
| `developer\ci\`, `developer\tools\` | Wartungs-/Prüfwerkzeuge, nicht Teil des normalen Builds. |
| `release-inbox\` | Optionaler lokaler Prüfbereich; kein Commit- oder Upload-Ort. |

So ist der heruntergeladene Ordner absichtlich geteilt: **oben liegen nur
Startanleitung, BAT und die wenigen Arbeitsbereiche; technische Tests,
Verträge und Werkzeuge sind unter `developer` gesammelt.**

## Beta zuerst — nichts automatisch veröffentlichen

Die vorbereitete Bridge ist **Version 7.6.4**. Der normale Doppelklick baut
`7.6.4-beta.1` lokal. Hier in der Sandbox wurde keine Windows-EXE gebaut oder
veröffentlicht.

Die Channel-Dateien in `update-system\channels\` bleiben `enabled: false` und
enthalten keine Download-URL oder Hash. Der separate Updater in
`update-system\updater\` ist noch nicht in die laufende
`app\ArenaBridge.ps1` integriert und wird von `Build-EXE.bat` nicht gestartet.
Der alte Updater und die alte Struktur im Hauptordner des Repositorys bleiben
unangetastet.

Erst nach deinem Windows-Test und deiner ausdrücklichen Freigabe darf die
normale `ArenaBridge.exe` als einziges App-Artefakt an einen GitHub-Release im
Repository `merta-studios/arenarobloxbridge` angehängt werden. Keine EXE,
Diagnose-Datei, persönliche ICO-Datei oder lokalen Build-Metadaten in Git
committen; Stable nicht vor dem Beta-Test aktivieren.

## Offline-Tests (nur Wartung/Entwicklung)

Im Ordner `next-update`:

```powershell
python -m pip install -r developer\tests\requirements-test.txt
python developer\tests\run_offline_tests.py
```

Der Runner führt die Offline-Regressionsskripte aus. Für Windows-spezifische
Parser-/Open-Cloud-Prüfungen:

```powershell
.\builder\parse-gate.ps1 -Path .\app\ArenaBridge.ps1
.\developer\tests\test_v762_runtime.ps1
```

Ein erfolgreicher Offline-Test ist keine Roblox-Studio-Live-Abnahme. Auch der
Build-Smoke-Test ersetzt nicht deinen anschließenden Test der normalen Beta-EXE.
