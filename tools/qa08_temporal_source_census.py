"""Authenticated QA08 temporal anchor census, diagnostic only, no PPU parity."""
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
import hashlib

AUTH_SHA='10bd91c7be06e3ac832675f2b5268bf179a2b03b5f07dcf8fd632fad18372ec2'

def census(path):
    path=Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=AUTH_SHA:
        raise ValueError('untrusted archive epoch')
    with ZipFile(path) as z:
        rows=z.read('on-source.log').decode('ascii').splitlines()
    seen={}
    for row in rows:
        parts=row.split();typ=parts[0]
        if typ!='UR_QA08_LATE_PPU_SOURCE':continue
        fields=dict(token.split('=',1) for token in parts[1:])
        if fields['sub']!='0':continue
        key=(int(fields['frame']),int(fields['x']),int(fields['logical_y']))
        if key in seen:raise ValueError('duplicate main-source observation')
        seen[key]=fields['selected_rgb555']
    frames=sorted({f for f,_,_ in seen});anchors=sorted({(x,y) for _,x,y in seen},key=lambda p:(p[1],p[0]))
    if frames!=list(range(5176,5187)) or len(anchors)!=8 or len(seen)!=88:
        raise ValueError('incomplete source anchor census')
    patterns={f:[seen[(f,*p)] for p in anchors] for f in frames}
    transitions=[{'from':a,'to':b,'changed_anchors':sum(x!=y for x,y in zip(patterns[a],patterns[b]))}
                 for a,b in zip(frames,frames[1:])]
    phase_starts=[frames[0]]+[t['to'] for t in transitions if t['changed_anchors']]
    if phase_starts!=[5176,5177,5184] or any(t['changed_anchors'] not in (0,8) for t in transitions):
        raise ValueError('unexpected authenticated temporal phase')
    if any(Counter(patterns[f])!=Counter({'4210':2,'4631':2,'4a52':2,'56b5':2}) for f in frames):
        raise ValueError('per-frame palette-class census')
    return {'schema':'qa08-source-anchor-temporal-phase/1','frames':frames,
            'anchors_xy':anchors,'phase_starts':phase_starts,
            'patterns_by_frame':{str(k):v for k,v in patterns.items()},
            'transitions':transitions,'source_archive_sha256':AUTH_SHA,
            'original_native_ppu_pixel_parity':False,'release_gate_credit':0}
