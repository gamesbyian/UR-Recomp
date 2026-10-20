#!/usr/bin/env python3
"""ROM-free empirical integer brightness fit on immutable QA08 source observations.

This matches the *observed* renderer's 88 main-source/final pairs only. It
cannot prove hardware colour maths, P7 equivalence or historical source epoch.
"""
from pathlib import Path
from collections import Counter
import hashlib, json, zipfile, io

ARCHIVE_SHA='10bd91c7be06e3ac832675f2b5268bf179a2b03b5f07dcf8fd632fad18372ec2'
ANCHORS={(53,41),(65,52),(70,58),(84,77),(175,145),(187,160),(190,161),(202,182)}
FRAMES=set(range(5176,5187))

def scale_channel(v, brightness):
    if type(v) is not int or not 0<=v<=31 or type(brightness) is not int or not 0<=brightness<=15:
        raise ValueError('invalid five-bit channel or brightness')
    return (((v<<3)|(v>>2))*brightness)//15

def expected_rgb(word, brightness):
    if len(word)!=4 or any(c not in '0123456789abcdef' for c in word):
        raise ValueError('invalid RGB555 source word')
    value=int(word,16)
    return tuple(scale_channel((value>>shift)&31,brightness) for shift in (0,5,10))

def parse(rows):
    pairs={}; stages=Counter()
    for line in rows:
        toks=line.split(); typ=toks[0]
        if typ not in ('UR_QA08_LATE_PPU_SOURCE','UR_QA08_LATE_PPU_FINAL'):
            raise ValueError('unexpected source row')
        fields={}
        for token in toks[1:]:
            if '=' not in token: raise ValueError('malformed field')
            k,v=token.split('=',1)
            if k in fields:raise ValueError('duplicate field')
            fields[k]=v
        frame=int(fields['frame']);xy=(int(fields['x']),int(fields['logical_y']))
        if frame not in FRAMES or xy not in ANCHORS or int(fields['ppu_line'])!=xy[1]+1:
            raise ValueError('source coordinate out of scope')
        stage='final' if typ.endswith('FINAL') else fields['sub']
        if typ.endswith('SOURCE') and stage not in ('0','1'):
            raise ValueError('source cannot impersonate final')
        if typ.endswith('FINAL') and 'sub' in fields:
            raise ValueError('final cannot carry source stage')
        if stage not in ('0','1','final'):raise ValueError('unknown source stage')
        key=(frame,xy)
        if stage in pairs.setdefault(key,{}):raise ValueError('duplicate source stage')
        pairs[key][stage]=fields;stages[stage]+=1
    if len(pairs)!=88 or stages!=Counter({'0':88,'1':88,'final':88}):
        raise ValueError('incomplete bounded sample')
    words=Counter()
    for key, rec in pairs.items():
        main,sub,final=(rec[stage] for stage in ('0','1','final'))
        if (main['directcolor']!='0' or main['layer']!='0' or
            main['inidisp']!='0e' or final['inidisp']!='0e' or
            sub['inidisp']!='0e'):
            raise ValueError('unexpected colour source/brightness')
        slot=int(main['index'],16)
        if slot not in range(0x6c,0x70):raise ValueError('unexpected palette index')
        word=main['selected_rgb555']
        if word!=main['cgram_index_word'] or word!=main[f'cgram{slot:02x}']:
            raise ValueError('CGRAM selected-word contradiction')
        expected=expected_rgb(word,14)
        actual=tuple(int(c) for c in final['RGB8'].split(','))
        if actual!=expected:raise ValueError(f'brightness fit mismatch at {key}: {actual} != {expected}')
        words[word]+=1
    if len(words)!=4:raise ValueError('incomplete four-word palette census')
    return {'schema':'qa08-current-source-integer-brightness-fit/1',
            'source_triplets':88,'source_frames':11,
            'observed_rgb555_to_rgb8':{w:list(expected_rgb(w,14)) for w in sorted(words)},
            'observed_counts':dict(sorted(words.items())),
            'model':'expand RGB5 to RGB8 via (v<<3)|(v>>2), then floor(expanded*14/15)',
            'model_is_empirical_not_hardware_proof':True,
            'same_epoch_original_native_proven':False,
            'release_gate_credit':0}

def audit(path):
    blob=Path(path).read_bytes()
    if hashlib.sha256(blob).hexdigest()!=ARCHIVE_SHA:
        raise ValueError('immutable source archive mismatch')
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        if z.testzip() is not None:raise ValueError('ZIP CRC')
        return parse(z.read('on-source.log').decode('ascii').splitlines())
if __name__=='__main__':
    import sys
    print(json.dumps(audit(sys.argv[1]),indent=2,sort_keys=True))
