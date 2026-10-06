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
SCRIPT_DIR="$(dirname "$TITLE_SCRIPT")"
MAIN_MENU_SCRIPT="$SCRIPT_DIR/modern-regional-main-menu.script"
VERIFY_SCRIPT="$SCRIPT_DIR/modern-main-menu.script"
VISUAL_SCRIPT="$SCRIPT_DIR/title-transition-recon.script"

STATE="$TMPROOT/regional-host-state.txt"
PAL_LOG="$TMPROOT/regional-pal.log"
NTSC_LOG="$TMPROOT/regional-ntsc.log"
VERIFY_LOG="$TMPROOT/regional-verify.log"
MAIN_MENU_LOG="$TMPROOT/regional-main-menu-negative.log"
AUTHENTIC_LOG="$TMPROOT/regional-authentic-negative.log"
PAL_DUMPS="$TMPROOT/regional-pal-dumps"
NTSC_DUMPS="$TMPROOT/regional-ntsc-dumps"
MAIN_MENU_DUMPS="$TMPROOT/regional-main-menu-dumps"
AUTHENTIC_DUMPS="$TMPROOT/regional-authentic-dumps"
EUROPE_VISUAL_DUMPS="$TMPROOT/regional-europe-visual-dumps"
NA_VISUAL_DUMPS="$TMPROOT/regional-na-visual-dumps"
AUTHENTIC_VISUAL_DUMPS="$TMPROOT/regional-authentic-visual-dumps"
EUROPE_SCREENSHOT="$TMPROOT/regional-europe-title.ppm"
NA_SCREENSHOT="$TMPROOT/regional-na-title.ppm"
AUTHENTIC_SCREENSHOT="$TMPROOT/regional-authentic-title.ppm"
EUROPE_VISUAL_LOG="$TMPROOT/regional-europe-visual.log"
NA_VISUAL_LOG="$TMPROOT/regional-na-visual.log"
AUTHENTIC_VISUAL_LOG="$TMPROOT/regional-authentic-visual.log"
EUROPE_STATE_SNAPSHOT="$TMPROOT/regional-europe-host-state.txt"
SOURCE_RGB_SHA="f2e8abef59271b4e05b3fc49e6d8b70ae695a6e813347756c293ab7a4a023b5f"
TARGET_RGB_SHA="40405f18ff1b856f2afe9e5ddfac77bcbd71e5ac9357532ef311e9509f6695bb"

rm -f "$STATE" "$PAL_LOG" "$NTSC_LOG" "$VERIFY_LOG" "$MAIN_MENU_LOG" "$AUTHENTIC_LOG" \
  "$EUROPE_SCREENSHOT" "$NA_SCREENSHOT" "$AUTHENTIC_SCREENSHOT" \
  "$EUROPE_VISUAL_LOG" "$NA_VISUAL_LOG" "$AUTHENTIC_VISUAL_LOG" "$EUROPE_STATE_SNAPSHOT"
rm -rf "$PAL_DUMPS" "$NTSC_DUMPS" "$MAIN_MENU_DUMPS" "$AUTHENTIC_DUMPS" \
  "$EUROPE_VISUAL_DUMPS" "$NA_VISUAL_DUMPS" "$AUTHENTIC_VISUAL_DUMPS"
mkdir -p "$PAL_DUMPS" "$NTSC_DUMPS" "$MAIN_MENU_DUMPS" "$AUTHENTIC_DUMPS" \
  "$EUROPE_VISUAL_DUMPS" "$NA_VISUAL_DUMPS" "$AUTHENTIC_VISUAL_DUMPS"

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

ppm_crop_sha() {
  local ppm="$1"
  python3 - "$ppm" <<'PY'
import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
data = path.read_bytes()
if not data.startswith(b"P6\n"):
    raise SystemExit(f"not P6 PPM: {path}")
parts = data.split(b"\n", 3)
if len(parts) != 4:
    raise SystemExit(f"malformed PPM: {path}")
width, height = map(int, parts[1].split())
maxval = int(parts[2])
pixels = parts[3]
if (width, height, maxval) != (256, 224, 255):
    raise SystemExit(f"unexpected PPM geometry: {(width, height, maxval)}")
if len(pixels) != width * height * 3:
    raise SystemExit(f"unexpected PPM payload length: {len(pixels)}")
x0, y0, x1, y1 = 10, 1, 247, 81
crop = bytearray()
for y in range(y0, y1 + 1):
    start = (y * width + x0) * 3
    end = (y * width + x1 + 1) * 3
    crop.extend(pixels[start:end])
actual = hashlib.sha256(crop).hexdigest()
print(actual)
PY
}

