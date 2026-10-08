#!/usr/bin/env bash
# Fresh-process test of the settled Modern tour overview, not a mock renderer.
set -Eeuo pipefail
if [ "${1:-}" = "--inside" ]; then
  shift
  EXE="$1"; ROM="$2"; SCRIPT="$3"; LOG="$4"; DUMPS="$5"; ACTION="$6"
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
  xdotool key F7

  if [ "$ACTION" = "authentic" ]; then
    sleep 0.15
    ! grep -q "UR_TOUR_OVERVIEW OPENED" "$LOG"
    kill "$PID" 2>/dev/null || true
    wait "$PID" 2>/dev/null || true
    exit 0
  fi

  for _ in $(seq 1 250); do
    grep -q "UR_TOUR_OVERVIEW OPENED rider=0 bronze=0 silver=0 gold=0 visible=0055" "$LOG" && break
    kill -0 "$PID" 2>/dev/null || exit 1
    sleep 0.02
  done
  grep -q "UR_TOUR_OVERVIEW OPENED rider=0 bronze=0 silver=0 gold=0 visible=0055" "$LOG"

  for _ in $(seq 1 250); do
    grep -q "UR_TOUR_OVERVIEW PRESENT scale=" "$LOG" && break
    kill -0 "$PID" 2>/dev/null || exit 1
    sleep 0.02
  done
  grep -q "UR_TOUR_OVERVIEW PRESENT scale=" "$LOG"

  xdotool key Escape
  for _ in $(seq 1 250); do
    grep -q "UR_TOUR_OVERVIEW CLOSED" "$LOG" && break
    kill -0 "$PID" 2>/dev/null || exit 1
    sleep 0.02
  done
  grep -q "UR_TOUR_OVERVIEW CLOSED" "$LOG"
  ! grep -q "UR_PRACTICE STARTED" "$LOG"
  ! grep -q "UR_TOUR_CONTINUE STARTED" "$LOG"
  ! grep -q "UR_PROFILE_AUTOSAVE RESULT" "$LOG"
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
echo "UR_TOUR_OVERVIEW_ACCEPTANCE=passed"
