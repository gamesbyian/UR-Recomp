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
new='press right 300\ndump ws-product-motion-300\npress right 1\ndump ws-product-motion-301\npress right 149\ndump ws-product-motion-450\npress right 1\ndump ws-product-motion-451\npress right 149\ndump ws-product-motion-600\npress right 1\ndump ws-product-motion-601\npress right 149\ndump ws-product-motion-750\npress right 1\ndump ws-product-motion-751\npress right 149\ndump ws-product-after-scroll'
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
result={'schema':'ur-wide07-adjacent-obj-phase/1','source_sha':sha,'emulator_exit':status,'checkpoints':{},'usa_course_credit':0}
for tag in tags:
    files=sorted(root.joinpath('frames').glob(tag+'.*'))
    if not files: raise SystemExit('MISSING_CHECKPOINT '+tag)
    entry={'files':{p.name.removeprefix(tag+'.'):{'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}}
    info=root/'frames'/f'{tag}.info.json'
    if info.exists(): entry['info']=json.loads(info.read_text())
    for suffix in ('oam.bin','ppu.json','ppu-writes.json','vram.bin','cgram.bin'):
        p=root/'frames'/f'{tag}.{suffix}'
        if p.exists(): entry[suffix+'_present']=True
    result['checkpoints'][tag]=entry
(root/'obj-phase-inventory.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print('WIDE07_OBJ_PHASE',json.dumps(result,sort_keys=True))
if status: raise SystemExit('ORIGINAL_EXECUTION_FAILED')
if not any('oam' in k.lower() for v in result['checkpoints'].values() for k in v['files']): raise SystemExit('OAM_NOT_EMITTED: inspect source snesref dump adapter and extend it')
PY


# Capture corresponding native guest checkpoints on the same input route.
# A native host-frame number is NOT presumed equivalent to an original guest frame.
NATIVE_ROOT="/tmp/ur-wide07-native"
PROJECT="$NATIVE_ROOT/UniracersSNESRecomp"
mkdir -p "$NATIVE_ROOT" "$OUT/native/frames" "$OUT/native/dumps"
python3 tools/bootstrap_toolchain.py --offline --tool snesrecomp --jobs 2 >"$OUT/native/bootstrap.log" 2>&1
FRAMEWORK="$GITHUB_WORKSPACE/.tools/src/snesrecomp"
SNESRECOMP_ROOT="$FRAMEWORK" sh "$FRAMEWORK/tools/new_project/setup_project.sh" \
 --rom "$ROM" --dir "$NATIVE_ROOT" --name Uniracers --players 2 --yes \
 --no-ci --no-fetch-boxart --no-recomp-ui --no-netplay --no-github \
 --no-submodules --generate --no-build >"$OUT/native/setup.log" 2>&1
python3 tools/seed_native_widescreen_aot.py "$PROJECT/recomp" >"$OUT/native/seed.log" 2>&1
python3 "$FRAMEWORK/snesrecomp_cli.py" generate --rom "$ROM" \
 --project-root "$PROJECT" --cfg-dir recomp --out-dir src/gen \
 --funcs-h recomp/funcs.h --cfg-roots >"$OUT/native/generate.log" 2>&1
python3 tools/patch_widescreen_probe_host.py "$PROJECT/src/main.c" >"$OUT/native/patch.log" 2>&1
python3 tools/apply_native_widescreen_hook.py "$PROJECT/src/gen" \
 --json-out "$OUT/native/hook.json" >"$OUT/native/hook.log" 2>&1
python3 tools/bootstrap_toolchain.py --offline --tool sdl3 --clone-only >"$OUT/native/sdl3.log" 2>&1
cmake -S "$PROJECT" -B "$PROJECT/build" -G Ninja \
 -DCMAKE_BUILD_TYPE=Release -DSNESRECOMP_ROOT="$FRAMEWORK" \
 -DSNESRECOMP_SDL_BACKEND=SDL3 -DSNESRECOMP_SDL3_FETCH=ON \
 -DSDL_X11_XTEST=OFF \
 -DSNESRECOMP_SDL3_SOURCE_DIR="$GITHUB_WORKSPACE/.tools/src/sdl3/SDL3-3.4.10" \
 >"$OUT/native/cmake.log" 2>&1
cmake --build "$PROJECT/build" -j2 >"$OUT/native/build.log" 2>&1
EXE_NATIVE="$PROJECT/build/UniracersSNESRecomp"
sha256sum "$EXE_NATIVE" >>"$OUT/provenance.sha256"
set +e
SDL_AUDIODRIVER=dummy URRECOMP_WS_MARGIN=48 URRECOMP_WS_NATIVE_TRACE=1 \
 SNESRECOMP_DUMP_DIR="$OUT/native/dumps" \
 SNESRECOMP_FRAMEDUMP_PIXELS=1 \
 SNESRECOMP_FRAMEDUMP_START=1 SNESRECOMP_FRAMEDUMP_END=1200 \
 timeout --signal=TERM --kill-after=10s 480s xvfb-run -a \
 "$EXE_NATIVE" "$ROM" --script "$SCRIPT" --framedump "$OUT/native/frames" \
 >"$OUT/native/run.log" 2>&1
native_status=$?
set -e
printf '%s\\n' "$native_status" >"$OUT/native/exit.txt"
python3 - "$OUT" "$native_status" <<'PY_NATIVE'
import hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1]); status=int(sys.argv[2])
frames=sorted((root/'native/frames').glob('frame_*.bmp'))
# Retain bounded representative frames; keep full hashes and original guest inventory.
inventory={'schema':'ur-wide07-native-frame-inventory/1','native_exit':status,
           'native_frame_count':len(frames),'native_frames':[
           {'name':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
           for p in frames]}
(root/'native/inventory.json').write_text(json.dumps(inventory,indent=2)+'\\n')
for p in frames:
    frame=int(p.stem.split('_')[-1])
    if frame not in (299,300,301,302,449,450,451,452,599,600,601,602,749,750,751,752,899,900,901,902):
        p.unlink()
print('NATIVE_FRAME_INVENTORY',json.dumps({'status':status,'frames':len(frames)}))
if status: raise SystemExit('NATIVE_EXECUTION_FAILED')
if not frames: raise SystemExit('NATIVE_FRAMES_MISSING')
PY_NATIVE
