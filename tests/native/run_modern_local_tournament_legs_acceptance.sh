#!/usr/bin/env bash
set -Eeuo pipefail

# Native proof that a multi-leg event continues from the 2P RESULTS screen:
# real join -> F4 -> MEET EACH 2X -> START (OS-minted, 2 fixtures) -> arm
# leg 1 -> genuine stock 2P race -> receipt -> results notice -> F4 on the
# results screen -> arm leg 2 (the same seated pair, swapped seats).
if [ "$#" -ne 3 ]; then
  echo "usage: $0 <native-exe> <retail-rom> <work-dir>" >&2
  exit 2
fi
EXE="$1"
ROM="$2"
WORK="$3"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PREF_DIR="$WORK/prefs/gamesbyian/UR-Recomp"
LOG="$WORK/legs.log"
mkdir -p "$PREF_DIR" "$WORK/multiplayer-runs"

cat >"$PREF_DIR/profiles-v1.txt" <<'CATALOG_EOF'
UR-PROFILE-CATALOG/1
join.alpha|0|MIKE
join.bravo|1|ANDREW
CATALOG_EOF
printf 'seen-v1\n' >"$PREF_DIR/onboarding-v1.seen"
printf 'UR-HOST-STATE/6\nprofile=\npause_on_focus_loss=0\nvibration_enabled=1\n' >"$WORK/host-state.txt"

on_failure() {
  local rc=$?
  echo "UR_LOCAL_TOURNAMENT_LEGS_ACCEPTANCE_FAILED status=$rc" >&2
  [ -f "$LOG" ] && grep -v '^script ' "$LOG" >&2 || true
  return "$rc"
}
trap on_failure ERR

env -u UR_MULTIPLAYER_MATCH_ACCEPTANCE -u UR_LOCAL_TOURNAMENT_NATIVE_ACCEPTANCE \
    SDL_AUDIODRIVER=dummy \
    XDG_DATA_HOME="$WORK/prefs" \
    UR_HOST_STATE_PATH="$WORK/host-state.txt" \
    UR_MULTIPLAYER_MATCH_CAPTURE_DIRECTORY="$WORK/multiplayer-runs" \
    UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE=capture \
    UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE=legs \
    UR_PRODUCT_DIAGNOSTICS=1 \
    SNESRECOMP_INPUT_FILE="$REPO/tests/input/two-player-joined-records-acceptance.input" \
  timeout 390s xvfb-run -a "$EXE" "$ROM" \
    --script "$REPO/tests/input/two-player-records-acceptance.script" \
    >"$LOG" 2>&1

grep -q "UR_LOCAL_TOURNAMENT CREATED entrants=2 fixtures=2 courses=2 legs=2" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT ARMED fixture=0 course=course:01" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT CAPTURE_TAGGED" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT FIXTURE_COMMITTED" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT RESULT_NOTICE screen=F9 text=LEADS: MIKE 3 PTS 1/2" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE STEP 3 expected=1 visible=0" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT PANEL_OPENED page=overview" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE STEP 4 expected=1 visible=1 page=2 cursor=0 fixture=1" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT ARMED fixture=1 course=course:04" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE DONE mode=legs step=4 armed=1 fixture=1 visible=0" "$LOG"
# End Event: the unfinished two-leg event (leg 2 armed) is ended with two
# explicit confirms and replaced by a new one-leg event from Setup.
grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE STEP 7 expected=1 visible=1 page=1" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT END_CONFIRMED" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT CREATED entrants=2 fixtures=1 courses=2 legs=1" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE ENDED_AND_REPLACED pending=0 fixtures=1 legs=1" "$LOG"
! grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE UNEXPECTED_PAGE" "$LOG"
! grep -q "UR_LOCAL_TOURNAMENT FIXTURE_COMMIT_REJECTED" "$LOG"
echo "UR_LOCAL_TOURNAMENT_LEGS_ACCEPTANCE=two_leg_event leg1_credited leg2_armed_from_results end_event_replaced"
