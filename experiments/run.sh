#!/usr/bin/env bash
set -euo pipefail
OUT="${UR_EXPERIMENT_OUTPUT_DIR:?}"
mkdir -p "$OUT"
printf 'source=%s\n' "$UR_EXPERIMENT_SOURCE_SHA" > "$OUT/receipt.txt"
sudo apt-get -o Acquire::Retries=3 update
sudo apt-get -o Acquire::Retries=3 install -y --no-install-recommends pkg-config libgl-dev libx11-dev libxext-dev libxrandr-dev libxcursor-dev libxi-dev libxfixes-dev libxkbcommon-dev libwayland-dev libasound2-dev libpulse-dev libxss-dev libxtst-dev xvfb xauth
python3 tools/verify_rom.py reference/roms/retail/Uniracers_USA.sfc
python3 tools/bootstrap_toolchain.py --offline --tool snesrecomp --clone-only
FRAMEWORK="$PWD/.tools/src/snesrecomp"
TMP="$(mktemp -d)"
SNESRECOMP_ROOT="$FRAMEWORK" sh "$FRAMEWORK/tools/new_project/setup_project.sh" --rom "$PWD/reference/roms/retail/Uniracers_USA.sfc" --dir "$TMP" --name Uniracers --players 2 --yes --no-ci --no-fetch-boxart --no-recomp-ui --no-netplay --no-github --no-submodules --no-generate --no-build
ROOT="$TMP/UniracersSNESRecomp"
python3 tools/prepare_native_widescreen_product.py --framework "$FRAMEWORK" --project "$ROOT" --rom "$PWD/reference/roms/retail/Uniracers_USA.sfc" --json-out "$OUT/prepare.json"
python3 tools/patch_modern_product_host.py "$ROOT/src/main.c" --game-rtl "$ROOT/src/game_rtl.c" --cmake "$ROOT/CMakeLists.txt"
python3 tools/bootstrap_toolchain.py --offline --tool sdl3 --clone-only
cmake -S "$ROOT" -B "$ROOT/build" -DCMAKE_BUILD_TYPE=Release -DSNESRECOMP_ROOT="$FRAMEWORK" -DSNESRECOMP_SDL_BACKEND=SDL3 -DSNESRECOMP_SDL3_FETCH=ON -DSNESRECOMP_SDL3_SOURCE_DIR="$PWD/.tools/src/sdl3/SDL3-3.4.10"
cmake --build "$ROOT/build" -j4
EXE="$ROOT/build/UniracersSNESRecomp"
test -x "$EXE"
SAVE="$TMP/fresh-dragster-save"
mkdir -p "$SAVE" "$TMP/dumps"
printf '[General]\nDisableFrameDelay = 1\n' > "$SAVE/config.ini"
# Real shipping guest/controller script. Preserve only bounded non-ROM diagnostics.
set +e
SNESRECOMP_USER_DATA_DIR="$SAVE" SNESRECOMP_DUMP_DIR="$TMP/dumps" SDL_AUDIODRIVER=dummy timeout 300s xvfb-run -a "$EXE" "$PWD/reference/roms/retail/Uniracers_USA.sfc" --script "$PWD/tests/input/race-finish-dragster.script" > "$OUT/player.log" 2>&1
status=$?
set -e
printf 'route_exit=%s\n' "$status" >> "$OUT/receipt.txt"
grep -E 'config dir anchored|script|timeout|error|result' "$OUT/player.log" | tail -100 > "$OUT/route-signals.txt" || true
python3 - "$TMP/dumps" "$OUT" <<'PY'
import json,sys,hashlib,pathlib
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2])
records=[]
for f in sorted(root.glob("*.wram.bin")):
    data=f.read_bytes()
    def u16(addr): return int.from_bytes(data[addr:addr+2], "little") if len(data) >= addr+2 else None
    records.append(dict(
        name=f.stem, size=len(data), sha256=hashlib.sha256(data).hexdigest(),
        menu=data[0x9f], track=data[0xce], in_race=data[0x313],
        guest_state_word_0053=u16(0x53),
        direct_page_c6=u16(0xc6), direct_page_c8=u16(0xc8),
        direct_page_c0_cf=data[0xc0:0xd0].hex(),
    ))
(out/"checkpoints.json").write_text(json.dumps(records,indent=2))
print(json.dumps(records))
PY

sha256sum tests/input/race-finish-dragster.script > "$OUT/route.sha256"
# Preserve native checkpoint state and logs without shipping ROM or executable.
python3 - "$TMP/dumps" "$OUT" "$status" <<'PY'
import pathlib,json,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); status=int(sys.argv[3])
p=root/'race-results.wram.bin'
result={'exit':status,'result_checkpoint':p.exists(),'usa_course_credit':0,'historical_original_run':45293798231}
if p.exists():
 b=p.read_bytes(); result.update(menu=b[0x9f],track=b[0xce],in_race=b[0x313])
(out/'native-result.json').write_text(json.dumps(result,indent=2))
print(result)
assert status==0 and p.exists() and result['menu']==0x99
PY
