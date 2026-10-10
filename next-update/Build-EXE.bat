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
echo EXE-Symbol als auch im Bridge-Fenster eingebettet.
echo.
echo Vor dem spaeteren Test bitte andere ArenaBridge-Fenster schliessen.
echo.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0builder\Build-EXE.ps1" -Channel beta
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" goto build_failed

echo.
echo ================================================================
echo BUILD ERFOLGREICH
echo Diese EXE lokal testen:
echo "%~dp0release\ArenaBridge.exe"
echo.
echo Wenn beim Start kein Fenster erscheint, erst andere ArenaBridge-
echo Fenster schliessen und dann die Diagnose starten:
echo "%~dp0release\Start-Diagnostic.bat"
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
