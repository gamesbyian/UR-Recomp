#!/usr/bin/env bash
set -euo pipefail
OUT="$UR_EXPERIMENT_OUTPUT_DIR"
mkdir -p "$OUT/frames"
ROM="$GITHUB_WORKSPACE/reference/roms/retail/Uniracers_USA.sfc"
BASE="$GITHUB_WORKSPACE/tests/input/widescreen-product-acceptance.script"
SCRIPT="/tmp/ur-wide07-extra-motion.script"
python3 - "$BASE" "$SCRIPT" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text()
needle='press right 900\ndump ws-product-after-scroll'
assert src.count(needle)==1, 'original input script changed; do not silently alter route'
new='press right 300\ndump ws-product-motion-300\npress right 300\ndump ws-product-motion-600\npress right 300\ndump ws-product-after-scroll'
Path(sys.argv[2]).write_text(src.replace(needle,new))
PY
python3 tools/verify_rom.py "$ROM" >"$OUT/rom-identity.txt"
if ! pkg-config --exists sdl2; then
 sudo apt-get -o Acquire::Retries=3 update >"$OUT/apt.log" 2>&1
 sudo apt-get -o Acquire::Retries=3 install -y --no-install-recommends libsdl2-dev >>"$OUT/apt.log" 2>&1
fi
git submodule update --init --recursive snesrecomp >"$OUT/submodule.log" 2>&1
python3 tools/bootstrap_toolchain.py --offline --tool snes9x-libretro --jobs 2 >"$OUT/core-build.log" 2>&1
cmake -S snesrecomp/tools/snesref -B /tmp/ur-wide07-snesref -DCMAKE_BUILD_TYPE=Release >"$OUT/cmake.log" 2>&1
cmake --build /tmp/ur-wide07-snesref -j2 >>"$OUT/cmake.log" 2>&1
CORE="$GITHUB_WORKSPACE/.tools/src/snes9x-libretro/libretro/snes9x_libretro.so"
EXE=/tmp/ur-wide07-snesref/snesref
sha256sum "$ROM" "$BASE" "$SCRIPT" "$CORE" "$EXE" >"$OUT/provenance.sha256"
set +e
SNESREF_HEADLESS=1 SNESREF_FAST=1 SNESREF_WRAM_FILL=0 SNESREF_SCRIPT="$SCRIPT" SNESREF_DUMP_DIR="$OUT/frames" SDL_AUDIODRIVER=dummy timeout --signal=TERM --kill-after=10s 780s "$EXE" "$CORE" "$ROM" >"$OUT/original.log" 2>&1
status=$?
set -e
printf '%s\n' "$status" >"$OUT/exit.txt"
python3 - "$OUT" "$UR_EXPERIMENT_SOURCE_SHA" "$status" <<'PY'
import hashlib,json,struct,sys
from pathlib import Path
root=Path(sys.argv[1]); sha=sys.argv[2]; status=int(sys.argv[3])
result={'schema':'ur-wide07-original-intermediate-motion/1','source_sha':sha,'emulator_exit':status,'checkpoints':{},'native_comparison':False,'usa_course_credit':0}
for tag in ('ws-product-race','ws-product-motion-300','ws-product-motion-600','ws-product-after-scroll'):
 paths={ext:root/'frames'/f'{tag}.{ext}' for ext in ('fb.bmp','wram.bin','sram.bin','info.json')}
 if not all(p.is_file() for p in paths.values()): raise SystemExit('MISSING_ORIGINAL_FRAME '+tag)
 bmp=paths['fb.bmp'].read_bytes()
 if bmp[:2]!=b'BM' or struct.unpack_from('<ii',bmp,18)!=(256,224): raise SystemExit('INVALID_ORIGINAL_FRAME '+tag)
 if len(paths['wram.bin'].read_bytes())!=131072: raise SystemExit('INVALID_WRAM '+tag)
 result['checkpoints'][tag]={'framebuffer_sha256':hashlib.sha256(bmp).hexdigest(),'wram_sha256':hashlib.sha256(paths['wram.bin'].read_bytes()).hexdigest(),'info':json.loads(paths['info.json'].read_text())}
(root/'intermediate-motion.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print('WIDE07_INTERMEDIATE_ORIGINAL',json.dumps(result,sort_keys=True))
if status: raise SystemExit('ORIGINAL_EXECUTION_FAILED see original.log')
PY
