release/ ist der EINZIGE Ausgabeordner von next-update.

- ArenaRobloxBridge.exe: die veroeffentlichte Bridge. Wird nur nach erfolgreichem Test
  hier abgelegt (ersetzen, nicht als zweite Datei mit Versionsnamen).
  Es gibt GENAU DIESE EINE Programmdatei (Version 7.9.4).
- latest.json: wird automatisch vom GitHub-Workflow erzeugt. Nicht von Hand aendern.
- Build-EXE.bat legt hier zusaetzlich nur lokale Hilfsdateien ab
  (ArenaRobloxBridge.exe.sha256, release-metadata.json). Die sind nur lokal
  und werden nicht veroeffentlicht.
- Alte Diagnose-Dateien aus fruehreren Versionen (ArenaBridge-Diagnose.exe,
  Start-Diagnostic.bat, *.previous-*.exe) raeumt der Builder beim Bauen weg.

Ablauf: developer\docs\RELEASE-ABLAUF.md und ..\README.md.
