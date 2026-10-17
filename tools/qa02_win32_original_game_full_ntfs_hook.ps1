# QA-only original packaged Windows executable on a genuinely full NTFS VHDX.
[CmdletBinding()]
param(
  [ValidateSet('baseline','full','restored')][string]$Stage,
  [Parameter(Mandatory=$true)][string]$VolumeRoot,
  [Parameter(Mandatory=$true)][string]$ReceiptRoot
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$package = $env:UR_QA02_PACKAGED_GAME_DIR
$route = $env:UR_QA02_GAME_ROUTE
$rom = $env:UR_QA02_PERSONAL_ROM_SOURCE
if (-not $package -or -not $route -or -not $rom) {
  throw 'QA02_GAME_FAIL_CLOSED: exact package, route or USA ROM missing'
}
$exe = Join-Path $package 'UniracersSNESRecomp.exe'
$cmd = Join-Path $package 'run-baldosa-modern.cmd'
$installedRom = Join-Path $package 'Uniracers_USA.sfc'
$exeSHA = 'b0638f31aa8fa782b5c261b9898dd82c2bf5b751768995d0460a37949f1ac59a'
$cmdSHA = 'b61d6b3836e21da6dd91dc4bcbf5cff19a85df6f73f07ee2bcd29a377fc678c3'
$romSHA = '859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478'
foreach ($check in @(
  @{file=$exe;sha=$exeSHA},
  @{file=$cmd;sha=$cmdSHA},
  @{file=$rom;sha=$romSHA})) {
  if (-not (Test-Path -LiteralPath $check.file -PathType Leaf) -or
      (Get-FileHash -LiteralPath $check.file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $check.sha) {
    throw 'QA02_GAME_FAIL_CLOSED: original bound PE/CMD/USA-ROM hash mismatch'
  }
}
if (-not (Test-Path -LiteralPath $route -PathType Leaf)) {
  throw 'QA02_GAME_FAIL_CLOSED: original route missing'
}
if (-not $VolumeRoot.EndsWith(':\') -or
    ((Get-Volume -DriveLetter $VolumeRoot.Substring(0,1)).FileSystemLabel -ne 'URQA02FULL')) {
  throw 'QA02_GAME_FAIL_CLOSED: wrong isolated NTFS volume'
}
$dataRoot = Join-Path $VolumeRoot 'Original Win32 QA Game Profile With Spaces'
New-Item -ItemType Directory -Path $ReceiptRoot -Force | Out-Null
$manifestFile = Join-Path $ReceiptRoot 'baseline-manifest.json'
$reportFile = Join-Path $ReceiptRoot ($Stage + '-result.json')
$log = Join-Path $ReceiptRoot ($Stage + '-stdout.txt')
$stderr = Join-Path $ReceiptRoot ($Stage + '-stderr.txt')
function Canonical-Manifest {
  $items = @()
  if (Test-Path -LiteralPath $dataRoot -PathType Container) {
    foreach ($f in (Get-ChildItem -LiteralPath $dataRoot -File -Recurse | Sort-Object FullName)) {
      $rel = $f.FullName.Substring($dataRoot.Length).TrimStart('\').Replace('\','/')
      if ($rel -eq 'host-state-v1.txt' -or $rel -eq 'profiles-v1.txt' -or
          $rel -match '(^|/)(save\.srm|host-profile\.txt|native-sram-checkpoint\.pending)$') {
        $items += [ordered]@{
          path = $rel
          bytes = $f.Length
          sha256 = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
      }
    }
  }
  return $items
}
$failure = ''
$exitCode = -1
$timedOut = $false
try {
  if ($Stage -eq 'baseline') {
    New-Item -ItemType Directory -Path $dataRoot -ErrorAction Stop | Out-Null
    if (Test-Path -LiteralPath $installedRom) {
      throw 'QA02_GAME_FAIL_CLOSED: original ROM-free package unexpectedly carries ROM'
    }
    Copy-Item -LiteralPath $rom -Destination $installedRom
  } elseif (-not (Test-Path -LiteralPath $installedRom)) {
    throw 'QA02_GAME_FAIL_CLOSED: temporary original USA ROM missing'
  }
  $env:UR_RECOMP_USER_DATA_ROOT = $dataRoot
  $env:UR_BALDOSA_NO_HOLD = '1'
  $env:SDL_AUDIODRIVER = 'dummy'
  $env:SDL_VIDEODRIVER = 'windows'
  Remove-Item Env:UR_BALDOSA_RECOVERY_ACTION -ErrorAction SilentlyContinue
  Remove-Item Env:UR_BALDOSA_RECOVERY_PROFILE_ID -ErrorAction SilentlyContinue
  $arguments = '/d /s /c ""' + $cmd + '" --script "' + $route + '""'
  $proc = Start-Process -FilePath 'cmd.exe' -ArgumentList $arguments -WorkingDirectory $package -PassThru -NoNewWindow -RedirectStandardOutput $log -RedirectStandardError $stderr
  if (-not $proc.WaitForExit(150000)) {
    $timedOut = $true
    & taskkill.exe /F /T /PID $proc.Id 2>$null | Out-Null
    throw 'QA02_GAME_FAIL_CLOSED: game exceeded 150 second bounded session'
  }
  $exitCode = $proc.ExitCode
  $visible = ((Get-Content -LiteralPath $log -Raw -ErrorAction SilentlyContinue) +
              (Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue))
  if ($visible.Length -gt 3000000) {
    throw 'QA02_GAME_FAIL_CLOSED: original process log exceeded bound'
  }
  $canonical = @(Canonical-Manifest)
  if ($Stage -eq 'baseline') {
    $saves = @($canonical | Where-Object { $_.path -match '(^|/)save\.srm$' -and $_.bytes -eq 8192 })
    if ($exitCode -ne 0 -or $saves.Count -lt 1) {
      throw ('QA02_GAME_FAIL_CLOSED: authentic 8192-byte initial guest save absent; exit=' + $exitCode)
    }
    $canonical | ConvertTo-Json -Depth 5 | Out-File -LiteralPath $manifestFile -Encoding utf8
  } else {
    if (-not (Test-Path -LiteralPath $manifestFile)) {
      throw 'QA02_GAME_FAIL_CLOSED: original baseline canonical source receipt missing'
    }
    $old = @(Get-Content -LiteralPath $manifestFile -Raw | ConvertFrom-Json)
    $oldJSON = ConvertTo-Json -InputObject @($old) -Depth 5 -Compress
    $newJSON = ConvertTo-Json -InputObject @($canonical) -Depth 5 -Compress
    if ($Stage -eq 'full') {
      if ($oldJSON -ne $newJSON) {
        throw 'QA02_GAME_DATA_INTEGRITY_DEFECT: real full-volume process changed canonical save bytes'
      }
      if ($exitCode -ne 8 -or $visible -notmatch 'UR-BALDOSA-SAVE-FAILED:') {
        throw ('QA02_GAME_FAILURE_PATH_NOT_PROVEN: packaged launcher exit=' + $exitCode)
      }
    }
    if ($Stage -eq 'restored' -and $exitCode -ne 0) {
      throw ('QA02_GAME_FAIL_CLOSED: fresh game after space restoration exited ' + $exitCode)
    }
  }
} catch {
  $failure = [string]$_
}
$manifestAfter = @(Canonical-Manifest)
$markerSet = @(
  'UR-BALDOSA-STARTUP-SAVE-ROOT',
  'UR-BALDOSA-STARTUP-PREFLIGHT',
  'UR-BALDOSA-STARTUP-ROM-INVALID',
  'UR-BALDOSA-STARTUP-ROM-MISSING',
  'UR-BALDOSA-FIRST-RACER',
  'UR-BALDOSA-STARTUP-PROFILE-REJECTED',
  'UR-BALDOSA-SAVE-FAILED',
  'UR-BALDOSA-SWITCH-FAILED',
  'UR_BALDOSA_NATIVE_PROFILE',
  'first frame simulated'
)
$visibleMarkers = @()
if (Get-Variable visible -ErrorAction SilentlyContinue) {
  foreach ($marker in $markerSet) {
    if ($visible.Contains($marker)) { $visibleMarkers += $marker }
  }
}
$preflightReplayExit = -1
$preflightReplayClassification = ''
if ($visibleMarkers -contains 'UR-BALDOSA-STARTUP-PREFLIGHT') {
  $preflightLine = @(Get-Content -LiteralPath $cmd |
    Where-Object { $_ -match '^powershell.exe -NoProfile -NonInteractive -Command "' })
  if ($preflightLine.Count -ne 1) {
    $preflightReplayClassification = 'original command not uniquely found'
  } elseif ($preflightLine[0] -match '^powershell.exe -NoProfile -NonInteractive -Command "(.*)"  schema = 'UR-QA02-ORIGINAL-PACKAGED-GAME-REAL-NTFS-FULL/1'
  stage = $Stage
  tested_product_pr_merge = '2073471dd6bcf2d5dbc22042e587ddee1852af8c'
  tested_PE_SHA256 = $exeSHA
  tested_CMD_SHA256 = $cmdSHA
  route_SHA256 = (Get-FileHash -LiteralPath $route -Algorithm SHA256).Hash.ToLowerInvariant()
  Windows_process_exit = $exitCode
  original_preflight_replay_exit = $preflightReplayExit
  original_preflight_replay_diagnostic = $preflightReplayClassification
  original_launcher_bounded_markers = @($visibleMarkers)
  original_canonical_file_count = @($manifestAfter).Count
  timeout = $timedOut
  canonical_receipts = @($manifestAfter)
  stdout_SHA256 = $(if (Test-Path -LiteralPath $log) { (Get-FileHash -LiteralPath $log -Algorithm SHA256).Hash.ToLowerInvariant() } else { '' })
  stderr_SHA256 = $(if (Test-Path -LiteralPath $stderr) { (Get-FileHash -LiteralPath $stderr -Algorithm SHA256).Hash.ToLowerInvariant() } else { '' })
  result = $(if ($failure) { 'FAIL' } else { 'bounded_pass' })
  failure = $failure
  human_hardware_or_power_cut = $false
  release_gate_credit = 0
}
$report | ConvertTo-Json -Depth 7 | Out-File -LiteralPath $reportFile -Encoding utf8
if ($failure) { throw $failure }
Write-Output ('QA02_ORIGINAL_GAME_STAGE_PASS ' + $Stage + ' exit=' + $exitCode)
) {
    $sourceExpression = $Matches[1]
    $env:UR_BALDOSA_PACKAGE_DIR = $package + '\'
    $env:UR_BALDOSA_ROM = $installedRom
    $replay = @( & powershell.exe -NoProfile -NonInteractive -Command $sourceExpression 2>&1 )
    $preflightReplayExit = $LASTEXITCODE
    $preflightReplayClassification = (($replay | ForEach-Object { [string]$_ }) -join ' ')
    if ($preflightReplayClassification.Length -gt 480) {
      $preflightReplayClassification = $preflightReplayClassification.Substring(0,480)
    }
    if (-not $preflightReplayClassification) {
      $preflightReplayClassification = 'no stderr emitted'
    }
  }
}
$report = [ordered]@{
  schema = 'UR-QA02-ORIGINAL-PACKAGED-GAME-REAL-NTFS-FULL/1'
  stage = $Stage
  tested_product_pr_merge = '2073471dd6bcf2d5dbc22042e587ddee1852af8c'
  tested_PE_SHA256 = $exeSHA
  tested_CMD_SHA256 = $cmdSHA
  route_SHA256 = (Get-FileHash -LiteralPath $route -Algorithm SHA256).Hash.ToLowerInvariant()
  Windows_process_exit = $exitCode
  original_launcher_bounded_markers = @($visibleMarkers)
  original_canonical_file_count = @($manifestAfter).Count
  timeout = $timedOut
  canonical_receipts = @($manifestAfter)
  stdout_SHA256 = $(if (Test-Path -LiteralPath $log) { (Get-FileHash -LiteralPath $log -Algorithm SHA256).Hash.ToLowerInvariant() } else { '' })
  stderr_SHA256 = $(if (Test-Path -LiteralPath $stderr) { (Get-FileHash -LiteralPath $stderr -Algorithm SHA256).Hash.ToLowerInvariant() } else { '' })
  result = $(if ($failure) { 'FAIL' } else { 'bounded_pass' })
  failure = $failure
  human_hardware_or_power_cut = $false
  release_gate_credit = 0
}
$report | ConvertTo-Json -Depth 7 | Out-File -LiteralPath $reportFile -Encoding utf8
if ($failure) { throw $failure }
Write-Output ('QA02_ORIGINAL_GAME_STAGE_PASS ' + $Stage + ' exit=' + $exitCode)
