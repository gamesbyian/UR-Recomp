#!/usr/bin/env bash
set -Eeuo pipefail

# Native Modern results-navigation acceptance. Every case reaches a real stock
# results surface first. The host then drives the real keyboard handler, which
# hands Track/Tour/Next Event to the existing stock-menu transport.

if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  echo "usage: $0 <native-exe> <retail-rom> <work-dir> [selection|progression|isolation|earned|all]" >&2
  exit 2
fi

EXE="$1"
ROM="$2"
WORK="$3"
SHARD="${4:-all}"
case "$SHARD" in
  selection|progression|isolation|earned|all) ;;
  *)
    echo "unknown results-navigation shard: $SHARD" >&2
    exit 2
    ;;
esac
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$REPO/tests/input/modern-results-navigation.script"
EARNED_SCRIPT="$REPO/tests/input/modern-results-next-earned.script"
COLD_SCRIPT="$REPO/tests/input/modern-results-cold-reopen.script"
AUTH_SCRIPT="$REPO/tests/input/modern-results-navigation-authentic.script"
PRACTICE_SCRIPT="$REPO/tests/input/modern-practice-repeat-results.script"
CLEAN="$REPO/reference/imported/reverse-engineering/dessyreqt/SRAM/Clean.srm"

STATE="$WORK/results-nav-host-state.txt"
PREF_ROOT="$WORK/results-nav-xdg"
PREF_DIR="$PREF_ROOT/gamesbyian/UR-Recomp"
mkdir -p "$WORK" "$PREF_DIR"

