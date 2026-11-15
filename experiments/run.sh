#!/usr/bin/env bash
set -euo pipefail
OUT="${UR_EXPERIMENT_OUTPUT_DIR:?}"
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
cmake -S snesrecomp/tools/snesref -B /tmp/ur-wide07-postscroll-snesref -DCMAKE_BUILD_TYPE=Release > "$OUT/cmake.log" 2>&1
cmake --build /tmp/ur-wide07-postscroll-snesref -j2 >> "$OUT/cmake.log" 2>&1
CORE="$GITHUB_WORKSPACE/.tools/src/snes9x-libretro/libretro/snes9x_libretro.so"
EXE=/tmp/ur-wide07-postscroll-snesref/snesref
sha256sum "$ROM" "$BASE" "$CORE" "$EXE" > "$OUT/provenance.sha256"
for duration in 899 900; do
 mkdir -p "$OUT/atlas-$duration"
 python3 - "$BASE" "/tmp/ur-wide07-atlas-$duration.script" "$duration" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text()
needle='press right 900\ndump ws-product-after-scroll'
assert src.count(needle)==1, 'original route changed'
duration=int(sys.argv[3])
Path(sys.argv[2]).write_text(src.replace(needle,f'press right {duration}\ndump ws-product-atlas-{duration}'))
PY
 sha256sum "/tmp/ur-wide07-atlas-$duration.script" >> "$OUT/provenance.sha256"
 set +e
 SNESREF_HEADLESS=1 SNESREF_FAST=1 SNESREF_WRAM_FILL=0 SNESREF_SCRIPT="/tmp/ur-wide07-atlas-$duration.script" SNESREF_DUMP_DIR="$OUT/atlas-$duration" SDL_AUDIODRIVER=dummy timeout --signal=TERM --kill-after=10s 480s "$EXE" "$CORE" "$ROM" > "$OUT/emulator-$duration.log" 2>&1
 status=$?
 set -e
 printf '%s\n' "$status" > "$OUT/exit-$duration.txt"
 if (( status != 0 )); then echo "ORIGINAL_EXECUTION_FAILED $duration $status"; exit 1; fi
done
python3 - "$OUT" "$UR_EXPERIMENT_SOURCE_SHA" <<'PY'
import json,sys,hashlib
from pathlib import Path
root=Path(sys.argv[1]); sha=sys.argv[2]
data={'schema':'wide07-postscroll-local/1','source_sha':sha,'usa_course_credit':0,'pairs':[]}
for a,b in ((899,900),):
 def load(n,ext):
  return (root/f'atlas-{n}'/f'ws-product-atlas-{n}.{ext}').read_bytes()
 ia=json.loads(load(a,'info.json')); ib=json.loads(load(b,'info.json'))
 oa=load(a,'oam.bin'); ob=load(b,'oam.bin')
 fa=load(a,'fb.bgrx'); fb=load(b,'fb.bgrx')
 assert len(oa)==len(ob)==544 and len(fa)==len(fb)==229376
 result={'durations':[a,b],'frames':[ia['frame'],ib['frame']],
         'frame_delta':ib['frame']-ia['frame'],
         'oam_changed_offsets':[i for i,(x,y) in enumerate(zip(oa,ob)) if x!=y],
         'framebuffer_changed_pixels':sum(fa[i:i+4]!=fb[i:i+4] for i in range(0,len(fa),4)),
         'oam_sha256':[hashlib.sha256(x).hexdigest() for x in (oa,ob)],
         'fb_sha256':[hashlib.sha256(x).hexdigest() for x in (fa,fb)]}
 # Localize the first visible divergence, preserving scanline counts and bounds.
 changed=[i//4 for i in range(0,len(fa),4) if fa[i:i+4]!=fb[i:i+4]]
 if changed:
  xs=[p%256 for p in changed]; ys=[p//256 for p in changed]
  result['framebuffer_delta_geometry']={
   'bounds_xyxy':[min(xs),min(ys),max(xs),max(ys)],
   'first_changed_xy':[changed[0]%256,changed[0]//256],
   'changed_pixels_per_scanline':{str(y):sum(p//256==y for p in changed)
                                   for y in sorted(set(ys))}}
 else:
  result['framebuffer_delta_geometry']={'bounds_xyxy':None,'first_changed_xy':None,'changed_pixels_per_scanline':{}}
 # Preserve localized original-source pixel transition density in 16x16 cells.
 # This is a motion/phase diagnostic, not a native equivalence claim.
 tiles=[]
 for ty in range(14):
  row=[]
  for tx in range(16):
   count=sum(fa[(y*256+x)*4:(y*256+x+1)*4]!=fb[(y*256+x)*4:(y*256+x+1)*4]
             for y in range(ty*16,(ty+1)*16) for x in range(tx*16,(tx+1)*16))
   row.append(count)
  tiles.append(row)
 result['changed_pixels_16x16_tiles']=tiles
 result['tile_sum_check']=sum(map(sum,tiles))==result['framebuffer_changed_pixels']
 assert result['tile_sum_check'], 'TILE_ACCOUNTING_FAILED'
 # Classify all available source-state byte transitions, retaining offsets and counts.
 for ext in ('vram.bin','wram.bin','cgram.bin'):
  pa=root/f'atlas-{a}'/f'ws-product-atlas-{a}.{ext}'
  pb=root/f'atlas-{b}'/f'ws-product-atlas-{b}.{ext}'
  if not pa.exists() or not pb.exists():
   raise AssertionError(f'MISSING_SOURCE_STATE {ext}: {pa} {pb}')
  va,vb=pa.read_bytes(),pb.read_bytes()
  assert len(va)==len(vb), f'STATE_LENGTH_MISMATCH {ext}'
  offsets=[i for i,(x,y) in enumerate(zip(va,vb)) if x!=y]
  result[ext]={'bytes':len(va),'changed_count':len(offsets),
   'changed_offsets':offsets[:512],'offsets_truncated':len(offsets)>512,
   'sha256':[hashlib.sha256(x).hexdigest() for x in (va,vb)]}
 for ext in ('ppu.json','info.json'):
  pa=root/f'atlas-{a}'/f'ws-product-atlas-{a}.{ext}'
  pb=root/f'atlas-{b}'/f'ws-product-atlas-{b}.{ext}'
  if pa.exists() and pb.exists():
   va=json.loads(pa.read_text());vb=json.loads(pb.read_text())
   if isinstance(va,dict) and isinstance(vb,dict):
    result[ext+'_changed_fields']={k:[va.get(k),vb.get(k)] for k in sorted(set(va)|set(vb)) if va.get(k)!=vb.get(k)}
 data['pairs'].append(result)
(root/'comparison.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
print('WIDE07_POSTSCROLL_LOCAL',json.dumps(data,sort_keys=True))
assert all(p['frame_delta']==1 for p in data['pairs']), 'NOT_CONSECUTIVE_FRAMES'
PY
