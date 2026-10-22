"""Decision-only chromatic QA08 probe optimization; no captured PPU pixels.

Two brightness scalings fit all 88 authenticated grayscale triplets. Enumerate
six channel permutations x two scalings, then choose a probe maximizing the
minimum pairwise L1 distance. Distinguish model identifiability from noisy
measurement confidence. This is not a shipping colour correction.
"""
from itertools import combinations, permutations
from zipfile import ZipFile
from pathlib import Path
import hashlib, re

AUTHENTIC_SHA256 = '10bd91c7be06e3ac832675f2b5268bf179a2b03b5f07dcf8fd632fad18372ec2'
SCALES = ((14,15),(187,200))
PERMS = tuple(permutations(range(3)))

def expand(v):
    if type(v) is not int or not 0 <= v <= 31: raise ValueError('invalid RGB5')
    return (v<<3)|(v>>2)

def predict(channels):
    if (type(channels) is not tuple or len(channels)!=3 or
            any(type(v) is not int or not 0<=v<=31 for v in channels)):
        raise ValueError('invalid chromatic probe')
    return {f'{p}-{num}/{den}':tuple(expand(channels[i])*num//den for i in p)
            for p in PERMS for num,den in SCALES}

def _strict_observation_fields(line, event):
    """Parse one authenticated log line without duplicate keys or coercions."""
    tokens=line.split()
    if not tokens or tokens[0]!=event:
        raise ValueError("wrong QA08 source/final stage order")
    fields={}
    for token in tokens[1:]:
        if token.count("=")!=1:
            raise ValueError("malformed QA08 observation field")
        key,value=token.split("=",1)
        if not key or not value or key in fields:
            raise ValueError("duplicate or empty QA08 observation field")
        fields[key]=value
    return fields


def genuine_scale_compatibility(path):
    """Admit all 88 *consecutive* source0/source1/final triplets or fail.

    The historical census counted independent sub0 and final observations,
    silently ignoring sub1, ordering and duplicate ZIP names. This recovery
    strengthens the already-shipping read-only tool, not the PPU renderer.
    """
    blob=Path(path).read_bytes()
    if hashlib.sha256(blob).hexdigest()!=AUTHENTIC_SHA256:
        raise ValueError('unauthenticated source archive')
    with ZipFile(path) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or z.testzip() is not None:
            raise ValueError('duplicate or corrupt QA08 archive member')
        if 'on-source.log' not in names:
            raise ValueError('missing QA08 source log')
        rows=z.read('on-source.log').decode('ascii').splitlines()
    if len(rows)!=264:
        raise ValueError('incomplete QA08 source/final triplets')
    main={};finals={}
    for index in range(0,len(rows),3):
        a=_strict_observation_fields(rows[index], 'UR_QA08_LATE_PPU_SOURCE')
        b=_strict_observation_fields(rows[index+1], 'UR_QA08_LATE_PPU_SOURCE')
        c=_strict_observation_fields(rows[index+2], 'UR_QA08_LATE_PPU_FINAL')
        if a.get('sub')!='0' or b.get('sub')!='1':
            raise ValueError('wrong QA08 sub-stage order')
        try:
            key=tuple(a[field] for field in ('frame','x','logical_y'))
            if key in main or any(
                fields.get(field)!=a.get(field)
                for fields in (b,c) for field in ('frame','x','logical_y','ppu_line')
            ):
                raise ValueError('duplicate or cross-epoch QA08 stage')
            rgb555=a['selected_rgb555']
            if re.fullmatch(r'[0-7][0-9a-f]{3}',rgb555) is None:
                raise ValueError('malformed QA08 source RGB555')
            word=int(rgb555,16)
            rgb=c['RGB8'].split(',')
            if len(rgb)!=3 or any(re.fullmatch(r'(?:0|[1-9][0-9]*)',v) is None for v in rgb):
                raise ValueError('malformed QA08 final RGB8')
            colour=tuple(int(v) for v in rgb)
            if any(not 0<=v<=255 for v in colour):
                raise ValueError('out-of-range QA08 final RGB8')
        except KeyError as exc:
            raise ValueError('missing QA08 source/final identity or colour') from exc
        main[key]=word
        finals[key]=colour
    if len(main)!=88:
        raise ValueError('incomplete genuine source')
    fits={}
    for n,d in SCALES:
        fits[f'{n}/{d}']=all(tuple(expand((word>>s)&31)*n//d for s in (0,5,10))==finals[k]
                              for k,word in main.items())
    return {'source_triplets':88,'compatible_scalings':fits,'chromatic_source_observed':False}

def choose_probe():
    best=None
    for ch in combinations(range(32),3):
        preds=predict(ch)
        outputs=list(preds.values())
        if len(set(outputs))!=12:continue
        min_l1=min(sum(abs(a-b) for a,b in zip(u,v))
                   for i,u in enumerate(outputs) for v in outputs[i+1:])
        score=(min_l1, min(ch), -sum(ch))
        if best is None or score>best[0]:best=(score,ch,preds)
    if best is None:raise ValueError('no fully discriminating RGB5 probe')
    _,ch,preds=best
    # For each permutation, the two scalings are only one RGB8 count apart
    # in every channel. With +/-1 channel measurement uncertainty their
    # prediction intervals overlap, regardless of how many permutations split.
    same_perm_max=max(max(abs(a-b) for a,b in zip(preds[f'{p}-14/15'],preds[f'{p}-187/200']))
                      for p in PERMS)
    return {'schema':'qa08-future-probe-identifiability/1',
            'candidate_rgb555':f'{ch[0]|ch[1]<<5|ch[2]<<10:04x}',
            'channels_rgb5':list(ch),'predictions':preds,
            'distinct_exact_predictions':len(set(preds.values())),
            'minimum_pairwise_L1':best[0][0],
            'same_permutation_scale_Linf_at_most_one':same_perm_max<=1,
            'plus_minus_one_measurement_cannot_uniquely_identify_scaling':same_perm_max<=1,
            'future_probe_only':True,'same_epoch_ppu_proven':False,'release_gate_credit':0}
