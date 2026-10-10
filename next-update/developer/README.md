# Wartung und Tests (nicht für den normalen EXE-Start)

Alles Technische, was nicht zum normalen Nutzer-Klick gehört, liegt hier:

- `tests/` — Offline-Regressionsskripte, PowerShell-Checks und
  `requirements-test.txt`.
- `docs/` — Verträge, historische Hintergrundnotizen und Entwicklungsregeln.
- `ci/` — Beispiel für einen optionalen Windows-PowerShell-Parser-Workflow und
  den Generator des geprüften Open-Cloud-Katalogs.
- `tools/` — manuelle Diagnose-/Live-Abnahme-Werkzeuge.

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
oder lokaler Build löst kein öffentliches Nutzer-Update aus. Die Regeln für
Korrektur-PRs, explizite Freigabe und die spätere Nutzung des neuen
`update-system/` stehen in `../README.md` und `docs/GANZ WICHTIG LESEN VOR JEDER BEARBEITUNG`.
