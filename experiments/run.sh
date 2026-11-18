#!/usr/bin/env bash
set -euo pipefail
# Genuine original USA moving-course oracle; preserve failure logs and receipts.
OUT="$UR_EXPERIMENT_OUTPUT_DIR"
mkdir -p "$OUT/frames"
ROM="$GITHUB_WORKSPACE/reference/roms/retail/Uniracers_USA.sfc"
SCRIPT="$GITHUB_WORKSPACE/experiments/wide07-adjacent-phase.script"
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
labels=("ws-product-main-menu","ws-product-race-minus-one","ws-product-race","ws-product-race-plus-one","ws-product-after-scroll")
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
    "schema":"ur-wide07-original-adjacent-phase-capture/1",
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

# Compact, source-bound adjacent-frame measurement, emitted to job logs and JSON.
python3 - "$OUT" <<'PY'
import json, struct, sys
from pathlib import Path
root=Path(sys.argv[1])
tags=["ws-product-race-minus-one","ws-product-race","ws-product-race-plus-one"]
def read_bmp(tag):
    data=(root/"frames"/(tag+".fb.bmp")).read_bytes()
    offset=struct.unpack_from("<I",data,10)[0]
    w,h=struct.unpack_from("<ii",data,18)
    bpp=struct.unpack_from("<H",data,28)[0]
    if (w,abs(h))!=(256,224) or bpp not in (24,32):
        raise ValueError(f"unexpected BMP {tag}: {w}x{h} {bpp}bpp")
    stride=((w*bpp+31)//32)*4
    rows=[]
    for y in range(abs(h)):
        raw_y=abs(h)-1-y if h>0 else y
        line=data[offset+raw_y*stride:offset+(raw_y+1)*stride]
        rows.append([tuple(line[x*bpp//8:x*bpp//8+3]) for x in range(w)])
    return rows,bpp
frames={t:read_bmp(t) for t in tags}
out={"schema":"ur-wide07-original-adjacent-raster-delta/1","source_sha":__import__("os").environ["UR_EXPERIMENT_SOURCE_SHA"],"pairs":[]}
for a,b in zip(tags,tags[1:]):
    A,bppa=frames[a];B,bppb=frames[b]
    changed=[(x,y) for y in range(224) for x in range(256) if A[y][x]!=B[y][x]]
    xs=[x for x,y in changed];ys=[y for x,y in changed]
    row_counts={str(y):sum(1 for x,yy in changed if yy==y) for y in sorted(set(ys))}
    item={"from":a,"to":b,"changed_pixels":len(changed),"bbox":[min(xs),min(ys),max(xs),max(ys)] if changed else None,"row_counts":row_counts,"bmp_bits_per_pixel":[bppa,bppb]}
    out["pairs"].append(item)
    print("WIDE07_ADJACENT_RASTER_DELTA "+json.dumps(item,sort_keys=True))
(root/"original-adjacent-raster-delta.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
PY
