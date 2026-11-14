#!/usr/bin/env bash
set -euo pipefail
OUT="$UR_EXPERIMENT_OUTPUT_DIR"
mkdir -p "$OUT/frames"
ROM="$GITHUB_WORKSPACE/reference/roms/retail/Uniracers_USA.sfc"
BASE="$GITHUB_WORKSPACE/tests/input/widescreen-product-acceptance.script"
SCRIPT="/tmp/ur-wide07-obj-phase.script"
python3 - "$BASE" "$SCRIPT" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text()
needle='press right 900\ndump ws-product-after-scroll'
assert src.count(needle)==1, 'input route changed'
new='press right 300\ndump ws-product-motion-300\npress right 1\ndump ws-product-motion-301\npress right 1\ndump ws-product-motion-450\npress right 2\ndump ws-product-motion-451\npress right 149\ndump ws-product-motion-600\npress right 1\ndump ws-product-motion-601\npress right 149\ndump ws-product-motion-750\npress right 2\ndump ws-product-motion-751\npress right 149\ndump ws-product-after-scroll'
Path(sys.argv[2]).write_text(src.replace(needle,new))
PY
python3 tools/verify_rom.py "$ROM" >"$OUT/rom-identity.txt"
if ! pkg-config --exists sdl2; then
 sudo apt-get -o Acquire::Retries=3 update >"$OUT/apt.log" 2>&1
 sudo apt-get -o Acquire::Retries=3 install -y --no-install-recommends libsdl2-dev >>"$OUT/apt.log" 2>&1
fi
git submodule update --init --recursive snesrecomp >"$OUT/submodule.log" 2>&1
python3 tools/bootstrap_toolchain.py --offline --tool snes9x-libretro --jobs 2 >"$OUT/core-build.log" 2>&1
cmake -S snesrecomp/tools/snesref -B /tmp/ur-wide07-obj-snesref -DCMAKE_BUILD_TYPE=Release >"$OUT/cmake.log" 2>&1
cmake --build /tmp/ur-wide07-obj-snesref -j2 >>"$OUT/cmake.log" 2>&1
CORE="$GITHUB_WORKSPACE/.tools/src/snes9x-libretro/libretro/snes9x_libretro.so"
EXE=/tmp/ur-wide07-obj-snesref/snesref
sha256sum "$ROM" "$BASE" "$SCRIPT" "$CORE" "$EXE" >"$OUT/provenance.sha256"
set +e
SNESREF_HEADLESS=1 SNESREF_FAST=1 SNESREF_WRAM_FILL=0 SNESREF_SCRIPT="$SCRIPT" SNESREF_DUMP_DIR="$OUT/frames" SDL_AUDIODRIVER=dummy timeout --signal=TERM --kill-after=10s 780s "$EXE" "$CORE" "$ROM" >"$OUT/original.log" 2>&1
status=$?
set -e
printf '%s\n' "$status" >"$OUT/exit.txt"
python3 - "$OUT" "$UR_EXPERIMENT_SOURCE_SHA" "$status" <<'PY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1]); sha=sys.argv[2]; status=int(sys.argv[3])
tags=['ws-product-race','ws-product-motion-300','ws-product-motion-301','ws-product-motion-450','ws-product-motion-451','ws-product-motion-600','ws-product-motion-601','ws-product-motion-750','ws-product-motion-751','ws-product-after-scroll']
result={'schema':'ur-wide07-dump-cadence-calibration/1','source_sha':sha,'emulator_exit':status,'checkpoints':{},'usa_course_credit':0}
for tag in tags:
    files=sorted(root.joinpath('frames').glob(tag+'.*'))
    if not files:
        result['checkpoints'][tag]={'missing':True}
        continue
    entry={'files':{p.name.removeprefix(tag+'.'):{'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}}
    info=root/'frames'/f'{tag}.info.json'
    if info.exists(): entry['info']=json.loads(info.read_text())
    for suffix in ('oam.bin','ppu.json','ppu-writes.json','vram.bin','cgram.bin'):
        p=root/'frames'/f'{tag}.{suffix}'
        if p.exists(): entry[suffix+'_present']=True
    result['checkpoints'][tag]=entry
(root/'obj-phase-inventory.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print('WIDE07_OBJ_PHASE',json.dumps(result,sort_keys=True))
if status: raise SystemExit('ORIGINAL_EXECUTION_FAILED: inspect original.log and exit.txt retained in artifact')
if any(v.get('missing') for v in result['checkpoints'].values()): raise SystemExit('MISSING_CHECKPOINTS: inspect original.log and obj-phase-inventory.json')
if not any('oam' in k.lower() for v in result['checkpoints'].values() for k in v['files']): raise SystemExit('OAM_NOT_EMITTED: inspect source snesref dump adapter and extend it')
PY
