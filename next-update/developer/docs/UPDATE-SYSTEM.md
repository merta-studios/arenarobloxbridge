# Selbst-Update der Bridge (Version 7.9.2)

Dieses Dokument beschreibt das einfache Update-System. Es ersetzt den alten Updater,
die Kanäle beta/stable, Guard-Lock, PROTECTED.md und die Release-Gates. Alles davon
ist entfernt.

## Bausteine

| Baustein | Aufgabe |
| --- | --- |
| `app/version.json` | Die Version (einzige Quelle). Der Builder setzt sie in die EXE. |
| `builder/Build-EXE.ps1` | Ersetzt `__ARENA_BUILD_VERSION__` im Quelltext durch die Version aus `version.json`. Dateiversion = `<Version>.0`. |
| `release/ArenaBridge.exe` | Die veröffentlichte EXE. Eine Änderung dieser Datei auf `main` startet den Workflow. |
| `developer/tools/publish_latest.py` | Prüft die EXE und schreibt `release/latest.json`. |
| `.github/workflows/publish-bridge.yml` | Startet das Werkzeug und committet `latest.json` zurück. Liegt im Hauptordner, weil GitHub nur dort Workflows liest. |
| `release/latest.json` | Version, Größe, SHA-256, Download-Adresse (auf den Commit gepinnt), Versionsnotiz. |
| `app/ArenaBridge.ps1`, Block `ARENA-UPDATE-INTEGRATION` | Die Bridge-Seite: Prüfung, Fenster, Zähler, Papierkorb. |

## Ablauf beim Start der Bridge (nur als EXE)

1. **Aufräumen:** Steht in `%LOCALAPPDATA%\ArenaRobloxBridge\update-reminder.json` eine
   alte EXE (`pendingCleanup`), wird sie in den Papierkorb verschoben. Nur wenn die Datei
   nicht gesperrt ist (also nicht läuft) und nicht die eigene EXE ist.
2. **Prüfen:** `latest.json` wird geladen (Timeout 5 Sekunden, Zeitstempel gegen Caches).
   Geprüft werden: Versionsformat, Download-Adresse nur unter
   `raw.githubusercontent.com/merta-studios/arenarobloxbridge/`, SHA-256 (64 Hex-Zeichen),
   Größe zwischen 100 KB und 64 MB.
   - Fehler oder kein Internet: Bridge startet normal (fail-open).
   - Gleiche oder niedrigere Version: Bridge startet normal, Zähler wird zurückgesetzt.
3. **Update verfügbar:** Modales Fenster (620 x 660, ziehbar) vor den Diensten.
   Oben der Zeitstrahl "DEINE VERSION" -> "NEU FÜR DICH" mit laufender und neuer
   Version, darunter die Neuigkeiten als kurze Stichpunkte (Stichpunkt-Regel:
   siehe `docs/GANZ WICHTIG LESEN VOR JEDER BEARBEITUNG`).
   - "Jetzt installieren": merkt sich den Pfad der laufenden EXE als `pendingCleanup`,
     öffnet den Standard-Browser mit der EXE-Adresse. Danach nur noch "Schließen" (beendet die Bridge).
   - "Später": `laterClicks` +1, Bridge läuft weiter. Der Knopf zeigt keine
     Restzahl - wie oft "Später" noch möglich ist, bleibt ein Geheimnis des Programms.
   - Fenster ohne Auswahl geschlossen: wie "Später", außer wenn Pflicht (dann beendet sich die Bridge).
   - Ab 5 Klicks (pro angebotener Version) gibt es kein "Später" mehr. Die Bridge startet
     ohne Installation nicht weiter.
4. Der Zähler gilt pro Version. Erscheint eine neue Version, beginnt er bei 0.

## Veröffentlichung (Workflow)

- Trigger: Push auf `main`, der `next-update/release/ArenaBridge.exe` ändert (oder manuell).
- `publish_latest.py` prüft: Windows-x64-EXE; FileVersion der EXE = `version.json` + `.0`;
  Version höher als die veröffentlichte; gleiche Version nur mit identischer Datei.
- Download-Adresse: `https://raw.githubusercontent.com/<repo>/<commit>/next-update/release/ArenaBridge.exe`.
- Der Commit von `latest.json` trägt `[skip ci]` und löst keinen weiteren Lauf aus.
- Braucht `contents: write`. Ist `main` durch Branch-Schutz gesperrt, muss der Bot dort
  schreiben dürfen (Einstellungen im GitHub-Repository prüfen).

## Was bewusst NICHT gemacht wird

- Keine Code-Signatur (Azure Artifact Signing, Zertifikate, Authenticode). Folge: Windows
  SmartScreen und Virenscanner können warnen oder Fehlalarme melden. Das ist akzeptiert.
- Kein Selbst-Ersetzen der laufenden EXE. Der Nutzer startet die neue EXE selbst.
- Kein Hintergrund-Download, kein Fortschrittsbalken.

## Tests

- `developer/tests/test_v792_desktop_reliability.py` prüft die 7.9.2-Oberfläche
  (Stichpunkt-Regel, Zeitstrahl, "Später" ohne Zahl, weiches Ziehen/Scrollen,
  Einstellungen mit einem Knopf).
- `developer/tests/test_v900_update_flow.py` prüft unter Linux:
  Werkzeug gegen die echte EXE (inkl. Ablehnungsfälle), Workflow-Datei, Block-Struktur
  (Adressen, Limit 5, kein Prozess-Kill, Papierkorb-Aufruf, Reihenfolge vor den Diensten),
  XAML wohlgeformt, Versionsplatzhalter, Builder, Parser-Hinweise.
- **Nicht prüfbar unter Linux** (Pflicht auf Windows):
  1. Build-EXE.bat läuft durch; `Dateiversion` der EXE (Eigenschaften -> Details) = Version + `.0`.
  2. Start ohne Internet: Bridge startet normal.
  3. Update-Fenster erscheint (braucht eine zweite, neuere veröffentlichte Version),
     zeigt Zeitstrahl und Stichpunkte, "Später" zählt, nach 5 Klicks kein "Später" mehr.
  4. "Jetzt installieren" öffnet den Browser; nach Start der neuen EXE liegt die alte im Papierkorb.
  5. Die gebaute EXE zeigt im Fenster und in der Diagnose die richtige Version.
