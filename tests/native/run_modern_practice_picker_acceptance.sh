#!/usr/bin/env bash
# Fresh-process Windows-product host route on the SDL desktop adapter.
# Real keyboard events exercise the shipping modal and canonical stock route.
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
  [ -s "$DUMPS/practice-main-menu.wram.bin" ]
  WIN=""
  for _ in $(seq 1 100); do
    WIN=$(xdotool search --pid "$PID" 2>/dev/null | head -n1 || true)
    [ -n "$WIN" ] && break
    kill -0 "$PID" 2>/dev/null || exit 1
    sleep 0.05
  done
  [ -n "$WIN" ]
  xdotool windowfocus "$WIN"
  xdotool key F5

  if [ "$ACTION" = "authentic" ]; then
    sleep 0.15
    ! grep -q "UR_PRACTICE_PICKER OPENED" "$LOG"
    ! grep -q "UR_PRACTICE STARTED" "$LOG"
    kill "$PID" 2>/dev/null || true
    wait "$PID" 2>/dev/null || true
    exit 0
  fi

  for _ in $(seq 1 250); do
    grep -q "UR_PRACTICE_PICKER OPENED track=0 available=40" "$LOG" && break
    kill -0 "$PID" 2>/dev/null || exit 1
    sleep 0.02
  done
  grep -q "UR_PRACTICE_PICKER OPENED track=0 available=40" "$LOG"
  for _ in $(seq 1 250); do
    grep -q "UR_PRACTICE_PICKER PRESENT scale=" "$LOG" && break
    sleep 0.02
  done
  grep -q "UR_PRACTICE_PICKER PRESENT scale=" "$LOG"

  if [ "$ACTION" = "cancel" ]; then
    # Previous-tour wrapping must skip Hunter and retain the same slot.
    xdotool key Left
    for _ in $(seq 1 250); do
      grep -q "UR_PRACTICE_PICKER SELECTED track=35" "$LOG" && break
      sleep 0.02
    done
    grep -q "UR_PRACTICE_PICKER SELECTED track=35" "$LOG"
    xdotool key Escape
    for _ in $(seq 1 250); do
      grep -q "UR_PRACTICE_PICKER CANCELLED" "$LOG" && break
      sleep 0.02
    done
    grep -q "UR_PRACTICE_PICKER CANCELLED" "$LOG"
    ! grep -q "UR_PRACTICE STARTED" "$LOG"
    kill "$PID" 2>/dev/null || true
    wait "$PID" 2>/dev/null || true
    exit 0
  fi

  # Two stock catalog tours forward, preserving slot 1:
  # Crawler/Dragster (0) -> Jumper/Wobble (5) -> Shuffler/Looper (10).
  xdotool key Right
  for _ in $(seq 1 250); do
    grep -q "UR_PRACTICE_PICKER SELECTED track=5" "$LOG" && break
    sleep 0.02
  done
  grep -q "UR_PRACTICE_PICKER SELECTED track=5" "$LOG"
  xdotool key Right
  for _ in $(seq 1 250); do
    grep -q "UR_PRACTICE_PICKER SELECTED track=10" "$LOG" && break
    sleep 0.02
  done
  grep -q "UR_PRACTICE_PICKER SELECTED track=10" "$LOG"
  xdotool key Return
  for _ in $(seq 1 250); do
    grep -q "UR_PRACTICE_PICKER CONFIRMED track=10" "$LOG" && break
    sleep 0.02
  done
  grep -q "UR_PRACTICE_PICKER CONFIRMED track=10" "$LOG"
  wait "$PID"
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
  local name="$1"
  local dumps="$WORK/$name-dumps"
  local log="$WORK/$name.log"
  local home="$WORK/$name-data"
  local practice="$WORK/$name-practice"
  local run="$WORK/$name-run.urrun"
  mkdir -p "$dumps" "$home" "$practice"
  local mode=modern
  [ "$name" = "authentic" ] && mode=authentic

  SDL_AUDIODRIVER=dummy \
    UR_EXECUTION_MODE="$mode" \
    XDG_DATA_HOME="$home" \
    SNESRECOMP_DUMP_DIR="$dumps" \
    UR_PRODUCT_DIAGNOSTICS=1 \
    UR_ONBOARDING_STATE_PATH="$WORK/onboarding.seen" \
    UR_PRACTICE_SAVE_ROOT="$practice" \
    UR_PRACTICE_INPUT_PATH="$WORK/$name-input.txt" \
    UR_RUN_RECORD_CAPTURE_PATH="$run" \
    UR_EXIT_FRONTEND_ACCEPTANCE=active \
    timeout 120s xvfb-run -a bash "$0" --inside \
      "$EXE" "$ROM" "$SCRIPT" "$log" "$dumps" "$name"

  cat "$log"
  if [ "$name" = "launch" ]; then
    grep -q "UR_PRACTICE STARTED .*track=10" "$log"
    grep -q "UR_PRACTICE RACE_READY" "$log"
    grep -q "UR_PRACTICE RESTORED" "$log"
    grep -q "UR_EXIT_FRONTEND FRONTEND_READY menu=D7" "$log"
    ! grep -q "UR_PROFILE_AUTOSAVE RESULT" "$log"
    test ! -e "$run"
    test ! -e "$run.input"
    test ! -e "$run.urghost"
    python3 - "$dumps/practice-race-entered.wram.bin" <<'PY'
from pathlib import Path
import sys
wram = Path(sys.argv[1]).read_bytes()
if wram[0x0313] != 1 or wram[0x00CE] != 10:
    raise SystemExit(
        f"picker did not launch canonical Shuffler/Looper: "
        f"race={wram[0x0313]} course={wram[0x00CE]}")
print("UR_PRACTICE_PICKER_RESULT=canonical_track_10")
PY
    local before after
    before="$(sed -nE 's/.*UR_PRACTICE STARTED sram=([0-9A-F]+).*/\1/p' "$log" | tail -1)"
    after="$(sed -nE 's/.*UR_PRACTICE RESTORED sram=([0-9A-F]+).*/\1/p' "$log" | tail -1)"
    test -n "$before" && test "$before" = "$after"
  fi
}

run_case cancel
run_case launch
run_case authentic
echo "UR_PRACTICE_PICKER_ACCEPTANCE=passed"
