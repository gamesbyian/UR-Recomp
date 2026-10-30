# Persistent, source-verified Python for the owner's nonadministrator Windows runner.
$ErrorActionPreference = 'Stop'
if (-not $env:RUNNER_WORKSPACE -or -not $env:RUNNER_TEMP -or -not $env:GITHUB_PATH -or -not $env:GITHUB_WORKSPACE) {
  throw 'Required GitHub runner environment is missing.'
}
# The generic Windows/X64 runner labels are not a unique machine identity.
# Verified from the successful HP job #40975340422, not inferred from labels.
if ($env:RUNNER_NAME -ne 'hpmini-ur-recomp') {
  throw 'Refusing to attribute HP benchmark to a different self-hosted runner.'
}
$workRoot = Split-Path -Parent $env:RUNNER_WORKSPACE
$cache = Join-Path $workRoot '.devnode-tools'
$target = Join-Path $cache 'python-3.12.10'
$exe = Join-Path $target 'python.exe'
$zip = Join-Path $cache 'python-3.12.10-embed-amd64.zip'
$expectedSha256 = '4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3'
$url = 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip'
New-Item -Path $cache -ItemType Directory -Force | Out-Null
if (-not (Test-Path -LiteralPath $zip -PathType Leaf)) {
  $download = Join-Path $env:RUNNER_TEMP 'python-3.12.10-embed-amd64.download'
  Write-Output 'Downloading official Python 3.12.10 embeddable archive.'
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  Invoke-WebRequest -Uri $url -OutFile $download -UseBasicParsing
  if ((Get-FileHash -LiteralPath $download -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedSha256) {
    throw 'Downloaded Python archive SHA-256 differs from Python.org release SBOM.'
  }
  Move-Item -LiteralPath $download -Destination $zip
}
# Recheck the persistent ZIP every run, including runs using an existing cache.
# Never execute an old extracted interpreter merely because its version matches.
if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedSha256) {
  throw 'Cached Python archive SHA-256 mismatch; refusing untrusted executable.'
}
$staging = Join-Path $cache ('python-3.12.10-stage-' + $env:GITHUB_RUN_ID + '-' + $env:GITHUB_RUN_ATTEMPT)
if (Test-Path -LiteralPath $staging) {
  Remove-Item -LiteralPath $staging -Recurse -Force
}
New-Item -Path $staging -ItemType Directory -Force | Out-Null
# Re-extract the verified bytes each time rather than trusting mutable cached DLLs.
Expand-Archive -LiteralPath $zip -DestinationPath $staging -Force
if (-not (Test-Path -LiteralPath (Join-Path $staging 'python.exe') -PathType Leaf)) {
  throw 'Verified Python archive has no python.exe.'
}
if (Test-Path -LiteralPath $target) {
  Remove-Item -LiteralPath $target -Recurse -Force
}
Move-Item -LiteralPath $staging -Destination $target
$pth = Join-Path $target 'python312._pth'
@('python312.zip', '.', $env:GITHUB_WORKSPACE, (Join-Path $env:GITHUB_WORKSPACE 'tools'), 'import site') |
  Set-Content -LiteralPath $pth -Encoding ASCII
& $exe -c "import sys, unittest, subprocess, extract_menu_visual_language, probe_tier_opponents; assert sys.version_info[:3] == (3, 12, 10), sys.version"
if ($LASTEXITCODE -ne 0) { throw 'Python runtime self-check failed.' }
Add-Content -LiteralPath $env:GITHUB_PATH -Value $target
Write-Output 'Python 3.12.10 restored from SHA-256-verified persistent archive.'
