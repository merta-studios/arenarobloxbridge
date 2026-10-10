@echo off
setlocal
title Arena Roblox Bridge - Beta EXE Builder

echo.
echo ================================================================
echo ARENA ROBLOX BRIDGE - BETA-EXE BAUEN
echo ================================================================
echo Dies ist die einzige BAT-Datei, die du im Ordner next-update
echo ausfuehren musst. Sie baut nur die lokale Beta und veroeffentlicht
echo nichts.
echo.
echo Vor dem spaeteren Test bitte andere ArenaBridge-Fenster schliessen.
echo.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build-EXE.ps1" -Channel beta
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
echo NICHTS wurde hochgeladen. Die Release-Schritte stehen in:
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
