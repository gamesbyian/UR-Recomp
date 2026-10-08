#requires -Version 5.1
<#
.SYNOPSIS
  Verify the exact UR-Recomp portable Windows release without build tools.
.DESCRIPTION
  Designed for a fresh Windows 10/11 VM or test PC. Requires only Windows
  PowerShell 5.1. Checks the adjacent SHA-256 release sidecar, extracts with
  Windows Expand-Archive, checks every unpacked manifest file/hash/size and
  verifies that immutable package files remain unchanged after an optional
  real launch. Leaves the probe directory and diagnostics for inspection.
  Does not certify a specific GPU, controller or audio device on its own.
.EXAMPLE
  .\Test-URRecompPortable.ps1 -Archive .\UR-Recomp-Windows-x64.zip -Checksum .\UR-Recomp-Windows-x64.zip.sha256 -Destination "$env:TEMP\UR release probe"
.EXAMPLE
  .\Test-URRecompPortable.ps1 -Archive .\UR-Recomp-Windows-x64.zip -Checksum .\UR-Recomp-Windows-x64.zip.sha256 -Destination "$env:TEMP\UR live probe" -Launch
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Archive,
    [Parameter(Mandatory = $true)][string]$Checksum,
    [Parameter(Mandatory = $true)][string]$Destination,
    [switch]$Launch,
    [string]$InputScript
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Canonical USA retail fingerprint, pinned independently of the ZIP manifest.
# Keep this in sync with the tracked rom_identity.txt canonical source.
$canonicalRomSha256 = '859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478'

function Assert-Amd64PortableExecutable {
    param([Parameter(Mandatory = $true)][string]$Executable)

    # Inspect PE headers with stock .NET FileStream only. This confirms the
    # consumer receives an AMD64/PE32+ file without requiring Visual Studio,
    # dumpbin or any additional executable on a clean Windows machine.
    $message = 'Packaged executable must be an AMD64 PE32+ Windows binary'
    $stream = [IO.File]::OpenRead($Executable)
    try {
        if ($stream.Length -lt 90) { throw $message }
        $dos = New-Object byte[] 64
        if ($stream.Read($dos, 0, 64) -ne 64 -or
            $dos[0] -ne 0x4d -or $dos[1] -ne 0x5a) {
            throw $message
        }
        $peOffset = [BitConverter]::ToUInt32($dos, 60)
        if ($peOffset -lt 64 -or $peOffset -gt 16777216 -or
            ([long]$peOffset + 26) -gt $stream.Length) {
            throw $message
        }
        [void]$stream.Seek([long]$peOffset, [IO.SeekOrigin]::Begin)
        $pe = New-Object byte[] 26
        if ($stream.Read($pe, 0, 26) -ne 26 -or
            $pe[0] -ne 0x50 -or $pe[1] -ne 0x45 -or
            $pe[2] -ne 0 -or $pe[3] -ne 0) {
            throw $message
        }
        $optionalSize = [BitConverter]::ToUInt16($pe, 20)
        if ([BitConverter]::ToUInt16($pe, 4) -ne 0x8664 -or
            [BitConverter]::ToUInt16($pe, 24) -ne 0x20b -or
            $optionalSize -lt 2 -or
            ([long]$peOffset + 24 + $optionalSize) -gt $stream.Length) {
            throw $message
        }
    }
    finally {
        $stream.Dispose()
    }
}

