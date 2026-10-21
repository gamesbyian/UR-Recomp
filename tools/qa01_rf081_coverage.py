"""Independent RF081 sampling-coverage census; no USA event acceptance.

The archive proves selected snapshots exist, not a continuous, semantically
aligned original/native instruction or event trace. Never promote samples.
"""
import hashlib
import io
import json
import re
import zipfile

ARCHIVE_SHA256 = 'df35ddcd8e87bd6664e4e01fe6cbc91fabef6b45292d92564bdab92214bcff37'


def assess(raw):
    if type(raw) is not bytes or hashlib.sha256(raw).hexdigest() != ARCHIVE_SHA256:
        raise ValueError('wrong original RF081 evidence archive')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or z.testzip() is not None:
            raise ValueError('ambiguous RF081 archive')
        report = json.loads(z.read('producer-report.json'))
        result = json.loads(z.read('case-result.json'))
        frames = report.get('relative_sample_frames')
        event_frames = result.get('evidence',{}).get('original_event_frames')
        if (type(frames) is not list or len(frames) < 2 or
                any(type(x) is not int or x < 0 for x in frames) or
                frames != sorted(set(frames)) or frames[0] != 0 or
                type(event_frames) is not int or event_frames <= frames[-1] or
                result.get('disposition') != 'strict_candidate' or
                result['evidence'].get('source_original_movie_vs_fresh_guest_result_phase',{}).get(
                    'continuous_original_to_fresh_equivalence_proven') is not False):
            raise ValueError('source qualification or sample population changed')
        observed = set(names)
        expected = set()
        for frame in frames:
            stem = 'race-entered' if frame == 0 else f'scene-{frame:05d}'
            for side in ('ref','native'):
                for mem in ('wram','sram'):
                    name = f'work/zoom-zoo/replay/{side}/{stem}.{mem}.bin'
                    expected.add(name)
                    if name not in observed:
                        raise ValueError('missing raw original/native sample')
                    if z.getinfo(name).file_size != (131072 if mem == 'wram' else 8192):
                        raise ValueError('wrong raw sample length')
        for side in ('ref','native'):
            for stem in ('result-onset','result-stable'):
                for mem in ('wram','sram'):
                    name=f'work/zoom-zoo/replay/{side}/{stem}.{mem}.bin'
                    expected.add(name)
                    if name not in observed or z.getinfo(name).file_size != (131072 if mem=='wram' else 8192):
                        raise ValueError('missing or malformed result-stage raw sample')
        raw_names={n for n in names if re.fullmatch(
            r'work/zoom-zoo/replay/(ref|native)/(race-entered|result-onset|result-stable|scene-\d+)\.(wram|sram)\.bin',n)}
        if raw_names != expected:
            raise ValueError('unexpected or duplicate raw sample namespace')
        gaps=[b-a-1 for a,b in zip(frames,frames[1:])]+[event_frames-frames[-1]-1]
        return {'schema':'qa01-rf081-independent-sample-coverage/1',
                'source_archive_sha256':ARCHIVE_SHA256,
                'course':'USA Zoom Zoo Circuit',
                'sampled_race_frame_labels':len(frames),
                'source_event_duration_frames':event_frames,
                'maximum_unsampled_consecutive_frame_span':max(gaps),
                'unsampled_race_frame_labels':event_frames+1-len(frames),
                'paired_raw_memory_files':len(expected),
                'continuous_guest_execution_observed':False,
                'source_native_semantic_phase_qualified':False,
                'complete_USA_event_accepted':False,
                'release_gate_credit':0,'decision':'HOLD_SAMPLED_NOT_CONTINUOUS'}
