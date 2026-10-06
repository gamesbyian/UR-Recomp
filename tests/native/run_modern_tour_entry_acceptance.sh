#!/usr/bin/env bash
set -Eeuo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <native-exe> <retail-rom> <work-dir>" >&2
  exit 2
fi

EXE="$1"
ROM="$2"
WORK="$3"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ROUTE_SCRIPT="$REPO/tests/input/modern-tour-continue-acceptance.script"
STALE_SCRIPT="$REPO/tests/input/modern-tour-continue-stale.script"
AUTH_SCRIPT="$REPO/tests/input/modern-tour-continue-authentic.script"
CLEAN="$REPO/reference/imported/reverse-engineering/dessyreqt/SRAM/Clean.srm"

STATE="$WORK/tour-host-state.txt"
PREF_ROOT="$WORK/tour-xdg"
PREF_DIR="$PREF_ROOT/gamesbyian/UR-Recomp"
mkdir -p "$WORK" "$PREF_DIR"

dump_failure_evidence() {
  local status=$?
  echo "== Modern Tour acceptance failed: status=$status ==" >&2
  find "$WORK" -maxdepth 2 -type f -print >&2 2>/dev/null || true
  for log in "$WORK"/*.log; do
    [ -f "$log" ] || continue
    echo "===== $log =====" >&2
    cat "$log" >&2 || true
  done
  # A persistence-failure case may intentionally make its root read-only.
  find "$WORK" -maxdepth 1 -type d -name '*-profile' -exec chmod u+w {} \;     2>/dev/null || true
  return "$status"
}
trap dump_failure_evidence ERR


cat >"$STATE" <<'EOF'
UR-HOST-STATE/6
profile=resume.alpha
pause_on_focus_loss=0
vibration_enabled=1
EOF

cat >"$PREF_DIR/profiles-v1.txt" <<'EOF'
UR-PROFILE-CATALOG/1
resume.alpha|0|MIKE
EOF

# This acceptance owns Tour continuation, not first-run onboarding. Mark the
# existing Modern install as already onboarded so F3 reaches the Tour surface.
printf 'seen-v1\n' >"$PREF_DIR/onboarding-v1.seen"

make_fixture() {
  local root="$1"
  rm -rf "$root"
  mkdir -p "$root"
  python3 - "$CLEAN" "$root/save.srm" "$root/host-profile.txt" <<'PY'
from pathlib import Path
import sys

source, sram_path, profile_path = map(Path, sys.argv[1:])
sram = bytearray(source.read_bytes())
if len(sram) != 8192:
    raise SystemExit(f"unexpected clean SRAM size: {len(sram)}")

rider = 0
tour = 0
medal = sram[0x069C + 16 * tour + rider]
if medal != 0:
    raise SystemExit(f"clean fixture medal is not zero: {medal}")

flags = bytes((1, 1, 0, 0, 0))
sram[0x10AD] = 1
sram[0x0748] = rider
sram[0x1075:0x107A] = flags
sram_path.write_bytes(sram)
profile_path.write_text(
    "UR-HOST-PROFILE/4\n"
    "profile=resume.alpha\n"
    "generation=1\n"
    f"stock_sram={bytes(sram).hex()}\n"
    f"tour_resume={rider}:{tour}:{medal}:11000\n"
    "ghost_target=off\n"
    "racer_name=MIKE\n"
    "racer_index=0\n"
)
PY
}

wait_for_ui_case='
  set -euo pipefail
  EXE="$1"; ROM="$2"; SCRIPT="$3"; LOG="$4"; DUMPS="$5"; ACTION="$6"; ROOT="$7"
  "$EXE" "$ROM" --script "$SCRIPT" >"$LOG" 2>&1 &
  PID=$!

  for _ in $(seq 1 600); do
    [ -s "$DUMPS/tour-entry-main-ready.wram.bin" ] && break
    kill -0 "$PID" 2>/dev/null || exit 1
    sleep 0.05
  done
  [ -s "$DUMPS/tour-entry-main-ready.wram.bin" ]

  WIN=""
  for _ in $(seq 1 100); do
    WIN=$(xdotool search --pid "$PID" 2>/dev/null | head -n1 || true)
    [ -n "$WIN" ] && break
    kill -0 "$PID" 2>/dev/null || exit 1
    sleep 0.05
  done
  [ -n "$WIN" ]
  xdotool windowfocus "$WIN"

  case "$ACTION" in
    resume)
      xdotool key F3
      for _ in $(seq 1 100); do
        grep -q "UR_TOUR_ENTRY MENU_OPENED .*tier=BRONZE" "$LOG" && break
        kill -0 "$PID" 2>/dev/null || exit 1
        sleep 0.02
      done
      grep -q "UR_TOUR_ENTRY MENU_OPENED .*tier=BRONZE" "$LOG"
      xdotool key Return
      wait "$PID"
      ;;
    restart-confirm-cancel)
      xdotool key F3 Down Return Escape Escape
      for _ in $(seq 1 100); do
        grep -q "UR_TOUR_ENTRY CANCELLED" "$LOG" && break
        kill -0 "$PID" 2>/dev/null || exit 1
        sleep 0.02
      done
      grep -q "UR_TOUR_ENTRY CANCELLED" "$LOG"
      ! grep -q "UR_TOUR_CONTINUE STARTED" "$LOG"
      kill "$PID" 2>/dev/null || true
      wait "$PID" 2>/dev/null || true
      ;;
    cancel)
      xdotool key F3 Return
      for _ in $(seq 1 600); do
        [ -s "$DUMPS/tour-entry-post-rider-wipe.wram.bin" ] && break
        kill -0 "$PID" 2>/dev/null || exit 1
        sleep 0.02
      done
      [ -s "$DUMPS/tour-entry-post-rider-wipe.wram.bin" ]
      grep -q "UR_TOUR_CONTINUE STARTED intent=resume" "$LOG"
      xdotool key Escape
      for _ in $(seq 1 100); do
        grep -q "UR_TOUR_CONTINUE CANCELLED" "$LOG" && break
        kill -0 "$PID" 2>/dev/null || exit 1
        sleep 0.02
      done
      grep -q "UR_TOUR_CONTINUE ROLLED_BACK_PROFILE_SNAPSHOT" "$LOG"
      grep -q "UR_TOUR_CONTINUE CANCELLED" "$LOG"
      kill "$PID" 2>/dev/null || true
      wait "$PID" 2>/dev/null || true
      ;;
    failure)
      xdotool key F3 Return
      for _ in $(seq 1 100); do
        grep -q "UR_TOUR_CONTINUE INPUT_FAILED" "$LOG" && break
        kill -0 "$PID" 2>/dev/null || exit 1
        sleep 0.02
      done
      grep -q "UR_TOUR_CONTINUE INPUT_FAILED" "$LOG"
      ! grep -q "UR_TOUR_CONTINUE ROLLED_BACK_PROFILE_SNAPSHOT" "$LOG"
      kill "$PID" 2>/dev/null || true
      wait "$PID" 2>/dev/null || true
      ;;
    restart)
      xdotool key F3 Down Return Return
      wait "$PID"
      ;;
    restart-persist-fail)
      chmod a-w "$ROOT"
      xdotool key F3 Down Return Return
      for _ in $(seq 1 600); do
        grep -q "UR_TOUR_RESTART PROFILE_SAVE_FAILED" "$LOG" && break
        kill -0 "$PID" 2>/dev/null || break
        sleep 0.02
      done
      grep -q "UR_TOUR_RESTART PROFILE_SAVE_FAILED" "$LOG"
      wait "$PID" || true
      chmod u+w "$ROOT"
      ;;
    *)
      exit 2
      ;;
  esac
'

run_ui_case() {
  local name="$1"
  local action="$2"
  local root="$WORK/$name-profile"
  local dumps="$WORK/$name-dumps"
  local log="$WORK/$name.log"

  make_fixture "$root"
  rm -rf "$dumps"
  mkdir -p "$dumps"

  local extra_env=()
  if [ "$action" = "failure" ]; then
    # queue_relative_menu_input requires a regular writable file. Pointing it
    # at the profile directory deterministically forces the transport to fail.
    extra_env+=("UR_TOUR_CONTINUE_INPUT_PATH=$root")
  fi

  env "${extra_env[@]}" \
    SDL_AUDIODRIVER=dummy \
    XDG_DATA_HOME="$PREF_ROOT" \
    UR_PRODUCT_DIAGNOSTICS=1 \
    UR_HOST_STATE_PATH="$STATE" \
    UR_PROFILE_SAVE_ROOT="$root" \
    SNESRECOMP_DUMP_DIR="$dumps" \
    timeout 100s xvfb-run -a bash -c "$wait_for_ui_case" \
      bash "$EXE" "$ROM" "$ROUTE_SCRIPT" "$log" "$dumps" "$action" "$root"
}

# Fresh-process player-facing Resume.
run_ui_case resume resume
RESUME_ROOT="$WORK/resume-profile"
RESUME_DUMPS="$WORK/resume-dumps"
RESUME_LOG="$WORK/resume.log"
cat "$RESUME_LOG"
grep -q "UR_TOUR_ENTRY MENU_OPENED rider=0 tour=0 tier=BRONZE" "$RESUME_LOG"
grep -q "UR_TOUR_CONTINUE STARTED intent=resume rider=0 tour=0 completed=2 tier=BRONZE menu=D7 race=0" "$RESUME_LOG"
grep -q "UR_TOUR_CONTINUE READY intent=resume tour=0 menu=F6" "$RESUME_LOG"
grep -q "UR_TOUR_RESUME APPLIED" "$RESUME_LOG"
test -s "$RESUME_DUMPS/tour-continue-track-ready.wram.bin"

python3 - "$RESUME_DUMPS/tour-continue-track-ready.wram.bin" \
  "$RESUME_ROOT/host-profile.txt" "$RESUME_ROOT/save.srm" <<'PY'
from pathlib import Path
import sys

track = Path(sys.argv[1]).read_bytes()
profile = Path(sys.argv[2]).read_text().splitlines()
sram = Path(sys.argv[3]).read_bytes()

if track[0x009F] != 0xF6 or track[0x0313] == 1:
    raise SystemExit("Resume did not stop at stock TRACK_SELECT")
if track[0x00D0] != 0:
    raise SystemExit(f"Resume reached wrong tour row: {track[0x00D0]}")

resume = next(
    line.split("=", 1)[1]
    for line in profile
    if line.startswith("tour_resume=")
)
_, tour, _, flags = resume.split(":")
tour = int(tour)
expected = bytes(int(ch) for ch in flags)
actual = sram[0x1075 + 5 * tour:0x1075 + 5 * tour + 5]
if actual != expected:
    raise SystemExit(
        f"restored flags mismatch: expected={list(expected)} actual={list(actual)}"
    )
print("UR_TOUR_RESUME_NATIVE=player_surface restored=1 track_select=1")
PY

# Cancel the destructive Restart confirmation before any stock routing begins.
run_ui_case restart-confirm-cancel restart-confirm-cancel
CONFIRM_CANCEL_ROOT="$WORK/restart-confirm-cancel-profile"
CONFIRM_CANCEL_LOG="$WORK/restart-confirm-cancel.log"
cat "$CONFIRM_CANCEL_LOG"
grep -q "UR_TOUR_ENTRY CANCELLED" "$CONFIRM_CANCEL_LOG"
! grep -q "UR_TOUR_CONTINUE STARTED" "$CONFIRM_CANCEL_LOG"
grep -q '^tour_resume=0:0:0:11000$' "$CONFIRM_CANCEL_ROOT/host-profile.txt"
python3 - "$CONFIRM_CANCEL_ROOT/save.srm" <<'PY'
from pathlib import Path
import sys

row = Path(sys.argv[1]).read_bytes()[0x1075:0x107A]
if row != bytes((1, 1, 0, 0, 0)):
    raise SystemExit(
        f"Restart confirmation cancellation changed tour row: {list(row)}"
    )
print("UR_TOUR_RESTART_CONFIRM_CANCEL_NATIVE=route_started=0 progress_preserved=1")
PY

# Cancel after stock rider confirmation has crossed the destructive wipe.
run_ui_case cancel cancel
CANCEL_ROOT="$WORK/cancel-profile"
CANCEL_LOG="$WORK/cancel.log"
cat "$CANCEL_LOG"
grep -q '^tour_resume=0:0:0:11000$' "$CANCEL_ROOT/host-profile.txt"
python3 - "$CANCEL_ROOT/save.srm" <<'PY'
from pathlib import Path
import sys

row = Path(sys.argv[1]).read_bytes()[0x1075:0x107A]
if row != bytes((1, 1, 0, 0, 0)):
    raise SystemExit(f"cancel rollback did not restore tour row: {list(row)}")
print("UR_TOUR_CANCEL_NATIVE=post_wipe rollback_restored=1")
PY
! grep -q "UR_TOUR_RESTART RETIRED" "$CANCEL_LOG"

# Deterministic input-transport failure must preserve both metadata and SRAM.
run_ui_case failure failure
FAILURE_ROOT="$WORK/failure-profile"
FAILURE_LOG="$WORK/failure.log"
cat "$FAILURE_LOG"
grep -q '^tour_resume=0:0:0:11000$' "$FAILURE_ROOT/host-profile.txt"
python3 - "$FAILURE_ROOT/save.srm" <<'PY'
from pathlib import Path
import sys

row = Path(sys.argv[1]).read_bytes()[0x1075:0x107A]
if row != bytes((1, 1, 0, 0, 0)):
    raise SystemExit(f"routing failure changed tour row: {list(row)}")
print("UR_TOUR_ROUTE_FAILURE_NATIVE=pre_wipe_preserved_without_full_rollback=1")
PY
! grep -q "UR_TOUR_RESTART RETIRED" "$FAILURE_LOG"

# Confirmed Restart: same route, no restore, delayed retirement.
run_ui_case restart restart
RESTART_ROOT="$WORK/restart-profile"
RESTART_DUMPS="$WORK/restart-dumps"
RESTART_LOG="$WORK/restart.log"
cat "$RESTART_LOG"
grep -q "UR_TOUR_CONTINUE STARTED intent=restart rider=0 tour=0 completed=2 tier=BRONZE menu=D7 race=0" "$RESTART_LOG"
grep -q "UR_TOUR_CONTINUE READY intent=restart tour=0 menu=F6" "$RESTART_LOG"
grep -q "UR_TOUR_RESTART STOCK_RESET_PROVEN" "$RESTART_LOG"
grep -q "UR_TOUR_RESTART RETIRED" "$RESTART_LOG"
! grep -q "UR_TOUR_RESUME APPLIED" "$RESTART_LOG"
test -s "$RESTART_DUMPS/tour-continue-track-ready.wram.bin"

python3 - "$RESTART_LOG" "$RESTART_ROOT/host-profile.txt" \
  "$RESTART_ROOT/save.srm" <<'PY'
from pathlib import Path
import sys

log = Path(sys.argv[1]).read_text()
ready = log.index("UR_TOUR_CONTINUE READY intent=restart")
proven = log.index("UR_TOUR_RESTART STOCK_RESET_PROVEN")
retired = log.index("UR_TOUR_RESTART RETIRED")
if not ready < proven < retired:
    raise SystemExit(
        f"retirement timing invalid: ready={ready} proven={proven} retired={retired}"
    )

fields = dict(
    line.split("=", 1)
    for line in Path(sys.argv[2]).read_text().splitlines()[1:]
    if "=" in line
)
if fields.get("tour_resume") != "":
    raise SystemExit(
        f"Restart did not retire continuation: {fields.get('tour_resume')!r}"
    )

row = Path(sys.argv[3]).read_bytes()[0x1075:0x107A]
if row != bytes(5):
    raise SystemExit(f"Restart row was not stock-reset: {list(row)}")
print("UR_TOUR_RESTART_NATIVE=confirmed stock_reset_proven=1 retired=1")
PY

# A retirement persistence failure must not publish the stock wipe without
# retiring the matching host continuation. Make the profile root read-only
# only after the fresh process has reached settled main, then confirm Restart.
run_ui_case restart-persist-fail restart-persist-fail
RESTART_FAIL_ROOT="$WORK/restart-persist-fail-profile"
RESTART_FAIL_LOG="$WORK/restart-persist-fail.log"
cat "$RESTART_FAIL_LOG"
grep -q "UR_TOUR_RESTART PROFILE_SAVE_FAILED" "$RESTART_FAIL_LOG"
! grep -q "UR_TOUR_RESTART RETIRED" "$RESTART_FAIL_LOG"
grep -q '^tour_resume=0:0:0:11000$' "$RESTART_FAIL_ROOT/host-profile.txt"
python3 - "$RESTART_FAIL_ROOT/save.srm" <<'PY'
from pathlib import Path
import sys

row = Path(sys.argv[1]).read_bytes()[0x1075:0x107A]
if row != bytes((1, 1, 0, 0, 0)):
    raise SystemExit(
        f"failed Restart retirement changed durable row: {list(row)}"
    )
print("UR_TOUR_RESTART_PERSIST_FAILURE_NATIVE=continuation_and_sram_preserved=1")
PY

# Stale source mismatch must fail closed before routing.
STALE_ROOT="$WORK/stale-profile"
STALE_DUMPS="$WORK/stale-dumps"
STALE_LOG="$WORK/stale.log"
make_fixture "$STALE_ROOT"
rm -rf "$STALE_DUMPS"
mkdir -p "$STALE_DUMPS"
python3 - "$STALE_ROOT/host-profile.txt" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text()
stale = source.replace(
    "tour_resume=0:0:0:11000",
    "tour_resume=0:0:1:11000",
)
if stale == source:
    raise SystemExit("could not create stale continuation fixture")
path.write_text(stale)
PY

SDL_AUDIODRIVER=dummy \
XDG_DATA_HOME="$PREF_ROOT" \
UR_PRODUCT_DIAGNOSTICS=1 \
UR_TOUR_CONTINUE_ACCEPTANCE=1 \
UR_HOST_STATE_PATH="$STATE" \
UR_PROFILE_SAVE_ROOT="$STALE_ROOT" \
SNESRECOMP_DUMP_DIR="$STALE_DUMPS" \
timeout 100s xvfb-run -a "$EXE" "$ROM" --script "$STALE_SCRIPT" \
  >"$STALE_LOG" 2>&1

cat "$STALE_LOG"
grep -Eq "UR_TOUR_CONTINUE REJECTED .*profile=1 writable=1 continuation=1 snapshot=1 persisted_source=0 live_source=0" "$STALE_LOG"
! grep -q "UR_TOUR_CONTINUE STARTED" "$STALE_LOG"
! grep -q "UR_TOUR_RESUME APPLIED" "$STALE_LOG"

# Authentic mode must never expose or route Modern continuation.
AUTH_ROOT="$WORK/authentic-profile"
AUTH_DUMPS="$WORK/authentic-dumps"
AUTH_LOG="$WORK/authentic.log"
make_fixture "$AUTH_ROOT"
rm -rf "$AUTH_DUMPS"
mkdir -p "$AUTH_DUMPS"

SDL_AUDIODRIVER=dummy \
XDG_DATA_HOME="$PREF_ROOT" \
UR_EXECUTION_MODE=authentic \
UR_PRODUCT_DIAGNOSTICS=1 \
UR_TOUR_CONTINUE_ACCEPTANCE=1 \
UR_HOST_STATE_PATH="$STATE" \
UR_PROFILE_SAVE_ROOT="$AUTH_ROOT" \
SNESRECOMP_DUMP_DIR="$AUTH_DUMPS" \
timeout 100s xvfb-run -a "$EXE" "$ROM" --script "$AUTH_SCRIPT" \
  >"$AUTH_LOG" 2>&1

cat "$AUTH_LOG"
! grep -q "UR_TOUR_ENTRY MENU_OPENED" "$AUTH_LOG"
! grep -q "UR_TOUR_CONTINUE STARTED" "$AUTH_LOG"
! grep -q "UR_TOUR_RESUME APPLIED" "$AUTH_LOG"

echo "UR_TOUR_ENTRY_ACCEPTANCE_RESULT=resume_restart_confirm_cancel_route_cancel_route_failure_retirement_failure_timing_stale_authentic"
