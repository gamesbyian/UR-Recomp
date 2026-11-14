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

# Replay one identical real USA input script in stock Original and 16:9
# modes on the SAME native executable. Each mode starts with identical fresh
# launcher saves. Observe true framebuffer bytes at f=1045 and f=1946.
SAVES="$PROJ/build/saves"
if [ -d "$SAVES" ]; then
  cp -a "$SAVES" "$TMP/saves-initial"
fi
for view in original 16x9; do
  if [ -d "$TMP/saves-initial" ]; then
    rm -rf "$SAVES"
    cp -a "$TMP/saves-initial" "$SAVES"
  else
    rm -rf "$SAVES"
  fi
  DEST="$OUT/$view"
  mkdir -p "$DEST"
  STATE="$TMP/host-state-$view.txt"
  cat >"$STATE" <<EOF
UR-HOST-STATE/6
profile=
pause_on_focus_loss=1
vibration_enabled=1
display_mode=windowed
vsync=on
presentation_fps=game
output_resolution=native
widescreen=$view
EOF
  DUMPS="$TMP/dumps-$view"
  mkdir -p "$DUMPS"
  UR_PRODUCT_DIAGNOSTICS=1 UR_HOST_STATE_PATH="$STATE" \
    URRECOMP_WS_NATIVE_TRACE=1 SNESRECOMP_DUMP_DIR="$DUMPS" \
    SDL_AUDIODRIVER=dummy timeout 180s xvfb-run -a "$EXE" "$ROM" \
    --script "$GITHUB_WORKSPACE/tests/input/widescreen-product-acceptance.script" \
    >"$DEST/moving-course-run.log" 2>&1
  grep -q "UR_HOST_STATE LOADED" "$DEST/moving-course-run.log"
  if [ "$view" = "16x9" ]; then
    grep -q "URWS_PREP_EXT margin=48" "$DEST/moving-course-run.log"
    grep -q "URWS_SHADOW_EXT provider=course-runtime margin=48" "$DEST/moving-course-run.log"
  fi
  for t in ws-product-main-menu ws-product-race ws-product-after-scroll; do
    cp "$DUMPS/$t.fb.bmp" "$DEST/$t.fb.bmp"
  done
done
python3 - "$OUT" <<'PY'
import hashlib,json,os,re,struct,sys
from pathlib import Path
root=Path(sys.argv[1])
def bmp(view,tag):
  p=root/view/(tag+".fb.bmp")
  d=p.read_bytes()
  if d[:2]!=b"BM": raise AssertionError("not a real framebuffer: "+str(p))
  w,h=struct.unpack_from("<ii",d,18); bpp=struct.unpack_from("<H",d,28)[0]
  start=struct.unpack_from("<I",d,10)[0]
  assert w>0 and h!=0 and bpp==24, "unexpected framebuffer packing"
  stride=(w*3+3)//4*4; payload=d[start:start+stride*abs(h)]
  assert len(payload)==stride*abs(h)
  return {"width":w,"height":abs(h),"stride":stride,"payload":payload,
          "sha256":hashlib.sha256(d).hexdigest()}
def frame_tags(view):
  raw=(root/view/"moving-course-run.log").read_text(errors="replace")
  tags={}
  for match in re.finditer(r"script f=(\d+) dump (ws-product-(?:race|after-scroll)) ok",raw):
    tags[match.group(2)]=int(match.group(1))
  return tags
a=frame_tags("original"); b=frame_tags("16x9")
assert a==b, "Original and wide captures did not land on same guest frames"
assert a.get("ws-product-race")==1045 and a.get("ws-product-after-scroll")==1946
results={}
for tag in ("ws-product-race","ws-product-after-scroll"):
  fixed=bmp("original",tag); wide=bmp("16x9",tag)
  assert (fixed["width"],fixed["height"])==(256,224)
  assert (wide["width"],wide["height"])==(342,224)
  count=0; first=[]
  for y in range(224):
    fr=fixed["payload"][y*fixed["stride"]:y*fixed["stride"]+256*3]
    wr=wide["payload"][y*wide["stride"]+43*3:
                       y*wide["stride"]+(43+256)*3]
    for x in range(256):
      fi=fr[3*x:3*x+3]; wi=wr[3*x:3*x+3]
      if fi!=wi:
        count+=1
        if len(first)<12:
          first.append({"x":x,"y_file_row":y,"fixed_rgb_bgr":list(fi),
                        "wide_rgb_bgr":list(wi)})
  results[tag]={"guest_frame":a[tag], "pixels_compared":256*224,
                "centre_differing_pixels":count,
                "first_differences":first,
                "original_sha256":fixed["sha256"],"wide_sha256":wide["sha256"]}
front=bmp("original","ws-product-main-menu")
assert (front["width"],front["height"])==(256,224)
out={
  "schema":"ur-wide07-hosted-fixed-wide-matched-frames/1",
  "source_sha":os.environ["UR_EXPERIMENT_SOURCE_SHA"],
  "host":"native-linux-ubuntu-22.04",
  "matched_guest_frames":a,
  "centred_source_crop_x":43,
  "frame_pairs":results,
  "original_snes_emulator_oracle_proven":False,
  "widened_margin_original_tile_pixel_parity_proven":False,
  "usa_course_credit":0,
  "next_discriminator":"Compare margin-source tiles against separate original USA Snes9x PPU/VRAM/HDMA oracle at these frame identities and moving edges; local centre parity is only a necessary subtest.",
}
(root/"matched-centre-observation.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print("WIDE07_REAL_MATCHED_CENTRE",json.dumps(out,sort_keys=True))
PY
