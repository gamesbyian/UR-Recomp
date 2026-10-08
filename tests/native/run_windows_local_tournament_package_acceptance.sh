#!/usr/bin/env bash
set -Eeuo pipefail

# Windows-package proof of the player-facing Local Tournament route, run on
# the EXTRACTED portable package through its own launcher (run-uniracers.cmd)
# with an isolated per-user data root:
#   real SDL join -> F4 panel -> OS-minted event -> armed fixture -> genuine
#   stock 2P race -> receipt -> results notice; then a relaunched packaged
#   process restores the completed event (Standings) and History.
# Usage (Git Bash on Windows): <extracted-package-dir> <work-dir>
if [ "$#" -ne 2 ]; then
  echo "usage: $0 <extracted-package-dir> <work-dir>" >&2
  exit 2
fi
PACKAGE="$1"
WORK="$2"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
USER_DATA="$WORK/user data"
LOG="$WORK/tournament.log"
REOPEN_LOG="$WORK/reopen.log"
rm -rf "$USER_DATA"
mkdir -p "$USER_DATA" "$WORK/multiplayer-runs"
test -f "$PACKAGE/run-uniracers.cmd"

cat >"$USER_DATA/profiles-v1.txt" <<'CATALOG_EOF'
UR-PROFILE-CATALOG/1
join.alpha|0|MIKE
join.bravo|1|ANDREW
CATALOG_EOF
printf 'seen-v1\n' >"$USER_DATA/onboarding-v1.seen"
printf 'UR-HOST-STATE/6\nprofile=\npause_on_focus_loss=0\nvibration_enabled=1\n' >"$WORK/host-state.txt"

PACKAGE_WIN="$(cygpath -w "$PACKAGE")"
USER_DATA_WIN="$(cygpath -w "$USER_DATA")"
HOST_STATE_WIN="$(cygpath -w "$WORK/host-state.txt")"
RUNS_WIN="$(cygpath -w "$WORK/multiplayer-runs")"
INPUT_WIN="$(cygpath -w "$REPO/tests/input/two-player-joined-records-acceptance.input")"
SCRIPT_WIN="$(cygpath -w "$REPO/tests/input/two-player-records-acceptance.script")"

run_package() {
  local mode="$1" log="$2" limit="$3"
  set +e
  env -u UR_MULTIPLAYER_MATCH_ACCEPTANCE -u UR_LOCAL_TOURNAMENT_NATIVE_ACCEPTANCE \
      SDL_VIDEODRIVER=offscreen \
      SDL_AUDIODRIVER=dummy \
      UR_RECOMP_USER_DATA_ROOT="$USER_DATA_WIN" \
      UR_HOST_STATE_PATH="$HOST_STATE_WIN" \
      UR_MULTIPLAYER_MATCH_CAPTURE_DIRECTORY="$RUNS_WIN" \
      UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE=capture \
      UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE="$mode" \
      UR_PRODUCT_DIAGNOSTICS=1 \
      SNESRECOMP_INPUT_FILE="$INPUT_WIN" \
    timeout "$limit" powershell.exe -NoProfile -Command \
      "& '${PACKAGE_WIN}\\run-uniracers.cmd' --script '${SCRIPT_WIN}'; exit \$LASTEXITCODE" \
      >"$log" 2>&1
  local rc=$?
  set -e
  echo "$rc"
}

RC="$(run_package create "$LOG" 900)"
grep -v '^script ' "$LOG" | grep -E 'UR_LOCAL_(TOURNAMENT|MULTIPLAYER)|UR_MULTIPLAYER_MATCH' || true
test "$RC" -eq 0
grep -q "UR_LOCAL_MULTIPLAYER SESSION_READY" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT PANEL_OPENED page=setup" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT CREATED entrants=2 fixtures=1 courses=2 legs=1" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT ARMED fixture=0 course=course:01" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT CAPTURE_TAGGED" "$LOG"
grep -q "UR_MULTIPLAYER_MATCH CAPTURED .*course=course:01 p1=join.alpha p2=join.bravo outcome=1" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT FIXTURE_COMMITTED" "$LOG"
grep -q "UR_LOCAL_TOURNAMENT RESULT_NOTICE screen=F9 text=CHAMPION: MIKE" "$LOG"
! grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE UNEXPECTED_PAGE" "$LOG"
! grep -q "UR_LOCAL_TOURNAMENT FIXTURE_COMMIT_REJECTED" "$LOG"
test "$(find "$USER_DATA/local-tournaments" -type f -name 'fixture-0.urfixture' | wc -l)" -eq 1

# Relaunch the PACKAGED game: restore, Standings, History, then stop.
RC="$(run_package reopen "$REOPEN_LOG" 300)"
grep -v '^script ' "$REOPEN_LOG" | grep -E 'UR_LOCAL_TOURNAMENT' || true
test "$RC" -eq 0
grep -q "UR_LOCAL_TOURNAMENT SESSION_RESTORED" "$REOPEN_LOG"
grep -q "UR_LOCAL_TOURNAMENT HISTORY completed=1 unavailable=0" "$REOPEN_LOG"
grep -q "UR_LOCAL_TOURNAMENT PANEL_OPENED page=overview" "$REOPEN_LOG"
grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE DONE mode=reopen step=2 armed=0" "$REOPEN_LOG"
! grep -q "UR_LOCAL_TOURNAMENT SESSION_RESTORE_REJECTED" "$REOPEN_LOG"
echo "UR_WINDOWS_LOCAL_TOURNAMENT_PACKAGE_ACCEPTANCE=packaged_launcher minted_event stock_2p_receipt relaunch_restore_history"
