#!/usr/bin/env bash
set -euo pipefail
OUT="${UR_EXPERIMENT_OUTPUT_DIR:?}"
mkdir -p "$OUT"
# Temporary read-only transfers of authenticated GitHub Actions artifact ZIPs.
# These URLs expire 2026-11-16 20:07Z; rerun requires renewed source handoff.
curl -fLsS --retry 2 --max-time 60 'https://sdmntpreastus3.oaiusercontent.com/files/00000000-f244-8212-894a-9c1dee553787/raw?se=2026-11-16T21%3A03%3A59Z&sp=r&sv=2026-06-06&sr=b&scid=72f524e0-894a-5e54-b930-26178b69ddcc&skoid=04233560-0ad7-493e-8bf0-1347c317d021&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2026-11-16T15%3A58%3A34Z&ske=2026-11-17T15%3A58%3A34Z&sks=b&skv=2026-06-06&sig=nR0SdXaXZCLBqFIKdYo0Zvc2iizZKSGXtoCKh81XuAY%3D' -o /tmp/o.zip
curl -fLsS --retry 2 --max-time 60 'https://sdmntpreastus3.oaiusercontent.com/files/00000000-af9c-8212-a38e-a70d95e89d86/raw?se=2026-11-16T21%3A03%3A59Z&sp=r&sv=2026-06-06&sr=b&scid=3941d8f3-ccfd-5926-a2e4-ca73135810a2&skoid=04233560-0ad7-493e-8bf0-1347c317d021&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2026-11-16T14%3A51%3A53Z&ske=2026-11-17T14%3A51%3A53Z&sks=b&skv=2026-06-06&sig=Sod58e%2BQcyYbMbb1s0m/JiMymknpZKbD6XG9sefLur0%3D' -o /tmp/n.zip
sha256sum /tmp/o.zip /tmp/n.zip > "$OUT/zip-sha256.txt"
python3 - "$OUT" <<'PY'
import hashlib,json,struct,sys,zipfile
from pathlib import Path
out=Path(sys.argv[1]); o=zipfile.ZipFile('/tmp/o.zip'); n=zipfile.ZipFile('/tmp/n.zip')
(out/'manifest.json').write_text(json.dumps({'original':o.namelist(),'native':n.namelist()},indent=2))
def pick(z,suffix):
    matches=[x for x in z.namelist() if x.endswith(suffix)]
    if len(matches)!=1: raise ValueError(('MISSING_OR_AMBIGUOUS',suffix,matches))
    return z.read(matches[0])
def orig(i):
    b=pick(o,f'ws-product-atlas-{i}.fb.bgrx')
    assert len(b)==256*224*4,('ORIGINAL_DIM',len(b))
    return bytes(v for k in range(0,len(b),4) for v in (b[k+2],b[k+1],b[k]))
def nat(i):
    b=pick(n,f'native-{i}/state.fb.bmp')
    w,h=struct.unpack_from('<ii',b,18); off=struct.unpack_from('<I',b,10)[0]
    assert b[:2]==b'BM' and w==256 and abs(h)==224 and struct.unpack_from('<H',b,28)[0]==24,(w,h)
    stride=(w*3+3)&~3
    return bytes(v for y in range(224) for x in range(256) for v in (b[off+(y if h<0 else 223-y)*stride+3*x+2],b[off+(y if h<0 else 223-y)*stride+3*x+1],b[off+(y if h<0 else 223-y)*stride+3*x]))
a,b,c,d=orig(899),orig(902),nat(899),nat(900)
def changed(x,y): return {i//3 for i in range(0,len(x),3) if x[i:i+3]!=y[i:i+3]}
def xy(indices): return [[i%256,i//256] for i in sorted(indices)[:128]]
om,nm=changed(a,b),changed(c,d)
r={'schema':'wide07-real-byte-compare/1','original_artifact':14184488104,'original_sha':'05701c1d19389e90c86b8294a78e4d2ede95183b','native_artifact':14181849776,'native_sha':'150a0199853b514928803b552e6fd73b642e0ede','execution_sha':__import__('os').environ['UR_EXPERIMENT_SOURCE_SHA'],'dimensions':[256,224],'original_motion_pixels':len(om),'native_motion_pixels':len(nm),'motion_intersection':len(om&nm),'original_only_xy':xy(om-nm),'native_only_xy':xy(nm-om),'cross_engine_before_mismatch_pixels':len(changed(a,c)),'cross_engine_after_mismatch_pixels':len(changed(b,d)),'cross_engine_before_first_xy':xy(changed(a,c)),'cross_engine_after_first_xy':xy(changed(b,d)),'rgb_sha256':[hashlib.sha256(x).hexdigest() for x in (a,b,c,d)],'acceptance':0,'absolute_phase_proven':False}
r['original_info']=[json.loads(pick(o,f'ws-product-atlas-{i}.info.json')) for i in (899,902)]
r['native_info']=[json.loads(pick(n,f'native-{i}/state.info.json')) for i in (899,900)]
(out/'real-comparison.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print('REAL_BYTES_COMPARE',json.dumps({k:v for k,v in r.items() if not k.endswith('_info')},sort_keys=True))
PY
