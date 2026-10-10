@echo off
setlocal
set "CHANNEL=%~1"
if not defined CHANNEL set "CHANNEL=beta"
if /I not "%CHANNEL%"=="beta" if /I not "%CHANNEL%"=="stable" (
  echo Usage: Build-EXE.bat [beta^|stable]
  echo Default channel is beta.
  pause
  exit /b 2
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build-EXE.ps1" -Channel "%CHANNEL%"
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
  echo.
  echo Build failed with exit code %RESULT%.
) else (
  echo.
  echo Build finished. Review the build metadata before sharing anything.
)
pause
exit /b %RESULT%
