# Persistent portable Python for a nonadministrator Windows Actions service.
$ErrorActionPreference = 'Stop'
if (-not $env:RUNNER_WORKSPACE -or -not $env:RUNNER_TEMP -or -not $env:GITHUB_PATH -or -not $env:GITHUB_WORKSPACE) {
  throw 'Required GitHub runner environment is missing.'
}
$workRoot = Split-Path -Parent $env:RUNNER_WORKSPACE
$target = Join-Path $workRoot '.devnode-tools\python-3.12.10'
$exe = Join-Path $target 'python.exe'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
  $url = 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip'
  $zip = Join-Path $env:RUNNER_TEMP 'python-3.12.10-embed-amd64.zip'
  $staging = Join-Path $workRoot '.devnode-tools\python-3.12.10-incomplete'
  New-Item -Path (Split-Path -Parent $staging) -ItemType Directory -Force | Out-Null
  if (Test-Path -LiteralPath $staging) {
    Remove-Item -LiteralPath $staging -Recurse -Force
  }
  New-Item -Path $staging -ItemType Directory -Force | Out-Null
  Write-Output 'Downloading official Python 3.12.10 embeddable runtime.'
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
  Expand-Archive -LiteralPath $zip -DestinationPath $staging -Force
  if (-not (Test-Path -LiteralPath (Join-Path $staging 'python.exe'))) {
    throw 'Python archive has no python.exe.'
  }
  if (Test-Path -LiteralPath $target) {
    Remove-Item -LiteralPath $target -Recurse -Force
  }
  Move-Item -LiteralPath $staging -Destination $target
  Remove-Item -LiteralPath $zip -Force
}
$pth = Join-Path $target 'python312._pth'
@('python312.zip', '.', $env:GITHUB_WORKSPACE, (Join-Path $env:GITHUB_WORKSPACE 'tools'), 'import site') |
  Set-Content -LiteralPath $pth -Encoding ASCII
& $exe -c "import sys, unittest, subprocess; assert sys.version_info[:3] == (3, 12, 10), sys.version"
if ($LASTEXITCODE -ne 0) { throw 'Python runtime self-check failed.' }
Add-Content -LiteralPath $env:GITHUB_PATH -Value $target
Write-Output 'Portable Python 3.12.10 ready in persistent runner cache.'
