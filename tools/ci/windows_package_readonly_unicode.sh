#!/usr/bin/env bash
# Single-source shipping package check; hosted runs serially, HP may run
# concurrently only with the two disjoint offscreen package checks.
# No self-hosted PR routing or release acceptance changes.
# Quoted PowerShell source is intentionally literal at the Bash boundary.
set -euo pipefail
# Exercise the actual extracted shipping launcher twice. Deny NTFS
# writes to the disposable install tree, not merely its file attributes;
# user data must remain writable at a separate non-ASCII Windows path.
RO_PACKAGE="$RUNNER_TEMP/read-only portable/UR-Recomp-Windows-x64"
RO_USER="$RUNNER_TEMP/portable user café 雪"
RO_CALLER="$RUNNER_TEMP/read-only unrelated caller"
RO_DUMPS="$RUNNER_TEMP/read-only portable dumps"
test ! -e "$RO_PACKAGE"
test ! -e "$RO_USER"
mkdir -p "$(dirname "$RO_PACKAGE")" "$RO_CALLER" "$RO_DUMPS"
cp -R "$TEST_PACKAGE" "$RO_PACKAGE"
RO_PACKAGE_WIN="$(cygpath -w "$RO_PACKAGE")"
export RO_PACKAGE_WIN
RO_USER_WIN="$(cygpath -w "$RO_USER")"
RO_SCRIPT_WIN="$(cygpath -w "$RUNNER_TEMP/package-boot.script")"
export RO_SCRIPT_WIN
RO_DUMPS_WIN="$(cygpath -w "$RO_DUMPS")"

cleanup_readonly() {
  # PowerShell $ variables are literal source in the outer Bash process.
# shellcheck disable=SC2016
powershell.exe -NoProfile -NonInteractive -Command '
    $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    & icacls.exe $env:RO_PACKAGE_WIN /remove:d ("*" + $sid) /T | Out-Null
    exit $LASTEXITCODE
  ' || true
}
trap cleanup_readonly EXIT
# PowerShell $ variables are literal source in the outer Bash process.
# shellcheck disable=SC2016
powershell.exe -NoProfile -NonInteractive -Command '
  $ErrorActionPreference = "Stop"
  $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
  & icacls.exe $env:RO_PACKAGE_WIN /deny ("*" + $sid + ":(WD,AD,WA,WEA)") /T | Out-Null
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  try {
    [IO.File]::WriteAllText((Join-Path $env:RO_PACKAGE_WIN "write-probe.txt"), "unexpected")
    throw "Install tree unexpectedly writable"
  } catch [System.UnauthorizedAccessException] {
    Write-Output "WINDOWS_READONLY_INSTALL_DENIAL_VERIFIED"
  }
'
for boot in 1 2; do
  # Require each launch to produce its own fresh main-menu witness.
  rm -f "$RO_DUMPS/package-main-menu.wram.bin"
  set +e
  (
    cd "$RO_CALLER"
    # PowerShell $env references remain literal until the child command.
    # shellcheck disable=SC2016
    SDL_VIDEODRIVER=offscreen \
    SDL_AUDIODRIVER=dummy \
    SNESRECOMP_DUMP_DIR="$RO_DUMPS_WIN" \
    UR_RECOMP_USER_DATA_ROOT="$RO_USER_WIN" \
      timeout 300 powershell.exe -NoProfile -NonInteractive -Command \
        '& (Join-Path $env:RO_PACKAGE_WIN "run-uniracers.cmd") --script $env:RO_SCRIPT_WIN; exit $LASTEXITCODE' \
        >"$RUNNER_TEMP/read-only-unicode-boot-$boot.log" 2>&1
  )
  RO_RC=$?
  set -e
  cat "$RUNNER_TEMP/read-only-unicode-boot-$boot.log"
  test "$RO_RC" -eq 0
  grep -Fq "Config/saves anchored to user data" "$RUNNER_TEMP/read-only-unicode-boot-$boot.log"
  test -s "$RO_DUMPS/package-main-menu.wram.bin"
  python - "$RO_DUMPS/package-main-menu.wram.bin" <<'PY'
from pathlib import Path
import sys
wram = Path(sys.argv[1]).read_bytes()
assert wram[0x9F] == 0xD7, "read-only Unicode-path boot missed main menu"
PY
  test -f "$RO_USER/config.ini"
  test -f "$RO_USER/keybinds.ini"
  test -f "$RO_USER/mod-state.toml"
  test -d "$RO_USER/saves"
  test ! -e "$RO_PACKAGE/config.ini"
  test ! -e "$RO_PACKAGE/keybinds.ini"
  test ! -e "$RO_PACKAGE/saves"
  test ! -e "$RO_CALLER/config.ini"
  python tools/assemble_windows_package.py verify --package "$RO_PACKAGE"
  if [ "$boot" -eq 1 ]; then
    FIRST_CONFIG_SHA="$(sha256sum "$RO_USER/config.ini" | cut -d' ' -f1)"
    FIRST_KEYS_SHA="$(sha256sum "$RO_USER/keybinds.ini" | cut -d' ' -f1)"
  fi
done
test "$FIRST_CONFIG_SHA" = "$(sha256sum "$RO_USER/config.ini" | cut -d' ' -f1)"
test "$FIRST_KEYS_SHA" = "$(sha256sum "$RO_USER/keybinds.ini" | cut -d' ' -f1)"
echo "WINDOWS_READONLY_UNICODE_TWO_COLD_BOOTS ok"
