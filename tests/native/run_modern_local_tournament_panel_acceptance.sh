#!/usr/bin/env bash
set -Eeuo pipefail

# Native proof of the PLAYER-FACING Local Tournament route: real SDL join
# overlay confirms two profiles on stock 2P select -> F4 panel -> START
# creates an event with an OS-minted ID -> Enter arms the seated fixture ->
# genuine stock 2P race -> normal run+match pair -> fixture receipt ->
# fresh-process standings. No fixed tournament/attempt IDs are used.
if [ "$#" -ne 4 ]; then
  echo "usage: $0 <native-exe> <retail-rom> <work-dir> <pair-check-exe>" >&2
  exit 2
fi
EXE="$1"
ROM="$2"
WORK="$3"
PAIR_CHECK="$4"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$WORK"

env -u UR_LOCAL_TOURNAMENT_NATIVE_ACCEPTANCE \
  UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE=create \
  bash "$REPO/tests/native/run_modern_two_player_join_record_acceptance.sh" \
    "$EXE" "$ROM" "$WORK" "$PAIR_CHECK"

LOG="$WORK/real-joined-capture.log"
grep -q "UR_LOCAL_TOURNAMENT STRIP rows=F4/PAD LB TOURNAMENT" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT PANEL_OPENED page=setup" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE STEP 1 expected=1 visible=1 page=0 cursor=4 fixture=0 selected=2" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT CREATED entrants=2 fixtures=1 courses=2 legs=1" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE STEP 2 expected=1 visible=1 page=2 cursor=0 fixture=0" "$LOG"
# Turbo presents only some frames; require that the panel itself rendered.
grep -q "UR_LOCAL_TOURNAMENT PRESENT page=" "$LOG"
! grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE UNEXPECTED_PAGE" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT ARMED fixture=0 course=course:01" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE DONE mode=create step=2 armed=1 fixture=0 visible=0" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT STRIP rows=EVENT: RACE DRAGSTER F4/LB" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT CAPTURE_TAGGED" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT FIXTURE_COMMITTED" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT RESULT_NOTICE screen=.* text=CHAMPION: MIKE" "$LOG"
! grep -q "UR_LOCAL_TOURNAMENT ACCEPTANCE_ARMED" "$LOG"
! grep -q "UR_LOCAL_TOURNAMENT CAPTURE_NOT_ADMITTED" "$LOG"
! grep -q "UR_LOCAL_TOURNAMENT FIXTURE_COMMIT_REJECTED" "$LOG"
! grep -q "UR_LOCAL_TOURNAMENT UNFINISHED_ROUTE_CANCELLED" "$LOG"

CHECK="$WORK/check-local-tournament"
g++ -std=c++17 -Wall -Wextra -Werror -pedantic \
  -I "$REPO/native/product" -I "$REPO/native/title" \
  "$REPO/native/product/modern_racer_identity.cpp" \
  "$REPO/native/product/host_profile_runtime.cpp" \
  "$REPO/native/product/host_product_state.cpp" \
  "$REPO/native/product/output_resolution_policy.cpp" \
  "$REPO/native/product/completed_run_record.cpp" \
  "$REPO/native/product/completed_run_store.cpp" \
  "$REPO/native/product/local_multiplayer_match_binding.cpp" \
  "$REPO/native/product/multiplayer_match_record.cpp" \
  "$REPO/native/product/local_tournament_session_store.cpp" \
  "$REPO/native/product/local_tournament_fixture_launch_store.cpp" \
  "$REPO/native/product/local_tournament_result_link_store.cpp" \
  "$REPO/native/product/local_tournament_session_coordinator.cpp" \
  "$REPO/tests/native/local_tournament_live_capture_check.cpp" \
  -o "$CHECK"

"$CHECK" "$WORK/prefs/gamesbyian/UR-Recomp" "$WORK/multiplayer-runs" minted
test "$(find "$WORK/prefs/gamesbyian/UR-Recomp/local-tournaments" \
  -type f -name 'fixture-0.urfixture' | wc -l)" -eq 1

# Relaunch: the same two players rejoin in a NEW process. The panel must
# restore the completed event (Standings) and list it under History. The
# run is stopped once the panel route is proven; no second race is needed.
REOPEN_LOG="$WORK/reopen.log"
set +e
env -u UR_MULTIPLAYER_MATCH_ACCEPTANCE -u UR_LOCAL_TOURNAMENT_NATIVE_ACCEPTANCE \
    SDL_AUDIODRIVER=dummy \
    XDG_DATA_HOME="$WORK/prefs" \
    UR_HOST_STATE_PATH="$WORK/host-state.txt" \
    UR_MULTIPLAYER_MATCH_CAPTURE_DIRECTORY="$WORK/multiplayer-runs" \
    UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE=capture \
    UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE=reopen \
    UR_PRODUCT_DIAGNOSTICS=1 \
    SNESRECOMP_INPUT_FILE="$REPO/tests/input/two-player-joined-records-acceptance.input" \
  timeout 90s xvfb-run -a "$EXE" "$ROM" \
    --script "$REPO/tests/input/two-player-records-acceptance.script" \
    >"$REOPEN_LOG" 2>&1
set -e
grep -q "UR_LOCAL_TOURNAMENT SESSION_RESTORED" "$REOPEN_LOG"
grep -q "UR_LOCAL_TOURNAMENT HISTORY completed=1 unavailable=0" "$REOPEN_LOG"
grep -q "UR_LOCAL_TOURNAMENT PANEL_OPENED page=overview" "$REOPEN_LOG"
grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE STEP 1 expected=1 visible=1 page=1 .* history=1" "$REOPEN_LOG"
grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE STEP 2 expected=1 visible=1 page=3 .* history=1" "$REOPEN_LOG"
grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE DONE mode=reopen step=2 armed=0" "$REOPEN_LOG"
! grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE UNEXPECTED_PAGE" "$REOPEN_LOG"
! grep -q "UR_LOCAL_TOURNAMENT SESSION_RESTORE_REJECTED" "$REOPEN_LOG"
echo "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE=panel_created_minted_event stock_2p_fixture_persisted fresh_standings relaunch_panel_history"
