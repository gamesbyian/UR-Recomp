#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 4 ]; then
  echo "usage: $0 <exe> <rom> <title-script> <temp-root>" >&2
  exit 2
fi

EXE="$1"
ROM="$2"
TITLE_SCRIPT="$3"
TMPROOT="$4"

STATE="$TMPROOT/regional-host-state.txt"
PAL_LOG="$TMPROOT/regional-pal.log"
NTSC_LOG="$TMPROOT/regional-ntsc.log"
VERIFY_LOG="$TMPROOT/regional-verify.log"
PAL_DUMPS="$TMPROOT/regional-pal-dumps"
NTSC_DUMPS="$TMPROOT/regional-ntsc-dumps"

rm -f "$STATE" "$PAL_LOG" "$NTSC_LOG" "$VERIFY_LOG"
rm -rf "$PAL_DUMPS" "$NTSC_DUMPS"
mkdir -p "$PAL_DUMPS" "$NTSC_DUMPS"

run_secret_process() {
  local sequence="$1"
  local expected="$2"
  local expected_loaded="$3"
  local log="$4"
  local dumps="$5"

  timeout 90s xvfb-run -a bash -c '
    set -euo pipefail
    EXE="$1"
    ROM="$2"
    TITLE_SCRIPT="$3"
    STATE="$4"
    LOG="$5"
    DUMPS="$6"
    SEQUENCE="$7"
    EXPECTED="$8"
    EXPECTED_LOADED="$9"

    export SDL_AUDIODRIVER=dummy
    export UR_PRODUCT_DIAGNOSTICS=1
    export UR_HOST_STATE_PATH="$STATE"
    export SNESRECOMP_DUMP_DIR="$DUMPS"

    "$EXE" "$ROM" --script "$TITLE_SCRIPT" >"$LOG" 2>&1 &
    PID=$!

    for _ in $(seq 1 600); do
      ready=0
      [ -s "$DUMPS/regional-title-ready.wram.bin" ] && ready=1
      loaded=1
      if [ -n "$EXPECTED_LOADED" ]; then
        grep -q "UR_HOST_STATE LOADED regional_presentation=$EXPECTED_LOADED " "$LOG" || loaded=0
      fi
      if [ "$ready" -eq 1 ] && [ "$loaded" -eq 1 ]; then
        break
      fi
      kill -0 "$PID" 2>/dev/null || exit 1
      sleep 0.05
    done

    [ -s "$DUMPS/regional-title-ready.wram.bin" ]
    if [ -n "$EXPECTED_LOADED" ]; then
      grep -q "UR_HOST_STATE LOADED regional_presentation=$EXPECTED_LOADED " "$LOG"
    fi

    WIN=""
    for _ in $(seq 1 100); do
      WIN=$(xdotool search --pid "$PID" 2>/dev/null | head -n1 || true)
      [ -n "$WIN" ] && break
      sleep 0.05
    done
    [ -n "$WIN" ]

    xdotool windowfocus "$WIN"
    sleep 0.05
    # Intentional word splitting: sequence is e.g. "p a l".
    xdotool key --delay 40 $SEQUENCE

    for _ in $(seq 1 120); do
      if grep -q "UR_REGIONAL SWITCH source=keyboard presentation=$EXPECTED saved=1" "$LOG"; then
        break
      fi
      kill -0 "$PID" 2>/dev/null || true
      sleep 0.05
    done
    grep -q "UR_REGIONAL SWITCH source=keyboard presentation=$EXPECTED saved=1" "$LOG"

    wait "$PID" 2>/dev/null || true
  ' _ "$EXE" "$ROM" "$TITLE_SCRIPT" "$STATE" "$log" "$dumps"       "$sequence" "$expected" "$expected_loaded"
}

run_secret_process "p a l" "europe" "" "$PAL_LOG" "$PAL_DUMPS"
grep -q "^regional_presentation=europe$" "$STATE"

run_secret_process "n t s c" "north_america" "europe" "$NTSC_LOG" "$NTSC_DUMPS"
grep -q "^regional_presentation=north_america$" "$STATE"

SDL_AUDIODRIVER=dummy UR_PRODUCT_DIAGNOSTICS=1 UR_HOST_STATE_PATH="$STATE" timeout 90s xvfb-run -a "$EXE" "$ROM"   --script "$PWD/tests/input/modern-main-menu.script"   >"$VERIFY_LOG" 2>&1

grep -q "UR_HOST_STATE LOADED regional_presentation=north_america " "$VERIFY_LOG"

cat "$PAL_LOG"
cat "$NTSC_LOG"
cat "$VERIFY_LOG"
echo "UR_REGIONAL_RESULT=pal_saved_reloaded_ntsc_saved_reloaded"
