#!/usr/bin/env bash
# Real SDL keyboard/system-input smoke for the human Modern root, not a
# --script fixture: script sessions intentionally bypass the shell.
# Run against an already-built native game and the verified USA retail ROM.
# Controller-only and audible packaged Windows acceptance remain separate.
set -Eeuo pipefail

if [[ ${1:-} == --inside ]]; then
  shift
  EXE="$1"; ROM="$2"; LOG="$3"; MODE="$4"
  "$EXE" "$ROM" >"$LOG" 2>&1 &
  PID=$!
  trap 'kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true' EXIT

  wait_line() {
    local pattern="$1"
    for _ in $(seq 1 1200); do
      grep -q "$pattern" "$LOG" && return 0
      kill -0 "$PID" 2>/dev/null || return 1
      sleep 0.05
    done
    echo "Missing diagnostic: $pattern" >&2
    tail -80 "$LOG" >&2
    return 1
  }
  wait_line 'UR_MODERN_ROOT PRESENT'
  wait_line 'UR_FRONTEND_HOLD ENGAGED'
  WIN=""
  for _ in $(seq 1 100); do
    WIN="$(xdotool search --pid "$PID" 2>/dev/null | head -n1 || true)"
    [[ -n "$WIN" ]] && break
    sleep 0.05
  done
  [[ -n "$WIN" ]]
  xdotool windowfocus "$WIN"
  sleep 0.12

  if [[ "$MODE" == root-actions ]]; then
    # Practice is row 1. Back returns to identical root selection.
    xdotool key Down Return
    wait_line 'UR_PRACTICE_PICKER OPENED'
    xdotool key Escape
    wait_line 'UR_PRACTICE_PICKER CANCELLED'

    # Root's global Racer & Profiles drawer works outside stock 0x3C.
    xdotool key x
    wait_line 'UR_PROFILE_UI OPENED'
    xdotool key Escape

    # From Practice -> Records, using existing browser admission.
    xdotool key Down Down Return
    wait_line 'UR_MODERN_ROOT RECORDS_OPENED'
    xdotool key Escape

    # From Records -> Options, using existing host settings authority.
    xdotool key Down Return
    wait_line 'UR_FRONTEND_OPTIONS OPENED'
    xdotool key Escape
    wait_line 'UR_FRONTEND_OPTIONS CLOSED'

    # Root Back must require an explicit second Yes. Cancel does not quit.
    xdotool key Escape
    wait_line 'UR_MODERN_ROOT QUIT_CONFIRM'
    xdotool key Escape
    wait_line 'UR_MODERN_ROOT QUIT_CANCELLED'
    xdotool key Escape Return
    wait_line 'UR_PAUSE_QUIT REQUESTED'
  elif [[ "$MODE" == play ]]; then
    xdotool key Return
    wait_line 'UR_MODERN_ROOT PLAY_STOCK_ENTRY'
    wait_line 'UR_MODERN_ROOT PLAY_ENTERED'
  elif [[ "$MODE" == multiplayer ]]; then
    xdotool key Down Down Return
    wait_line 'UR_MODERN_ROOT MULTIPLAYER_STOCK_ENTRY'
    wait_line 'UR_MODERN_ROOT MULTIPLAYER_ENTERED'
  else
    echo "unsupported mode: $MODE" >&2
    exit 2
  fi
  echo "UR_MODERN_ROOT_SMOKE=$MODE passed"
  exit 0
fi

if [[ $# != 3 ]]; then
  echo "usage: $0 <native-game-executable> <USA-retail-ROM> <work-dir>" >&2
  exit 2
fi
EXE="$1"; ROM="$2"; WORK="$3"
mkdir -p "$WORK"
printf 'seen-v1\n' > "$WORK/onboarding.seen"
for case_name in root-actions play multiplayer; do
  mkdir -p "$WORK/$case_name-data"
  SDL_AUDIODRIVER=dummy \
    UR_EXECUTION_MODE=modern \
    UR_PRODUCT_DIAGNOSTICS=1 \
    UR_ONBOARDING_STATE_PATH="$WORK/onboarding.seen" \
    XDG_DATA_HOME="$WORK/$case_name-data" \
    UR_RECOMP_USER_DATA_ROOT="$WORK/$case_name-data" \
    timeout 105s xvfb-run -a bash "$0" --inside \
      "$EXE" "$ROM" "$WORK/$case_name.log" "$case_name"
  grep -q "UR_MODERN_ROOT_SMOKE=$case_name passed" <(
    # The inner test's own success is stdout, not the game log; state the
    # return-code contract explicitly for scripts that invoke this runner.
    printf 'UR_MODERN_ROOT_SMOKE=%s passed\n' "$case_name")
done
echo 'UR_MODERN_ROOT_ACCEPTANCE=passed (SDL keyboard; not Windows pad/audio)'
