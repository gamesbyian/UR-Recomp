#!/usr/bin/env bash
set -Eeuo pipefail
OUT="${UR_EXPERIMENT_OUTPUT_DIR:?}"
mkdir -p "$OUT" "$HOME/build"
sudo apt-get -o Acquire::Retries=3 update
sudo apt-get -o Acquire::Retries=3 install -y --no-install-recommends xvfb pkg-config libgl-dev libx11-dev libxext-dev libxrandr-dev libxcursor-dev libxi-dev libxfixes-dev libxkbcommon-dev libwayland-dev libasound2-dev libpulse-dev libxss-dev libxtst-dev
python3 tools/verify_rom.py reference/roms/retail/Uniracers_USA.sfc
python3 tools/bootstrap_toolchain.py --offline --tool snesrecomp --clone-only
python3 tools/bootstrap_toolchain.py --offline --tool sdl3 --clone-only
FRAMEWORK="$GITHUB_WORKSPACE/.tools/src/snesrecomp"
TMP="$HOME/build"
SNESRECOMP_ROOT="$FRAMEWORK" sh "$FRAMEWORK/tools/new_project/setup_project.sh" --rom "$GITHUB_WORKSPACE/reference/roms/retail/Uniracers_USA.sfc" --dir "$TMP" --name Uniracers --players 2 --yes --no-ci --no-fetch-boxart --no-recomp-ui --no-netplay --no-github --no-submodules --no-generate --no-build
ROOT="$TMP/UniracersSNESRecomp"
python3 tools/prepare_native_widescreen_product.py --framework "$FRAMEWORK" --project "$ROOT" --rom "$GITHUB_WORKSPACE/reference/roms/retail/Uniracers_USA.sfc" --json-out "$OUT/prepare.json"
python3 tools/patch_modern_product_host.py "$ROOT/src/main.c" --game-rtl "$ROOT/src/game_rtl.c" --cmake "$ROOT/CMakeLists.txt"
# Opt-in, experiment-branch-only observation of the actual word delivered by
# RtlRunFrame and the stock guest screen, without changing game behavior.
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
path=Path("native/product/uniracers_modern_host.cpp")
if not path.is_file():
    raise SystemExit(f"missing repository-owned product host: {path}")
s=path.read_text()
# Host Enter was observed as handled=0 on stock 2P Results. Remove this
# inert host action in the ephemeral experiment, leaving actual guest input
# responsible for navigation and fixture result capture.
old_confirm = "const int key = continue_legs && step == 5 ? SDLK_RETURN\n        : step == 0 || step == 3 || step == 5 ? SDLK_F4"
new_confirm = """if (continue_legs && step == 5) {
        product_diagnostic("UR_LOCAL_TOURNAMENT SECOND_LEG_HOST_ACTION_SKIPPED");
        return;
    }
    const int key = step == 0 || step == 3 || step == 5 ? SDLK_F4"""
