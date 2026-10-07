#!/usr/bin/env bash
set -Eeuo pipefail

# Native pad glyph acceptance. On-screen pad hints name the physical button
# the live [GamepadMap] binds to each SNES control, reverse-looked-up through
# SNESRecomp's own GamepadMap authority. The default map is positional, so
# SNES B (jump) is the south button "A"; after a config.ini remap moves SNES
# B to the right trigger, a fresh process must show "RT".

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <native-exe> <retail-rom> <work-dir>" >&2
  exit 2
fi

EXE="$1"
ROM="$2"
WORK="$3"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$REPO/tests/input/modern-onboarding-glyphs.script"
mkdir -p "$WORK/user"

dump_failure_evidence() {
  local status=$?
  echo "== Modern pad glyph acceptance failed: status=$status ==" >&2
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

run_native() {
  local name="$1"
  env \
    SDL_AUDIODRIVER=dummy \
    UR_PRODUCT_DIAGNOSTICS=1 \
    UR_HOST_STATE_PATH="$STATE" \
    UR_ONBOARDING_STATE_PATH="$WORK/never-seen-$name" \
    SNESRECOMP_USER_DATA_DIR="$WORK/user" \
    timeout 120s xvfb-run -a "$EXE" "$ROM" --script "$SCRIPT" \
      >"$WORK/$name.log" 2>&1
}

bindings() {
  grep -m 1 '^UR_ONBOARDING BINDINGS ' "$1"
}

# 1. Default map: physical glyphs, not SNES letters.
run_native default
B=$(bindings "$WORK/default.log")
echo "$B"
for want in pad_left=LEFT pad_right=RIGHT pad_jump=A pad_brake=X pad_a=B pad_x=Y pad_l=LB pad_r=RB; do
  grep -q " $want\( \|$\)" <<<"$B"
done
CONFIG="$WORK/user/config.ini"
grep -q '^Controls = *DpadUp, DpadDown, DpadLeft, DpadRight, Back, Start, B, A, Y, X, Lb, Rb$' "$CONFIG"

# 2. Remap SNES B (the 8th Controls entry) to the right trigger.
sed -i -E 's/^(Controls = *DpadUp, DpadDown, DpadLeft, DpadRight, Back, Start, B), A,/\1, R2,/' "$CONFIG"
grep -q '^Controls = *DpadUp, DpadDown, DpadLeft, DpadRight, Back, Start, B, R2, Y, X, Lb, Rb$' "$CONFIG"
run_native remapped
R=$(bindings "$WORK/remapped.log")
echo "$R"
grep -q " pad_jump=RT\( \|$\)" <<<"$R"
grep -q " pad_a=B\( \|$\)" <<<"$R"
echo "UR_PAD_GLYPH_ACCEPTANCE_RESULT=default_positional_glyphs_remap_followed_fresh_process"
