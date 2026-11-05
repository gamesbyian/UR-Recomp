#!/usr/bin/env bash
# Single-source shipping package check; hosted runs serially, HP may run
# concurrently only with the two disjoint offscreen package checks.
# No self-hosted PR routing or release acceptance changes.
set -euo pipefail
# Exercise a player launch with NO explicit UR_RECOMP_USER_DATA_ROOT.
# The normal profile Roaming root is authoritative for first boot.
APPDATA_DIR="$RUNNER_TEMP/default player roaming data"
DEFAULT_USER_DATA="$APPDATA_DIR/gamesbyian/UR-Recomp"
DEFAULT_CALLER="$RUNNER_TEMP/default launch caller"
DEFAULT_DUMPS="$RUNNER_TEMP/default appdata boot dumps"
mkdir -p "$APPDATA_DIR" "$DEFAULT_CALLER" "$DEFAULT_DUMPS"
test ! -e "$DEFAULT_USER_DATA"
APPDATA_WIN="$(cygpath -w "$APPDATA_DIR")"
PACKAGE_WIN="$(cygpath -w "$TEST_PACKAGE")"
SCRIPT_WIN="$(cygpath -w "$RUNNER_TEMP/package-boot.script")"
DUMPS_WIN="$(cygpath -w "$DEFAULT_DUMPS")"
DEFAULT_USER_WIN="$(cygpath -w "$DEFAULT_USER_DATA")"

set +e
(
  cd "$DEFAULT_CALLER"
  env -u UR_RECOMP_USER_DATA_ROOT \
    APPDATA="$APPDATA_WIN" \
    SDL_VIDEODRIVER=offscreen \
    SDL_AUDIODRIVER=dummy \
    SNESRECOMP_DUMP_DIR="$DUMPS_WIN" \
      timeout 300 powershell.exe -NoProfile -Command \
        "& '${PACKAGE_WIN}\\run-uniracers.cmd' --script '${SCRIPT_WIN}'; exit \$LASTEXITCODE" \
        >"$RUNNER_TEMP/package-default-appdata-boot.log" 2>&1
)
RC=$?
set -e
cat "$RUNNER_TEMP/package-default-appdata-boot.log"
test "$RC" -eq 0
python - "$DEFAULT_DUMPS/package-main-menu.wram.bin" <<'PY'
import pathlib, sys
wram = pathlib.Path(sys.argv[1]).read_bytes()
assert wram[0x9F] == 0xD7, "default APPDATA packaged main menu not reached"
print("WINDOWS_PACKAGE_DEFAULT_APPDATA_MAIN_MENU ok")
PY
test -f "$DEFAULT_USER_DATA/config.ini"
test -f "$DEFAULT_USER_DATA/keybinds.ini"
test -f "$DEFAULT_USER_DATA/mod-state.toml"
test -d "$DEFAULT_USER_DATA/saves"
test ! -e "$TEST_PACKAGE/config.ini"
test ! -e "$TEST_PACKAGE/saves"
test ! -e "$DEFAULT_CALLER/config.ini"
grep -Fq "Config/saves anchored to user data" "$RUNNER_TEMP/package-default-appdata-boot.log"
grep -Fq "$DEFAULT_USER_WIN" "$RUNNER_TEMP/package-default-appdata-boot.log"
python tools/assemble_windows_package.py verify --package "$TEST_PACKAGE"
echo "WINDOWS_PACKAGE_DEFAULT_APPDATA_ROOT ok"
