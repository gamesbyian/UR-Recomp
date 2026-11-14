#!/usr/bin/env bash
set -euo pipefail
# Genuine original USA moving-course oracle; preserve failure logs and receipts.
OUT="$UR_EXPERIMENT_OUTPUT_DIR"
mkdir -p "$OUT/frames"
ROM="$GITHUB_WORKSPACE/reference/roms/retail/Uniracers_USA.sfc"
SCRIPT="$GITHUB_WORKSPACE/tests/input/widescreen-product-acceptance.script"
python3 tools/verify_rom.py "$ROM" | tee "$OUT/rom-identity.txt"
test -s "$SCRIPT"
# A missing library is an installation job, not grounds to stop development.
if ! pkg-config --exists sdl2; then
  sudo apt-get -o Acquire::Retries=3 update >"$OUT/apt-update.log" 2>&1
  sudo apt-get -o Acquire::Retries=3 install -y --no-install-recommends libsdl2-dev >>"$OUT/apt-update.log" 2>&1
fi
git submodule update --init --recursive snesrecomp >"$OUT/submodule.log" 2>&1
git -C snesrecomp rev-parse HEAD >"$OUT/snesref-source-head.txt"
python3 tools/bootstrap_toolchain.py --offline --tool snes9x-libretro --jobs 2 >"$OUT/original-core-build.log" 2>&1
ROOT="/tmp/wide07-original-snesref"
mkdir -p "$ROOT"
cmake -S snesrecomp/tools/snesref -B "$ROOT" -DCMAKE_BUILD_TYPE=Release >"$OUT/snesref-cmake.log" 2>&1
cmake --build "$ROOT" -j2 >>"$OUT/snesref-cmake.log" 2>&1
CORE="$GITHUB_WORKSPACE/.tools/src/snes9x-libretro/libretro/snes9x_libretro.so"
EXE="$ROOT/snesref"
test -f "$CORE" && test -x "$EXE"
sha256sum "$ROM" "$SCRIPT" "$CORE" "$EXE" >"$OUT/source-and-executables.sha256"
set +e
SNESREF_HEADLESS=1 SNESREF_FAST=1 SNESREF_WRAM_FILL=0 \
SNESREF_SCRIPT="$SCRIPT" SNESREF_DUMP_DIR="$OUT/frames" SDL_AUDIODRIVER=dummy \
  timeout --signal=TERM --kill-after=10s 780s "$EXE" "$CORE" "$ROM" \
  >"$OUT/original-script.log" 2>&1
status=$?
set -e
printf '%s\n' "$status" >"$OUT/original-script-exit.txt"
python3 - "$OUT" "$UR_EXPERIMENT_SOURCE_SHA" "$status" <<'PY'
import hashlib,json,struct,sys
from pathlib import Path
root=Path(sys.argv[1])
source_sha=sys.argv[2]
status=int(sys.argv[3])
labels=("ws-product-main-menu","ws-product-race","ws-product-after-scroll")
dumps={}
for tag in labels:
    p=root/"frames"/(tag+".fb.bmp")
    w=root/"frames"/(tag+".wram.bin")
    s=root/"frames"/(tag+".sram.bin")
    i=root/"frames"/(tag+".info.json")
    if not p.is_file() or not w.is_file() or not s.is_file() or not i.is_file():
        raise SystemExit("ORIGINAL_CAPTURE_MISSING "+tag+"; inspect original-script.log")
    raw=p.read_bytes()
    if len(raw)<54 or raw[:2]!=b"BM":
        raise SystemExit("ORIGINAL_CAPTURE_NOT_BMP "+tag)
    width,height=struct.unpack_from("<ii",raw,18)
    if (width,abs(height))!=(256,224) or len(w.read_bytes())!=131072 or len(s.read_bytes())!=8192:
        raise SystemExit("ORIGINAL_CAPTURE_INVALID_DIMENSIONS_OR_MEMORY "+tag)
    dumps[tag]={
        "width":width,"height":abs(height),
        "framebuffer_sha256":hashlib.sha256(raw).hexdigest(),
        "wram_sha256":hashlib.sha256(w.read_bytes()).hexdigest(),
        "sram_sha256":hashlib.sha256(s.read_bytes()).hexdigest(),
        "metadata":json.loads(i.read_text()),
    }
result={
    "schema":"ur-wide07-genuine-original-usa-ppu-capture/1",
    "source_sha":source_sha,
    "execution_exit_status":status,
    "original_snes9x_executed":status==0,
    "checkpoints":dumps,
    "original_native_semantic_registration_proven":False,
    "original_native_pixel_parity_proven":False,
    "wide_margin_source_parity_proven":False,
    "usa_course_credit":0,
    "next_discriminator":"Compare authentic Snes9x PPU, WRAM, scroll and source frame tags to native fixed/wide captures at the same semantic course events. Investigate any first difference in actual tile/HDMA origins."
}
(root/"original-usa-ppu-observation.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print("WIDE07_ACTUAL_SNES9X_CAPTURE "+json.dumps({"source_sha":source_sha,"checkpoints":list(dumps),"exit":status,"credit":0}))
if status!=0:
    raise SystemExit("original Snesref script failed; see log")
PY
