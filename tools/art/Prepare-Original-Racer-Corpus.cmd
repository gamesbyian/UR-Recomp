@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem Owner-only local ROM source export; this launcher never downloads a ROM.
rem Keep this CMD beside Prepare-Original-Racer-Corpus.ps1 in tools\art.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Prepare-Original-Racer-Corpus.ps1" %*
set "exitcode=%ERRORLEVEL%"
echo.
if not "%exitcode%"=="0" (
  echo Private source export was not completed. No evidence should be submitted.
) else (
  echo Private source export finished. The source images remain on this PC only.
)
pause
exit /b %exitcode%
