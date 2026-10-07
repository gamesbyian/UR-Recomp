#!/usr/bin/env bash
set -Eeuo pipefail

# Native Next Event acceptance. A named Modern profile with an unfinished
# Crawler tour (four of five events qualified) opens the real Tour surface,
# confirms the preselected Next Event row, and must reach an authoritative
# stock tour race on the one remaining event through ordinary menu input.
# A two-of-five row must not offer Next Event at all.

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <native-exe> <retail-rom> <work-dir>" >&2
  exit 2
fi

EXE="$1"
ROM="$2"
WORK="$3"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$REPO/tests/input/modern-tour-next-event-acceptance.script"
CLEAN="$REPO/reference/imported/reverse-engineering/dessyreqt/SRAM/Clean.srm"

STATE="$WORK/next-event-host-state.txt"
PREF_ROOT="$WORK/next-event-xdg"
PREF_DIR="$PREF_ROOT/gamesbyian/UR-Recomp"
mkdir -p "$WORK" "$PREF_DIR"

dump_failure_evidence() {
  local status=$?
  echo "== Modern Next Event acceptance failed: status=$status ==" >&2
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
profile=resume.alpha
pause_on_focus_loss=0
vibration_enabled=1
STATE_EOF

cat >"$PREF_DIR/profiles-v1.txt" <<'CATALOG_EOF'
UR-PROFILE-CATALOG/1
resume.alpha|0|MIKE
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
if medal != 0:
    raise SystemExit(f"clean fixture medal is not zero: {medal}")

flags = bytes(int(ch) for ch in flags_text)
sram[0x10AD] = 1
sram[0x0748] = rider
sram[0x1075:0x107A] = flags
sram_path.write_bytes(sram)
profile_path.write_text(
    "UR-HOST-PROFILE/4\n"
    "profile=resume.alpha\n"
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
  local flags="$2"
  local mode="$3"
  local root="$WORK/$name-profile"
  local dumps="$WORK/$name-dumps"
  local log="$WORK/$name.log"

  make_fixture "$root" "$flags"
  rm -rf "$dumps"
  mkdir -p "$dumps"

  # UR_NEXT_EVENT_ACCEPTANCE presses F3 / Enter / Escape through the real
  # Modern keyboard handler on emulated-frame boundaries. The run ends via
  # the script (race reached) or the hook's own desktop quit.
  SDL_AUDIODRIVER=dummy \
  XDG_DATA_HOME="$PREF_ROOT" \
  UR_PRODUCT_DIAGNOSTICS=1 \
  UR_NEXT_EVENT_ACCEPTANCE="$mode" \
  UR_HOST_STATE_PATH="$STATE" \
  UR_PROFILE_SAVE_ROOT="$root" \
  SNESRECOMP_DUMP_DIR="$dumps" \
  timeout 150s xvfb-run -a "$EXE" "$ROM" --script "$SCRIPT" \
    >"$log" 2>&1
}

# Ambiguous two-of-five row: Next Event is not offered.
run_case ambiguous 11000 inspect
AMBIGUOUS_LOG="$WORK/ambiguous.log"
cat "$AMBIGUOUS_LOG"
grep -q "UR_TOUR_ENTRY MENU_OPENED rider=0 tour=0 tier=BRONZE next_event=0" "$AMBIGUOUS_LOG"
! grep -q "UR_TOUR_CONTINUE STARTED" "$AMBIGUOUS_LOG"

# Unique four-of-five row: one confirm reaches the remaining event's race.
run_case next-event 11110 confirm
NEXT_ROOT="$WORK/next-event-profile"
NEXT_DUMPS="$WORK/next-event-dumps"
NEXT_LOG="$WORK/next-event.log"
cat "$NEXT_LOG"
grep -q "UR_TOUR_ENTRY MENU_OPENED rider=0 tour=0 tier=BRONZE next_event=1" "$NEXT_LOG"
grep -q "UR_TOUR_CONTINUE STARTED intent=next_event rider=0 tour=0 completed=4 tier=BRONZE menu=D7 race=0" "$NEXT_LOG"
grep -q "UR_TOUR_CONTINUE READY intent=next_event tour=0 menu=F6" "$NEXT_LOG"
grep -q "UR_TOUR_RESUME APPLIED" "$NEXT_LOG"
grep -q "UR_NEXT_EVENT SELECTING track=4 slot=4" "$NEXT_LOG"
grep -q "UR_NEXT_EVENT RACE_ENTERED" "$NEXT_LOG"
grep -q "UR_NEXT_EVENT RACE_VERIFIED expected=4 actual=4 course_equal=1" "$NEXT_LOG"
! grep -q "UR_TOUR_CONTINUE ABORTED" "$NEXT_LOG"
! grep -q "UR_TOUR_CONTINUE ROLLED_BACK_PROFILE_SNAPSHOT" "$NEXT_LOG"

python3 - "$NEXT_LOG" "$NEXT_DUMPS/next-event-track-select.wram.bin" \
  "$NEXT_DUMPS/next-event-race-entered.wram.bin" <<'PY'
from pathlib import Path
import sys

log = Path(sys.argv[1]).read_text()
order = [
    log.index("UR_TOUR_RESUME APPLIED"),
    log.index("UR_NEXT_EVENT SELECTING"),
    log.index("UR_NEXT_EVENT RACE_ENTERED"),
    log.index("UR_NEXT_EVENT RACE_VERIFIED"),
]
if order != sorted(order):
    raise SystemExit(f"Next Event lifecycle out of order: {order}")

track = Path(sys.argv[2]).read_bytes()
race = Path(sys.argv[3]).read_bytes()
if track[0x009F] != 0xF6 or track[0x0313] == 1:
    raise SystemExit("Next Event did not pass through stock TRACK_SELECT")
if race[0x0313] != 1:
    raise SystemExit("Next Event did not enter an authoritative race")
if race[0x00D0] != 0:
    raise SystemExit(f"Next Event left the saved tour row: {race[0x00D0]}")
print("UR_NEXT_EVENT_NATIVE=one_action stock_route=1 course_equal=1 tour_row=0")
PY

# Cancelling after the restore, while the host still owns the stock cursor,
# releases the route before any race and preserves the restored progress.
run_case cancel 11110 cancel
CANCEL_ROOT="$WORK/cancel-profile"
CANCEL_LOG="$WORK/cancel.log"
cat "$CANCEL_LOG"
grep -q "UR_NEXT_EVENT SELECTING track=4 slot=4" "$CANCEL_LOG"
grep -q "UR_TOUR_CONTINUE CANCELLED" "$CANCEL_LOG"
! grep -q "UR_NEXT_EVENT RACE_ENTERED" "$CANCEL_LOG"
grep -q '^tour_resume=0:0:0:11110$' "$CANCEL_ROOT/host-profile.txt"
python3 - "$CANCEL_ROOT/save.srm" <<'PY'
from pathlib import Path
import sys

row = Path(sys.argv[1]).read_bytes()[0x1075:0x107A]
if row != bytes((1, 1, 1, 1, 0)):
    raise SystemExit(f"Next Event cancel changed tour row: {list(row)}")
print("UR_NEXT_EVENT_CANCEL_NATIVE=race_entered=0 progress_preserved=1")
PY

echo "UR_NEXT_EVENT_ACCEPTANCE_RESULT=ambiguous_hidden_unique_routed_verified_cancel_preserved"
