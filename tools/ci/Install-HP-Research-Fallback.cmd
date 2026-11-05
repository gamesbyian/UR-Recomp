@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-HP-Research-Fallback.ps1"
if errorlevel 1 (
  echo.
  echo Installation failed; no GitHub research was dispatched.
  pause
  exit /b 1
)
echo.
pause