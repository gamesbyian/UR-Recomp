#!/usr/bin/env bash
set -euo pipefail
# WIDE-07 attempt 2: genuinely build and run the current product's USA
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

STATE="$TMP/host-state-v6.txt"
cat >"$STATE" <<'EOF'
UR-HOST-STATE/6
profile=
pause_on_focus_loss=1
vibration_enabled=1
display_mode=windowed
vsync=on
presentation_fps=game
output_resolution=native
widescreen=16x9
EOF
DUMPS="$TMP/dumps"
mkdir -p "$DUMPS"
UR_PRODUCT_DIAGNOSTICS=1 UR_HOST_STATE_PATH="$STATE" \
  URRECOMP_WS_NATIVE_TRACE=1 SNESRECOMP_DUMP_DIR="$DUMPS" \
  SDL_AUDIODRIVER=dummy timeout 160s xvfb-run -a "$EXE" "$ROM" \
  --script "$GITHUB_WORKSPACE/tests/input/widescreen-product-acceptance.script" \
  >"$LOG" 2>&1
grep -q "URWS_PREP_EXT margin=48" "$LOG"
grep -q "URWS_SHADOW_EXT provider=course-runtime margin=48" "$LOG"
for t in ws-product-main-menu ws-product-race ws-product-after-scroll; do
  cp "$DUMPS/$t.fb.bmp" "$OUT/$t.fb.bmp"
done
python3 - "$OUT" <<'PY'
import hashlib, json, os, struct, sys
from pathlib import Path
root=Path(sys.argv[1])
def bitmap(name):
    data=(root/(name+".fb.bmp")).read_bytes()
    assert data[:2]==b"BM", "not a real source framebuffer BMP"
    w,h=struct.unpack_from("<ii",data,18)
    depth=struct.unpack_from("<H",data,28)[0]
    assert w>0 and h!=0 and depth in (24,32)
    start=struct.unpack_from("<I",data,10)[0]
    stride=(w*depth+31)//32*4
    pixels=data[start:start+stride*abs(h)]
    assert len(pixels)==stride*abs(h)
    return dict(width=w,height=abs(h),depth=depth,pixels=pixels,
                sha256=hashlib.sha256(data).hexdigest())
menu=bitmap("ws-product-main-menu")
race=bitmap("ws-product-race")
moving=bitmap("ws-product-after-scroll")
assert (menu["width"],menu["height"])==(256,224), "frontend unexpectedly widened"
assert (race["width"],race["height"])==(342,224), "race not authentic 16:9 source width"
assert (moving["width"],moving["height"])==(342,224), "moving course not 342x224"
assert len(race["pixels"])==len(moving["pixels"])
difference=sum(x!=y for x,y in zip(race["pixels"],moving["pixels"]))
assert difference>0, "moving-course framebuffer has no changed pixel bytes"
result={
    "schema":"ur-wide07-hosted-native-moving-course/1",
    "source_sha":os.environ["UR_EXPERIMENT_SOURCE_SHA"],
    "display_frontend":[menu["width"],menu["height"]],
    "display_race":[race["width"],race["height"]],
    "display_after_scroll":[moving["width"],moving["height"]],
    "rgb_payload_byte_differences":difference,
    "frames_sha256":{k:v["sha256"] for k,v in
        (("frontend",menu),("race",race),("after_scroll",moving))},
    "native_moving_course_executed":True,
    "source_original_vs_native_pixel_parity_proven":False,
    "source_scroll_and_margin_parity_proven":False,
    "usa_course_credit":0,
    "next_discriminator":"Match source-original USA per-frame course tiles/HDMA scroll to native expanded margin RGB in this same moving route; diagnose first observable mismatch.",
}
(root/"moving-course-observation.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print("WIDE07_REAL_MOVING_COURSE",json.dumps(result,sort_keys=True))
PY