run_visual_process() {
  local state="$1"
  local expected_loaded="$2"
  local screenshot="$3"
  local dumps="$4"
  local log="$5"
  local execution_mode="${6:-modern}"

  rm -f "$screenshot" "$log"
  rm -rf "$dumps"
  mkdir -p "$dumps"

  SDL_AUDIODRIVER=dummy \
  UR_PRODUCT_DIAGNOSTICS=1 \
  UR_EXECUTION_MODE="$execution_mode" \
  UR_HOST_STATE_PATH="$state" \
  SNESRECOMP_DUMP_DIR="$dumps" \
  SNESRECOMP_SCREENSHOT="$screenshot" \
  SNESRECOMP_SCREENSHOT_FRAME=300 \
  timeout 90s xvfb-run -a "$EXE" "$ROM" --script "$VISUAL_SCRIPT" >"$log" 2>&1
  cat "$log"

  test -s "$screenshot"
  test -s "$dumps/boot-300.wram.bin"
  if [ "$execution_mode" = modern ]; then
    grep -q "UR_HOST_STATE LOADED regional_presentation=$expected_loaded " "$log"
  else
    grep -q "UR_HOST_STATE AUTHENTIC_INERT" "$log"
  fi
}

run_secret_process "p a l" "europe" "" "$PAL_LOG" "$PAL_DUMPS"
grep -q "^regional_presentation=europe$" "$STATE"
cp "$STATE" "$EUROPE_STATE_SNAPSHOT"

run_visual_process "$STATE" "europe" "$EUROPE_SCREENSHOT" "$EUROPE_VISUAL_DUMPS" "$EUROPE_VISUAL_LOG"
grep -q "UR_REGIONAL_TITLE visible=unirally guest_state_unchanged=1" "$EUROPE_VISUAL_LOG"
EUROPE_VISIBLE_SHA="$(ppm_crop_sha "$EUROPE_SCREENSHOT")"
test "$EUROPE_VISIBLE_SHA" = "$TARGET_RGB_SHA"
echo "UR_REGIONAL_VISIBLE EUROPE=$EUROPE_VISIBLE_SHA"

run_visual_process "$EUROPE_STATE_SNAPSHOT" "europe" "$AUTHENTIC_SCREENSHOT" "$AUTHENTIC_VISUAL_DUMPS" "$AUTHENTIC_VISUAL_LOG" "authentic"
AUTHENTIC_VISIBLE_SHA="$(ppm_crop_sha "$AUTHENTIC_SCREENSHOT")"
echo "UR_REGIONAL_VISIBLE AUTHENTIC=$AUTHENTIC_VISIBLE_SHA"

run_secret_process "n t s c" "north_america" "europe" "$NTSC_LOG" "$NTSC_DUMPS"
grep -q "^regional_presentation=north_america$" "$STATE"

run_visual_process "$STATE" "north_america" "$NA_SCREENSHOT" "$NA_VISUAL_DUMPS" "$NA_VISUAL_LOG"
NA_VISIBLE_SHA="$(ppm_crop_sha "$NA_SCREENSHOT")"
echo "UR_REGIONAL_VISIBLE NORTH_AMERICA=$NA_VISIBLE_SHA"
test "$EUROPE_VISIBLE_SHA" != "$NA_VISIBLE_SHA"
test "$AUTHENTIC_VISIBLE_SHA" = "$NA_VISIBLE_SHA"
echo "UR_REGIONAL_VISIBLE_SHA europe=$EUROPE_VISIBLE_SHA north_america=$NA_VISIBLE_SHA authentic=$AUTHENTIC_VISIBLE_SHA"

for suffix in wram.bin sram.bin vram.bin cgram.bin oam.bin; do
  cmp "$EUROPE_VISUAL_DUMPS/boot-300.$suffix" "$NA_VISUAL_DUMPS/boot-300.$suffix"
done

