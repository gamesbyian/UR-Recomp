# Product-owned actual Win32 source game against one disposable NTFS-full VHDX.
# Reuses the independently proven QA02 VHDX/NTFS method without altering
# QA's apparatus or touching any attached physical/system disk.
[CmdletBinding()]
param(
  [ValidateRange(96,256)][int]$MaximumMegabytes = 128,
  [ValidatePattern('^[A-Z]$')][string]$DriveLetter = 'W',
  [Parameter(Mandatory=$true)][string]$Output
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows' -or
    -not $env:GITHUB_WORKSPACE -or -not $env:GITHUB_SHA -or
    -not $env:RUNNER_TEMP -or $DriveLetter -ne 'W') {
  throw 'FAIL_CLOSED: ephemeral GitHub Windows runner and isolated W: only'
}
$drive = $DriveLetter + ':\'
if (Test-Path -LiteralPath $drive) { throw 'FAIL_CLOSED: disk letter in use' }
$root = Join-Path $env:RUNNER_TEMP 'ur-product-only-ephemeral-full-NTFS'
if (Test-Path -LiteralPath $root) { throw 'FAIL_CLOSED: test already has a VHDX' }
New-Item -ItemType Directory -Path $root -Force | Out-Null
$disk = Join-Path $root 'ur-product-test-only.vhdx'
$commands = Join-Path $root 'diskpart-only-this-vhd.txt'
$launcher = Join-Path $env:RUNNER_TEMP 'Baldosa Native Extracted Launcher QA\Extracted Baldosa Candidate With Spaces\run-baldosa-modern.cmd'
$rom = Join-Path $env:GITHUB_WORKSPACE 'reference\roms\retail\Uniracers_USA.sfc'
$fixture = Join-Path $env:GITHUB_WORKSPACE 'baldosa\build-ur-win\ur-baldosa-modern-profile-fixture.exe'
$seed = Join-Path $env:RUNNER_TEMP 'UR Baldosa Win32 Pause Route\baseline\Modern Player Data With Spaces\saves\save.srm'
$source = Join-Path $env:GITHUB_WORKSPACE 'tools\baldosa_win32_real_ntfs_diskfull_game.py'
$user = $drive + 'Exact Original Guest On Disposable NTFS'
$out = [IO.Path]::GetFullPath($Output)
if ($out.StartsWith($drive, [StringComparison]::OrdinalIgnoreCase) -or
    $out.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
  throw 'FAIL_CLOSED: evidence cannot be written inside VHDX'
}
New-Item -ItemType Directory -Force -Path $out | Out-Null
foreach ($file in @($launcher,$rom,$fixture,$seed,$source)) {
  if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
    throw ('FAIL_CLOSED: source candidate or original fixture missing: ' + $file)
  }
}
function Invoke-OnlyOriginalVHD([string[]]$instructions) {
  [IO.File]::WriteAllLines($commands, $instructions, [Text.Encoding]::ASCII)
  $text = (& diskpart.exe /s $commands 2>&1 | Out-String)
  if ($LASTEXITCODE -ne 0 -or $text -match 'DiskPart has encountered an error' -or
      $text -match 'The arguments specified for this command are not valid') {
    throw ('FAIL_CLOSED: isolated VHDX diskpart failure: ' + $text)
  }
}
function Invoke-OriginalPhase([string]$phase) {
  & python $source --phase $phase --launcher $launcher --rom $rom --fixture $fixture --seed $seed --user $user --out $out --timeout 120
  if ($LASTEXITCODE -ne 0) {
    throw ('FAIL_CLOSED: actual original Windows product ' + $phase + ' failed')
  }
}
$filler = $drive + 'ur-product-ntfs-only-fill.bin'
$secondFile = $drive + 'other-process-8192.bin'
$attached = $false
$filled = $false
$accepted = [long]0
try {
  $quoted = '"' + $disk + '"'
  Invoke-OnlyOriginalVHD @(
    ('create vdisk file=' + $quoted + " maximum=$MaximumMegabytes type=expandable"),
    ('select vdisk file=' + $quoted),
    'attach vdisk',
    'create partition primary',
    'format fs=ntfs quick label="URMODFULL"',
    ('assign letter=' + $DriveLetter)
  )
  $attached = $true
  Start-Sleep -Seconds 3
  $volume = Get-Volume -DriveLetter $DriveLetter -ErrorAction Stop
  if ($volume.FileSystem -ne 'NTFS' -or $volume.FileSystemLabel -ne 'URMODFULL' -or
      $volume.Size -lt 32MB -or $volume.Size -gt 300MB) {
    throw 'FAIL_CLOSED: unexpected attached NTFS identity'
  }
  $originalFree = [long]$volume.SizeRemaining
  if ($originalFree -lt 32MB -or $originalFree -gt 300MB) {
    throw 'FAIL_CLOSED: unexpected original disposable free space'
  }
  # Author original-format Windows profile+SRAM with the shipping native C++
  # fixture before exhaustion, then execute a clean source CMD warm-up.
  Invoke-OriginalPhase 'prepare'
  $beforeFill = Get-Volume -DriveLetter $DriveLetter -ErrorAction Stop
  if ($beforeFill.SizeRemaining -lt 1MB) {
    throw 'FAIL_CLOSED: original profile unexpectedly filled NTFS'
  }
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
          $accepted += $block.Length
          $attempts++
        }
        catch [IO.IOException] {
          $code = $_.Exception.HResult -band 0xffff
          if ($code -ne 112 -and $code -ne 39) {
            throw ('FAIL_CLOSED: unrelated actual NTFS I/O error ' + $code)
          }
          $filled = $true
          break
        }
      }
      if ($attempts -ge 16384) {
        throw 'FAIL_CLOSED: bounded W: filler loop exhausted'
      }
    }
  }
  finally {
    try { $stream.Dispose() }
    catch [IO.IOException] {
      $code = $_.Exception.HResult -band 0xffff
      if ($code -ne 112 -and $code -ne 39) {
        throw ('FAIL_CLOSED: unrelated NTFS close error ' + $code)
      }
      $filled = $true
      $stream.SafeFileHandle.Dispose()
    }
  }
  if (-not $filled) {
    throw 'FAIL_CLOSED: real Windows NTFS never reported 112'
  }
  $childCode = @'
