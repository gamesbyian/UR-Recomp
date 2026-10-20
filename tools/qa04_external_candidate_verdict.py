#!/usr/bin/env python3
"""Independent *classification* of pinned hosted Windows package evidence.

This is not a physical test, candidate nomination, or gate-authoritative ledger.
Inputs must be obtained from separate evidence authorities, not guessed from
an archive's own manifest. The classifier refuses malformed or unbound pins.
"""
import re

_HEX40 = re.compile(r'^[0-9a-f]{40}$')
_HEX64 = re.compile(r'^[0-9a-f]{64}$')


def classify(*, tested_source, current_main, nominated_source,
             tested_inner_zip, nominated_inner_zip, hosted_package_verified,
             physical_journey_verified=False):
    for key, value in [('tested_source', tested_source), ('current_main', current_main),
                       ('nominated_source', nominated_source)]:
        if not isinstance(value, str) or not _HEX40.fullmatch(value):
            raise ValueError('invalid externally pinned SHA: '+key)
    for key, value in [('tested_inner_zip', tested_inner_zip),
                       ('nominated_inner_zip', nominated_inner_zip)]:
        if not isinstance(value, str) or not _HEX64.fullmatch(value):
            raise ValueError('invalid externally pinned SHA: '+key)
    if type(hosted_package_verified) is not bool or type(physical_journey_verified) is not bool:
        raise ValueError('evidence claims must be exact booleans')
    source_matches_nomination = tested_source == nominated_source
    package_matches_nomination = tested_inner_zip == nominated_inner_zip
    source_matches_main = tested_source == current_main
    blockers = []
    if not hosted_package_verified:
        blockers.append('hosted_package_not_independently_verified')
    if not source_matches_nomination:
        blockers.append('tested_source_not_nominated_source')
    if not package_matches_nomination:
        blockers.append('tested_inner_zip_not_nominated_zip')
    if not source_matches_main:
        blockers.append('tested_source_not_current_main')
    if not physical_journey_verified:
        blockers.append('physical_journey_not_verified')
    # Even a nominal match does not prove 12 separate QA gates.
    return {'schema':'ur-qa04-independent-candidate-pin-classification/1',
            'source_matches_nomination':source_matches_nomination,
            'inner_zip_matches_nomination':package_matches_nomination,
            'source_matches_current_main':source_matches_main,
            'hosted_package_verified':hosted_package_verified,
            'physical_journey_verified':physical_journey_verified,
            'release_gate_credit':0,'decision':'HOLD' if blockers else 'READY_FOR_SEPARATE_GATE_REVIEW',
            'blockers':blockers}
