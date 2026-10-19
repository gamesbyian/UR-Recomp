#!/usr/bin/env python3
"""Bounded RF076 research-only RF047 shared recorder capacity source patch.

A genuine original/native Zoo run produced 8192 complete atomic RF047
records, then QA01RF047NATIVE_TRUNCATED while compiled D4EE/D4F0 opcodes
continued executing. For ONE disposable nine-frame campaign, retain all
guest instruction markers up to 131072. Preserve the strict truncation guard.
This does not touch guest emulation, timing, original emulator, or QA verdicts.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

SOURCE = Path('snesrecomp/runner/src/beam_frame_driver.c')
SOURCE_PIN = 'UR_QA01_RF047_NATIVE_NMI_RETURN_SOURCE_PIN'
OLD_LIMIT = 'if (ur_rf047_events++ >= 8192u) {'
OLD_OVERFLOW = 'if (ur_rf047_events == 8193u)'
NEW_LIMIT = 'if (ur_rf047_events++ >= 131072u) {'
NEW_OVERFLOW = 'if (ur_rf047_events == 131073u)'
TAG = 'UR_QA01_RF076_FINITE_RECORDER_CAP_131072'


def patch(source: str) -> str:
    if TAG in source or NEW_LIMIT in source or NEW_OVERFLOW in source:
        raise ValueError('RF076 recorder cap already or partly adjusted')
    if SOURCE_PIN not in source or source.count(OLD_LIMIT) != 1 or \
       source.count(OLD_OVERFLOW) != 1 or \
       source.count('QA01RF047NATIVE_TRUNCATED') != 2:
        # One format literal in the truncated event function plus one
        # source comment in the reusable observer are allowed only if the
        # source-pinned RF047 implementation matches exactly.
        raise ValueError('RF076 original RF047 shared recorder structure changed')
    updated = source.replace(OLD_LIMIT,
        '/* ' + TAG + ': full 9-frame CPU witness; never suppress overflow. */\n  '+
        NEW_LIMIT, 1).replace(OLD_OVERFLOW, NEW_OVERFLOW, 1)
    if updated.count(NEW_LIMIT) != 1 or updated.count(NEW_OVERFLOW) != 1 or \
       updated.count('ur_rf047_emit("QA01RF047NATIVE_TRUNCATED\\n");') != 1:
        raise ValueError('RF076 widened finite limit lost hard overflow path')
    return updated


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',required=True,type=Path)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    path=args.root.resolve()/SOURCE
    raw=path.read_text(encoding='utf8')
    updated=patch(raw)
    path.write_text(updated,encoding='utf8')
    receipt={
        'schema':'ur-qa01-rf076-native-bounded-observer-capacity-source/1',
        'source':SOURCE.as_posix(),
        'source_before_sha256':hashlib.sha256(raw.encode()).hexdigest(),
        'source_after_sha256':hashlib.sha256(updated.encode()).hexdigest(),
        'prior_atomic_event_limit':8192,
        'temporary_atomic_event_limit':131072,
        'still_emits_explicit_truncated_event':True,
        'source_original_native_same_phase_proven':False,
        'guest_opcodes_observed_by_static_patcher':False,
        'accepted_USA_events':0,
    }
    encoded=json.dumps(receipt,sort_keys=True,indent=2)+'\n'
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(encoded)
    else:
        print(encoded,end='')


if __name__ == '__main__':
    main()
