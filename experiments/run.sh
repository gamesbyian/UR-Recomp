#!/usr/bin/env bash
set -euo pipefail
OUT="${UR_EXPERIMENT_OUTPUT_DIR:?}"
mkdir -p "$OUT"
# Temporary read-only transfers of authenticated GitHub Actions artifact ZIPs.
# Read-only authenticated artifact handoffs expire 2026-11-16 23:07Z.
curl -fLsS --retry 2 --max-time 60 'https://sdmntprcentralus.oaiusercontent.com/files/00000000-0ed8-81f5-be28-c70b391041e1/raw?se=2026-11-16T23%3A07%3A07Z&sp=r&sv=2026-06-06&sr=b&scid=6263af6d-04f0-5866-a667-571cb19305fe&skoid=a1be202a-6464-476c-a496-723317c4a4db&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2026-11-16T22%3A53%3A52Z&ske=2026-11-17T22%3A53%3A52Z&sks=b&skv=2026-06-06&sig=xkMUbiocxWsm6a5NArw9lRQPLK0iWkeOLuFDQTCnQDA%3D' -o /tmp/o.zip
curl -fLsS --retry 2 --max-time 60 'https://sdmntprcentralus.oaiusercontent.com/files/00000000-7cc4-81f5-87bb-5d6c7a183f40/raw?se=2026-11-16T23%3A07%3A07Z&sp=r&sv=2026-06-06&sr=b&scid=578a8df4-8d8b-50cd-8768-b5e1f0409dbb&skoid=add8ee7d-5fc7-451e-b06e-a82b2276cf62&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2026-11-16T22%3A29%3A10Z&ske=2026-11-17T22%3A29%3A10Z&sks=b&skv=2026-06-06&sig=ATeKcTm8c5cb9RZ2IqiLLPG6B/7DYliDRf//8pKfF6Q%3D' -o /tmp/n.zip
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

python3 - "$OUT" <<'PY'
import collections,json,struct,sys,zipfile
from pathlib import Path
out=Path(sys.argv[1]); o=zipfile.ZipFile('/tmp/o.zip'); n=zipfile.ZipFile('/tmp/n.zip')
def pick(z,s):
    matches=[x for x in z.namelist() if x.endswith(s)]
    if len(matches)!=1: raise ValueError(('ambiguous',s,matches))
    return z.read(matches[0])
def orig(i):
    b=pick(o,f'ws-product-atlas-{i}.fb.bgrx')
    assert len(b)==256*224*4
    return bytes(v for k in range(0,len(b),4) for v in (b[k+2],b[k+1],b[k]))
def nat(i):
    b=pick(n,f'native-{i}/state.fb.bmp'); w,h=struct.unpack_from('<ii',b,18); off=struct.unpack_from('<I',b,10)[0]
    assert b[:2]==b'BM' and w==256 and abs(h)==224 and struct.unpack_from('<H',b,28)[0]==24
    stride=(w*3+3)&~3
    return bytes(v for y in range(224) for x in range(256) for v in (b[off+(y if h<0 else 223-y)*stride+3*x+2],b[off+(y if h<0 else 223-y)*stride+3*x+1],b[off+(y if h<0 else 223-y)*stride+3*x]))
report={'schema':'wide07-authentic-channel-diagnosis/1','execution_sha':__import__('os').environ['UR_EXPERIMENT_SOURCE_SHA'],'phase_accepted':False,'usa_course_credit':0,'pairs':[]}
for oi,ni in ((899,899),(902,900)):
    a,b=orig(oi),nat(ni)
    counts=[sum(a[3*i+c]!=b[3*i+c] for i in range(256*224)) for c in range(3)]
    delta=[collections.Counter(b[3*i+c]-a[3*i+c] for i in range(256*224)).most_common(12) for c in range(3)]
    report['pairs'].append({'original_index':oi,'native_index':ni,'channel_mismatch_pixels':dict(zip(('R','G','B'),counts)),'channel_delta_top':dict(zip(('R','G','B'),delta)),'original_info':json.loads(pick(o,f'ws-product-atlas-{oi}.info.json')),'native_info':json.loads(pick(n,f'native-{ni}/state.info.json'))})
(out/'channel-diagnosis.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print('REAL_CHANNEL_DIAGNOSIS',json.dumps(report,sort_keys=True))
PY
