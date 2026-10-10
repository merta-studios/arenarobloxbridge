@echo off
setlocal
title Arena Roblox Bridge - Beta EXE Builder

echo.
echo ================================================================
echo ARENA ROBLOX BRIDGE - BETA-EXE BAUEN
echo ================================================================
echo Das ist der einzige normale Startknopf. Er baut die lokale Beta,
echo laedt keine Release-Datei hoch und aendert keine Update-Manifeste.
echo.
echo EIGENES EXE-LOGO (optional):
echo Lege deine Windows-ICO-Datei unter diesem Namen ab:
echo "%~dp0app\assets\ArenaBridge.custom.ico"
echo Wenn die Datei fehlt, wird das Standard-Logo verwendet.
echo.
echo Vor dem spaeteren Test bitte andere ArenaBridge-Fenster schliessen.
echo.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0builder\Build-EXE.ps1" -Channel beta
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" goto build_failed

echo.
echo ================================================================
echo BUILD ERFOLGREICH
echo Normale Beta-EXE - diese Datei auf dem PC testen:
echo "%~dp0user-builds\beta\ArenaBridge.exe"
echo.
echo Wenn beim Start kein Fenster erscheint, erst andere ArenaBridge-
echo Fenster schliessen und dann die Diagnose starten:
echo "%~dp0user-builds\beta\Start-Diagnostic.bat"
echo.
echo NICHTS wurde hochgeladen. Anleitung:
echo "%~dp0START-HIER.txt"
echo ================================================================
goto done

:build_failed
echo.
echo BUILD FEHLGESCHLAGEN (Exit-Code %RESULT%).
echo Lies die Fehlermeldung direkt ueber dieser Zeile.
echo Es wurde keine neue Beta veroeffentlicht.
echo Hilfe: "%~dp0START-HIER.txt"

:done
echo.
pause
exit /b %RESULT%
