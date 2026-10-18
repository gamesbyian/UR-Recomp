# Original Windows QA-only fault apparatus, never product acceptance.
# Create a brand-new isolated NTFS VHDX on a disposable GitHub Actions runner,
# exhaust actual free bytes and require a second real process to see Win32 112.
[CmdletBinding()]
param(
  [ValidateRange(96,256)][int]$MaximumMegabytes = 128,
  [ValidatePattern('^[A-Z]$')][string]$DriveLetter = 'W',
  [Parameter(Mandatory=$true)][string]$Output,
  [string]$ProductHook = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows' -or
    -not $env:RUNNER_TEMP -or -not $env:GITHUB_SHA) {
  throw 'FAIL_CLOSED: require disposable hosted Windows Actions runner'
}
$drive = $DriveLetter + ':\'
if (Test-Path -LiteralPath $drive) { throw 'FAIL_CLOSED: drive letter already exists' }
$root = Join-Path $env:RUNNER_TEMP 'qa02-ephemeral-NTFS-VHDX-only'
if (Test-Path -LiteralPath $root) { throw 'FAIL_CLOSED: transient QA root already exists' }
New-Item -ItemType Directory -Path $root | Out-Null
$disk = Join-Path $root 'ur-qa02-only.vhdx'
$diskpartScript = Join-Path $root 'diskpart.txt'
$attached = $false
$filled = $false
$total = [long]0
if ($ProductHook -and (-not (Test-Path -LiteralPath $ProductHook -PathType Leaf))) {
  throw 'FAIL_CLOSED: optional independent game callback missing'
}
function Invoke-OnlyQAHook([string]$stage) {
  if ($ProductHook) {
    $receiptDir = Join-Path $env:RUNNER_TEMP 'qa02-game-on-real-full-volume'
    New-Item -ItemType Directory -Path $receiptDir -Force | Out-Null
    & $ProductHook -Stage $stage -VolumeRoot $drive -ReceiptRoot $receiptDir
    if (-not $?) { throw ("FAIL_CLOSED: original game QA hook stage failed: " + $stage) }
  }
}

