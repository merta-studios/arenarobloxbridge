release/ ist der EINZIGE Ausgabeordner von next-update.

- Build-EXE.bat schreibt hier den lokalen Test-Build: ArenaBridge.exe,
  ArenaBridge-Diagnose.exe, Start-Diagnostic.bat, Pruefsummen und
  release-metadata.json. Diese Dateien sind lokal und werden durch .gitignore
  geschuetzt (ausser ArenaBridge.exe, siehe .gitignore).
- Testbauten fuer den Selbst-Update-Test (Invoke-SelfUpdateSmoke.ps1) werden
  NIE hier abgelegt, sondern in einen Ordner unter %TEMP%.
- Im Repository liegt aktuell KEINE ausfuehrbare Datei. Die naechste freigegebene
  Release-Session braucht die exakt getestete ArenaBridge.exe von dir.
- Es gibt keine beta/stable-Unterordner, keinen release-inbox- und keinen user-builds-Ordner.
