#!/usr/bin/env bash
set -Eeuo pipefail
# Explicit negative diagnostics, never inverted-grep under Bash errexit.
source "$(dirname "${BASH_SOURCE[0]}")/assert_absent_grep.sh"

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
# This is an independent test with a disposable profile root. Refuse an
# existing work directory (including symlinks) rather than recursively
# deleting a caller's saves, fixtures or earlier acceptance evidence.
if [[ -z "$WORK" || -e "$WORK" || -L "$WORK" ]]; then
  echo "Windows tournament QA requires a new, non-existing work directory" >&2
  exit 2
fi
# Only an already-existing parent is admissible: canonicalize it before
# touching anything, including junction/symlink ancestors. A work tree under
# the extracted package would itself contaminate immutable package evidence.
if [[ ! -d "$PACKAGE" || ! -d "$(dirname "$WORK")" ]]; then
  echo "Windows tournament QA requires existing package and work parent directories" >&2
  exit 2
fi
package_root="$(cd -P -- "$PACKAGE" && pwd -P)"
work_parent="$(cd -P -- "$(dirname "$WORK")" && pwd -P)"
if [[ "$work_parent" == "$package_root" || "$work_parent" == "$package_root/"* ]]; then
  echo "Windows tournament QA work directory cannot be inside the package" >&2
  exit 2
fi
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
USER_DATA="$WORK/user data"
LOG="$WORK/tournament.log"
REOPEN_LOG="$WORK/reopen.log"
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
      QA_PACKAGE_LAUNCHER="$PACKAGE_WIN\\run-uniracers.cmd" \
      QA_SCRIPT_PATH="$SCRIPT_WIN" \
    timeout "$limit" powershell.exe -NoProfile -NonInteractive -Command \
      '& $env:QA_PACKAGE_LAUNCHER --script $env:QA_SCRIPT_PATH; exit $LASTEXITCODE' \
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
assert_absent_grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE UNEXPECTED_PAGE" "$LOG" || exit 1
assert_absent_grep -q "UR_LOCAL_TOURNAMENT FIXTURE_COMMIT_REJECTED" "$LOG" || exit 1
test "$(find "$USER_DATA/local-tournaments" -type f -name '*.urfixture' | wc -l)" -eq 1

# Inspect real files, not only a success log emitted before durable I/O.
# Capture hashes before the fresh process: opening Standings/History must
# neither rewrite a completed run nor produce a duplicate sidecar/receipt.
mapfile -d '' -t runs < <(find "$WORK/multiplayer-runs" -maxdepth 1 -type f -name '*.urrun' -print0)
mapfile -d '' -t matches < <(find "$WORK/multiplayer-runs" -maxdepth 1 -type f -name '*.urmatch' -print0)
mapfile -d '' -t receipts < <(find "$USER_DATA/local-tournaments" -type f -name '*.urfixture' -print0)
test "${#runs[@]}" -eq 1
test "${#matches[@]}" -eq 1
test "${#receipts[@]}" -eq 1
test "${matches[0]}" = "${runs[0]}.urmatch"
test -s "${runs[0]}"
test -s "${matches[0]}"
test -s "${receipts[0]}"
run_hash="$(sha256sum "${runs[0]}" | cut -d ' ' -f 1)"
match_hash="$(sha256sum "${matches[0]}" | cut -d ' ' -f 1)"
receipt_hash="$(sha256sum "${receipts[0]}" | cut -d ' ' -f 1)"
create_log_hash="$(sha256sum "$LOG" | cut -d ' ' -f 1)"

# Relaunch the PACKAGED game: restore, Standings, History, then stop.
RC="$(run_package reopen "$REOPEN_LOG" 300)"
grep -v '^script ' "$REOPEN_LOG" | grep -E 'UR_LOCAL_TOURNAMENT' || true
test "$RC" -eq 0
grep -q "UR_LOCAL_TOURNAMENT SESSION_RESTORED" "$REOPEN_LOG"
grep -q "UR_LOCAL_TOURNAMENT HISTORY completed=1 unavailable=0" "$REOPEN_LOG"
grep -q "UR_LOCAL_TOURNAMENT PANEL_OPENED page=overview" "$REOPEN_LOG"
grep -q "UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE DONE mode=reopen step=2 armed=0" "$REOPEN_LOG"
assert_absent_grep -q "UR_LOCAL_TOURNAMENT SESSION_RESTORE_REJECTED" "$REOPEN_LOG" || exit 1
# This transcript does not exist until after the second process exits.
reopen_log_hash="$(sha256sum "$REOPEN_LOG" | cut -d ' ' -f 1)"
test "$(find "$WORK/multiplayer-runs" -maxdepth 1 -type f -name '*.urrun' | wc -l)" -eq 1
test "$(find "$WORK/multiplayer-runs" -maxdepth 1 -type f -name '*.urmatch' | wc -l)" -eq 1
test "$(find "$USER_DATA/local-tournaments" -type f -name '*.urfixture' | wc -l)" -eq 1
test "$(sha256sum "${runs[0]}" | cut -d ' ' -f 1)" = "$run_hash"
test "$(sha256sum "${matches[0]}" | cut -d ' ' -f 1)" = "$match_hash"
test "$(sha256sum "${receipts[0]}" | cut -d ' ' -f 1)" = "$receipt_hash"
test "$(sha256sum "$LOG" | cut -d ' ' -f 1)" = "$create_log_hash"
test "$(sha256sum "$REOPEN_LOG" | cut -d ' ' -f 1)" = "$reopen_log_hash"
# Preserve a compact, non-ROM receipt beside existing logs. A developer
# running the route outside the approved Windows workflow gets explicit
# unpinned provenance, not an accidental candidate-bound certification.
printf 'schema=ur-windows-tournament-artifacts/1\nbackend=snesrecomp\nsource_commit=%s\ninner_zip_sha256=%s\nrun_file=%s\nrun_sha256=%s\nmatch_file=%s\nmatch_sha256=%s\nreceipt_file=%s\nreceipt_sha256=%s\ncreate_log_sha256=%s\nreopen_log_sha256=%s\nfresh_process_reopen=passed\n' \
  "${QA_APPROVED_SHA:-unbound}" "${QA_APPROVED_ZIP_SHA256:-unbound}" \
  "${runs[0]##*/}" "$run_hash" "${matches[0]##*/}" "$match_hash" \
  "${receipts[0]##*/}" "$receipt_hash" "$create_log_hash" "$reopen_log_hash" \
  > "$WORK/tournament-artifacts.log"
echo "UR_WINDOWS_LOCAL_TOURNAMENT_PACKAGE_ACCEPTANCE=packaged_launcher minted_event stock_2p_receipt relaunch_restore_history immutable_pair_and_receipt"
