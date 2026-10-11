@echo off
setlocal
title Arena Roblox Bridge - Update holen
rem Einmaliges Migrationswerkzeug fuer Installationen OHNE eingebauten Updater
rem (alles vor 7.7.0). Es laedt nur von GitHub und beendet kein Programm.
rem Ordner kann mitgegeben werden:  ArenaBridge-Update-Holen.cmd "C:\ArenaBridge"

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0ArenaBridge-Update-Holen.ps1" %*
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" goto failed

echo.
echo FERTIG. Es wurde nichts geloescht; eine alte Fassung liegt als Backup im
echo Unterordner .arena-update\backup der Installation.
goto done

:failed
echo.
echo ABBRUCH (Exit-Code %RESULT%). Deine bisherige Installation ist unveraendert.
echo Hilfe: lies die Meldung ueber dieser Zeile.

:done
echo.
pause
exit /b %RESULT%