function Invoke-OnlyThisVHD([string[]]$instructions) {
  [IO.File]::WriteAllLines($diskpartScript, $instructions, [Text.Encoding]::ASCII)
  $out = (& diskpart.exe /s $diskpartScript 2>&1 | Out-String)
  if ($LASTEXITCODE -ne 0 -or
      $out -match 'DiskPart has encountered an error' -or
      $out -match 'The arguments specified for this command are not valid') {
    throw ('FAIL_CLOSED: selected isolated VHD diskpart failure: ' + $out)
  }
}
try {
  $quotedDisk = '"' + $disk + '"'
  Invoke-OnlyThisVHD @(
    ('create vdisk file=' + $quotedDisk +
     " maximum=$MaximumMegabytes type=expandable"),
    ('select vdisk file=' + $quotedDisk),
    'attach vdisk',
    'create partition primary',
    'format fs=ntfs quick label="URQA02FULL"',
    ('assign letter=' + $DriveLetter)
  )
  $attached = $true
  Start-Sleep -Seconds 3
  $vol = Get-Volume -DriveLetter $DriveLetter -ErrorAction Stop
  if ($vol.FileSystem -ne 'NTFS' -or $vol.FileSystemLabel -ne 'URQA02FULL' -or
      $vol.Size -lt 32MB -or $vol.Size -gt 300MB) {
    throw 'FAIL_CLOSED: isolated NTFS identity or capacity incorrect'
  }
  $startFree = [long]$vol.SizeRemaining
  if ($startFree -lt 32MB -or $startFree -gt 300MB) {
    throw 'FAIL_CLOSED: implausible initial free bytes'
  }
  $incumbent = Join-Path $drive 'incumbent-8192.bin'
  $saved = New-Object byte[] 8192
  for ($i=0; $i -lt $saved.Length; $i++) {
    $saved[$i] = [byte](($i * 37 + 13) % 256)
  }
  [IO.File]::WriteAllBytes($incumbent, $saved)
  $incumbentSHA = (Get-FileHash -LiteralPath $incumbent -Algorithm SHA256).Hash.ToLowerInvariant()
  Invoke-OnlyQAHook 'baseline'

  $filler = Join-Path $drive 'filler.bin'
  $stream = [IO.FileStream]::new(
    $filler, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write,
    [IO.FileShare]::None, 65536, [IO.FileOptions]::WriteThrough)
  try {
    foreach ($chunk in @(1MB, 4096, 1)) {
      $block = New-Object byte[] $chunk
      $attempts = 0
      while ($attempts -lt 16384) {
        try {
          $stream.Write($block, 0, $block.Length)
          $stream.Flush($true)
          $total += $block.Length
          $attempts++
        }
        catch [IO.IOException] {
          $win32 = $_.Exception.HResult -band 0xffff
          if ($win32 -ne 112 -and $win32 -ne 39) {
            throw "FAIL_CLOSED: actual unexpected I/O error $win32"
          }
          $filled = $true
          break
        }
      }
      if ($attempts -ge 16384) {
        throw 'FAIL_CLOSED: bounded isolated NTFS filler limit hit'
      }
    }
  }
  finally {
    # The first real Windows run proved NTFS ERROR_DISK_FULL, but FileStream
    # also surfaced 112 during the final Dispose/flush. This is another
    # genuine OS-volume-full failure, not a reason to abort before the
    # independent second-process check or falsely report product failure.
    try { $stream.Dispose() }
    catch [IO.IOException] {
      $win32 = $_.Exception.HResult -band 0xffff
      if ($win32 -ne 112 -and $win32 -ne 39) {
        throw "FAIL_CLOSED: unrelated final stream close error $win32"
      }
      $filled = $true
      $stream.SafeFileHandle.Dispose()
    }
  }
  if (-not $filled) { throw 'FAIL_CLOSED: genuine disk-full not observed' }

  # An independent child process tests CREATE+WRITE while the VHD is full.
  $childPath = Join-Path $root 'second-writer.ps1'
  $childCode = @'
param([string]$Path)
try {
  [IO.File]::WriteAllBytes($Path, (New-Object byte[] 8192))
  exit 9
} catch [IO.IOException] {
  $win32 = $_.Exception.HResult -band 0xffff
  if ($win32 -eq 112 -or $win32 -eq 39) { exit 112 }
  exit 2
}
'@
  [IO.File]::WriteAllText($childPath, $childCode, [Text.Encoding]::ASCII)
  $next = Join-Path $drive 'second-new-8192.bin'
  $cmdArgs = @('-NoLogo','-NoProfile','-NonInteractive',
               '-ExecutionPolicy','Bypass','-File',
               ('"' + $childPath + '"'),'-Path',('"' + $next + '"'))
  $child = Start-Process -FilePath 'powershell.exe' -ArgumentList $cmdArgs -PassThru -Wait -WindowStyle Hidden
  if ($child.ExitCode -ne 112) {
    throw ("FAIL_CLOSED: real fresh second process did not observe disk-full: " + $child.ExitCode)
  }
  if ((Get-FileHash -LiteralPath $incumbent -Algorithm SHA256).Hash.ToLowerInvariant() -ne $incumbentSHA) {
    throw 'FAIL_CLOSED: original incumbent changed during actual disk-full'
  }
  Invoke-OnlyQAHook 'full'
  Remove-Item -LiteralPath $filler -Force
  Remove-Item -LiteralPath $next -Force -ErrorAction SilentlyContinue
  [IO.File]::WriteAllBytes($next, (New-Object byte[] 8192))
  if ((Get-Item -LiteralPath $next).Length -ne 8192 -or
      (Get-FileHash -LiteralPath $incumbent -Algorithm SHA256).Hash.ToLowerInvariant() -ne $incumbentSHA) {
    throw 'FAIL_CLOSED: restoration lost verified previous or new data'
  }
  Invoke-OnlyQAHook 'restored'
  $report = [ordered]@{
    schema = 'UR-QA02-REAL-WIN32-ISOLATED-NTFS-DISKFULL-PREFLIGHT/1'
    source_revision = $env:GITHUB_SHA
    VHDX_isolated_NTFS = $true
    actual_Win32_disk_full_observed = $true
    genuine_second_process_ERROR_DISK_FULL = 112
    real_original_8192_bytes_preserved = $true
    recovered_new_write_bytes = 8192
    original_free_bytes = $startFree
    accepted_filler_bytes = $total
    capacity_megabytes = $MaximumMegabytes
    checker_sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    native_game_tested = [bool]$ProductHook
    native_game_receipt_is_independent_stage_file = [bool]$ProductHook
    game_ROM_used_in_ephemeral_runner = [bool]$ProductHook
    user_ROM_or_player_data_used = [bool]$ProductHook
    private_player_save_uploaded = $false
    power_loss_or_partial_IO_tested = $false
    physical_operator = $false
    release_gate_credit = 0
  }
  New-Item -ItemType Directory -Path (Split-Path -Parent $Output) -Force | Out-Null
  $report | ConvertTo-Json -Depth 5 | Out-File -LiteralPath $Output -Encoding utf8
  Write-Output ('QA02_REAL_NTFS_DISK_FULL_APPARATUS_PASS ' + ($report | ConvertTo-Json -Compress))
}
finally {
  # Deliberately no 'select disk', 'clean', or commands affecting system disks.
  if (Test-Path -LiteralPath $disk) {
    try {
      Invoke-OnlyThisVHD @(
        ('select vdisk file=' + '"' + $disk + '"'),
        'detach vdisk'
      )
    }
    catch {
      Write-Warning ('Ephemeral VHD detach incomplete; runner is disposable: ' + $_)
    }
  }
  if (Test-Path -LiteralPath $root) {
    Remove-Item -LiteralPath $root -Force -Recurse -ErrorAction SilentlyContinue
  }
}
