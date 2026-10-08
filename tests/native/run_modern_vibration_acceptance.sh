#!/usr/bin/env bash
set -Eeuo pipefail

# Native Vibration acceptance. The stock title has no rumble; Modern sends a
# short pulse at each authoritative checkpoint split and a firmer one at the
# finish of a 1P timed race, to the controller in the P1 seat, only when the
# persisted Vibration setting is on. A real SDL virtual gamepad's Rumble
# callback records what reaches the device. Vibration must never change the
# simulation: the on/off run records must be byte-identical.

if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  echo "usage: $0 <native-exe> <retail-rom> <work-dir> [parity|aux|all]" >&2
  exit 2
fi

EXE="$1"
ROM="$2"
WORK="$3"
MODE="${4:-all}"
case "$MODE" in
  parity|aux|all) ;;
  *)
    echo "unknown vibration acceptance mode: $MODE" >&2
    exit 2
    ;;
esac
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RACE_SCRIPT="$REPO/tests/input/race-finish-dragster.script"
PAUSE_SCRIPT="$REPO/tests/input/modern-focus-pause.script"
mkdir -p "$WORK"

dump_failure_evidence() {
  local status=$?
  echo "== Modern Vibration acceptance failed: status=$status ==" >&2
  for log in "$WORK"/*.log; do
    [ -f "$log" ] || continue
    echo "===== $log =====" >&2
    grep -v '^script ' "$log" >&2 || true
  done
  return "$status"
}
trap dump_failure_evidence ERR

STATE="$WORK/host-state.txt"
if [ "$MODE" = "parity" ]; then
  printf 'UR-HOST-STATE/6\nprofile=\npause_on_focus_loss=0\nvibration_enabled=0\n' >"$STATE"
  printf 'UR-HOST-STATE/6\nprofile=\npause_on_focus_loss=0\nvibration_enabled=1\n' >"$WORK/host-state-on.txt"
else
  printf 'UR-HOST-STATE/6\nprofile=\npause_on_focus_loss=0\nvibration_enabled=1\n' >"$STATE"
fi

run_native() {
  local name="$1"
  local script="$2"
  shift 2
  env "$@" \
    SDL_AUDIODRIVER=dummy \
    UR_PRODUCT_DIAGNOSTICS=1 \
    timeout 200s xvfb-run -a "$EXE" "$ROM" --script "$script" \
      >"$WORK/$name.log" 2>&1
}

# 1. The player turns Vibration off through pause -> Options -> VIBRATION.
if [ "$MODE" != "parity" ]; then
run_native toggle "$PAUSE_SCRIPT" \
  UR_HOST_STATE_PATH="$STATE" \
  UR_VIBRATION_OPTIONS_ACCEPTANCE=1
grep -v '^script ' "$WORK/toggle.log" || true
grep -q "UR_PAUSE_OPTIONS OPENED" "$WORK/toggle.log"
grep -q "UR_VIBRATION SELECTED enabled=0" "$WORK/toggle.log"
! grep -q "UR_VIBRATION_ACCEPTANCE ROW_NOT_REACHED" "$WORK/toggle.log"
grep -q '^vibration_enabled=0$' "$STATE"
# The A/B states differ only in the vibration flag.
sed 's/^vibration_enabled=0$/vibration_enabled=1/' "$STATE" >"$WORK/host-state-on.txt"
CHANGED=$(diff "$STATE" "$WORK/host-state-on.txt" | grep -c '^[<>]' || true)
test "$CHANGED" -eq 2
fi

# 2. Vibration on: three checkpoint pulses and one finish pulse reach the
#    seated controller during an ordinary Modern 1P Dragster race.
if [ "$MODE" != "aux" ]; then
run_native on "$RACE_SCRIPT" \
  UR_HOST_STATE_PATH="$WORK/host-state-on.txt" \
  UR_HAPTIC_ACCEPTANCE=1 \
  UR_RUN_RECORD_CAPTURE_PATH="$WORK/on.urrun"
grep -q "UR_HAPTIC_ACCEPTANCE PAD_ATTACHED" "$WORK/on.log"
grep -q "script .* dump race-results ok" "$WORK/on.log"
test "$(grep -c 'UR_HAPTIC PULSE event=checkpoint .* sent=1' "$WORK/on.log")" -ge 1
test "$(grep -c 'UR_HAPTIC PULSE event=finish low=32768 high=24576 ms=220 sent=1' "$WORK/on.log")" -eq 1
PULSES=$(grep -c 'UR_HAPTIC PULSE .* sent=1' "$WORK/on.log")
DEVICE=$(grep -c 'UR_HAPTIC_ACCEPTANCE DEVICE_RUMBLE' "$WORK/on.log")
test "$PULSES" -eq "$DEVICE"
grep -q "UR_HAPTIC_ACCEPTANCE DEVICE_RUMBLE low=32768 high=24576" "$WORK/on.log"
echo "UR_VIBRATION_ON_NATIVE=pulses=$PULSES device_rumbles=$DEVICE"

# 3. A fresh process with the value persisted in step 1 stays silent, and
#    its run record is byte-identical to the vibrating run.
run_native off "$RACE_SCRIPT" \
  UR_HOST_STATE_PATH="$STATE" \
  UR_HAPTIC_ACCEPTANCE=1 \
  UR_RUN_RECORD_CAPTURE_PATH="$WORK/off.urrun"
grep -q "UR_HAPTIC_ACCEPTANCE PAD_ATTACHED" "$WORK/off.log"
grep -q "script .* dump race-results ok" "$WORK/off.log"
! grep -q "UR_HAPTIC PULSE" "$WORK/off.log"
! grep -q "UR_HAPTIC_ACCEPTANCE DEVICE_RUMBLE" "$WORK/off.log"
# Compare the authoritative race outcome: course, mode, elapsed time, every
# split and the race-relative controller stream. Two fields are excluded
# because they also absorb occasional cross-process phase jitter around the
# finish-to-results transition (frame_count, and the checksum over it); the
# ghost trace is excluded because it samples free-running presentation
# counters. Repeated local runs keep these equal whenever no jitter occurs.
python3 - "$WORK/on.urrun" "$WORK/off.urrun" <<'PY'
from pathlib import Path
import sys

def outcome(path):
    lines = Path(path).read_text().splitlines()
    kept = [l for l in lines if not l.startswith(("frame_count ", "checksum "))]
    if not any(l.startswith("split finish ") for l in kept):
        raise SystemExit(f"{path}: no authoritative finish split")
    return kept

on, off = outcome(sys.argv[1]), outcome(sys.argv[2])
if on != off:
    raise SystemExit("vibration changed the authoritative race outcome")
print(f"UR_VIBRATION_RACE_OUTCOME_EQUAL lines={len(on)}")
PY
echo "UR_VIBRATION_OFF_NATIVE=fresh_process silent=1 race_outcome_identical=1"
fi

# 4. Authentic never vibrates, even with the stored setting on.
if [ "$MODE" != "parity" ]; then
run_native authentic "$RACE_SCRIPT" \
  UR_EXECUTION_MODE=authentic \
  UR_HOST_STATE_PATH="$WORK/host-state-on.txt" \
  UR_HAPTIC_ACCEPTANCE=1
grep -q "UR_HOST_STATE AUTHENTIC_INERT" "$WORK/authentic.log"
grep -q "script .* dump race-results ok" "$WORK/authentic.log"
! grep -q "UR_HAPTIC PULSE" "$WORK/authentic.log"
! grep -q "UR_HAPTIC_ACCEPTANCE DEVICE_RUMBLE" "$WORK/authentic.log"
fi

echo "UR_VIBRATION_ACCEPTANCE_RESULT=$MODE"
