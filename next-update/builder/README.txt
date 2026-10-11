INTERNE BUILD-WERKZEUGE
=======================

Build-EXE.ps1 und parse-gate.ps1 sind interne Helfer. Starte nicht direkt diese
Dateien, sondern doppelklicke im Ordner next-update die Datei Build-EXE.bat.

Der lokale Build schreibt ausschliesslich nach ..\release\ :
  ArenaBridge.exe, ArenaBridge-Diagnose.exe, Start-Diagnostic.bat,
  Pruefsummen und release-metadata.json.

Die Version kommt aus ..\app\version.json. Der Builder setzt sie an allen Stellen
ein, wo der Platzhalter __ARENA_BUILD_VERSION__ steht, und setzt die Dateiversion
der EXE auf <Version>.0. Danach prueft der Builder den PowerShell-Parser und einen
isolierten Start der EXE.

Der Builder bettet keinen Updater mehr ein. Die Update-Logik steht direkt in
app\ArenaBridge.ps1 (Block ARENA-UPDATE-INTEGRATION). Details: ..\developer\docs\UPDATE-SYSTEM.md.

Das Windows-EXE-Symbol kommt aus ..\app\assets\ArenaBridge.ico. Das Logo
..\app\assets\neueslogo.png wird im Fenster und als Symbol verwendet.
