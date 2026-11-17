#!/usr/bin/env bash
set -euo pipefail
OUT="${UR_EXPERIMENT_OUTPUT_DIR:?}"; mkdir -p "$OUT"
curl -fLsS --retry 2 --max-time 90 'https://sdmntpraustraliaeast.oaiusercontent.com/files/00000000-f47c-81fa-ac55-30ab16c26bd1/raw?se=2026-11-17T02%3A00%3A54Z&sp=r&sv=2026-06-06&sr=b&scid=63ca9e7a-2105-5772-9245-f26651c43898&skoid=f8b66c09-1aa0-4801-9884-173c5cef2b8c&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2026-11-17T00%3A55%3A10Z&ske=2026-11-18T00%3A55%3A10Z&sks=b&skv=2026-06-06&sig=V/AMZ61aBs01WF0CEBbMiE3ktGCO9hhdUbQaBL5xv44%3D' -o /tmp/o.zip
curl -fLsS --retry 2 --max-time 90 'https://sdmntpraustraliaeast.oaiusercontent.com/files/00000000-54cc-81fa-8afe-5f0561bae23d/raw?se=2026-11-17T02%3A00%3A53Z&sp=r&sv=2026-06-06&sr=b&scid=3631ab53-f210-5c88-b51c-1f944c55a527&skoid=f8b66c09-1aa0-4801-9884-173c5cef2b8c&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2026-11-17T00%3A57%3A09Z&ske=2026-11-18T00%3A57%3A09Z&sks=b&skv=2026-06-06&sig=uSgc5r0IQvGdzdcQgaL7XWn0FP8DBZ%2B1jKSlDPoJqYI%3D' -o /tmp/n.zip
sha256sum /tmp/o.zip /tmp/n.zip > "$OUT/input-zip-hashes.txt"
python3 - "$OUT" <<'PY'
import json,struct,zipfile,os,sys
from pathlib import Path
out=Path(sys.argv[1]); oz=zipfile.ZipFile('/tmp/o.zip'); nz=zipfile.ZipFile('/tmp/n.zip')
def get(z,s):
 m=[p for p in z.namelist() if p.endswith(s)]
 if len(m)!=1: raise RuntimeError(('AMBIGUOUS',s,m))
 return z.read(m[0])
def original(i):
 b=get(oz,f'ws-product-atlas-{i}.fb.bgrx')
 assert len(b)==256*224*4
 return [b[j+1] for j in range(0,len(b),4)]
def native(i):
 b=get(nz,f'native-{i}/state.fb.bmp')
 w,h=struct.unpack_from('<ii',b,18); off=struct.unpack_from('<I',b,10)[0]
 assert b[:2]==b'BM' and (w,abs(h))==(256,224) and struct.unpack_from('<H',b,28)[0]==24
 stride=(w*3+3)&~3
 return [b[off+(y if h<0 else 223-y)*stride+3*x+1] for y in range(224) for x in range(256)]
rep={(v<<2)|(v>>4) for v in range(64)}
scale={(v*255+31)//63 for v in range(64)}
def classify(vals):
 return {'replication_only':sum(v in rep and v not in scale for v in vals),'scaled_only':sum(v in scale and v not in rep for v in vals),'both':sum(v in rep and v in scale for v in vals),'neither':sum(v not in rep and v not in scale for v in vals)}
pairs=[]
for oi,ni in ((899,899),(902,900)):
 a=original(oi); b=native(ni)
 witnesses=[{'xy':[j%256,j//256],'original_g':x,'native_g':y,'original_rep':x in rep,'original_scaled':x in scale,'native_rep':y in rep,'native_scaled':y in scale} for j,(x,y) in enumerate(zip(a,b)) if x!=y][:32]
 pairs.append({'original_index':oi,'native_index':ni,'original':classify(a),'native':classify(b),'mismatched_green':sum(x!=y for x,y in zip(a,b)),'witnesses':witnesses,'original_info':json.loads(get(oz,f'ws-product-atlas-{oi}.info.json')),'native_info':json.loads(get(nz,f'native-{ni}/state.info.json'))})
r={'schema':'wide07-real-green-expansion/1','source_sha':os.environ['UR_EXPERIMENT_SOURCE_SHA'],'original_artifact':14184488104,'original_producer_sha':'05701c1d19389e90c86b8294a78e4d2ede95183b','native_artifact':14181849776,'native_producer_sha':'150a0199853b514928803b552e6fd73b642e0ede','phase_proven':False,'accepted_courses':0,'pairs':pairs}
(out/'green-expansion.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print('REAL_GREEN_EXPANSION',json.dumps(r,sort_keys=True))
PY
