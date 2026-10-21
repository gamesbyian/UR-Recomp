#!/usr/bin/env python3
"""Independent raw-byte census of exact RF081 research-guest memory pairs.

Research-only sampled frame checkpoints, NOT continuous original/native
event parity, executable provenance, or shipping Windows persistence.
"""
from collections import Counter
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import json

ARCHIVE_SHA = 'df35ddcd8e87bd6664e4e01fe6cbc91fabef6b45292d92564bdab92214bcff37'
ROOT = 'work/zoom-zoo/replay/'
SIZES = {'wram': 131072, 'sram': 8192}


def census(raw: bytes) -> dict:
    if type(raw) is not bytes or sha256(raw).hexdigest() != ARCHIVE_SHA:
        raise ValueError('RF081 frozen archive digest mismatch')
    with ZipFile(BytesIO(raw)) as z:
        if z.testzip() is not None:
            raise ValueError('RF081 CRC failure')
        members = z.namelist()
        if len(members) != len(set(members)):
            raise ValueError('duplicate ZIP members')
        names = set(members)
        out = {}
        for kind, size in SIZES.items():
            ref = {name[len(ROOT+'ref/'):]: name for name in names
                   if name.startswith(ROOT+'ref/') and name.endswith('.'+kind+'.bin')}
            native = {name[len(ROOT+'native/'):]: name for name in names
                      if name.startswith(ROOT+'native/') and name.endswith('.'+kind+'.bin')}
            if ref.keys() != native.keys() or not ref:
                raise ValueError('incomplete original/native '+kind+' paired population')
            count = Counter()
            rows = []
            for label in sorted(ref):
                a, b = z.read(ref[label]), z.read(native[label])
                if len(a) != size or len(b) != size:
                    raise ValueError('incorrect '+kind+' image size')
                offsets = [i for i in range(size) if a[i] != b[i]]
                count.update(offsets)
                rows.append({'label': label, 'exact': not offsets,
                             'different_bytes': len(offsets),
                             'original_sha256': sha256(a).hexdigest(),
                             'native_sha256': sha256(b).hexdigest()})
            out[kind] = {
                'paired_samples': len(rows),
                'exact_pairs': sum(r['exact'] for r in rows),
                'differing_byte_occurrences': sum(count.values()),
                'different_offsets_hex': {f'{k:04X}': count[k] for k in sorted(count)},
                'pairs': rows,
            }
    return {'schema': 'qa01-rf081-independent-raw-pairs/1',
            'case_zip_sha256': ARCHIVE_SHA, 'observations': out,
            'sampled_semantic_phase_equivalence_proven': False,
            'continuous_original_native_event_proven': False,
            'windows_disk_persistence_proven': False,
            'accepted_USA_events': 0, 'adjudication': 'HOLD'}


def inspect(path):
    return census(Path(path).read_bytes())

if __name__ == '__main__':
    import sys
    print(json.dumps(inspect(sys.argv[1]), indent=2, sort_keys=True))
