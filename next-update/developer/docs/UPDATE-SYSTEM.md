# Selbst-Update der Bridge (Version 7.9.1)

Dieses Dokument beschreibt das einfache Update-System. Es ersetzt den alten Updater,
die Kanaele beta/stable, Guard-Lock, PROTECTED.md und die Release-Gates. Alles davon
ist entfernt.

## Bausteine

| Baustein | Aufgabe |
| --- | --- |
| `app/version.json` | Die Version (einzige Quelle). Der Builder setzt sie in die EXE. |
| `builder/Build-EXE.ps1` | Ersetzt `__ARENA_BUILD_VERSION__` im Quelltext durch die Version aus `version.json`. Dateiversion = `<Version>.0`. |
| `release/ArenaBridge.exe` | Die veroeffentlichte EXE. Eine Aenderung dieser Datei auf `main` startet den Workflow. |
| `developer/tools/publish_latest.py` | Prueft die EXE und schreibt `release/latest.json`. |
| `.github/workflows/publish-bridge.yml` | Startet das Werkzeug und committet `latest.json` zurueck. Liegt im Hauptordner, weil GitHub nur dort Workflows liest. |
| `release/latest.json` | Version, Groesse, SHA-256, Download-Adresse (auf den Commit gepinnt), Versionsnotiz. |
| `app/ArenaBridge.ps1`, Block `ARENA-UPDATE-INTEGRATION` | Die Bridge-Seite: Pruefung, Fenster, Zaehler, Papierkorb. |

## Ablauf beim Start der Bridge (nur als EXE)

1. **Aufraeumen:** Steht in `%LOCALAPPDATA%\ArenaRobloxBridge\update-reminder.json` eine
   alte EXE (`pendingCleanup`), wird sie in den Papierkorb verschoben. Nur wenn die Datei
   nicht gesperrt ist (also nicht laeuft) und nicht die eigene EXE ist.
2. **Pruefen:** `latest.json` wird geladen (Timeout 5 Sekunden, Zeitstempel gegen Caches).
   Geprueft werden: Versionsformat, Download-Adresse nur unter
   `raw.githubusercontent.com/merta-studios/arenarobloxbridge/`, SHA-256 (64 Hex-Zeichen),
   Groesse zwischen 100 KB und 64 MB.
   - Fehler oder kein Internet: Bridge startet normal (fail-open).
   - Gleiche oder niedrigere Version: Bridge startet normal, Zaehler wird zurueckgesetzt.
3. **Update verfuegbar:** Modales Fenster (quadratisch, 470 x 470) vor den Diensten.
   - "Jetzt installieren": merkt sich den Pfad der laufenden EXE als `pendingCleanup`,
     oeffnet den Standard-Browser mit der EXE-Adresse. Danach nur noch "Schliessen" (beendet die Bridge).
   - "Spaeter": `laterClicks` +1, Bridge laeuft weiter.
   - Fenster ohne Auswahl geschlossen: wie "Spaeter", ausser wenn Pflicht (dann beendet sich die Bridge).
   - Ab 5 Klicks (pro angebotener Version) gibt es kein "Spaeter" mehr. Die Bridge startet
     ohne Installation nicht weiter.
4. Der Zaehler gilt pro Version. Erscheint eine neue Version, beginnt er bei 0.

## Veroeffentlichung (Workflow)

- Trigger: Push auf `main`, der `next-update/release/ArenaBridge.exe` aendert (oder manuell).
- `publish_latest.py` prueft: Windows-x64-EXE; FileVersion der EXE = `version.json` + `.0`;
  Version hoeher als die veroeffentlichte; gleiche Version nur mit identischer Datei.
- Download-Adresse: `https://raw.githubusercontent.com/<repo>/<commit>/next-update/release/ArenaBridge.exe`.
- Der Commit von `latest.json` traegt `[skip ci]` und loest keinen weiteren Lauf aus.
- Braucht `contents: write`. Ist `main` durch Branch-Schutz gesperrt, muss der Bot dort
  schreiben duerfen (Einstellungen im GitHub-Repository pruefen).

## Was bewusst NICHT gemacht wird

- Keine Code-Signatur (Azure Artifact Signing, Zertifikate, Authenticode). Folge: Windows
  SmartScreen und Virenscanner koennen warnen oder Fehlalarme melden. Das ist akzeptiert.
- Kein Selbst-Ersetzen der laufenden EXE. Der Nutzer startet die neue EXE selbst.
- Kein Hintergrund-Download, kein Fortschrittsbalken.

## Tests

- `developer/tests/test_v900_update_flow.py` prueft unter Linux:
  Werkzeug gegen die echte EXE (inkl. Ablehnungsfaelle), Workflow-Datei, Block-Struktur
  (Adressen, Limit 5, kein Prozess-Kill, Papierkorb-Aufruf, Reihenfolge vor den Diensten),
  XAML wohlgeformt, Versionsplatzhalter, Builder, Parser-Hinweise.
- **Nicht pruefbar unter Linux** (Pflicht auf Windows):
  1. Build-EXE.bat laeuft durch; `Dateiversion` der EXE (Eigenschaften -> Details) = Version + `.0`.
  2. Start ohne Internet: Bridge startet normal.
  3. Update-Fenster erscheint (braucht eine zweite, neuere veroeffentlichte Version),
     "Spaeter" zaehlt, nach 5 Klicks kein "Spaeter" mehr.
  4. "Jetzt installieren" oeffnet den Browser; nach Start der neuen EXE liegt die alte im Papierkorb.
  5. Die gebaute EXE zeigt im Fenster und in der Diagnose die richtige Version.
