#!/usr/bin/env bash
# Single-source shipping package check; hosted runs serially, HP may run
# concurrently only with the two disjoint offscreen package checks.
# No self-hosted PR routing or release acceptance changes.
set -euo pipefail
# Invoke the exact shipped verifier in launch mode. It uses native
# Expand-Archive internally and boots the actual product executable.
# This catches path quoting failures that a harmless cmd stub cannot.
SPECIAL_EXTRACT="$RUNNER_TEMP/package & bang! (installed)"
SPECIAL_DUMPS="$RUNNER_TEMP/package-special-path-dumps"
test ! -e "$SPECIAL_EXTRACT"
mkdir -p "$SPECIAL_DUMPS"
VERIFIER_WIN="$(cygpath -w "$GITHUB_WORKSPACE/tools/Test-URRecompPortable.ps1")"
ARCHIVE_WIN="$(cygpath -w "$PACKAGE_ARCHIVE")"
CHECKSUM_WIN="$(cygpath -w "$PACKAGE_ARCHIVE_CHECKSUM")"
EXTRACT_WIN="$(cygpath -w "$SPECIAL_EXTRACT")"
SCRIPT_WIN="$(cygpath -w "$RUNNER_TEMP/package-boot.script")"
DUMPS_WIN="$(cygpath -w "$SPECIAL_DUMPS")"
SDL_VIDEODRIVER=offscreen \
SDL_AUDIODRIVER=dummy \
SNESRECOMP_DUMP_DIR="$DUMPS_WIN" \
  timeout 300 powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass \
    -File "$VERIFIER_WIN" -Archive "$ARCHIVE_WIN" \
    -Checksum "$CHECKSUM_WIN" -Destination "$EXTRACT_WIN" \
    -InputScript "$SCRIPT_WIN" \
    | tee "$RUNNER_TEMP/package-special-path-verifier.log"
grep -Fq "UR_PORTABLE_REAL_WINDOWS_LAUNCH_EXITED_OK" "$RUNNER_TEMP/package-special-path-verifier.log"
grep -Fq "UR_PORTABLE_CLEAN_MACHINE_PACKAGE_OK" "$RUNNER_TEMP/package-special-path-verifier.log"

SPECIAL_PACKAGE="$SPECIAL_EXTRACT/UR-Recomp-Windows-x64"
SPECIAL_USER="$SPECIAL_EXTRACT/isolated-user-data"
SPECIAL_CALLER="$SPECIAL_EXTRACT/unrelated launch working directory"
PACKAGE_WIN="$(cygpath -w "$SPECIAL_PACKAGE")"
USER_WIN="$(cygpath -w "$SPECIAL_USER")"
STARTUP_LOG="$SPECIAL_USER/diagnostics/startup.log"
test -f "$STARTUP_LOG"
grep -Fq "package_root=$PACKAGE_WIN" "$STARTUP_LOG"
grep -Fq "user_data_root=$USER_WIN" "$STARTUP_LOG"
grep -Fq "process_exit=0" "$STARTUP_LOG"
test ! -e "$SPECIAL_CALLER/config.ini"
test ! -e "$SPECIAL_CALLER/keybinds.ini"
test ! -e "$SPECIAL_CALLER/saves"
test ! -e "$SPECIAL_PACKAGE/config.ini"
test ! -e "$SPECIAL_PACKAGE/saves"
python - "$SPECIAL_DUMPS/package-main-menu.wram.bin" <<'PY'
from pathlib import Path
import sys
wram = Path(sys.argv[1]).read_bytes()
assert wram[0x9F] == 0xD7, "special-path packaged main menu not reached"
print("WINDOWS_PACKAGE_SPECIAL_PATH_MAIN_MENU ok")
PY
python tools/assemble_windows_package.py verify --package "$SPECIAL_PACKAGE"
echo "WINDOWS_PACKAGE_SPECIAL_PATH_ISOLATION ok"
