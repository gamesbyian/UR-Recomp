#Requires -Version 5.1
<#
Offline, private, explicit owner-run source-racer corpus preparation.

Never fetch a ROM, publish source images, write inside the checkout,
or assume that original 2D source families imply verified 3D cameras.
Run from the adjacent .cmd on the owner's HP Windows 10 machine.
#>
[CmdletBinding()]
param(
    [string] $RomPath = "",
    [string] $OutputParent = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ExpectedRomSha256 = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
$ExpectedRomBytes = 2097152
$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
$ExportScript = Join-Path $RepoRoot "tools\art\export_registered_original_racer_corpus.py"
$FreezeScript = Join-Path $RepoRoot "tools\art\freeze_racer_source_family_splits.py"
$SourceRegistry = Join-Path $RepoRoot "analysis\data\racer-hd-replacement-prototype.json"

function Fail([string] $Message) {
    throw $Message
}

function Select-LocalOriginalRom {
    try {
        Add-Type -AssemblyName System.Windows.Forms
        $picker = New-Object System.Windows.Forms.OpenFileDialog
        $picker.Title = "Select your local, legally obtained Uniracers USA ROM"
        $picker.Filter = "SNES ROM (*.sfc;*.smc)|*.sfc;*.smc|All files (*.*)|*.*"
        $picker.Multiselect = $false
        $picker.CheckFileExists = $true
        $result = $picker.ShowDialog()
        if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
            return $picker.FileName
        }
        Fail "No ROM was selected. Nothing was exported."
    } catch {
        # Interactive terminals without WinForms can supply the path.
        Write-Host "ROM selection dialog unavailable or dismissed: $($_.Exception.Message)"
        $selected = Read-Host "Full path to your existing USA ROM (leave blank to cancel)"
        if ([string]::IsNullOrWhiteSpace($selected)) {
            Fail "No ROM path provided. Nothing was exported."
        }
        return $selected.Trim('"')
    }
}

function Find-CompatiblePython {
    $candidates = @(
        @{ Program = "py"; Prefix = @("-3") },
        @{ Program = "python"; Prefix = @() },
        @{ Program = "python3"; Prefix = @() }
    )
    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Program -ErrorAction SilentlyContinue)) {
            continue
        }
        $prefix = @($candidate.Prefix)
        $program = [string] $candidate.Program
        & $program @prefix -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 12)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $candidate
        }
    }
    Fail "Python 3.10+ is required. Install Python for Windows or its py launcher; then rerun."
}

function Invoke-CheckedPython([hashtable] $Runtime, [string[]] $Arguments) {
    $program = $Runtime.Program
    $prefix = @($Runtime.Prefix)
    & $program @prefix @Arguments
    if ($LASTEXITCODE -ne 0) {
        Fail "Source corpus tool exited with code $LASTEXITCODE. Any receipt-less output is incomplete."
    }
}

