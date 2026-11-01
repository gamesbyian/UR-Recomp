# Owner-run only. Installs a current-user, logon-session Windows scheduled task.
# No GitHub token, network download, privilege elevation or immediate dispatch.
$ErrorActionPreference = 'Stop'
$TaskName = 'UR-Recomp HP Research Missed-Schedule Fallback'
$InstallRoot = Join-Path $env:LOCALAPPDATA 'UR-Recomp\HPResearchFallback'
$Source = Join-Path $PSScriptRoot 'hp_research_fallback.py'
$Target = Join-Path $InstallRoot 'hp_research_fallback.py'
if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
    throw 'hp_research_fallback.py must be alongside this installer.'
}
if (-not [Environment]::Is64BitOperatingSystem) {
    throw 'This package is for the owner Windows x64 HP host only.'
}
$Python = Get-Command py.exe -ErrorAction Stop
$GitHub = Get-Command gh.exe -ErrorAction Stop
& $Python.Source -3 --version | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Python 3 via py.exe is required.' }
# The token remains in the existing GitHub CLI credential store. No new token
# is generated, printed, copied or stored by this package.
& $GitHub.Source auth status -h github.com *> $null
if ($LASTEXITCODE -ne 0) { throw 'Authenticate gh first using gh auth login.' }
New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
Copy-Item -LiteralPath $Source -Destination $Target -Force
$Action = New-ScheduledTaskAction -Execute $Python.Source -Argument ('-3 "' + $Target + '" --once --state-dir "' + $InstallRoot + '"') -WorkingDirectory $InstallRoot
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(3) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 3650)
$Principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$Settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 3) -StartWhenAvailable
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null
Write-Host 'Installed 15-minute, current-user fallback checks. GitHub cron is unchanged.'
Write-Host 'No dispatch was made by the installer. Runs only while this user remains logged on.'
Write-Host "Read last decision: $InstallRoot\last-status.json"
Write-Host "Remove task: Uninstall-HP-Research-Fallback.cmd"