dump_failure_evidence() {
  local status=$?
  echo "== Modern results-navigation acceptance failed: status=$status ==" >&2
  for log in "$WORK"/*.log; do
    [ -f "$log" ] || continue
    echo "===== $log =====" >&2
    cat "$log" >&2 || true
  done
  return "$status"
}
trap dump_failure_evidence ERR

cat >"$STATE" <<'STATE_EOF'
UR-HOST-STATE/6
profile=results.alpha
pause_on_focus_loss=0
vibration_enabled=1
STATE_EOF

cat >"$PREF_DIR/profiles-v1.txt" <<'CATALOG_EOF'
UR-PROFILE-CATALOG/1
results.alpha|0|MIKE
CATALOG_EOF
printf 'seen-v1\n' >"$PREF_DIR/onboarding-v1.seen"

make_fixture() {
  local root="$1"
  local flags="$2"
  rm -rf "$root"
  mkdir -p "$root"
  python3 - "$CLEAN" "$root/save.srm" "$root/host-profile.txt" "$flags" <<'PY'
from pathlib import Path
import sys

source, sram_path, profile_path = map(Path, sys.argv[1:4])
flags_text = sys.argv[4]
sram = bytearray(source.read_bytes())
if len(sram) != 8192:
    raise SystemExit(f"unexpected clean SRAM size: {len(sram)}")

rider = 0
tour = 0
medal = sram[0x069C + 16 * tour + rider]
flags = bytes(int(ch) for ch in flags_text)
if len(flags) != 5 or any(flag > 1 for flag in flags):
    raise SystemExit(f"invalid fixture flags: {flags_text}")

sram[0x10AD] = 1
sram[0x0748] = rider
sram[0x1075:0x107A] = flags
sram_path.write_bytes(sram)
profile_path.write_text(
    "UR-HOST-PROFILE/4\n"
    "profile=results.alpha\n"
    "generation=1\n"
    f"stock_sram={bytes(sram).hex()}\n"
    f"tour_resume={rider}:{tour}:{medal}:{flags_text}\n"
    "ghost_target=off\n"
    "racer_name=MIKE\n"
    "racer_index=0\n"
)
PY
}

run_case() {
  local name="$1"
  local initial_flags="$2"
  local mode="$3"
  local input_script="${4:-$SCRIPT}"
  local root="$WORK/$name-profile"
  local dumps="$WORK/$name-dumps"
  local log="$WORK/$name.log"

  make_fixture "$root" "$initial_flags"
  rm -rf "$dumps"
  mkdir -p "$dumps"

  SDL_AUDIODRIVER=dummy \
  XDG_DATA_HOME="$PREF_ROOT" \
  UR_PRODUCT_DIAGNOSTICS=1 \
  UR_RESULTS_NAV_ACCEPTANCE="$mode" \
  UR_HOST_STATE_PATH="$STATE" \
  UR_PROFILE_SAVE_ROOT="$root" \
  SNESRECOMP_DUMP_DIR="$dumps" \
    timeout 180s xvfb-run -a "$EXE" "$ROM" --script "$input_script" \
      >"$log" 2>&1
}

if [ "$SHARD" = "all" ] || [ "$SHARD" = "selection" ]; then
# One prequalified event is already authoritative. The scripted race replays
# an already-qualified stock event, so the row must remain ambiguous and unchanged.
run_case ambiguous 01000 inspect
cat "$WORK/ambiguous.log"
grep -q "UR_RESULTS_NAV MENU .*next=0 track=1 tour=1 .*records=1 practice=0" "$WORK/ambiguous.log"
! grep -q "UR_RESULTS_NAV NEXT_EVENT_STARTED" "$WORK/ambiguous.log"

# Track Select uses the same reboot + rider/tour route as Resume, then the
# existing continuation authority restores the result row before releasing.
run_case track 01000 track
cat "$WORK/track.log"
grep -q "UR_RESULTS_NAV ACCEPT target=track" "$WORK/track.log"
grep -q "UR_RESULTS_NAV TRACK_SELECT_STARTED" "$WORK/track.log"
grep -q "UR_TOUR_RESUME APPLIED" "$WORK/track.log"
grep -q "UR_RESULTS_NAV TRACK_SELECT_READY" "$WORK/track.log"
grep -q "UR_RESULTS_NAV ACCEPT_TRACK_READY" "$WORK/track.log"
! grep -q "UR_TOUR_CONTINUE ABORTED" "$WORK/track.log"

fi

if [ "$SHARD" = "all" ] || [ "$SHARD" = "progression" ]; then
# Tour Select stops on stock TOUR_SELECT. Because rider confirmation has already
# crossed the stock qualification wipe, it must use the existing exact profile
# snapshot rollback before input ownership is released.
run_case tour 01000 tour
cat "$WORK/tour.log"
grep -q "UR_RESULTS_NAV ACCEPT target=tour" "$WORK/tour.log"
grep -q "UR_RESULTS_NAV TOUR_SELECT_STARTED" "$WORK/tour.log"
grep -q "UR_TOUR_CONTINUE ROLLED_BACK_PROFILE_SNAPSHOT" "$WORK/tour.log"
grep -q "UR_RESULTS_NAV TOUR_SELECT_READY" "$WORK/tour.log"
grep -q "UR_RESULTS_NAV ACCEPT_TOUR_READY" "$WORK/tour.log"
! grep -q "UR_TOUR_CONTINUE ABORTED" "$WORK/tour.log"

python3 - "$WORK/tour-profile/save.srm" "$WORK/tour-profile/host-profile.txt" <<'PY'
from pathlib import Path
import sys

sram = Path(sys.argv[1]).read_bytes()
profile = Path(sys.argv[2]).read_text()
row = sram[0x1075:0x107A]
if row != bytes((0, 1, 0, 0, 0)):
    raise SystemExit(f"Tour Select did not preserve authoritative progression: {list(row)}")
if "tour_resume=0:0:0:01000" not in profile:
    raise SystemExit("Tour Select profile continuation diverged from result row")
print("UR_RESULTS_TOUR_SELECT_NATIVE=stock_menu=1 rollback_preserved=1")
PY

# Four events are prequalified with Crawler as the sole remaining event.
# Replaying the proven Crawler finish does not invent a new qualification, so
# the authoritative 01111 row remains four-of-five at Results and Crawler is
# still the one unique Next Event target.
run_case next 01111 next
python3 - "$WORK/next-dumps/race-results.sram.bin" <<'PY'
from pathlib import Path
import sys

sram = Path(sys.argv[1]).read_bytes()
row = sram[0x1075:0x107A]
if row != bytes((0, 1, 1, 1, 1)):
    raise SystemExit(
        f"Next Event fixture lost authoritative four-of-five row: {list(row)}"
    )
print("UR_RESULTS_NEXT_FIXTURE_NATIVE=results_row=01111 unique_track=0")
PY
cat "$WORK/next.log"
grep -q "UR_RESULTS_NAV MENU .*next=1 track=1 tour=1 .*records=1 practice=0" "$WORK/next.log"
grep -q "UR_RESULTS_NAV ACCEPT target=next" "$WORK/next.log"
grep -q "UR_RESULTS_NAV NEXT_EVENT_STARTED" "$WORK/next.log"
grep -q "UR_NEXT_EVENT SELECTING track=0 slot=0" "$WORK/next.log"
grep -q "UR_NEXT_EVENT RACE_ENTERED" "$WORK/next.log"
grep -q "UR_NEXT_EVENT RACE_VERIFIED expected=0 actual=0 course_equal=1" "$WORK/next.log"
grep -q "UR_RESULTS_NAV ACCEPT_NEXT_RACE" "$WORK/next.log"
! grep -q "UR_TOUR_CONTINUE ABORTED" "$WORK/next.log"

fi

if [ "$SHARD" = "earned" ]; then
# Additional opt-in complete-product negative discriminator, not a rewrite of
# the established route pass: start from an explicitly seeded four-of-five
# row, ENTER a real derived Next Event, then PLAY the second stock race.
run_case next-earned 01111 next-earned "$EARNED_SCRIPT"
cat "$WORK/next-earned.log"
grep -q "UR_NEXT_EVENT RACE_VERIFIED expected=0 actual=0 course_equal=1" "$WORK/next-earned.log"
grep -q "UR_RESULTS_NAV ACCEPT_NEXT_RACE" "$WORK/next-earned.log"
grep -q "UR_RESULTS_NAV NEXT_EARNED_RESULT observed=1 source_finish=1 persisted=1 sram_changed=1" "$WORK/next-earned.log"

# A new process must actually reload the product's committed SRAM. The
# pre-seeded fixture is NOT a source-earned event and never earns ONE-03.
COLD_ROOT="$WORK/next-earned-profile"
COLD_DUMPS="$WORK/next-earned-cold-dumps"
COLD_LOG="$WORK/next-earned-cold.log"
mkdir -p "$COLD_DUMPS"
SDL_AUDIODRIVER=dummy \
XDG_DATA_HOME="$PREF_ROOT" \
UR_PRODUCT_DIAGNOSTICS=1 \
UR_PROFILE_SRAM_DIAGNOSTICS=1 \
UR_HOST_STATE_PATH="$STATE" \
UR_PROFILE_SAVE_ROOT="$COLD_ROOT" \
SNESRECOMP_DUMP_DIR="$COLD_DUMPS" \
  timeout 70s xvfb-run -a "$EXE" "$ROM" --script "$COLD_SCRIPT" \
    >"$COLD_LOG" 2>&1
grep -q "UR_PROFILE_SRAM LOADED" "$COLD_LOG"
python3 - "$WORK/next-earned-dumps/race-results.sram.bin" \
          "$WORK/next-earned-dumps/next-event-race-results.sram.bin" \
          "$COLD_ROOT/save.srm" "$COLD_ROOT/host-profile.txt" \
          "$COLD_DUMPS/cold-main-menu.sram.bin" <<'PY'
from pathlib import Path
import sys
first, second, saved, profile, reopened = map(Path, sys.argv[1:])
first_raw, second_raw = first.read_bytes(), second.read_bytes()
saved_raw, cold_raw = saved.read_bytes(), reopened.read_bytes()
if any(len(value) != 8192 for value in
       (first_raw, second_raw, saved_raw, cold_raw)):
    raise SystemExit("ONE-03 next earned: invalid actual SRAM image size")
if first_raw[0x1075:0x107A] != bytes((0, 1, 1, 1, 1)):
    raise SystemExit("ONE-03 next earned: initial four-of-five row changed")
if second_raw == first_raw:
    raise SystemExit("ONE-03 next earned: follow-on result earned no SRAM change")
# Changed lap/record metadata alone is not tour progression. A genuinely
# qualifying fifth event must advance the selected tour bit or the awarded
# medal; completing a tour may legitimately reset all five bits.
initial_row = first_raw[0x1075:0x107A]
final_row = second_raw[0x1075:0x107A]
initial_medal = first_raw[0x069C]
final_medal = second_raw[0x069C]
if initial_row == final_row and initial_medal == final_medal:
    raise SystemExit("ONE-03 next earned: source race produced no tour progression or medal")
if initial_medal == final_medal and any(
        a == 1 and b != 1 for a, b in zip(initial_row, final_row)):
    raise SystemExit("ONE-03 next earned: prior completed tour flags were lost")
if saved_raw != cold_raw:
    raise SystemExit("ONE-03 next earned: fresh process did not reload saved SRAM")
fields = dict(line.split("=", 1) for line in profile.read_text().splitlines()
              if "=" in line)
if bytes.fromhex(fields["stock_sram"]) != saved_raw:
    raise SystemExit("ONE-03 next earned: typed profile and SRAM diverged")
print("UR_RESULTS_NAV NEXT_EARNED_COLD_REOPEN=source_second_result=1 byte_equal=1")
PY
fi

if [ "$SHARD" = "all" ] || [ "$SHARD" = "isolation" ]; then
# Quick Practice results retain only Repeat Practice + Records. No progression
# navigation can be inferred from the disposable SRAM.
PRACTICE_ROOT="$WORK/practice-save"
PRACTICE_LOG="$WORK/practice.log"
PRACTICE_DUMPS="$WORK/practice-dumps"
rm -rf "$PRACTICE_ROOT" "$PRACTICE_DUMPS"
mkdir -p "$PRACTICE_ROOT" "$PRACTICE_DUMPS"
SDL_AUDIODRIVER=dummy \
XDG_DATA_HOME="$PREF_ROOT" \
UR_PRODUCT_DIAGNOSTICS=1 \
UR_RESULTS_NAV_ACCEPTANCE=practice \
UR_PRACTICE_ACCEPTANCE=1 \
UR_PRACTICE_SAVE_ROOT="$PRACTICE_ROOT" \
UR_HOST_STATE_PATH="$STATE" \
SNESRECOMP_DUMP_DIR="$PRACTICE_DUMPS" \
  timeout 180s xvfb-run -a "$EXE" "$ROM" --script "$PRACTICE_SCRIPT" \
    >"$PRACTICE_LOG" 2>&1
cat "$PRACTICE_LOG"
grep -q "UR_RESULTS_NAV MENU .*next=0 track=0 tour=0 repeat=1 records=1 practice=1" "$PRACTICE_LOG"
! grep -q "UR_RESULTS_NAV .*_STARTED" "$PRACTICE_LOG"
! grep -q "UR_PROFILE_AUTOSAVE RESULT" "$PRACTICE_LOG"

# The player-facing results rematch must restore disposable Practice state,
# reboot to stock MAIN, and use the original target-aware Quick Practice
# launch route. The input script reaches results, then awaits a second race.
REMATCH_ROOT="$WORK/practice-rematch-save"
REMATCH_LOG="$WORK/practice-rematch.log"
REMATCH_DUMPS="$WORK/practice-rematch-dumps"
rm -rf "$REMATCH_ROOT" "$REMATCH_DUMPS"
mkdir -p "$REMATCH_ROOT" "$REMATCH_DUMPS"
SDL_AUDIODRIVER=dummy \
XDG_DATA_HOME="$PREF_ROOT" \
UR_PRODUCT_DIAGNOSTICS=1 \
UR_FAST_REPEAT_ACCEPTANCE=1 \
UR_PRACTICE_ACCEPTANCE=1 \
UR_PRACTICE_SAVE_ROOT="$REMATCH_ROOT" \
UR_HOST_STATE_PATH="$STATE" \
SNESRECOMP_DUMP_DIR="$REMATCH_DUMPS" \
  timeout 180s xvfb-run -a "$EXE" "$ROM" --script "$PRACTICE_SCRIPT" \
    >"$REMATCH_LOG" 2>&1
cat "$REMATCH_LOG"
grep -q "UR_FAST_NAV REPEAT_PRACTICE_ROUTER_REQUESTED" "$REMATCH_LOG"
grep -q "UR_PRACTICE RESTORED" "$REMATCH_LOG"
grep -q "UR_FAST_NAV REPEAT_PRACTICE_ROUTER_STARTED" "$REMATCH_LOG"
grep -q "UR_FAST_NAV REPEAT_PRACTICE_ROUTER_RACE_READY" "$REMATCH_LOG"
! grep -q "UR_FAST_NAV REPEAT_PRACTICE_ROUTER_FAILED" "$REMATCH_LOG"
! grep -q "UR_PRACTICE COURSE_MISMATCH" "$REMATCH_LOG"
! grep -q "UR_PROFILE_AUTOSAVE RESULT" "$REMATCH_LOG"

# Authentic mode never acquires the results-navigation surface.
AUTH_ROOT="$WORK/authentic-profile"
make_fixture "$AUTH_ROOT" 01000
AUTH_LOG="$WORK/authentic.log"
SDL_AUDIODRIVER=dummy \
XDG_DATA_HOME="$PREF_ROOT" \
UR_EXECUTION_MODE=authentic \
UR_PRODUCT_DIAGNOSTICS=1 \
UR_RESULTS_NAV_ACCEPTANCE=inspect \
UR_HOST_STATE_PATH="$STATE" \
UR_PROFILE_SAVE_ROOT="$AUTH_ROOT" \
  timeout 180s xvfb-run -a "$EXE" "$ROM" --script "$AUTH_SCRIPT" \
    >"$AUTH_LOG" 2>&1
cat "$AUTH_LOG"
grep -q "UR_HOST_STATE AUTHENTIC_INERT" "$AUTH_LOG"
! grep -q "UR_RESULTS_NAV MENU" "$AUTH_LOG"
! grep -q "UR_RESULTS_NAV .*_STARTED" "$AUTH_LOG"

fi

echo "UR_RESULTS_NAV_ACCEPTANCE_RESULT=$SHARD"
