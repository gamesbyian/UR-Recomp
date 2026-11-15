#!/usr/bin/env bash
set -euo pipefail
# WIDE-07 command-boundary minimal repro: genuinely build and run the current product's USA
# moving-course 1P path on the hosted native emulator. Original/world parity
# must be checked separately; this experiment only establishes executable
# scene, source geometry and movement without fabricating source frames.
ROM="$GITHUB_WORKSPACE/reference/roms/retail/Uniracers_USA.sfc"
OUT="$UR_EXPERIMENT_OUTPUT_DIR"
mkdir -p "$OUT"
TMP=$(mktemp -d)
FRAMEWORK="$GITHUB_WORKSPACE/.tools/src/snesrecomp"
PROJ="$TMP/native/UniracersSNESRecomp"
LOG="$OUT/moving-course-run.log"
echo "SOURCE_SHA=$UR_EXPERIMENT_SOURCE_SHA" >"$OUT/build-stage.log"
trap 'status=$?; echo "EXIT_STATUS=$status" >>"$OUT/build-stage.log"; exit "$status"' EXIT

python3 tools/verify_rom.py "$ROM"
sudo apt-get -o Acquire::Retries=2 -o Acquire::http::Timeout=30 update \
  >>"$OUT/build-stage.log" 2>&1
sudo apt-get -o Acquire::Retries=2 -o Acquire::http::Timeout=30 install -y --no-install-recommends \
  pkg-config xvfb xdotool libgl-dev libx11-dev libxext-dev libxrandr-dev \
  libxcursor-dev libxi-dev libxfixes-dev libxkbcommon-dev libwayland-dev \
  libasound2-dev libpulse-dev libxss-dev libxtst-dev >>"$OUT/build-stage.log" 2>&1

python3 tools/bootstrap_toolchain.py --offline --tool snesrecomp --clone-only \
  >>"$OUT/build-stage.log" 2>&1
python3 tools/bootstrap_toolchain.py --offline --tool sdl3 --clone-only \
  >>"$OUT/build-stage.log" 2>&1
mkdir -p "$TMP/native"
SNESRECOMP_ROOT="$FRAMEWORK" \
  sh "$FRAMEWORK/tools/new_project/setup_project.sh" \
    --rom "$ROM" --dir "$TMP/native" --name Uniracers --players 2 \
    --yes --no-ci --no-fetch-boxart --no-recomp-ui --no-netplay \
    --no-github --no-submodules --no-generate --no-build >>"$OUT/build-stage.log" 2>&1
python3 tools/prepare_native_widescreen_product.py \
  --framework "$FRAMEWORK" --project "$PROJ" --rom "$ROM" \
  --json-out "$OUT/source-preparation.json" >>"$OUT/build-stage.log" 2>&1
python3 tools/patch_modern_product_host.py "$PROJ/src/main.c" \
  --game-rtl "$PROJ/src/game_rtl.c" --cmake "$PROJ/CMakeLists.txt" \
  >>"$OUT/build-stage.log" 2>&1

cmake -S "$PROJ" -B "$PROJ/build" -DCMAKE_BUILD_TYPE=Release \
  -DSNESRECOMP_ROOT="$FRAMEWORK" -DSNESRECOMP_SDL_BACKEND=SDL3 \
  -DSNESRECOMP_SDL3_FETCH=ON \
  -DSNESRECOMP_SDL3_SOURCE_DIR="$GITHUB_WORKSPACE/.tools/src/sdl3/SDL3-3.4.10" \
  >>"$OUT/build-stage.log" 2>&1
cmake --build "$PROJ/build" -j2 >>"$OUT/build-stage.log" 2>&1
EXE="$PROJ/build/UniracersSNESRecomp"
test -x "$EXE"
sha256sum "$EXE" >"$OUT/actual-native-executable.sha256"


# Capture both native phases within ONE process. Independent process startup
# follows asynchronous scene checkpoints and previously yielded [1945,1942]
# despite input durations [899,900] (Actions run 43711997665). The paired
# dumps must share a deterministic checkpoint; the scripted dump itself advances\n# no guest frame; this attempt measures the guest-frame cadence of a two-frame right-input command.
BASE="$GITHUB_WORKSPACE/tests/input/widescreen-product-acceptance.script"
SCRIPT="$TMP/native-pair.script"
python3 - "$BASE" "$SCRIPT" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text()
needle='press right 900\ndump ws-product-after-scroll'
assert src.count(needle)==1, 'PRODUCT_ROUTE_CHANGED'
replacement='press right 899\ndump ws-product-native-899\npress right 2\ndump ws-product-native-900\ndump ws-product-native-901'
Path(sys.argv[2]).write_text(src.replace(needle,replacement))
PY
DUMPS="$TMP/native-pair-dumps"
mkdir -p "$DUMPS"
STATE="$TMP/host-state-pair.txt"
cat >"$STATE" <<EOF
UR-HOST-STATE/6
profile=
pause_on_focus_loss=1
vibration_enabled=1
display_mode=windowed
vsync=on
presentation_fps=game
output_resolution=native
widescreen=original
EOF
UR_PRODUCT_DIAGNOSTICS=1 UR_HOST_STATE_PATH="$STATE" \
  URRECOMP_WS_NATIVE_TRACE=1 SNESRECOMP_DUMP_DIR="$DUMPS" \
  SDL_AUDIODRIVER=dummy timeout 180s xvfb-run -a "$EXE" "$ROM" \
  --script "$SCRIPT" >"$OUT/native-pair.log" 2>&1