function Assert-PackageFiles {
    param([Parameter(Mandatory = $true)][string]$PackageRoot)

    $manifestPath = Join-Path $PackageRoot 'PACKAGE-MANIFEST.json'
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw 'The extracted package has no PACKAGE-MANIFEST.json'
    }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($manifest.schema_version -ne 1 -or
        $manifest.package_format -cne 'ur-recomp-windows-x64-portable-v1' -or
        [string]::IsNullOrWhiteSpace([string]$manifest.source_revision)) {
        throw 'The package manifest has an unsupported schema or missing revision'
    }
    $entries = @($manifest.files)
    if ($entries.Count -lt 6 -or $entries.Count -gt 10000) {
        throw 'The package manifest has an implausible entry count'
    }

    $seen = @{}
    $mustHave = @(
        'UniracersSNESRecomp.exe', 'Uniracers_USA.sfc', 'rom.cfg',
        'run-uniracers.cmd', 'README.txt'
    )
    $total = [int64]0
    foreach ($entry in $entries) {
        $relative = [string]$entry.path
        if ($relative -match '(?:^|/)\.\.?(/|$)' -or
            $relative -match '[\\:]' -or
            [string]::IsNullOrWhiteSpace($relative) -or
            ($relative -notin $mustHave -and
             -not $relative.StartsWith('mods/', [StringComparison]::Ordinal))) {
            throw "Unsafe or unexpected package member: $relative"
        }
        # Mod selection state is mutable user data, not an immutable catalog
        # asset. Reject it even if a separately supplied manifest/checksum
        # claims it is an ordinary mods/** payload.
        if ($relative -ieq 'mods/preloaded/state.toml') {
            throw 'Mutable mod-selection state must not be shipped in the package'
        }
        if ($seen.ContainsKey($relative)) {
            throw "Duplicate package member: $relative"
        }
        $seen[$relative] = $true
        $member = Join-Path $PackageRoot ($relative.Replace('/', [IO.Path]::DirectorySeparatorChar))
        if (-not (Test-Path -LiteralPath $member -PathType Leaf)) {
            throw "Missing extracted payload: $relative"
        }
        $size = [int64]$entry.size
        $digest = [string]$entry.sha256
        # A self-consistent package manifest and checksum do not establish
        # that this is the canonical Uniracers ROM accepted by the build.
        if ($relative -ieq 'Uniracers_USA.sfc' -and
            $digest -cne $canonicalRomSha256) {
            throw 'Packaged ROM does not match canonical USA retail identity'
        }
        if ($size -lt 0 -or $size -gt 536870912 -or
            $digest -cnotmatch '\A[0-9a-f]{64}\z') {
            throw "Invalid manifest payload metadata: $relative"
        }
        $total += $size
        if ($total -gt 2147483648) {
            throw 'Package payload exceeds portable release size limit'
        }
        $file = Get-Item -LiteralPath $member
        if ($file.Length -ne $size) {
            throw "Incorrect extracted file size: $relative"
        }
        $actualHash = (Get-FileHash -LiteralPath $member -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -cne $digest) {
            throw "Incorrect extracted file SHA-256: $relative"
        }
    }
    foreach ($required in $mustHave) {
        if (-not $seen.ContainsKey($required)) {
            throw "Missing required package member in manifest: $required"
        }
    }
    if (-not @($seen.Keys | Where-Object { $_.StartsWith('mods/', [StringComparison]::Ordinal) }).Count) {
        throw 'The package has no immutable mod payload'
    }
    $actualFiles = @(Get-ChildItem -LiteralPath $PackageRoot -Recurse -File -Force)
    if ($actualFiles.Count -ne ($entries.Count + 1)) {
        throw 'Extracted package has extra or missing payload files'
    }
    foreach ($file in $actualFiles) {
        if ($file.FullName -eq $manifestPath) { continue }
        $relative = $file.FullName.Substring($PackageRoot.Length + 1).Replace('\', '/')
        if (-not $seen.ContainsKey($relative)) {
            throw "Unmanifested extracted file: $relative"
        }
    }

    $romConfig = [IO.File]::ReadAllBytes((Join-Path $PackageRoot 'rom.cfg'))
    $expectedConfig = [Text.Encoding]::ASCII.GetBytes("Uniracers_USA.sfc`n")
    if ([Convert]::ToBase64String($romConfig) -cne [Convert]::ToBase64String($expectedConfig)) {
        throw 'Packaged rom.cfg is not the canonical package-relative ROM path'
    }
    $readme = Get-Content -LiteralPath (Join-Path $PackageRoot 'README.txt') -Raw -Encoding UTF8
    if (-not $readme.Contains("Source revision: $($manifest.source_revision)`n")) {
        throw 'README build revision does not match the manifest'
    }
    Assert-Amd64PortableExecutable -Executable (Join-Path $PackageRoot 'UniracersSNESRecomp.exe')
    Write-Output "UR_PORTABLE_BINARY_VERIFIED machine=AMD64 format=PE32+"
    Write-Output "UR_PORTABLE_ROM_IDENTITY_VERIFIED sha256=$canonicalRomSha256"
    Write-Output "UR_PORTABLE_MANIFEST_VERIFIED files=$($entries.Count) revision=$($manifest.source_revision)"
}

