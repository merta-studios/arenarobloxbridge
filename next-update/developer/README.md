# Wartung und Tests (nicht für den normalen EXE-Start)

Alles Technische, was nicht zum normalen Nutzer-Klick gehört, liegt hier:

- `tests/` — Offline-Regressionsskripte, PowerShell-Checks und
  `requirements-test.txt`.
- `docs/` — Verträge, historische Hintergrundnotizen und Entwicklungsregeln.
  Verbindlich: `docs/GANZ WICHTIG LESEN VOR JEDER BEARBEITUNG` (Stand 7.9.2) —
  dort steht auch die Stichpunkt-Regel für die Nutzer-Notizen.
- `ci/` — Beispiel für einen optionalen Windows-PowerShell-Parser-Workflow und
  den Generator des geprüften Open-Cloud-Katalogs.
- `tools/publish_latest.py` liegt unter `tools/` und erzeugt `release/latest.json` (vom Workflow aufgerufen).
- `tools/` — manuelle Diagnose-/Live-Abnahme-Werkzeuge. Dazu das Umlaut-Werkzeug
  `tools/german_umlauts.py` (prüft/überführt `ae/oe/ue/ss` in echte Umlaute;
  ohne `--write` nur ein Zählbericht) mit seinem Tokenizer `tools/ps_text_tokens.py`.

## Offline-Tests starten

Vom Ordner `next-update` aus:

```powershell
python -m pip install -r developer\tests\requirements-test.txt
python developer\tests\run_offline_tests.py
```

Die Tests bauen oder starten keine EXE. Für Windows PowerShell 5.1 zusätzlich:

```powershell
.\builder\parse-gate.ps1 -Path .\app\ArenaBridge.ps1
.\developer\tests\test_v762_runtime.ps1
```

Zum bloßen Bauen/Testen des privaten Kandidaten brauchst du den Ordner `developer` nicht:

```text
Build-EXE.bat
```

Der Build-Ausgang liegt im einzigen Ordner `next-update/release/`. Ein Merge
oder lokaler Build löst kein öffentliches Nutzer-Update aus. Ablauf des
Selbst-Updates: `../README.md`. Technik und Tests: `docs/UPDATE-SYSTEM.md`.