assert s.count(old_confirm) == 1, "stock Results host key route changed"
s = s.replace(old_confirm, new_confirm, 1)
anchor="    g_surface = decision.surface;\n"
assert s.count(anchor)==1, "missing or duplicate game-surface anchor"
trace='''    if (stats && stats->frame >= 59000 && stats->frame <= 62000 &&
        (stats->frame % 24 == 0 ||
         stats->controller_word != g_qa03_previous_controller_word ||
         g_surface != g_qa03_previous_surface)) {
        std::fprintf(stderr,
            "QA03_RESOLVED_INPUT frame=%llu word=%06X stock_menu=%02X race_state=%02X surface=%d selection_ram_0090_00A7=%02X,%02X,%02X,%02X,%02X,%02X,%02X,%02X\\n",
            static_cast<unsigned long long>(stats->frame),
            static_cast<unsigned>(stats->controller_word),
            static_cast<unsigned>(g_ram[0x0313]),
            static_cast<unsigned>(g_ram[0x009F]),
            static_cast<int>(g_surface),
            static_cast<unsigned>(g_ram[0x0090]),
            static_cast<unsigned>(g_ram[0x0094]),
            static_cast<unsigned>(g_ram[0x0098]),
            static_cast<unsigned>(g_ram[0x009C]),
            static_cast<unsigned>(g_ram[0x00A0]),
            static_cast<unsigned>(g_ram[0x00A4]),
            static_cast<unsigned>(g_ram[0x00A6]),
            static_cast<unsigned>(g_ram[0x00A7]));
    }
    if (stats) {
        g_qa03_previous_controller_word = stats->controller_word;
        g_qa03_previous_surface = g_surface;
    }
'''
# Local function statics avoid changing exported interfaces or game state.
trace=trace.replace("g_qa03_previous_controller_word", "qa03_previous_controller_word").replace("g_qa03_previous_surface", "qa03_previous_surface")
trace="    static uint32_t qa03_previous_controller_word = 0;\n    static int qa03_previous_surface = -1;\n".replace("\\n", "\n")+trace
s=s.replace(anchor,anchor+trace,1)
path.write_text(s)
print(f"QA03 instrumented source: {path}")
PY
cmake -S "$ROOT" -B "$ROOT/build" -DCMAKE_BUILD_TYPE=Release -DSNESRECOMP_ROOT="$FRAMEWORK" -DSNESRECOMP_SDL_BACKEND=SDL3 -DSNESRECOMP_SDL3_FETCH=ON -DSNESRECOMP_SDL3_SOURCE_DIR="$GITHUB_WORKSPACE/.tools/src/sdl3/SDL3-3.4.10"
cmake --build "$ROOT/build" -j"$(nproc)"
python3 - "$OUT/qa03-second-leg.input" <<'PY'
import pathlib,sys
original=pathlib.Path("tests/input/two-player-joined-records-acceptance.input").read_text()
# Retain genuine first fixture input; extend ordinary controller actions
# beyond the first result instead of injecting a synthetic fixture result.
with open(sys.argv[1],"w") as f:
    f.write(original)
    for index, frame in enumerate(range(60000,165000,24)):
        # The earlier 081/080 cadence held the 080 action continuously,
        # while 100/080 pulsed Start but still never released that action.
        # Source-bound VS route tests Start (100) as confirmation, with release edges:
        # 001 is a nonzero, parser-valid release word (000 is rejected).
        # No result or store mutation is synthesized.
        # Release Start between presses from the first
        # continuation frame. Prior 081/080 never tested Start.
        word = "001" if index % 2 == 0 else "100"
        f.write(f"{frame}:24:{word}:000\n")
PY
printf 'turbo on\nwait 170000\ndump qa03-second-leg-unresolved\nquit\n' >"$OUT/qa03-second-leg.script"
WORK="$HOME/qa03"
PREF="$WORK/prefs/gamesbyian/UR-Recomp"
mkdir -p "$PREF" "$WORK/multiplayer-runs"
printf 'UR-PROFILE-CATALOG/1\njoin.alpha|0|MIKE\njoin.bravo|1|ANDREW\n' >"$PREF/profiles-v1.txt"
printf 'seen-v1\n' >"$PREF/onboarding-v1.seen"
printf 'UR-HOST-STATE/6\nprofile=\npause_on_focus_loss=0\nvibration_enabled=1\n' >"$WORK/host-state.txt"
set +e
env -u UR_MULTIPLAYER_MATCH_ACCEPTANCE -u UR_LOCAL_TOURNAMENT_NATIVE_ACCEPTANCE SDL_AUDIODRIVER=dummy XDG_DATA_HOME="$WORK/prefs" UR_HOST_STATE_PATH="$WORK/host-state.txt" UR_MULTIPLAYER_MATCH_CAPTURE_DIRECTORY="$WORK/multiplayer-runs" UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE=capture UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE=legs_continue UR_PRODUCT_DIAGNOSTICS=1 SNESRECOMP_INPUT_FILE="$OUT/qa03-second-leg.input" timeout 900s xvfb-run -a "$ROOT/build/UniracersSNESRecomp" "$GITHUB_WORKSPACE/reference/roms/retail/Uniracers_USA.sfc" --script "$OUT/qa03-second-leg.script" >"$OUT/qa03-game.log" 2>&1
RC=$?
set -e
printf 'exit=%s source=%s\n' "$RC" "$UR_EXPERIMENT_SOURCE_SHA" >"$OUT/status.txt"
grep -E 'UR_LOCAL_TOURNAMENT|UR_MULTIPLAYER_MATCH|UR_PROFILE_UI|QA03_RESOLVED_INPUT|first frame simulated' "$OUT/qa03-game.log" | tail -n 100 >"$OUT/qa03-markers.txt" || true
grep -q 'UR_LOCAL_TOURNAMENT FIXTURE_COMMITTED' "$OUT/qa03-game.log"
grep -q 'UR_LOCAL_TOURNAMENT ARMED fixture=1' "$OUT/qa03-game.log"
grep -q 'UR_LOCAL_TOURNAMENT GUEST_SECOND_LEG_COMMITTED' "$OUT/qa03-game.log"
test "$RC" -eq 0
echo 'QA03_SECOND_GUEST_LEG=PASS'