# Navigable main menu (0xD7) is explicitly not an admission surface.
timeout 90s xvfb-run -a bash -c '
  set -euo pipefail
  EXE="$1"; ROM="$2"; SCRIPT="$3"; STATE="$4"; LOG="$5"; DUMPS="$6"
  export SDL_AUDIODRIVER=dummy UR_PRODUCT_DIAGNOSTICS=1
  export UR_HOST_STATE_PATH="$STATE" SNESRECOMP_DUMP_DIR="$DUMPS"
  "$EXE" "$ROM" --script "$SCRIPT" >"$LOG" 2>&1 &
  PID=$!
  for _ in $(seq 1 600); do
    [ -s "$DUMPS/regional-main-menu-ready.wram.bin" ] && break
    kill -0 "$PID" 2>/dev/null || exit 1
    sleep 0.05
  done
  [ -s "$DUMPS/regional-main-menu-ready.wram.bin" ]
  WIN=""
  for _ in $(seq 1 100); do
    WIN=$(xdotool search --pid "$PID" 2>/dev/null | head -n1 || true)
    [ -n "$WIN" ] && break
    sleep 0.05
  done
  [ -n "$WIN" ]
  xdotool windowfocus "$WIN"
  xdotool key --delay 40 p a l
  wait "$PID" 2>/dev/null || true
' _ "$EXE" "$ROM" "$MAIN_MENU_SCRIPT" "$STATE" "$MAIN_MENU_LOG" "$MAIN_MENU_DUMPS"
! grep -q "UR_REGIONAL SWITCH" "$MAIN_MENU_LOG"
grep -q "^regional_presentation=north_america$" "$STATE"

# Authentic mode must ignore the stored Modern regional state and all secrets.
timeout 90s xvfb-run -a bash -c '
  set -euo pipefail
  EXE="$1"; ROM="$2"; SCRIPT="$3"; STATE="$4"; LOG="$5"; DUMPS="$6"
  export SDL_AUDIODRIVER=dummy UR_PRODUCT_DIAGNOSTICS=1
  export UR_EXECUTION_MODE=authentic
  export UR_HOST_STATE_PATH="$STATE" SNESRECOMP_DUMP_DIR="$DUMPS"
  "$EXE" "$ROM" --script "$SCRIPT" >"$LOG" 2>&1 &
  PID=$!
  for _ in $(seq 1 600); do
    [ -s "$DUMPS/regional-title-ready.wram.bin" ] && break
    kill -0 "$PID" 2>/dev/null || exit 1
    sleep 0.05
  done
  [ -s "$DUMPS/regional-title-ready.wram.bin" ]
  WIN=""
  for _ in $(seq 1 100); do
    WIN=$(xdotool search --pid "$PID" 2>/dev/null | head -n1 || true)
    [ -n "$WIN" ] && break
    sleep 0.05
  done
  [ -n "$WIN" ]
  xdotool windowfocus "$WIN"
  xdotool key --delay 40 p a l
  wait "$PID" 2>/dev/null || true
' _ "$EXE" "$ROM" "$TITLE_SCRIPT" "$STATE" "$AUTHENTIC_LOG" "$AUTHENTIC_DUMPS"
grep -q "UR_HOST_STATE AUTHENTIC_INERT" "$AUTHENTIC_LOG"
! grep -q "UR_REGIONAL SWITCH" "$AUTHENTIC_LOG"
grep -q "^regional_presentation=north_america$" "$STATE"

SDL_AUDIODRIVER=dummy \
UR_PRODUCT_DIAGNOSTICS=1 \
UR_HOST_STATE_PATH="$STATE" \
timeout 90s xvfb-run -a "$EXE" "$ROM" --script "$VERIFY_SCRIPT" >"$VERIFY_LOG" 2>&1
grep -q "UR_HOST_STATE LOADED regional_presentation=north_america " "$VERIFY_LOG"

cat "$PAL_LOG"
cat "$NTSC_LOG"
cat "$MAIN_MENU_LOG"
cat "$AUTHENTIC_LOG"
cat "$VERIFY_LOG"
cat "$EUROPE_VISUAL_LOG"
cat "$NA_VISUAL_LOG"
cat "$AUTHENTIC_VISUAL_LOG"
echo "UR_REGIONAL_RESULT=pal_saved_unirally_visible_ntsc_saved_uniracers_visible_guest_state_equal_main_menu_inert_authentic_canonical"