function Write-NewUtf8File([string] $Path, [string] $Content) {
    # Use a no-BOM UTF-8 file for Python's JSON parser on Windows PowerShell 5.
    # Never use Set-Content or Out-File to overwrite an evidence receipt.
    $utf8 = [System.Text.UTF8Encoding]::new($false)
    $stream = [System.IO.FileStream]::new(
        $Path,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try {
        $bytes = $utf8.GetBytes($Content)
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    } finally {
        $stream.Dispose()
    }
}

$exitCode = 1
try {
    if (-not (Test-Path -LiteralPath $ExportScript -PathType Leaf) -or
        -not (Test-Path -LiteralPath $FreezeScript -PathType Leaf) -or
        -not (Test-Path -LiteralPath $SourceRegistry -PathType Leaf)) {
        Fail "This launcher must remain inside a current UR-Recomp repository checkout."
    }

    if ([string]::IsNullOrWhiteSpace($RomPath)) {
        $RomPath = Select-LocalOriginalRom
    }
    $romFile = Get-Item -LiteralPath $RomPath -ErrorAction Stop
    if ($romFile.PSIsContainer -or $romFile.Length -ne $ExpectedRomBytes) {
        Fail "Selected file must be exactly 2,097,152 bytes (canonical USA ROM)."
    }
    $realSha = (Get-FileHash -LiteralPath $romFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($realSha -ne $ExpectedRomSha256) {
        Fail "Selected ROM SHA-256 is not the exact original USA reference. No data was exported."
    }

    if ([string]::IsNullOrWhiteSpace($OutputParent)) {
        if (-not $env:LOCALAPPDATA) {
            Fail "LOCALAPPDATA is unavailable; supply an explicit private -OutputParent."
        }
        $OutputParent = Join-Path $env:LOCALAPPDATA "UR-Recomp\private-original-racer-corpora"
    }
    $privateParent = [System.IO.Path]::GetFullPath($OutputParent)
    $repoPrefix = $RepoRoot.TrimEnd('\') + '\'
    if ($privateParent.Equals($RepoRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
        $privateParent.StartsWith($repoPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        Fail "Private source corpus must be outside the public UR-Recomp checkout."
    }
    [System.IO.Directory]::CreateDirectory($privateParent) | Out-Null

    $runtime = Find-CompatiblePython
    $runId = (Get-Date -Format "yyyyMMdd-HHmmss") + "-" + [Guid]::NewGuid().ToString("N").Substring(0, 8)
    $output = Join-Path $privateParent ("original-racer-" + $runId)
    if (Test-Path -LiteralPath $output) {
        Fail "Source corpus output already exists; refusing to overwrite it."
    }

    Push-Location $RepoRoot
    try {
        Write-Host "Verified the exact original USA ROM. Generating private source frames..."
        Invoke-CheckedPython $runtime @(
            $ExportScript, "--rom", $romFile.FullName,
            "--registry", $SourceRegistry,
            "--out", $output
        )
        $receipt = Join-Path $output "source-corpus.json"
        if (-not (Test-Path -LiteralPath $receipt -PathType Leaf)) {
            Fail "Source export has no verified completion receipt. Treat output as incomplete."
        }

        # All source-family roles default to diagnostic. The owner/agent
        # must *separately* designate fit vs withheld roles before fitting.
        $python = $runtime.Program
        $prefix = @($runtime.Prefix)
        $templateLines = & $python @prefix $FreezeScript $receipt "--template"
        if ($LASTEXITCODE -ne 0 -or -not $templateLines) {
            Fail "Source-family role template generation failed."
        }
        $draftPath = Join-Path $output "roles-draft-all-diagnostic.json"
        Write-NewUtf8File $draftPath (($templateLines -join [Environment]::NewLine) +
                                       [Environment]::NewLine)
        $diagnosticLines = & $python @prefix $FreezeScript $receipt $draftPath
        if ($LASTEXITCODE -ne 0 -or -not $diagnosticLines) {
            Fail "Original-source diagnostic grouping verification failed."
        }
        $diagnosticPath = Join-Path $output "source-family-diagnostic-groups.json"
        Write-NewUtf8File $diagnosticPath (($diagnosticLines -join [Environment]::NewLine) +
                                            [Environment]::NewLine)

        $source = Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json
        Write-Host ""
        Write-Host "SOURCE CORPUS EXPORTED AND VERIFIED" -ForegroundColor Green
        Write-Host "Private folder: $output"
        Write-Host ("Registered windows: " + @($source.registered_source_windows).Count)
        Write-Host ("Distinct source binary silhouettes: " + $source.unique_binary_silhouettes)
        Write-Host "Diagnostic role draft: $draftPath"
        Write-Host "Source family grouping: $diagnosticPath"
        Write-Host "No original ROM, source PNG or private raster was uploaded."
        Write-Host "No fit/heldout family or original 1994 camera was declared verified."
        $exitCode = 0
    } finally {
        Pop-Location
    }
} catch {
    Write-Host ""
    Write-Host ("PRIVATE SOURCE EXPORT NOT COMPLETE: " + $_.Exception.Message) -ForegroundColor Red
    Write-Host "An incomplete directory without source-corpus.json is NEVER valid evidence."
} finally {
    Write-Host "No network upload or automatic GitHub publication is part of this launcher."
}

exit $exitCode