param([string]$Path)
try {
  [IO.File]::WriteAllBytes($Path, (New-Object byte[] 8192))
  exit 9
} catch [IO.IOException] {
  $code = $_.Exception.HResult -band 0xffff
  if ($code -eq 112 -or $code -eq 39) { exit 112 }
  exit 2
}
'@
  $childFile = Join-Path $root 'original-independent-diskfull-writer.ps1'
  [IO.File]::WriteAllText($childFile, $childCode, [Text.Encoding]::ASCII)
  $args = @('-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy',
            'Bypass','-File',('"' + $childFile + '"'),
            '-Path',('"' + $secondFile + '"'))
  $child = Start-Process -FilePath 'powershell.exe' -ArgumentList $args -Wait -PassThru -WindowStyle Hidden
  if ($child.ExitCode -ne 112) {
    throw ('FAIL_CLOSED: actual independent Windows process did not report 112: ' + $child.ExitCode)
  }
  $report = [ordered]@{
    schema = 'ur-product-source-real-win32-ntfs-diskfull-substrate/1'
    actual_ephemeral_ntfs_vhdx = $true
    original_source_warm_boot_completed_before_fill = $true
    original_free_bytes = $originalFree
    free_bytes_before_fill = [long]$beforeFill.SizeRemaining
    accepted_filler_bytes = $accepted
    fresh_process_os_error = 112
    capacity_megabytes = $MaximumMegabytes
    tested_commit = $env:GITHUB_SHA
    product_not_release_qa = $true
    power_loss_or_short_write = $false
    release_gate_credit = 0
  }
  ($report | ConvertTo-Json -Depth 5) | Out-File -LiteralPath (Join-Path $out 'real-ntfs-substrate.json') -Encoding utf8
  # The original game must reach a real 1P race, try its NORMAL guest save
  # while this NTFS volume is physically full, and return visible exit 8.
  Invoke-OriginalPhase 'full'
  # No disk cleanup or modifications on other volumes.
  Remove-Item -LiteralPath $filler -Force
  Remove-Item -LiteralPath $secondFile -Force -ErrorAction SilentlyContinue
  $post = Get-Volume -DriveLetter $DriveLetter -ErrorAction Stop
  if ($post.SizeRemaining -lt 1MB) {
    throw 'FAIL_CLOSED: isolated W: free space not restored'
  }
  Invoke-OriginalPhase 'cold'
  # Preserve the exact independently accepted 25-member early refusal
  # artifact unchanged. The second, different failure phase has its own
  # sibling output and never writes its evidence onto disposable W:.
  $postrawSource = Join-Path $env:GITHUB_WORKSPACE 'tools\baldosa_win32_real_ntfs_postraw_game.py'
  if (-not (Test-Path -LiteralPath $postrawSource -PathType Leaf)) {
    throw 'FAIL_CLOSED: owning original-game postraw researcher missing'
  }
  $postrawOutput = $out + '-postraw'
  if (Test-Path -LiteralPath $postrawOutput) {
    throw 'FAIL_CLOSED: postraw source evidence root unexpectedly exists'
  }
  & python $postrawSource --launcher $launcher --rom $rom --fixture $fixture --seed $seed --user $user --out $postrawOutput --timeout 120
  if ($LASTEXITCODE -ne 0) {
    throw 'FAIL_CLOSED: actual original Windows postraw full-volume typed publication unproven'
  }
  Write-Output 'UR_ORIGINAL_CMD_REAL_NTFS_DISK_FULL_PRODUCT_PASS'
  Write-Output 'UR_ORIGINAL_CMD_REAL_NTFS_POSTRAW_TYPED_FULL_PRODUCT_PASS'
}
finally {
  if ($attached) {
    try {
      Invoke-OnlyOriginalVHD @(('select vdisk file=' + '"' + $disk + '"'),'detach vdisk')
    }
    catch {
      Write-Warning ('Only own disposable VHD detach refused: ' + $_)
    }
  }
  Remove-Item -LiteralPath $root -Force -Recurse -ErrorAction SilentlyContinue
}
