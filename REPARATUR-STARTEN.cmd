@echo off
REM ============================================================================
REM REPARATUR-STARTEN.cmd  --  Startet REPARATUR-7.3.1.ps1 auf Windows PowerShell
REM ============================================================================
REM Doppelklick auf DIESE Datei repariert eine bereits installierte 7.3.0, die
REM wegen Parse-Fehler gar nicht startet. Es wird Windows PowerShell 5.1
REM benutzt (die Engine, auf der der Fehler auftritt). Die Arbeit erledigt
REM REPARATUR-7.3.1.ps1 im selben Ordner.
REM
REM Nach der Reparatur START-BRIDGE.cmd starten - Fenster oeffnet sich.
REM ============================================================================
setlocal
cd /d "%~dp0"

echo.
echo ============================================================================
echo  Arena Roblox Bridge 7.3.1 - REPARATUR (Parser-Reparatur fuer 7.3.0)
echo ============================================================================
echo.

REM Sicherstellen, dass das Reparatur-Skript da ist
if not exist "%~dp0REPARATUR-7.3.1.ps1" (
    echo FEHLER: REPARATUR-7.3.1.ps1 nicht gefunden im selben Ordner.
    echo        Bitte beide Dateien (REPARATUR-STARTEN.cmd und REPARATUR-7.3.1.ps1)
    echo        in denselben Ordner legen (kann ein beliebiger Ordner sein - die
    echo        Zieldatei wird automatisch unter %%LOCALAPPDATA%% gesucht).
    pause
    exit /b 2
)

REM Starte mit Windows PowerShell 5.1 (nicht pwsh) - das ist die Engine mit dem
REM Parse-Verhalten. ExecutionPolicy Bypass, damit das Skript laeuft, ohne die
REM System-Policy zu veraendern.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0REPARATUR-7.3.1.ps1"
set "EL=%ERRORLEVEL%"

echo.
if "%EL%"=="0" (
    echo REPARATUR abgeschlossen (ExitCode %EL%).
    echo Jetzt START-BRIDGE.cmd starten.
) else (
    echo REPARATUR fehlgeschlagen oder abgebrochen (ExitCode %EL%).
    echo Die Sicherung ArenaBridge.ps1.bak-731 liegt im App-Ordner.
)
echo.
pause
endlocal
