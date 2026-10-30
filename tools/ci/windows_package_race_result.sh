#!/usr/bin/env bash
# Exact packaged Windows race-result contract. Shared between hosted serial
# acceptance and HP-only overlapped acceptance; never accept prior-run dumps.
set -euo pipefail
DUMPS="$RUNNER_TEMP/package-race-result-dumps"
rm -rf -- "$DUMPS"
mkdir -p "$DUMPS"
rm -f -- "$RUNNER_TEMP/package-race-result.log"
PACKAGE_WIN="$(cygpath -w "$TEST_PACKAGE")"
USER_DATA_WIN="$(cygpath -w "$PACKAGE_USER_DATA")"
SCRIPT_WIN="$(cygpath -w "$GITHUB_WORKSPACE/tests/input/ui-race-result-route.script")"
DUMPS_WIN="$(cygpath -w "$DUMPS")"
set +e
SDL_VIDEODRIVER=offscreen \
SDL_AUDIODRIVER=dummy \
SNESRECOMP_DUMP_DIR="$DUMPS_WIN" \
UR_RECOMP_USER_DATA_ROOT="$USER_DATA_WIN" \
  timeout 600 powershell.exe -NoProfile -Command \
    "& '${PACKAGE_WIN}\\run-uniracers.cmd' --script '${SCRIPT_WIN}'; exit \$LASTEXITCODE" \
    >"$RUNNER_TEMP/package-race-result.log" 2>&1
RC=$?
set -e
tail -n 50 "$RUNNER_TEMP/package-race-result.log"
test "$RC" -eq 0
python tools/check_result_screen_time.py \
  --dump-dir "$DUMPS" \
  --checkpoint race-results
grep -Fq "Config/saves anchored to user data" "$RUNNER_TEMP/package-race-result.log"
grep -Fq "$USER_DATA_WIN" "$RUNNER_TEMP/package-race-result.log"
python tools/assemble_windows_package.py verify --package "$TEST_PACKAGE"
echo "WINDOWS_PACKAGE_RACE_RESULT ok"
