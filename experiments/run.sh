#!/usr/bin/env bash
set -euo pipefail
OUT="${UR_EXPERIMENT_OUTPUT_DIR:?}"; mkdir -p "$OUT"
curl -fLsS --retry 2 --max-time 90 'https://sdmntprsoutheastus3.oaiusercontent.com/files/00000000-9f2c-820c-a803-e3432d6a57e7/raw?se=2026-11-17T06%3A04%3A37Z&sp=r&sv=2026-06-06&sr=b&scid=462ddfff-1033-5c48-ac46-a9cbb6106f50&skoid=f28c0102-4d9d-4950-baf0-4a8e5f6cf9d4&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2026-11-17T03%3A49%3A08Z&ske=2026-11-18T03%3A49%3A08Z&sks=b&skv=2026-06-06&sig=%2BY0/JX/ULkwG46osFojsPDKZo54OwySjY70MbI6NCV0%3D' -o /tmp/o.zip
curl -fLsS --retry 2 --max-time 90 'https://sdmntprsoutheastus3.oaiusercontent.com/files/00000000-0274-820c-af26-1c3709b764aa/raw?se=2026-11-17T06%3A04%3A37Z&sp=r&sv=2026-06-06&sr=b&scid=b6acc487-f578-5c17-ae89-a7b9cac49e2d&skoid=f28c0102-4d9d-4950-baf0-4a8e5f6cf9d4&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2026-11-17T03%3A46%3A36Z&ske=2026-11-18T03%3A46%3A36Z&sks=b&skv=2026-06-06&sig=eAFrKHcAcPuP3ysD7iC2kjRLUrpRTqtj/r21sugy4eQ%3D' -o /tmp/n.zip
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
five={(v<<3)|(v>>2) for v in range(32)}
rep={(v<<2)|(v>>4) for v in range(64)}
to_native={(g<<3)|(g>>2):g for g in range(32)}
def normalize_native(g):
 if g not in to_native: return None
 v=to_native[g]; six=(v<<1)|(v>>4)
 return (six<<2)|(six>>4)
scale={(v*255+31)//63 for v in range(64)}
def classify(vals):
 return {'replication_only':sum(v in rep and v not in scale for v in vals),'scaled_only':sum(v in scale and v not in rep for v in vals),'both':sum(v in rep and v in scale for v in vals),'neither':sum(v not in rep and v not in scale for v in vals)}
pairs=[]
for oi,ni in ((899,899),(902,900)):
 a=original(oi); b=native(ni)
 witnesses=[{'xy':[j%256,j//256],'original_g':x,'native_g':y,'original_rep':x in rep,'original_scaled':x in scale,'native_rep':y in rep,'native_scaled':y in scale} for j,(x,y) in enumerate(zip(a,b)) if x!=y][:32]
 residual=[{'xy':[j%256,j//256],'original_g':x,'native_g':y,'normalized_native_g':normalize_native(y)} for j,(x,y) in enumerate(zip(a,b)) if normalize_native(y)!=x]
 print('REAL_FIVEBIT_RESIDUAL',oi,ni,'native_fivebit_compatible',sum(y in five for y in b),'residual_count',len(residual),'first',residual[:12])
 pairs.append({'native_fivebit_compatible':sum(y in five for y in b),'original_fivebit_compatible':sum(x in five for x in a),'normalized_residual_count':len(residual),'normalized_residual_first_32':residual[:32],'original_index':oi,'native_index':ni,'original':classify(a),'native':classify(b),'mismatched_green':sum(x!=y for x,y in zip(a,b)),'witnesses':witnesses,'original_info':json.loads(get(oz,f'ws-product-atlas-{oi}.info.json')),'native_info':json.loads(get(nz,f'native-{ni}/state.info.json'))})
r={'schema':'wide07-real-fivebit-normalization/1','source_sha':os.environ['UR_EXPERIMENT_SOURCE_SHA'],'original_artifact':14184488104,'original_producer_sha':'05701c1d19389e90c86b8294a78e4d2ede95183b','native_artifact':14181849776,'native_producer_sha':'150a0199853b514928803b552e6fd73b642e0ede','phase_proven':False,'accepted_courses':0,'pairs':pairs}
(out/'fivebit-real.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print('REAL_FIVEBIT_NORMALIZATION',json.dumps(r,sort_keys=True))
PY
