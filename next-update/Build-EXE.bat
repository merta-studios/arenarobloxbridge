@echo off
setlocal
title Arena Roblox Bridge - lokaler Test-Build

echo.
echo ================================================================
echo ARENA ROBLOX BRIDGE - LOKALEN TEST-BUILD BAUEN
echo ================================================================
echo Dies baut nur deine private Test-EXE. Es wird nichts veroeffentlicht,
echo kein Nutzer aktualisiert und kein Update-Manifest geaendert.
echo.
echo Das neue Logo aus app\assets\neueslogo.png wird sowohl als
echo EXE-Symbol als auch im Bridge-Fenster eingebettet, und das Bild
echo app\assets\liquidglasbackground.png wird der Fensterhintergrund.
echo.
echo Ergebnis: GENAU EINE Datei mit dem Programm -
echo   release\ArenaRobloxBridge.exe
echo Es gibt kein zweites Programm und keine Diagnose-EXE mehr.
echo.
echo Vor dem spaeteren Test bitte andere ArenaBridge-Fenster schliessen.
echo.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0builder\Build-EXE.ps1" -Channel stable -NonInteractive
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" goto build_failed

echo.
echo ================================================================
echo BUILD ERFOLGREICH
echo Genau diese eine Datei lokal testen:
echo "%~dp0release\ArenaRobloxBridge.exe"
echo.
echo Wenn beim Start kein Fenster erscheint, erst alle anderen
echo ArenaBridge-Fenster schliessen und die Datei erneut starten.
echo Hinweise stehen dann hier:
echo   "%LOCALAPPDATA%\START-CHECK.txt"
echo   "%LOCALAPPDATA%\ArenaRobloxBridge\bin\startup-diagnose.txt"
echo.
echo Dieser private Test-Build wurde NICHT hochgeladen.
echo Anleitung: "%~dp0START-HIER.txt"
echo ================================================================
goto done

:build_failed
echo.
echo BUILD FEHLGESCHLAGEN (Exit-Code %RESULT%).
echo Lies die Fehlermeldung direkt ueber dieser Zeile.
echo Es wurde keine neue Version veroeffentlicht.
echo Hilfe: "%~dp0START-HIER.txt"

:done
echo.
pause
exit /b %RESULT%
