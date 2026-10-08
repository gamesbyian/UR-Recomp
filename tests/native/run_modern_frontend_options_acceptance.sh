#!/usr/bin/env bash
# Real Windows-equivalent desktop frontend Options admission and Authentic isolation.
set -Eeuo pipefail

if [ "${1:-}" = "--inside" ]; then
  shift
  EXE="$1"; ROM="$2"; SCRIPT="$3"; LOG="$4"; DUMPS="$5"; MODE="$6"
  "$EXE" "$ROM" --script "$SCRIPT" >"$LOG" 2>&1 &
  PID=$!
  trap 'kill "$PID" 2>/dev/null || true' EXIT

  for _ in $(seq 1 600); do
    [ -s "$DUMPS/practice-main-menu.wram.bin" ] && break
    kill -0 "$PID" 2>/dev/null || exit 1
    sleep 0.05
  done
  test -s "$DUMPS/practice-main-menu.wram.bin"

  WIN=""
  for _ in $(seq 1 100); do
    WIN="$(xdotool search --pid "$PID" 2>/dev/null | head -n1 || true)"
    [ -n "$WIN" ] && break
    kill -0 "$PID" 2>/dev/null || exit 1
    sleep 0.05
  done
  test -n "$WIN"
  xdotool windowfocus "$WIN"
  xdotool key F10

  if [ "$MODE" = "authentic" ]; then
    sleep 0.15
    ! grep -q "UR_FRONTEND_OPTIONS OPENED" "$LOG"
    ! grep -q "UR_FRONTEND_OPTIONS PRESENT" "$LOG"
    kill "$PID" 2>/dev/null || true
    wait "$PID" 2>/dev/null || true
    exit 0
  fi

  for _ in $(seq 1 250); do
    grep -q "UR_FRONTEND_OPTIONS OPENED" "$LOG" && break
    kill -0 "$PID" 2>/dev/null || exit 1
    sleep 0.02
  done
  grep -q "UR_FRONTEND_OPTIONS OPENED" "$LOG"
  for _ in $(seq 1 250); do
    grep -q "UR_FRONTEND_OPTIONS PRESENT scale=" "$LOG" && break
    kill -0 "$PID" 2>/dev/null || exit 1
    sleep 0.02
  done
  grep -q "UR_FRONTEND_OPTIONS PRESENT scale=" "$LOG"

  # The shipping pause Options model has nine steps from Focus Pause to
  # Volume. Change the framework's real volume (not a host copy).
  xdotool key --repeat 9 --delay 55 Down
  xdotool key Right
  for _ in $(seq 1 250); do
    grep -q "UR_VOLUME SELECTED percent=" "$LOG" && break
    kill -0 "$PID" 2>/dev/null || exit 1
    sleep 0.02
  done
  grep -q "UR_VOLUME SELECTED percent=" "$LOG"

  # Closing the modal must not resume/advance stock navigation or launch play.
  xdotool key F10
  for _ in $(seq 1 250); do
    grep -q "UR_FRONTEND_OPTIONS CLOSED" "$LOG" && break
    kill -0 "$PID" 2>/dev/null || exit 1
    sleep 0.02
  done
  grep -q "UR_FRONTEND_OPTIONS CLOSED" "$LOG"
  ! grep -q "UR_PRACTICE STARTED" "$LOG"
  ! grep -q "UR_TOUR_CONTINUE STARTED" "$LOG"
  ! grep -q "UR_PAUSE_OPTIONS OPENED" "$LOG"
  kill "$PID" 2>/dev/null || true
  wait "$PID" 2>/dev/null || true
  exit 0
fi

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <native-exe> <retail-rom> <work-dir>" >&2
  exit 2
fi
EXE="$1"; ROM="$2"; WORK="$3"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$REPO/tests/input/modern-practice-route.script"
mkdir -p "$WORK"
printf 'seen-v1\n' >"$WORK/onboarding.seen"

run_case() {
  local mode="$1"
  mkdir -p "$WORK/$mode-data" "$WORK/$mode-dumps"
  SDL_AUDIODRIVER=dummy \
    UR_EXECUTION_MODE="$mode" \
    UR_PRODUCT_DIAGNOSTICS=1 \
    UR_ONBOARDING_STATE_PATH="$WORK/onboarding.seen" \
    XDG_DATA_HOME="$WORK/$mode-data" \
    SNESRECOMP_DUMP_DIR="$WORK/$mode-dumps" \
    timeout 110s xvfb-run -a bash "$0" --inside \
      "$EXE" "$ROM" "$SCRIPT" "$WORK/$mode.log" \
      "$WORK/$mode-dumps" "$mode"
  cat "$WORK/$mode.log"
}
run_case modern
run_case authentic
echo "UR_FRONTEND_OPTIONS_ACCEPTANCE=passed"
