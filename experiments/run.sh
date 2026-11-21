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
cmake -S "$ROOT" -B "$ROOT/build" -DCMAKE_BUILD_TYPE=Release -DSNESRECOMP_ROOT="$FRAMEWORK" -DSNESRECOMP_SDL_BACKEND=SDL3 -DSNESRECOMP_SDL3_FETCH=ON -DSNESRECOMP_SDL3_SOURCE_DIR="$GITHUB_WORKSPACE/.tools/src/sdl3/SDL3-3.4.10"
cmake --build "$ROOT/build" -j"$(nproc)"
python3 - "$OUT/qa03-second-leg.input" <<'PY'
import pathlib,sys
original=pathlib.Path("tests/input/two-player-joined-records-acceptance.input").read_text()
# Retain genuine first fixture input; extend ordinary controller actions
# beyond the first result instead of injecting a synthetic fixture result.
with open(sys.argv[1],"w") as f:
    f.write(original)
    for frame in range(4200,105000,24):
        f.write(f"{frame}:24:081:000\n")
PY
printf 'turbo on\nwait 110000\ndump qa03-second-leg-unresolved\nquit\n' >"$OUT/qa03-second-leg.script"
WORK="$HOME/qa03"
PREF="$WORK/prefs/gamesbyian/UR-Recomp"
mkdir -p "$PREF" "$WORK/multiplayer-runs"
printf 'UR-PROFILE-CATALOG/1\njoin.alpha|0|MIKE\njoin.bravo|1|ANDREW\n' >"$PREF/profiles-v1.txt"
printf 'seen-v1\n' >"$PREF/onboarding-v1.seen"
printf 'UR-HOST-STATE/6\nprofile=\npause_on_focus_loss=0\nvibration_enabled=1\n' >"$WORK/host-state.txt"
set +e
env -u UR_MULTIPLAYER_MATCH_ACCEPTANCE -u UR_LOCAL_TOURNAMENT_NATIVE_ACCEPTANCE SDL_AUDIODRIVER=dummy XDG_DATA_HOME="$WORK/prefs" UR_HOST_STATE_PATH="$WORK/host-state.txt" UR_MULTIPLAYER_MATCH_CAPTURE_DIRECTORY="$WORK/multiplayer-runs" UR_LOCAL_MULTIPLAYER_JOIN_ACCEPTANCE=capture UR_LOCAL_TOURNAMENT_PANEL_ACCEPTANCE=legs_continue UR_PRODUCT_DIAGNOSTICS=1 SNESRECOMP_INPUT_FILE="$OUT/qa03-second-leg.input" timeout 900s xvfb-run -a "$ROOT/build/UniracersSNESRecomp" "$GITHUB_WORKSPACE/reference/roms/retail/Uniracers_USA.sfc" --script "$GITHUB_WORKSPACE/"$OUT/qa03-second-leg.script" >"$OUT/qa03-game.log" 2>&1
RC=$?
set -e
printf 'exit=%s source=%s\n' "$RC" "$UR_EXPERIMENT_SOURCE_SHA" >"$OUT/status.txt"
grep -E 'UR_LOCAL_TOURNAMENT|UR_MULTIPLAYER_MATCH|UR_PROFILE_UI|first frame simulated' "$OUT/qa03-game.log" | tail -n 100 >"$OUT/qa03-markers.txt" || true
grep -q 'UR_LOCAL_TOURNAMENT FIXTURE_COMMITTED' "$OUT/qa03-game.log"
grep -q 'UR_LOCAL_TOURNAMENT ARMED fixture=1' "$OUT/qa03-game.log"
grep -q 'UR_LOCAL_TOURNAMENT GUEST_SECOND_LEG_COMMITTED' "$OUT/qa03-game.log"
test "$RC" -eq 0
echo 'QA03_SECOND_GUEST_LEG=PASS'
