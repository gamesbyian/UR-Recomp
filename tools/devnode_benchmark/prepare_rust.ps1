# Install a pinned Rust/Cargo MSVC toolchain once, in the Windows runner's writable cache.
# This is an isolated native build experiment. No registry or machine PATH edits.
$ErrorActionPreference = 'Stop'
if (-not $env:RUNNER_WORKSPACE -or -not $env:RUNNER_TEMP -or
    -not $env:GITHUB_ENV -or -not $env:GITHUB_PATH) {
  throw 'Required GitHub Actions service environment is unavailable.'
}
$cacheRoot = Join-Path (Split-Path -Parent $env:RUNNER_WORKSPACE) '.devnode-tools'
$env:RUSTUP_HOME = Join-Path $cacheRoot 'rustup'
$env:CARGO_HOME = Join-Path $cacheRoot 'cargo'
New-Item -ItemType Directory -Force -Path $env:RUSTUP_HOME, $env:CARGO_HOME | Out-Null
$bin = Join-Path $env:CARGO_HOME 'bin'
$env:PATH = $bin + ';' + $env:PATH
$rustup = Join-Path $bin 'rustup.exe'
$toolchain = '1.97.1-x86_64-pc-windows-msvc'
if (-not (Test-Path -LiteralPath $rustup -PathType Leaf)) {
  $base = 'https://static.rust-lang.org/rustup/archive/1.29.0/x86_64-pc-windows-msvc/rustup-init.exe'
  $exe = Join-Path $env:RUNNER_TEMP 'rustup-init.exe'
  $sum = $exe + '.sha256'
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  Write-Output 'Downloading official pinned rustup 1.29.0 installer and its SHA-256 manifest.'
  Invoke-WebRequest -Uri $base -OutFile $exe -UseBasicParsing
  Invoke-WebRequest -Uri ($base + '.sha256') -OutFile $sum -UseBasicParsing
  $expected = ((Get-Content -LiteralPath $sum -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
  $actual = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($expected -notmatch '^[0-9a-f]{64}$' -or $expected -ne $actual) {
    throw 'rustup-init SHA-256 does not match the official manifest.'
  }
  & $exe -y --no-modify-path --profile minimal --default-host x86_64-pc-windows-msvc --default-toolchain $toolchain
  if ($LASTEXITCODE -ne 0) { throw "rustup-init exited $LASTEXITCODE" }
  Remove-Item -LiteralPath $exe, $sum -Force -ErrorAction SilentlyContinue
} else {
  Write-Output 'Reusing existing rustup installation under runner writable cache.'
}
if (-not (Test-Path -LiteralPath $rustup -PathType Leaf)) {
  throw 'rustup.exe missing after initial setup.'
}
& $rustup toolchain install $toolchain --profile minimal
if ($LASTEXITCODE -ne 0) { throw "rustup toolchain install exited $LASTEXITCODE" }
& $rustup default $toolchain
if ($LASTEXITCODE -ne 0) { throw "rustup default exited $LASTEXITCODE" }
$rustc = Join-Path $bin 'rustc.exe'
$cargo = Join-Path $bin 'cargo.exe'
& $rustc --version
if ($LASTEXITCODE -ne 0) { throw 'rustc cannot start.' }
& $cargo --version
if ($LASTEXITCODE -ne 0) { throw 'cargo cannot start.' }
Add-Content -LiteralPath $env:GITHUB_ENV -Value "RUSTUP_HOME=$env:RUSTUP_HOME"
Add-Content -LiteralPath $env:GITHUB_ENV -Value "CARGO_HOME=$env:CARGO_HOME"
Add-Content -LiteralPath $env:GITHUB_PATH -Value $bin
Write-Output 'Pinned Rust/Cargo toolchain is ready for subsequent build steps.'
