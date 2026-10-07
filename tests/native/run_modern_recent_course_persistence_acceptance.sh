#!/usr/bin/env bash
set -Eeuo pipefail

# Native durable Recent Course acceptance. Recent Course is profile navigation
# metadata (profile codec v5 recent_track): it must be written without
# capturing SRAM or bumping the autosave generation, restored in a fresh
# process for the same named profile, fail closed when malformed, and stay
# inert in Authentic mode.

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <native-exe> <retail-rom> <work-dir>" >&2
  exit 2
fi

EXE="$1"
ROM="$2"
WORK="$3"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PERSIST_SCRIPT="$REPO/tests/input/modern-recent-course-persist.script"
RESTORE_SCRIPT="$REPO/tests/input/modern-recent-course-restore.script"
MAIN_SCRIPT="$REPO/tests/input/modern-main-menu.script"
CLEAN="$REPO/reference/imported/reverse-engineering/dessyreqt/SRAM/Clean.srm"

STATE="$WORK/recent-host-state.txt"
PREF_ROOT="$WORK/recent-xdg"
PREF_DIR="$PREF_ROOT/gamesbyian/UR-Recomp"
mkdir -p "$WORK" "$PREF_DIR"

dump_failure_evidence() {
  local status=$?
  echo "== Modern durable Recent Course acceptance failed: status=$status ==" >&2
  for log in "$WORK"/*.log; do
    [ -f "$log" ] || continue
    echo "===== $log =====" >&2
    cat "$log" >&2 || true
  done
  for profile in "$WORK"/*-profile/host-profile.txt; do
    [ -f "$profile" ] || continue
    echo "===== $profile (without SRAM) =====" >&2
    grep -v '^stock_sram=' "$profile" >&2 || true
  done
  return "$status"
}
trap dump_failure_evidence ERR

cat >"$STATE" <<'STATE_EOF'
UR-HOST-STATE/6
profile=recent.alpha
pause_on_focus_loss=0
vibration_enabled=1
STATE_EOF

cat >"$PREF_DIR/profiles-v1.txt" <<'CATALOG_EOF'
UR-PROFILE-CATALOG/1
recent.alpha|0|MIKE
CATALOG_EOF
printf 'seen-v1\n' >"$PREF_DIR/onboarding-v1.seen"

# make_fixture <root> <header-version> <recent-track-or-empty>
make_fixture() {
  local root="$1"
  local version="$2"
  local recent="$3"
  rm -rf "$root"
  mkdir -p "$root"
  python3 - "$CLEAN" "$root/save.srm" "$root/host-profile.txt" \
    "$version" "$recent" <<'PY'
from pathlib import Path
import sys

source, sram_path, profile_path = map(Path, sys.argv[1:4])
version, recent = sys.argv[4], sys.argv[5]
sram = source.read_bytes()
if len(sram) != 8192:
    raise SystemExit(f"unexpected clean SRAM size: {len(sram)}")
sram_path.write_bytes(sram)
lines = [
    f"UR-HOST-PROFILE/{version}",
    "profile=recent.alpha",
    "generation=1",
    f"stock_sram={sram.hex()}",
    "tour_resume=",
    "ghost_target=off",
    "racer_name=MIKE",
    "racer_index=0",
]
if version == "5":
    lines.append(f"recent_track={recent}")
profile_path.write_text("\n".join(lines) + "\n")
PY
}

run_native() {
  local root="$1"
  local dumps="$2"
  local log="$3"
  local script="$4"
  shift 4
  rm -rf "$dumps"
  mkdir -p "$dumps"
  env "$@" \
    SDL_AUDIODRIVER=dummy \
    XDG_DATA_HOME="$PREF_ROOT" \
    UR_PRODUCT_DIAGNOSTICS=1 \
    UR_HOST_STATE_PATH="$STATE" \
    UR_PROFILE_SAVE_ROOT="$root" \
    SNESRECOMP_DUMP_DIR="$dumps" \
    timeout 150s xvfb-run -a "$EXE" "$ROM" --script "$script" \
      >"$log" 2>&1
}

# A. A v4 profile races Dragster: Recent Course is written as v5 metadata
#    only. The exact SRAM snapshot and autosave generation are untouched.
A_ROOT="$WORK/persist-profile"
A_LOG="$WORK/persist.log"
make_fixture "$A_ROOT" 4 ""
cp "$A_ROOT/host-profile.txt" "$WORK/persist-before.txt"
run_native "$A_ROOT" "$WORK/persist-dumps" "$A_LOG" "$PERSIST_SCRIPT"
cat "$A_LOG"
grep -q "UR_FAST_NAV RECENT_OBSERVED track=0 profile_context=named" "$A_LOG"
grep -q "UR_FAST_NAV RECENT_PERSISTED track=0 generation=1" "$A_LOG"
! grep -q "UR_FAST_NAV RECENT_RESTORED" "$A_LOG"
! grep -q "UR_PROFILE_AUTOSAVE RESULT" "$A_LOG"
python3 - "$WORK/persist-before.txt" "$A_ROOT/host-profile.txt" <<'PY'
from pathlib import Path
import sys

def fields(path):
    lines = Path(path).read_text().splitlines()
    return lines[0], dict(line.split("=", 1) for line in lines[1:])

before_header, before = fields(sys.argv[1])
after_header, after = fields(sys.argv[2])
if before_header != "UR-HOST-PROFILE/4" or after_header != "UR-HOST-PROFILE/5":
    raise SystemExit(f"unexpected headers: {before_header} -> {after_header}")
if after.get("recent_track") != "0":
    raise SystemExit(f"recent_track not persisted: {after.get('recent_track')!r}")
for key in ("profile", "generation", "stock_sram", "tour_resume",
            "ghost_target", "racer_name", "racer_index"):
    if before[key] != after[key]:
        raise SystemExit(f"Recent Course persistence changed {key}")
print("UR_RECENT_PERSIST_NATIVE=metadata_only recent_track=0 sram_equal=1 generation_equal=1")
PY

# B. A fresh process restores a non-default Recent Course (Crawler slot 4,
#    Monster) for the same profile and relaunches it as isolated Practice.
B_ROOT="$WORK/restore-profile"
B_LOG="$WORK/restore.log"
make_fixture "$B_ROOT" 5 4
cp "$B_ROOT/host-profile.txt" "$WORK/restore-before.txt"
run_native "$B_ROOT" "$WORK/restore-dumps" "$B_LOG" "$RESTORE_SCRIPT" \
  UR_RECENT_COURSE_ACCEPTANCE=1 \
  UR_PRACTICE_SAVE_ROOT="$WORK/restore-practice-save" \
  UR_PRACTICE_INPUT_PATH="$WORK/restore-practice-input.txt"
cat "$B_LOG"
grep -q "UR_FAST_NAV RECENT_RESTORED track=4" "$B_LOG"
grep -q "UR_FAST_NAV RECENT_PRACTICE track=4" "$B_LOG"
grep -q "UR_PRACTICE STARTED .* track=4" "$B_LOG"
grep -q "UR_PRACTICE RACE_READY" "$B_LOG"
! grep -q "UR_FAST_NAV RECENT_PERSISTED" "$B_LOG"
cmp "$WORK/restore-before.txt" "$B_ROOT/host-profile.txt"
echo "UR_RECENT_RESTORE_NATIVE=fresh_process track=4 practice_isolated=1 profile_unchanged=1"

# C. An out-of-catalog Recent Course fails closed: the profile is not
#    trusted, nothing is restored, and the file is not rewritten.
C_ROOT="$WORK/malformed-profile"
C_LOG="$WORK/malformed.log"
make_fixture "$C_ROOT" 5 45
cp "$C_ROOT/host-profile.txt" "$WORK/malformed-before.txt"
run_native "$C_ROOT" "$WORK/malformed-dumps" "$C_LOG" "$MAIN_SCRIPT"
cat "$C_LOG"
grep -q "UR_PROFILE_STATE MALFORMED_READ_ONLY" "$C_LOG"
! grep -q "UR_FAST_NAV RECENT_RESTORED" "$C_LOG"
cmp "$WORK/malformed-before.txt" "$C_ROOT/host-profile.txt"
echo "UR_RECENT_MALFORMED_NATIVE=fail_closed restored=0 rewritten=0"

# D. Authentic mode never reads or applies Modern profile metadata.
D_ROOT="$WORK/authentic-profile"
D_LOG="$WORK/authentic.log"
make_fixture "$D_ROOT" 5 4
cp "$D_ROOT/host-profile.txt" "$WORK/authentic-before.txt"
run_native "$D_ROOT" "$WORK/authentic-dumps" "$D_LOG" "$MAIN_SCRIPT" \
  UR_EXECUTION_MODE=authentic
cat "$D_LOG"
grep -q "UR_HOST_STATE AUTHENTIC_INERT" "$D_LOG"
! grep -q "UR_FAST_NAV RECENT_RESTORED" "$D_LOG"
cmp "$WORK/authentic-before.txt" "$D_ROOT/host-profile.txt"

echo "UR_RECENT_COURSE_PERSISTENCE_ACCEPTANCE_RESULT=metadata_only_persist_fresh_restore_malformed_fail_closed_authentic_inert"
