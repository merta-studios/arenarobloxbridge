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
