#!/usr/bin/env bash
# Native SDL acceptance: two consecutive real Practice finishes and repeats.
# The first repeat is the existing one-shot acceptance hook. The second uses
# the actual R keyboard shortcut, observed by the shipping host.
set -Eeuo pipefail

if [ "${1:-}" = "--inside" ]; then
  shift
  EXE="$1"; ROM="$2"; SCRIPT="$3"; LOG="$4"; DUMPS="$5"
  "$EXE" "$ROM" --script "$SCRIPT" >"$LOG" 2>&1 &
  PID=$!
  trap 'kill "$PID" 2>/dev/null || true' EXIT
  for _ in $(seq 1 2400); do
    [ -s "$DUMPS/practice-repeat-second-results.wram.bin" ] && break
    kill -0 "$PID" 2>/dev/null || { cat "$LOG" >&2; exit 1; }
    sleep 0.05
  done
  [ -s "$DUMPS/practice-repeat-second-results.wram.bin" ]
  WIN=""
  for _ in $(seq 1 100); do
    WIN="$(xdotool search --pid "$PID" 2>/dev/null | head -n1 || true)"
    [ -n "$WIN" ] && break
    kill -0 "$PID" 2>/dev/null || exit 1
    sleep 0.05
  done
  [ -n "$WIN" ]
  xdotool windowfocus "$WIN"
  xdotool key --clearmodifiers r
  wait "$PID"
  exit 0
fi

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <native-exe> <retail-rom> <work-dir>" >&2
  exit 2
fi
EXE="$1"; ROM="$2"; WORK="$3"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$REPO/tests/input/modern-practice-two-repeat-cycles.script"
DUMPS="$WORK/dumps"
LOG="$WORK/practice-two-repeat-cycles.log"
PRACTICE_ROOT="$WORK/practice-save"
PRACTICE_INPUT="$WORK/practice-input.txt"
RUN="$WORK/practice-completed.urrun"
mkdir -p "$WORK"
rm -rf "$DUMPS" "$PRACTICE_ROOT"
mkdir -p "$DUMPS" "$PRACTICE_ROOT"

SDL_AUDIODRIVER=dummy \
UR_PRODUCT_DIAGNOSTICS=1 \
UR_PRACTICE_ACCEPTANCE=1 \
UR_FAST_REPEAT_ACCEPTANCE=1 \
UR_PRACTICE_SAVE_ROOT="$PRACTICE_ROOT" \
UR_PRACTICE_INPUT_PATH="$PRACTICE_INPUT" \
UR_RUN_RECORD_CAPTURE_PATH="$RUN" \
SNESRECOMP_DUMP_DIR="$DUMPS" \
  timeout 240s xvfb-run -a bash "$0" --inside "$EXE" "$ROM" "$SCRIPT" "$LOG" "$DUMPS"

cat "$LOG"
[ "$(grep -c 'UR_FAST_NAV REPEAT_PRACTICE' "$LOG")" -eq 2 ]
[ "$(grep -c 'UR_FAST_NAV REPEAT_VERIFIED sram_equal=1 course_equal=1 practice=1' "$LOG")" -eq 2 ]
! grep -q 'UR_PROFILE_AUTOSAVE RESULT' "$LOG"
test ! -e "$RUN"
test ! -e "$RUN.input"
test ! -e "$RUN.urghost"
python3 - \
  "$DUMPS/practice-repeat-first-race.wram.bin" \
  "$DUMPS/practice-repeat-second-race.wram.bin" \
  "$DUMPS/practice-repeat-third-race.wram.bin" \
  "$DUMPS/practice-repeat-first-results.wram.bin" \
  "$DUMPS/practice-repeat-second-results.wram.bin" <<'PYINNER'
from pathlib import Path
import sys
first, second, third, result1, result2 = (Path(x).read_bytes() for x in sys.argv[1:])
if not all(len(data) > 0x0313 for data in (first, second, third, result1, result2)):
    raise SystemExit("truncated native WRAM dump")
if any(data[0x0313] != 1 for data in (first, second, third)):
    raise SystemExit("one of the three authoritative races was not active")
if any(data[0x009F] != 0x99 for data in (result1, result2)):
    raise SystemExit("one of the two completed races lacked stock results")
tracks = [data[0x00CE] for data in (first, second, third)]
if len(set(tracks)) != 1:
    raise SystemExit(f"Practice course changed over repeats: {tracks}")
print(f"UR_PRACTICE_TWO_REPEAT_CYCLES=passed course={tracks[0]} results=2 repeats=2")
PYINNER
