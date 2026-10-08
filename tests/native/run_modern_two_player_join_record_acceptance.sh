#!/usr/bin/env bash
set -Eeuo pipefail

# Reuses an already-built native desktop product and the established stock 2P
# capture acceptance route. Unlike the original capture test, the two
# participants here are REAL, explicitly confirmed Modern join-overlay profiles.
# No UR_MULTIPLAYER_MATCH_ACCEPTANCE synthetic participant seeding is allowed.
if [ "$#" -ne 4 ]; then
  echo "usage: $0 <native-exe> <retail-rom> <work-dir> <pair-check-exe>" >&2
  exit 2
fi

EXE="$1"
ROM="$2"
WORK="$3"
PAIR_CHECK="$4"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PREF_ROOT="$WORK/prefs"
PREF_DIR="$PREF_ROOT/gamesbyian/UR-Recomp"
MATCHES="$WORK/multiplayer-runs"
LOG="$WORK/real-joined-capture.log"
mkdir -p "$PREF_DIR" "$MATCHES"

cat >"$PREF_DIR/profiles-v1.txt" <<'CATALOG_EOF'
UR-PROFILE-CATALOG/1
join.alpha|0|MIKE
join.bravo|1|ANDREW
CATALOG_EOF
printf 'seen-v1\n' >"$PREF_DIR/onboarding-v1.seen"
printf 'UR-HOST-STATE/6\nprofile=\npause_on_focus_loss=0\nvibration_enabled=1\n' >"$WORK/host-state.txt"

on_failure() {
  local rc=$?
  echo "UR_TWO_PLAYER_REAL_JOIN_CAPTURE_FAILED status=$rc" >&2
  if [ -f "$LOG" ]; then
    grep -v '^script ' "$LOG" >&2 || true
  fi
  return "$rc"
}
trap on_failure ERR

env -u UR_MULTIPLAYER_MATCH_ACCEPTANCE \
    SDL_AUDIODRIVER=dummy \
    XDG_DATA_HOME="$PREF_ROOT" \
    UR_HOST_STATE_PATH="$WORK/host-state.txt" \
    UR_MULTIPLAYER_MATCH_CAPTURE_DIRECTORY="$MATCHES" \
    UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE=capture \
    UR_PRODUCT_DIAGNOSTICS=1 \
    SNESRECOMP_INPUT_FILE="$REPO/tests/input/two-player-joined-records-acceptance.input" \
  timeout 390s xvfb-run -a "$EXE" "$ROM" \
    --script "$REPO/tests/input/two-player-records-acceptance.script" \
    >"$LOG" 2>&1

grep -q "UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE PADS_ATTACHED" "$LOG"
grep -q "UR_LOCAL_MULTIPLAYER PROFILE_DUPLICATE" "$LOG"
grep -q "UR_LOCAL_MULTIPLAYER SESSION_READY" "$LOG"
grep -q "UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE DONE ready=1 overlay=0 p1=join.alpha p2=join.bravo" "$LOG"
grep -q "UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE RACE_CONTINUES" "$LOG"
grep -q "UR_MULTIPLAYER_MATCH CAPTURE_STARTED" "$LOG"
grep -q "UR_MULTIPLAYER_MATCH CAPTURED" "$LOG"
grep -q "UR_MULTIPLAYER_MATCH REAL_JOIN_CAPTURE_COMPLETE" "$LOG"
grep -q "UR_MULTIPLAYER_MATCH ACCEPTANCE_COMPLETE" "$LOG"
! grep -q "UR_MULTIPLAYER_MATCH ACCEPTANCE_PROFILES_SEEDED" "$LOG"
test "$(find "$MATCHES" -maxdepth 1 -type f -name '*.urrun' | wc -l)" -eq 1
test "$(find "$MATCHES" -maxdepth 1 -type f -name '*.urrun.urmatch' | wc -l)" -eq 1

RUN="$(find "$MATCHES" -maxdepth 1 -type f -name '*.urrun' -print -quit)"
"$PAIR_CHECK" "$RUN" "$WORK/real-joined-relative.input" join.alpha join.bravo \
  | tee "$WORK/real-joined-pair-check.log"
grep -q "UR_MULTIPLAYER_MATCH_PAIR_CHECK PASS course=course:01 p1=join.alpha p2=join.bravo" \
  "$WORK/real-joined-pair-check.log"

echo "UR_TWO_PLAYER_REAL_JOIN_CAPTURE=two_framework_pads distinct_confirmed_profiles stock_race authoritative_saved_pair fresh_process"
