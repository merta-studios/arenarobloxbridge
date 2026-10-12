INTERNE BUILD-WERKZEUGE
=======================

Build-EXE.ps1 und parse-gate.ps1 sind interne Helfer. Starte nicht direkt diese
Dateien, sondern doppelklicke im Ordner next-update die Datei Build-EXE.bat.

Der lokale Build schreibt ausschließlich nach ..\release\ und erzeugt dort GENAU
EINE Programmdatei:

  ArenaRobloxBridge.exe

Dazu nur lokale Hilfsdateien (Prüfsumme, release-metadata.json), die nicht
veröffentlicht werden. Version 7.9.4: Der frühere zweite Bau
(ArenaBridge-Diagnose.exe) und der Starter Start-Diagnostic.bat entfallen. Alte
Reste aus früheren Builds (Diagnose-Dateien, *.previous-*.exe) entfernt der
Builder beim Bauen, damit im Ordner genau eine EXE liegt.

Die Version kommt aus ..\app\version.json. Der Builder setzt sie an allen Stellen
ein, wo der Platzhalter __ARENA_BUILD_VERSION__ steht, und setzt die Dateiversion
der EXE auf <Version>.0. Danach prüft der Builder den PowerShell-Parser und einen
isolierten Start der EXE (Build-Smoke-Test).

Der Builder bettet keinen Updater mehr ein. Die Update-Logik steht direkt in
app\ArenaBridge.ps1 (Block ARENA-UPDATE-INTEGRATION). Details: ..\developer\docs\UPDATE-SYSTEM.md.

Das Windows-EXE-Symbol kommt aus ..\app\assets\ArenaBridge.ico. Das Logo
..\app\assets\neueslogo.png wird im Fenster und als Symbol verwendet.

Fehlersuche ohne zweite EXE: Die Bridge schreibt ihre Startdiagnose selbst nach
%LOCALAPPDATA%\START-CHECK.txt und %LOCALAPPDATA%\ArenaRobloxBridge\bin\startup-diagnose.txt.
