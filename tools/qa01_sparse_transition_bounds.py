"""Read-only RF081 sparse-scene transition bounds, no event/causality verdict.

The exact/nonexact predicate need not be monotone. Adjacent observed states
only constrain parity of transitions between them, not the actual number.
"""
from __future__ import annotations
import hashlib
import re
import zipfile
from pathlib import Path

RF081_SHA256 = 'df35ddcd8e87bd6664e4e01fe6cbc91fabef6b45292d92564bdab92214bcff37'
TOTAL_SCENE_FRAMES = 5163
PAIR = re.compile(r'^work/zoom-zoo/replay/ref/scene-(\d{5})\.wram\.bin$')


def transition_bounds(samples: list[tuple[int, bool]], last_frame: int) -> dict:
    if type(last_frame) is not int or last_frame < 1:
        raise ValueError('invalid scene horizon')
    if (not isinstance(samples, list) or not samples or
            any(not isinstance(s, (list, tuple)) or len(s) != 2 or
                type(s[0]) is not int or type(s[1]) is not bool for s in samples)):
        raise ValueError('invalid sampled states')
    if (not 1 <= samples[0][0] <= last_frame or
            any(a[0] >= b[0] for a, b in zip(samples, samples[1:])) or
            samples[-1][0] > last_frame):
        raise ValueError('sample frame labels must be increasing within horizon')
    lower = upper = 0
    opposite = []
    same_gap_excursions = []
    for (f0, v0), (f1, v1) in zip(samples, samples[1:]):
        distance = f1 - f0
        parity = int(v0 != v1)
        minimum = parity
        maximum = distance if distance % 2 == parity else distance - 1
        lower += minimum
        upper += maximum
        if parity:
            opposite.append((f0, f1, minimum, maximum))
        elif distance >= 3:
            same_gap_excursions.append((f0, f1, maximum))
    suffix = last_frame - samples[-1][0]
    upper += suffix
    return {
        'sample_count': len(samples),
        'first_sample': samples[0][0],
        'last_sample': samples[-1][0],
        'last_frame': last_frame,
        'minimum_transitions_between_observed_samples': lower,
        'maximum_transitions_in_observed_span_and_suffix': upper,
        'unconstrained_suffix_frame_count': suffix,
        'opposite_state_brackets': opposite,
        'same_state_gaps_permitting_unobserved_excursions': same_gap_excursions,
        'monotonic_first_transition_inference_justified': False,
        'independently_accepted_USA_events': 0,
    }


def audit(path: Path) -> dict:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != RF081_SHA256:
        raise ValueError('wrong RF081 evidence epoch/digest')
    import io
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('duplicate ZIP member names')
        name_set = set(names)
        samples = []
        for name in names:
            match = PAIR.fullmatch(name)
            if not match:
                continue
            frame = int(match.group(1))
            native = name.replace('/ref/', '/native/')
            if native not in name_set:
                raise ValueError('missing paired native scene')
            original = archive.read(name)
            compiled = archive.read(native)
            if len(original) != 131072 or len(compiled) != 131072:
                raise ValueError('wrong WRAM image length')
            samples.append((frame, original != compiled))
    samples.sort()
    if len(samples) != 41:
        raise ValueError('unexpected scene sample census')
    out = transition_bounds(samples, TOTAL_SCENE_FRAMES)
    out['source_sha256'] = RF081_SHA256
    out['first_nonexact_sample'] = next((f for f, v in samples if v), None)
    return out


if __name__ == '__main__':
    import json
    import sys
    if len(sys.argv) != 2:
        raise SystemExit('usage: qa01_sparse_transition_bounds.py ARCHIVED_RF081_ZIP')
    print(json.dumps(audit(Path(sys.argv[1])), indent=2))
