#!/usr/bin/env bash
set -euo pipefail
OUT="$UR_EXPERIMENT_OUTPUT_DIR"
mkdir -p "$OUT"
ROM="$GITHUB_WORKSPACE/reference/roms/retail/Uniracers_USA.sfc"
BASE="$GITHUB_WORKSPACE/tests/input/widescreen-product-acceptance.script"
python3 tools/verify_rom.py "$ROM" > "$OUT/rom-identity.txt"
if ! pkg-config --exists sdl2; then
 sudo apt-get -o Acquire::Retries=3 update > "$OUT/apt.log" 2>&1
 sudo apt-get -o Acquire::Retries=3 install -y --no-install-recommends libsdl2-dev >> "$OUT/apt.log" 2>&1
fi
git submodule update --init --recursive snesrecomp > "$OUT/submodule.log" 2>&1
python3 tools/bootstrap_toolchain.py --offline --tool snes9x-libretro --jobs 2 > "$OUT/core-build.log" 2>&1
cmake -S snesrecomp/tools/snesref -B /tmp/ur-wide07-cross-run-snesref -DCMAKE_BUILD_TYPE=Release > "$OUT/cmake.log" 2>&1
cmake --build /tmp/ur-wide07-cross-run-snesref -j2 >> "$OUT/cmake.log" 2>&1
CORE="$GITHUB_WORKSPACE/.tools/src/snes9x-libretro/libretro/snes9x_libretro.so"
EXE=/tmp/ur-wide07-cross-run-snesref/snesref
sha256sum "$ROM" "$BASE" "$CORE" "$EXE" > "$OUT/provenance.sha256"
for duration in 299 300; do
 mkdir -p "$OUT/frames-$duration"
 python3 - "$BASE" "/tmp/ur-wide07-cross-$duration.script" "$duration" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text()
needle='press right 900\ndump ws-product-after-scroll'
assert src.count(needle)==1, 'original route changed'
duration=int(sys.argv[3])
Path(sys.argv[2]).write_text(src.replace(needle,f'press right {duration}\ndump ws-product-cross-{duration}'))
PY
 sha256sum "/tmp/ur-wide07-cross-$duration.script" >> "$OUT/provenance.sha256"
 set +e
 SNESREF_HEADLESS=1 SNESREF_FAST=1 SNESREF_WRAM_FILL=0 SNESREF_SCRIPT="/tmp/ur-wide07-cross-$duration.script" SNESREF_DUMP_DIR="$OUT/frames-$duration" SDL_AUDIODRIVER=dummy timeout --signal=TERM --kill-after=10s 780s "$EXE" "$CORE" "$ROM" > "$OUT/original-$duration.log" 2>&1
 status=$?
 set -e
 printf '%s\n' "$status" > "$OUT/exit-$duration.txt"
 if (( status != 0 )); then echo "ORIGINAL_EXECUTION_FAILED $duration $status"; exit 1; fi
done
python3 - "$OUT" "$UR_EXPERIMENT_SOURCE_SHA" <<'PY'
import json,sys,hashlib
from pathlib import Path
root=Path(sys.argv[1]); sha=sys.argv[2]
data={'schema':'wide07-cross-run-frame/1','source_sha':sha,'usa_course_credit':0,'samples':{}}
for n in (299,300):
 p=root/f'frames-{n}'/f'ws-product-cross-{n}'
 info=json.loads(Path(str(p)+'.info.json').read_text())
 oam=Path(str(p)+'.oam.bin').read_bytes()
 fb=Path(str(p)+'.fb.bgrx').read_bytes()
 data['samples'][str(n)]={'frame':info['frame'],'oam_sha256':hashlib.sha256(oam).hexdigest(),'fb_sha256':hashlib.sha256(fb).hexdigest(),'oam_size':len(oam),'fb_size':len(fb)}
assert data['samples']['300']['frame']-data['samples']['299']['frame']==1, 'NOT_CONSECUTIVE_FRAMES'
a=(root/'frames-299/ws-product-cross-299.oam.bin').read_bytes()
b=(root/'frames-300/ws-product-cross-300.oam.bin').read_bytes()
fa=(root/'frames-299/ws-product-cross-299.fb.bgrx').read_bytes()
fb=(root/'frames-300/ws-product-cross-300.fb.bgrx').read_bytes()
data['oam_changed_offsets']=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
data['framebuffer_changed_pixels']=sum(fa[i:i+4]!=fb[i:i+4] for i in range(0,len(fa),4))
(root/'comparison.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
print('WIDE07_CROSS_RUN',json.dumps(data,sort_keys=True))
PY
