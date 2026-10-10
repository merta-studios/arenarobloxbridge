INTERNE BUILD-WERKZEUGE
=======================

Build-EXE.ps1 und parse-gate.ps1 sind interne Helfer. Fuer den normalen
Ablauf keine dieser Dateien direkt starten. Gehe eine Ebene nach oben und
doppelklicke Build-EXE.bat.

Der lokale Test-Build wird immer in den einzigen Ausgabeordner geschrieben:

    ..\release\ArenaBridge.exe

Die normalen Builds veroeffentlichen nichts, aendern keine Update-Manifeste
und aktualisieren keine Nutzer. Die Diagnose-EXE, Start-Diagnostic.bat,
Pruefsummen und release-metadata.json liegen als lokale Hilfsdateien im selben
release\-Ordner und duerfen nicht veroeffentlicht werden.

Das Windows-EXE-Symbol kommt aus ..\app\assets\ArenaBridge.ico; dieses ICO
wurde aus dem verbindlichen Logo ..\app\assets\neueslogo.png erzeugt. Der
Builder bindet ausserdem genau die PNG in die Bridge-Oberflaeche ein und
prueft beides im isolierten EXE-Smoke-Test.

UPDATER UND TESTBAU (7.7.0)

Der Builder bettet ..\update-system\updater\Update-Bridge.ps1 als Base64 mit fester
SHA-256 in die EXE ein. Die EXE braucht keine separate Updater-Datei. Der Parse-Gate
prueft Bridge und Updater vor dem Build.

Ein Testbau fuer den Selbst-Update-Test ist NUR ueber -TestFixtureBuild moeglich.
Er verlangt -OutputDirectory ausserhalb des Repositorys (z. B. unter %TEMP%), nur
Kanal beta, und schreibt nie nach release\. Normale Builds setzen den Testschalter
fest auf 0; dann ist der Test-Manifestpfad in der EXE nicht erreichbar.
-TestFileVersion (z. B. 7.7.1.0) setzt nur die Dateiversion eines solchen Testbaus.
Siehe developer\tests\Invoke-SelfUpdateSmoke.ps1.
