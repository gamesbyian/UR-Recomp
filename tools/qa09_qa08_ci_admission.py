#!/usr/bin/env python3
"""Read-only classifier for previously observed QA08 Windows experiment outcomes.

No workflow dispatch, release gate, renderer equivalence or external source
authenticity is inferred from caller-supplied evidence.
"""


def classify(*, source_sha, tested_sha, guest_on_off_equal,
             historic_crc_equal, archive_authenticated):
    for value in (source_sha, tested_sha):
        if type(value) is not str or len(value) != 40 or any(
                ch not in '0123456789abcdef' for ch in value):
            raise ValueError('invalid pinned commit SHA')
    if any(type(v) is not bool for v in (
            guest_on_off_equal, historic_crc_equal, archive_authenticated)):
        raise ValueError('evidence claims must be booleans')
    blockers=[]
    if source_sha != tested_sha: blockers.append('source epoch changed')
    if not archive_authenticated: blockers.append('source archive unauthenticated')
    if not guest_on_off_equal: blockers.append('ON/OFF guest CRC mismatch')
    if not historic_crc_equal: blockers.append('historic RF017 mismatch')
    return {'schema':'qa09-qa08-independent-ci-admission/1',
            'decision':'HOLD' if blockers else 'REVIEW_NEW_INDEPENDENT_EVIDENCE',
            'blockers':blockers,'release_gate_credit':0,
            'physical_windows_acceptance':False,
            'source_epoch_original_native_parity_proven':False}
