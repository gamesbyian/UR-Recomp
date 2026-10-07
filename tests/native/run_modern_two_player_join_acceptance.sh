#!/usr/bin/env bash
set -Eeuo pipefail

# Native Modern 2P join acceptance. The ordinary stock route reaches the 2P
# select surface (0x3D), where Modern opens the local multiplayer join
# overlay. Two named SDL virtual gamepads seated by the framework join P1 and
# P2 with their real buttons; the overlay names each seat's device from the
# presentation-safe seat projection. P2 first tries P1's profile and is
# refused as a duplicate, then confirms a distinct profile, and the session
# becomes ready. Authentic never opens the join surface.

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <native-exe> <retail-rom> <work-dir>" >&2
  exit 2
fi

EXE="$1"
ROM="$2"
WORK="$3"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$REPO/tests/input/modern-two-player-join.script"
INPUT="$REPO/tests/input/modern-two-player-join.input"
mkdir -p "$WORK"

dump_failure_evidence() {
  local status=$?
  echo "== Modern 2P join acceptance failed: status=$status ==" >&2
  for log in "$WORK"/*.log; do
    [ -f "$log" ] || continue
    echo "===== $log =====" >&2
    grep -v '^script ' "$log" >&2 || true
  done
  return "$status"
}
trap dump_failure_evidence ERR

PREF_ROOT="$WORK/xdg"
PREF_DIR="$PREF_ROOT/gamesbyian/UR-Recomp"
mkdir -p "$PREF_DIR"
cat >"$PREF_DIR/profiles-v1.txt" <<'CATALOG_EOF'
UR-PROFILE-CATALOG/1
join.alpha|0|MIKE
join.bravo|1|ANNA
CATALOG_EOF
printf 'seen-v1\n' >"$PREF_DIR/onboarding-v1.seen"

STATE="$WORK/host-state.txt"
printf 'UR-HOST-STATE/6\nprofile=\npause_on_focus_loss=0\nvibration_enabled=1\n' >"$STATE"

run_native() {
  local name="$1"
  shift
  env "$@" \
    SDL_AUDIODRIVER=dummy \
    XDG_DATA_HOME="$PREF_ROOT" \
    UR_PRODUCT_DIAGNOSTICS=1 \
    UR_HOST_STATE_PATH="$STATE" \
    UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE=1 \
    SNESRECOMP_INPUT_FILE="$INPUT" \
    timeout 200s xvfb-run -a "$EXE" "$ROM" --script "$SCRIPT" \
      >"$WORK/$name.log" 2>&1
}

# 1. Modern: both seats join with their own device, P2 is refused P1's
#    profile, then both confirm distinct profiles.
run_native modern
LOG="$WORK/modern.log"
grep -v '^script ' "$LOG" | grep -E 'UR_LOCAL_MULTIPLAYER|UR_CONTROLLER SEAT' || true
grep -q "UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE PADS_ATTACHED" "$LOG"
grep -q "UR_CONTROLLER SEAT_CONNECTED seat=1 name=UR JOIN PAD ONE" "$LOG"
grep -q "UR_CONTROLLER SEAT_CONNECTED seat=2 name=UR JOIN PAD TWO" "$LOG"
grep -q "UR_LOCAL_MULTIPLAYER JOIN_OPENED" "$LOG"
grep -q "UR_LOCAL_MULTIPLAYER SEAT slot=P1 device=PAD UR JOIN PAD ONE" "$LOG"
grep -q "UR_LOCAL_MULTIPLAYER SEAT slot=P2 device=PAD UR JOIN PAD TWO" "$LOG"
grep -q "UR_LOCAL_MULTIPLAYER PROFILE_DUPLICATE" "$LOG"
test "$(grep -c 'UR_LOCAL_MULTIPLAYER SESSION_READY' "$LOG")" -eq 1
# The duplicate refusal precedes the ready session.
DUP=$(grep -n "UR_LOCAL_MULTIPLAYER PROFILE_DUPLICATE" "$LOG" | head -n 1 | cut -d: -f1)
READY=$(grep -n "UR_LOCAL_MULTIPLAYER SESSION_READY" "$LOG" | head -n 1 | cut -d: -f1)
test "$DUP" -lt "$READY"
grep -q "UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE DONE ready=1 overlay=0 p1=join.alpha p2=join.bravo" "$LOG"
! grep -q "UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE JOIN_NOT_OPENED" "$LOG"
echo "UR_TWO_PLAYER_JOIN_NATIVE=devices_named duplicate_refused ready p1=join.alpha p2=join.bravo"

# 2. Authentic: the same pads and route never open the Modern join surface.
run_native authentic UR_EXECUTION_MODE=authentic
grep -q "UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE JOIN_NOT_OPENED" "$WORK/authentic.log"
! grep -q "UR_LOCAL_MULTIPLAYER JOIN_OPENED" "$WORK/authentic.log"
! grep -q "UR_LOCAL_MULTIPLAYER SEAT " "$WORK/authentic.log"
echo "UR_TWO_PLAYER_JOIN_AUTHENTIC=inert"

echo "UR_TWO_PLAYER_JOIN_ACCEPTANCE_RESULT=two_devices_joined_named_duplicate_refused_distinct_profiles_ready_authentic_inert"
