"""Source-pinned RF081 opposite-state frame priority, no parity credit.

Narrow verbatim extraction of QA01 H26 first-party five-line research logic.
"""
import hashlib, io, re, zipfile
RF081_SHA = 'df35ddcd8e87bd6664e4e01fe6cbc91fabef6b45292d92564bdab92214bcff37'


def _sha(blob):
    return hashlib.sha256(blob).hexdigest()


def qa01_transition_priority(raw: bytes) -> dict:
    """Rank *bounded* opposite-state samples, not the unbounded long tail.

    No monotonicity or semantic phase equality is assumed between samples.
    """
    if type(raw) is not bytes or _sha(raw) != RF081_SHA:
        raise ValueError('wrong genuine RF081 archive')
    by_frame = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or z.testzip() is not None:
            raise ValueError('ambiguous or corrupt RF081 ZIP')
        for name in names:
            m = re.fullmatch(r'work/zoom-zoo/replay/ref/scene-(\d{5})\.wram\.bin', name)
            if not m: continue
            f = int(m.group(1)); peer = name.replace('/ref/', '/native/', 1)
            if f in by_frame or peer not in names:
                raise ValueError('missing or duplicated pair')
            a,b = z.read(name), z.read(peer)
            if len(a) != 131072 or len(b) != 131072:
                raise ValueError('bad unmasked WRAM size')
            diff = [i for i,(x,y) in enumerate(zip(a,b)) if x != y]
            if diff and diff != [0x1ed,0x1ee,0x1ef,0x1f0]:
                raise ValueError('unexpected mismatch class, review required')
            by_frame[f] = bool(diff)
    if len(by_frame) != 41: raise ValueError('unexpected scene population')
    labels = sorted(by_frame)
    changes = []
    for lo,hi in zip(labels,labels[1:]):
        if by_frame[lo] == by_frame[hi]: continue
        missing = hi-lo-1
        changes.append({'from':lo,'to':hi,'from_nonexact':by_frame[lo],
                        'to_nonexact':by_frame[hi],'unobserved':missing,
                        'next_probe':lo+1 if missing else None,
                        'first_possible_transition':lo+1})
    actionable = [x for x in changes if x['unobserved']]
    actionable.sort(key=lambda x:(x['from'],x['unobserved']))
    return {'schema':'qa01-opposite-state-probe-priority/1','archive_sha256':RF081_SHA,
            'scene_pairs':len(labels),'first_observed_nonexact_frame':min(f for f in labels if by_frame[f]),
            'opposite_state_brackets':len(changes),'brackets_with_unobserved_frames':len(actionable),
            'earliest_bounded_probe':actionable[0]['next_probe'],
            'earliest_bounded_interval':[actionable[0]['from'],actionable[0]['to']],
            'next_onset_probe':next(x['next_probe'] for x in actionable if not x['from_nonexact'] and x['to_nonexact']),
            'tail_2401_to_5163_has_no_known_right_endpoint':True,
            'longest_tail_midpoint_3782_cannot_localize_first_mismatch':True,
            'transition_brackets':changes,'assume_monotonicity':False,
            'new_guest_observations':0,'complete_event_credit':0}


