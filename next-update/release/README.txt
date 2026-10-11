release/ ist der EINZIGE Ausgabeordner von next-update.

- ArenaBridge.exe: die veroeffentlichte Bridge. Wird nur nach erfolgreichem Test
  hier abgelegt (ersetzen, nicht als zweite Datei mit Versionsnamen).
- latest.json: wird automatisch vom GitHub-Workflow erzeugt. Nicht von Hand aendern.
- Build-EXE.bat legt hier zusaetzlich lokale Hilfsdateien ab (Diagnose-EXE,
  Start-Diagnostic.bat, Pruefsummen, release-metadata.json). Die sind nur lokal
  und werden nicht veroeffentlicht.

Ablauf: developer\docs\RELEASE-ABLAUF.md und ..\README.md.
