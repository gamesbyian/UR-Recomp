@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Unregister-ScheduledTask -TaskName 'UR-Recomp HP Research Missed-Schedule Fallback' -Confirm:$false -ErrorAction Stop; Write-Host 'Task removed. Local diagnostics retained under LOCALAPPDATA.'"
if errorlevel 1 (pause & exit /b 1)
pause