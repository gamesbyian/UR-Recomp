"""Independent sampled raw-memory difference census; diagnostic, never parity."""
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile
import json
from qa01_rf081_coverage import assess, ARCHIVE_SHA256


def census(raw):
    coverage = assess(raw)
    if coverage['release_gate_credit'] != 0:
        raise ValueError('source qualification changed')
    with ZipFile(BytesIO(raw)) as z:
        frames = json.loads(z.read('producer-report.json'))['relative_sample_frames']
        rows=[]
        for frame in frames:
            stem = 'race-entered' if frame == 0 else f'scene-{frame:05d}'
            for kind in ('wram','sram'):
                left=z.read(f'work/zoom-zoo/replay/ref/{stem}.{kind}.bin')
                right=z.read(f'work/zoom-zoo/replay/native/{stem}.{kind}.bin')
                if len(left)!=len(right):
                    raise ValueError('mismatched sample lengths')
                rows.append({'frame':frame,'kind':kind,
                             'different_bytes':sum(a!=b for a,b in zip(left,right)),
                             'sample_size':len(left)})
        return {'schema':'qa01-rf081-sampled-byte-differences/1',
                'archive_sha256':ARCHIVE_SHA256,'rows':rows,
                'total_sampled_byte_differences':sum(r['different_bytes'] for r in rows),
                'phase_aligned':False,'continuous_equivalence':False,
                'release_gate_credit':0,'decision':'HOLD_SAMPLED_PHASE_UNQUALIFIED'}


def cross_stage_census(raw):
    """Count two terminal snapshots separately from the 42 sparse race labels.

    This is a byte census, not semantic-phase equivalence or an event verdict.
    """
    scene = census(raw)  # independent SHA/coverage gate, never event credit
    stages = []
    with ZipFile(BytesIO(raw)) as z:
        for stage in ('result-onset', 'result-stable'):
            for kind in ('wram', 'sram'):
                prefix = 'work/zoom-zoo/replay/'
                original = z.read(f'{prefix}ref/{stage}.{kind}.bin')
                native = z.read(f'{prefix}native/{stage}.{kind}.bin')
                if len(original) != len(native):
                    raise ValueError('terminal stage size mismatch')
                positions = [i for i,(a,b) in enumerate(zip(original,native)) if a != b]
                stages.append({'stage':stage,'kind':kind,'different_bytes':len(positions),
                               'different_offsets':positions,'sample_size':len(original)})
    rows = scene['rows']
    return {'schema':'qa01-rf081-cross-stage-census/1',
            'archive_sha256':ARCHIVE_SHA256,
            'race_frame_labels':len({r['frame'] for r in rows}),
            'race_memory_pairs':len(rows),
            'terminal_memory_pairs':len(stages),
            'terminal_stages':stages,
            'total_wram_differences':sum(r['different_bytes'] for r in rows if r['kind']=='wram') +
                                     sum(r['different_bytes'] for r in stages if r['kind']=='wram'),
            'total_sram_differences':sum(r['different_bytes'] for r in rows if r['kind']=='sram') +
                                     sum(r['different_bytes'] for r in stages if r['kind']=='sram'),
            'source_phase_equivalence':False,
            'complete_event_admitted':False,
            'release_gate_credit':0,
            'decision':'HOLD_SAMPLED_AND_TERMINAL_PHASES_UNQUALIFIED'}
