#!/usr/bin/env bash
set -Eeuo pipefail

# Native proof: real independent SDL join-overlay confirmation -> genuine
# guest ordinary 2P result -> normal run+match pair -> captured pre-race
# tournament token -> durable receipt -> fresh-process standings.
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

# This intentionally invokes the OTHER (real-join-to-Records) acceptance.
# That helper does not seed synthetic participants and exits only after the
# normal stock 2P result has been saved. It exists on PR #808.
UR_LOCAL_TOURNAMENT_NATIVE_ACCEPTANCE=join.alpha,join.bravo \
  bash "$REPO/tests/native/run_modern_two_player_join_record_acceptance.sh" \
    "$EXE" "$ROM" "$WORK" "$PAIR_CHECK"

LOG="$WORK/real-joined-capture.log"
grep -q "UR_LOCAL_TOURNAMENT ACCEPTANCE_ARMED" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT CAPTURE_TAGGED" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT FIXTURE_COMMITTED" "$LOG"
! grep -q "UR_LOCAL_TOURNAMENT CAPTURE_NOT_ADMITTED" "$LOG"
! grep -q "UR_LOCAL_TOURNAMENT FIXTURE_COMMIT_REJECTED" "$LOG"

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

"$CHECK" "$WORK/prefs/gamesbyian/UR-Recomp" "$WORK/multiplayer-runs"
test "$(find "$WORK/prefs/gamesbyian/UR-Recomp/local-tournaments" \
  -type f -name 'fixture-0.urfixture' | wc -l)" -eq 1
echo "UR_LOCAL_TOURNAMENT_NATIVE_ACCEPTANCE=stock_2p_fixture_persisted_fresh_standings"