grep -q "UR_HOST_STATE LOADED" "$OUT/native-pair.log"
for duration in 899 900 901; do
  DEST="$OUT/native-$duration"
  mkdir -p "$DEST"
  grep -q "dump ws-product-native-$duration ok" "$OUT/native-pair.log"
  for ext in fb.bmp wram.bin info.json; do
    test -s "$DUMPS/ws-product-native-$duration.$ext" || {
      echo "MISSING_NATIVE_DUMP duration=$duration ext=$ext"; exit 1;
    }
    cp "$DUMPS/ws-product-native-$duration.$ext" "$DEST/state.$ext"
  done
  sha256sum "$SCRIPT" "$DEST/state.fb.bmp" "$DEST/state.wram.bin" \
    >> "$OUT/native-provenance.sha256"
done

python3 - "$OUT" <<'PY'
import hashlib,json,os,re,struct,sys
from pathlib import Path
root=Path(sys.argv[1])
def bmp(n):
 d=(root/f'native-{n}'/'state.fb.bmp').read_bytes()
 assert d[:2]==b'BM'
 w,h=struct.unpack_from('<ii',d,18)
 bpp=struct.unpack_from('<H',d,28)[0]
 start=struct.unpack_from('<I',d,10)[0]
 assert abs(h)==224 and bpp==24 and w in (256,342,344,352), (w,h,bpp)
 stride=(w*3+3)//4*4
 payload=d[start:start+stride*224]
 assert len(payload)==stride*224
 return payload,stride,w,hashlib.sha256(d).hexdigest()
a,sa,wa,ha=bmp(899);b,sb,wb,hb=bmp(900)
c,sc,wc,hc=bmp(901)
assert wa==wc, f'NATIVE_FRAME_WIDTH_CHANGED {wa} {wc}'
assert wa==wb, f'NATIVE_FRAME_WIDTH_CHANGED {wa} {wb}'
def pixels(buf,stride,width):
 return [buf[y*stride+x*3:y*stride+x*3+3] for y in range(224) for x in range(width)]
pa,pb=pixels(a,sa,wa),pixels(b,sb,wb)
changed=[i for i,(x,y) in enumerate(zip(pa,pb)) if x!=y]
changed_set=set(changed)
tiles=[[sum((y*wa+x) in changed_set for y in range(ty*16,(ty+1)*16)
             for x in range(tx*16,min((tx+1)*16,wa)))
        for tx in range((wa+15)//16)] for ty in range(14)]
assert sum(map(sum,tiles))==len(changed)
meta=[json.loads((root/f'native-{n}'/'state.info.json').read_text()) for n in (899,900,901)]
wram=[(root/f'native-{n}'/'state.wram.bin').read_bytes() for n in (899,900,901)]
assert all(len(x)==131072 for x in wram)
frame=[m.get('frame') for m in meta]
assert all(isinstance(x,int) for x in frame) and frame[0]<=frame[1]<=frame[2], f'REVERSED_NATIVE_INPUT_CADENCE {frame}'
assert frame[2]>frame[0], f'NONADVANCING_NATIVE_INPUT {frame}'
assert frame[2]==frame[1], f'DUMP_ADVANCED_GUEST_FRAME {frame}'
result={'schema':'wide07-native-postscroll-pair/1','source_sha':os.environ['UR_EXPERIMENT_SOURCE_SHA'],
 'host':'github-hosted-ubuntu','input_right_frames':[899,900,901],
 'native_framebuffer_width':wa,'native_guest_frames':frame,'native_frame_delta':frame[1]-frame[0], 'native_per_command_guest_deltas':[frame[1]-frame[0],frame[2]-frame[1]], 'native_total_guest_delta':frame[2]-frame[0],
 'native_capture_interval':'one press right 2 command then immediate no-input dump',
 'framebuffer_changed_pixels':len(changed),'changed_pixels_16x16_tiles':tiles,
 'first_changed_xy':([changed[0]%wa,changed[0]//wa] if changed else None),
 'wram_changed_bytes':sum(x!=y for x,y in zip(wram[0],wram[1])),
 'wram_changed_bytes_second_interval':sum(x!=y for x,y in zip(wram[1],wram[2])),
 'framebuffer_sha256':[ha,hb,hc],
 'wram_sha256':[hashlib.sha256(x).hexdigest() for x in wram],
 'two_frame_command_boundary_probe':True,'original_snes9x_parity_proven':False,'usa_course_credit':0}
(root/'native-postscroll-comparison.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print('WIDE07_NATIVE_POSTSCROLL',json.dumps({k:v for k,v in result.items() if k!='changed_pixels_16x16_tiles'},sort_keys=True))
PY
