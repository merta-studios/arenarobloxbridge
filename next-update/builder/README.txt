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

Viren-Fehlalarme (seit 8.0.0): Der normale Bau ist unsigniert, und genau das
meldet VirusTotal regelmäßig (beim 7.9.5-Build 15 von 58 Engines) - ein bekanntes
Fehlalarm-Muster für PowerShell-Programme, die mit ps2exe in eine EXE gepackt
werden. Auf Wunsch signiert der Builder die fertige EXE (Authenticode):

  -SignCertificatePath <pfx> | -SignCertificateThumbprint <40 Hex-Zeichen>
  -SignCertificatePassword <passwort>   (sonst ARENABRIDGE_SIGN_PFX_PASSWORD)
  -SignTimestampUrl <adresse>            (leer lassen = ohne Zeitstempel)

Statt der Parameter dürfen auch die Umgebungsvariablen ARENABRIDGE_SIGN_PFX und
ARENABRIDGE_SIGN_PFX_PASSWORD gesetzt werden - dann genügt weiter der gewohnte
Doppelklick auf Build-EXE.bat. Signiert wird VOR dem Smoke-Test; ist die
Signatur nicht gültig, bricht der Bau ab und es wird nichts eingesetzt.

Ursache, Meldewege der Scanner-Hersteller und ein fertiger Meldetext:
..\developer\docs\FALSE-POSITIVE-MELDUNG.md.

Der Builder bettet keinen Updater mehr ein. Die Update-Logik steht direkt in
app\ArenaBridge.ps1 (Block ARENA-UPDATE-INTEGRATION). Details: ..\developer\docs\UPDATE-SYSTEM.md.

Das Windows-EXE-Symbol kommt aus ..\app\assets\ArenaBridge.ico. Das Logo
..\app\assets\neueslogo.png wird im Fenster und als Symbol verwendet.

Fehlersuche ohne zweite EXE: Die Bridge schreibt ihre Startdiagnose selbst nach
%LOCALAPPDATA%\START-CHECK.txt und %LOCALAPPDATA%\ArenaRobloxBridge\bin\startup-diagnose.txt.

CI-Test-Build: Der GitHub-Actions-Workflow (exe-builder.yml) baut Test-Stände
automatisch mit -Channel beta nach ..\beta-release\ArenaRobloxBridge.exe, ohne
..\release\ArenaRobloxBridge.exe oder ..\release\latest.json zu verändern.


