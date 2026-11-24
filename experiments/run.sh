#!/usr/bin/env bash
set -euo pipefail
OUT="$UR_EXPERIMENT_OUTPUT_DIR"; mkdir -p "$OUT/dumps"
ROM="$GITHUB_WORKSPACE/reference/roms/retail/Uniracers_USA.sfc"
ROUTE="$GITHUB_WORKSPACE/tests/input/race-finish-dragster.script"
python3 tools/verify_rom.py "$ROM" > "$OUT/rom-identity.txt"
sha256sum "$ROUTE" > "$OUT/route.sha256"
if ! pkg-config --exists sdl2; then
 sudo apt-get -o Acquire::Retries=3 update > "$OUT/apt.log" 2>&1
 sudo apt-get -o Acquire::Retries=3 install -y --no-install-recommends libsdl2-dev >> "$OUT/apt.log" 2>&1
fi
git submodule update --init --recursive snesrecomp > "$OUT/submodule.log" 2>&1
python3 tools/bootstrap_toolchain.py --offline --tool snes9x-libretro --jobs 2 > "$OUT/core-build.log" 2>&1
cmake -S snesrecomp/tools/snesref -B /tmp/ur-dragster-snesref -DCMAKE_BUILD_TYPE=Release > "$OUT/cmake.log" 2>&1
cmake --build /tmp/ur-dragster-snesref -j2 >> "$OUT/cmake.log" 2>&1
CORE="$GITHUB_WORKSPACE/.tools/src/snes9x-libretro/libretro/snes9x_libretro.so"
EXE=/tmp/ur-dragster-snesref/snesref
sha256sum "$CORE" "$EXE" >> "$OUT/route.sha256"
set +e
SNESREF_HEADLESS=1 SNESREF_FAST=1 SNESREF_WRAM_FILL=0 SNESREF_SCRIPT="$ROUTE" SNESREF_DUMP_DIR="$OUT/dumps" SDL_AUDIODRIVER=dummy timeout --signal=TERM --kill-after=10s 780s "$EXE" "$CORE" "$ROM" > "$OUT/original.log" 2>&1
status=$?
set -e
python3 - "$OUT" "$UR_EXPERIMENT_SOURCE_SHA" "$status" <<'PY'
from pathlib import Path
import sys,json,hashlib
root=Path(sys.argv[1]); sha=sys.argv[2]; status=int(sys.argv[3])
files=sorted(p for p in (root/'dumps').rglob('*') if p.is_file())
manifest=[{'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
tags=sorted({p.name.split('.')[0] for p in files})
result={'schema':'ur-dragster-original-course-discriminator/1','source_sha':sha,'route':'tests/input/race-finish-dragster.script','route_provenance':'Dessyreqt-derived candidate, not an independently authenticated complete route','emulator_exit':status,'checkpoints':tags,'files':manifest,'original_result_observed':'race-results' in tags,'usa_course_credit':0}
(root/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print('DRAGSTER_ORIGINAL_RESULT',json.dumps({'exit':status,'checkpoints':tags,'result':result['original_result_observed']}))
if status: raise SystemExit('ORIGINAL_ROUTE_EXECUTION_FAILED')
if not result['original_result_observed']: raise SystemExit('ORIGINAL_RESULT_NOT_OBSERVED')
PY
