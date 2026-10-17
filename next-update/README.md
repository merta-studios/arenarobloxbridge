# Arena Roblox Bridge — 8.0.5 vorbereitet

> **8.0.5 ist als Quellstand vorbereitet, nicht veröffentlicht.** Terrain-Werkzeuge,
> Kamera-Selbstheilung, GUI-Design 3.0 mit 40 Stilen und 18 Widgets sowie eine
> selbstheilende Desktop-Verknüpfung. Alles aus 8.0.3 bleibt erhalten.
> Offline-Prüfungen ersetzen keinen Windows-/Studio-Test. EXE und
> `release/latest.json` wurden nicht verändert.
>
> **Arbeite nur in `next-update/`.** Der alte Bereich im Repository-Hauptordner
> bleibt unverändert. Abnahme und bekannte Grenzen:
> [8.0.5-Checkliste](developer/docs/V8_0_5_ACCEPTANCE.md).

## Der Ablauf in einem Satz

Du änderst etwas in einer Session → „mach Pull Request“ → Link öffnen → mergen →
ZIP laden → `Build-EXE.bat` → testen → bei gutem Stand die EXE nach
`next-update/release/ArenaRobloxBridge.exe` legen → der Workflow macht den Rest.

## Zwei feste Regeln ab 7.9.4

- **Genau eine Programmdatei:** Der Builder erzeugt nur noch
  `next-update\release\ArenaRobloxBridge.exe`. Es gibt keine zweite EXE
  (früher `ArenaBridge-Diagnose.exe`) und kein `Start-Diagnostic.bat` mehr.
  Alte Reste und Sicherungskopien räumt der Builder aus `release\` weg.
- **Installation über die Download-Seite:** Die Bridge prüft Updates weiter im
  Repository (`latest.json`). Wer das Update wirklich installieren will, bekommt
  aber diese Seite im Browser: <https://arena-rblx-bridge.netlify.app/>.
  Dort liegt immer die neueste `ArenaRobloxBridge.exe`.

## Die Schritte im Detail

1. **Änderung im Chat beschreiben.** Die KI arbeitet nur in `next-update/` auf dem
   Session-Branch.
2. **„mach Pull Request“** sagen. Du bekommst einen Link (PR = Vorschlag zum
   Übernehmen der Änderung). Du prüfst und klickst **Merge** (Übernehmen in `main`).
3. **ZIP holen:** Auf GitHub beim Code-Button **Download ZIP** wählen. Entpacken.
4. **Bauen:** Im Ordner `next-update` doppelklicken auf **`Build-EXE.bat`**.
   Die fertige Test-EXE liegt danach in `next-update\release\ArenaRobloxBridge.exe`.
5. **Testen:** Diese EXE auf deinem PC starten (andere ArenaBridge-Fenster vorher
   schließen).
### Regel für die Neuigkeiten (Stichpunkt-Regel, dauerhaft)

Die Notizen zu einer Version stehen in `app/version.json`. Sie sind **kurze
Stichpunkte im Ton für die Nutzer**: `notes[0]` beginnt mit `• <Version> — TITEL:`,
danach folgen mindestens vier Stichpunkte (je `• ` davor, höchstens 240 Zeichen),
die ganze Notiz bleibt unter 600 Zeichen. Kurz feiern, was die Nutzer bekommen —
kein Owner-Fließtext, keine Datei-Labels. Das Update-Fenster und der
„Update installiert“-Hinweis zeigen diese Stichpunkte einzeln; der
„Später“-Knopf zeigt nie eine Restzahl (das bleibt ein Geheimnis des Programms).
`developer/tests/test_v792_desktop_reliability.py` prüft die Regel mit.

6. **Veröffentlichen (nur bei gutem Stand):** Die getestete
   `ArenaRobloxBridge.exe` in den GitHub-Ordner `next-update/release/` hochladen und
   auf `main` speichern (ersetzen). Dabei muss die Version in der EXE neuer sein
   als die bisher veröffentlichte — hier ist 7.9.5 als Testversion vorbereitet.
   Es wird **nur diese eine Datei** hochgeladen (keine Diagnose-Dateien, keine
   Metadaten).
7. **Der Workflow läuft automatisch** (GitHub-Reiter **Actions**, Lauf „Bridge-Version
   veröffentlichen“). Er prüft die EXE, berechnet Prüfsumme und Größe und schreibt
   `next-update/release/latest.json`. Ab da sehen alle Bridges beim nächsten Start
   das Update.

## Fachbegriffe kurz erklärt

- **PR (Pull Request):** Vorschlag, eine Änderung in `main` zu übernehmen.
- **Merge:** Übernehmen des PR in `main`.
- **Branch:** Eigene Arbeitskopie im Repository (diese Session: `arena/96da4d4b-arenarobloxbridge`).
- **Workflow / Action:** Automatischer Ablauf bei GitHub. Läuft nach Änderungen auf `main`.
- **latest.json:** Kleine Datei mit der neuesten Version, Größe, Prüfsumme und Download-Adresse.
- **Prüfsumme (SHA-256):** Fingerabdruck einer Datei. Stimmt er nicht, ist die Datei nicht die richtige.
- **Commit-SHA:** Eindeutige Nummer eines Speicherstands. Die Download-Adresse zeigt darauf,
  damit immer genau diese EXE geladen wird.

## Ordner-Übersicht

| Ordner / Datei | Inhalt |
| --- | --- |
| `app/` | Quellcode der Bridge (`ArenaBridge.ps1`) und `version.json` (Versionsquelle) |
| `builder/` | Bau-Werkzeuge (`Build-EXE.ps1`), von `Build-EXE.bat` aufgerufen |
| `release/` | **Einziger Ausgabeordner.** Genau eine Programmdatei: `ArenaRobloxBridge.exe`, dazu `latest.json` (automatisch) |
| `website/` | Quelle der Download-Website für Netlify — live unter <https://arena-rblx-bridge.netlify.app/> |
| `developer/` | Tests, Doku, Werkzeuge (`tools/publish_latest.py` für den Workflow) |
| `../.github/workflows/publish-bridge.yml` | Der Workflow, der `latest.json` erzeugt |

## Offline-Tests

Vom Ordner `next-update` aus:

```text
python -m pip install -r developer\tests\requirements-test.txt
python developer\tests\run_offline_tests.py
```

Die Tests bauen keine EXE und starten keine Bridge. Was sie nicht können
(WPF-Fenster, Papierkorb, Windows-PowerShell), steht in
`developer/docs/UPDATE-SYSTEM.md` und muss auf deinem Windows-PC geprüft werden.

Weitere Doku: `developer/docs/RELEASE-ABLAUF.md` (Ablauf), `developer/docs/UPDATE-SYSTEM.md` (Technik).
