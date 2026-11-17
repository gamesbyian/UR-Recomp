#!/usr/bin/env bash
set -euo pipefail
OUT="${UR_EXPERIMENT_OUTPUT_DIR:?}"; mkdir -p "$OUT"
curl -fLsS --retry 2 --max-time 90 'https://sdmntprcentralus.oaiusercontent.com/files/00000000-def4-81f5-a747-364b0fd7aa16/raw?se=2026-11-17T03%3A02%3A40Z&sp=r&sv=2026-06-06&sr=b&scid=8f935cb2-f1f6-59b3-8152-c959c44a1911&skoid=de71a0d5-fb02-4fce-be69-9296aced242b&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2026-11-17T00%3A12%3A25Z&ske=2026-11-18T00%3A12%3A25Z&sks=b&skv=2026-06-06&sig=y7kfrnFxDo0rfKRpM3az4lJ8PUnB3q96OJVU2NObZMs%3D' -o /tmp/o.zip
curl -fLsS --retry 2 --max-time 90 'https://sdmntprcentralus.oaiusercontent.com/files/00000000-66c4-81f5-b618-17e025cf1c78/raw?se=2026-11-17T03%3A02%3A40Z&sp=r&sv=2026-06-06&sr=b&scid=253d4d75-e24c-553d-9c5c-b0ff7a21e2ba&skoid=de71a0d5-fb02-4fce-be69-9296aced242b&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2026-11-17T00%3A00%3A06Z&ske=2026-11-18T00%3A00%3A06Z&sks=b&skv=2026-06-06&sig=ZpNkrWXYncANm3TyVMgjlVo1iuVjhoF90CvKqOXSkEM%3D' -o /tmp/n.zip
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