if (-not [IO.Path]::IsPathRooted($Destination)) {
    throw 'Destination must be an absolute directory path'
}
$destinationPath = [IO.Path]::GetFullPath($Destination)
if (Test-Path -LiteralPath $destinationPath) {
    throw "Destination already exists. Use a fresh test directory: $destinationPath"
}
$archivePath = (Resolve-Path -LiteralPath $Archive -ErrorAction Stop).ProviderPath
$checksumPath = (Resolve-Path -LiteralPath $Checksum -ErrorAction Stop).ProviderPath
if (-not (Test-Path -LiteralPath $archivePath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $checksumPath -PathType Leaf)) {
    throw 'Both the release ZIP and adjacent SHA-256 sidecar must exist'
}
$checksumLine = [IO.File]::ReadAllText($checksumPath, [Text.Encoding]::ASCII)
$match = [regex]::Match($checksumLine, '\A([0-9a-f]{64})  ([^\r\n]+)\n\z')
if (-not $match.Success -or
    $match.Groups[2].Value -cne [IO.Path]::GetFileName($archivePath)) {
    throw 'Invalid canonical ZIP checksum sidecar'
}
$archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($archiveHash -cne $match.Groups[1].Value) {
    throw 'Release ZIP does not match the supplied SHA-256 sidecar'
}
Write-Output "UR_PORTABLE_ARCHIVE_VERIFIED sha256=$archiveHash"

# The test directory must be new: never overlay or delete a player's install.
Expand-Archive -LiteralPath $archivePath -DestinationPath $destinationPath
$packageRoot = Join-Path $destinationPath 'UR-Recomp-Windows-x64'
if (-not (Test-Path -LiteralPath $packageRoot -PathType Container)) {
    throw 'Expected UR-Recomp-Windows-x64 directory missing after extraction'
}
Assert-PackageFiles -PackageRoot $packageRoot
if (Test-Path -LiteralPath (Join-Path $packageRoot 'config.ini')) {
    throw 'Mutable config.ini was shipped inside the immutable package'
}
if (Test-Path -LiteralPath (Join-Path $packageRoot 'saves')) {
    throw 'Mutable saves directory was shipped inside the package'
}

if ($Launch -or -not [string]::IsNullOrWhiteSpace($InputScript)) {
    $userRoot = Join-Path $destinationPath 'isolated-user-data'
    $caller = Join-Path $destinationPath 'unrelated launch working directory'
    New-Item -ItemType Directory -Path $caller | Out-Null
    $launcher = Join-Path $packageRoot 'run-uniracers.cmd'
    $gameArgs = @()
    if (-not [string]::IsNullOrWhiteSpace($InputScript)) {
        $scriptFile = (Resolve-Path -LiteralPath $InputScript).ProviderPath
        $gameArgs = @('--script', $scriptFile)
    }
    $previousRoot = [Environment]::GetEnvironmentVariable('UR_RECOMP_USER_DATA_ROOT', 'Process')
    try {
        $env:UR_RECOMP_USER_DATA_ROOT = $userRoot
        Push-Location -LiteralPath $caller
        try {
            # Actual Windows video/audio drivers remain selected by the host.
            & $launcher @gameArgs
            $exitCode = $LASTEXITCODE
        }
        finally {
            Pop-Location
        }
    }
    finally {
        [Environment]::SetEnvironmentVariable('UR_RECOMP_USER_DATA_ROOT', $previousRoot, 'Process')
    }
    if ($exitCode -ne 0) {
        throw "Packaged launcher returned exit code $exitCode. Inspect $userRoot\diagnostics\startup.log"
    }
    foreach ($name in @('config.ini', 'keybinds.ini', 'mod-state.toml')) {
        if (-not (Test-Path -LiteralPath (Join-Path $userRoot $name) -PathType Leaf)) {
            throw "Launcher did not create user-owned $name"
        }
        if (Test-Path -LiteralPath (Join-Path $packageRoot $name)) {
            throw "Package directory was modified by launching: $name"
        }
    }
    if (-not (Test-Path -LiteralPath (Join-Path $userRoot 'saves') -PathType Container)) {
        throw 'Launcher did not create user-owned saves directory'
    }
    $startupLog = Join-Path $userRoot 'diagnostics\startup.log'
    if (-not (Test-Path -LiteralPath $startupLog -PathType Leaf)) {
        throw 'Expected startup diagnostics log was not created'
    }
    Assert-PackageFiles -PackageRoot $packageRoot
    Write-Output "UR_PORTABLE_REAL_WINDOWS_LAUNCH_EXITED_OK user_data=$userRoot"
}
Write-Output "UR_PORTABLE_CLEAN_MACHINE_PACKAGE_OK extracted=$packageRoot"
