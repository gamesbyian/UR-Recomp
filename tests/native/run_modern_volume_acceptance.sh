#!/usr/bin/env bash
set -Eeuo pipefail

# Native Volume acceptance. Volume is the framework's own [Sound] Volume
# (config.ini, keypad +/-, OSD bar); the Modern Options VOLUME row only steps
# that authority. A player lowers it from pause -> Options -> VOLUME with the
# real keys, the framework writes config.ini on exit, and a fresh process
# loads the new value. Modern keeps no second copy in host state.

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <native-exe> <retail-rom> <work-dir>" >&2
  exit 2
fi

EXE="$1"
ROM="$2"
WORK="$3"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PAUSE_SCRIPT="$REPO/tests/input/modern-focus-pause.script"
mkdir -p "$WORK/user"

dump_failure_evidence() {
  local status=$?
  echo "== Modern Volume acceptance failed: status=$status ==" >&2
  for log in "$WORK"/*.log; do
    [ -f "$log" ] || continue
    echo "===== $log =====" >&2
    grep -v '^script ' "$log" >&2 || true
  done
  return "$status"
}
trap dump_failure_evidence ERR

STATE="$WORK/host-state.txt"
printf 'UR-HOST-STATE/6\nprofile=\npause_on_focus_loss=0\n' >"$STATE"
cp "$STATE" "$WORK/host-state-before.txt"

run_native() {
  local name="$1"
  shift
  env "$@" \
    SDL_AUDIODRIVER=dummy \
    UR_PRODUCT_DIAGNOSTICS=1 \
    SNESRECOMP_USER_DATA_DIR="$WORK/user" \
    UR_HOST_STATE_PATH="$STATE" \
    timeout 200s xvfb-run -a "$EXE" "$ROM" --script "$PAUSE_SCRIPT" \
      >"$WORK/$name.log" 2>&1
}

percent_of() {
  sed -n "s/^$2 percent=\([0-9][0-9]*\)$/\1/p" "$1" | tail -n 1
}

# 1. Lower the volume through the Options row: Left, Left, Enter = -5%.
run_native adjust UR_VOLUME_OPTIONS_ACCEPTANCE=adjust
grep -v '^script ' "$WORK/adjust.log" || true
grep -q "UR_PAUSE_OPTIONS OPENED" "$WORK/adjust.log"
! grep -q "UR_VOLUME_ACCEPTANCE ROW_NOT_REACHED" "$WORK/adjust.log"
START=$(percent_of "$WORK/adjust.log" "UR_VOLUME_ACCEPTANCE START")
test -n "$START"
test "$START" -ge 10
test "$(grep -c '^UR_VOLUME SELECTED percent=' "$WORK/adjust.log")" -eq 3
EXPECTED=$((START - 5))
test "$(percent_of "$WORK/adjust.log" "UR_VOLUME SELECTED")" -eq "$EXPECTED"
grep -q "^Volume = $EXPECTED$" "$WORK/user/config.ini"
echo "UR_VOLUME_ADJUST_NATIVE=start=$START selected=$EXPECTED"

# The framework config is the only store that changed.
cmp -s "$STATE" "$WORK/host-state-before.txt"

# 2. A fresh process loads the persisted framework value.
run_native verify UR_VOLUME_OPTIONS_ACCEPTANCE=verify
LOADED=$(percent_of "$WORK/verify.log" "UR_VOLUME_ACCEPTANCE START")
test "$LOADED" -eq "$EXPECTED"
! grep -q "^UR_VOLUME SELECTED" "$WORK/verify.log"
echo "UR_VOLUME_PERSIST_NATIVE=fresh_process loaded=$LOADED"

echo "UR_VOLUME_ACCEPTANCE_RESULT=options_row_steps_framework_volume_persisted_fresh_process_no_host_state_copy"
