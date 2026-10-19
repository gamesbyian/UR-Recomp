#!/usr/bin/env python3
"""ROM-free consumer for opt-in real original Snes9x fetched-opcode records.

Original source-local event ordinals, NOT host-frame parity or native RF047
ordinals. Missing fetches stay missing. A logged nmi_before row is not a
fetched opcode. No binary epoch is borrowed from RF071/072 or RF073.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

TAG = 'QA01RF076ORIGPC seq='
EVENT = re.compile(r'QA01RF076ORIGPC seq=(\d+) (.*)$')
FIELDS = re.compile(r'([A-Za-z][A-Za-z0-9]*)=([^\s]+)')
FETCH_TARGETS = {0x82D4EE, 0x82D4F0, 0x82D4F2, 0x82D4F4, 0x82D4F5}


def inspect(log: str) -> dict:
    if 'QA01RF076ORIGPC_TRUNCATED' in log:
        raise ValueError('original fetched opcode marker stream truncated')
    parsed = []
    for line in log.splitlines():
        if TAG not in line:
            continue
        if not line.startswith(TAG) or line.count(TAG) != 1:
            raise ValueError('original marker mixed with untrusted fragmented logger')
        m = EVENT.fullmatch(line)
        if m is None:
            raise ValueError('original marker truncated or malformed')
        pairs = FIELDS.findall(m.group(2))
        if not pairs or ' '.join(f'{k}={v}' for k,v in pairs) != m.group(2):
            raise ValueError('original opcode marker malformed fields')
        row = dict(pairs)
        if len(row) != len(pairs) or int(m.group(1)) != len(parsed)+1:
            raise ValueError('original opcode marker duplicate/unsorted sequence')
        try:
            frame = int(row['f'])
            pc = int(row['actualFetchedPC'], 16)
            op = int(row['fetchedOpcode'], 16)
            sp = int(row['S'], 16)
            v, h = int(row['v']), int(row['h'])
            wai = int(row['wai'])
        except (ValueError,KeyError) as exc:
            raise ValueError('original opcode marker missing source context') from exc
        if not 1017 <= frame <= 1025 or not 0 <= pc <= 0xffffff or \
           not 0 <= op <= 255 or not 0 <= sp <= 0xffff or \
           not 0 <= v <= 311 or h < 0 or wai not in (0,1):
            raise ValueError('original opcode marker outside bounded source context')
        if row.get('stage') not in ('fetch', 'nmi_pending', 'nmi_before'):
            raise ValueError('original opcode marker invalid source stage')
        if row['stage']=='fetch' and pc not in FETCH_TARGETS:
            raise ValueError('original actual fetched instruction not in source allowlist')
        if row['stage'] in ('nmi_pending','nmi_before') and op != 0:
            raise ValueError('original non-fetched NMI sentinel incorrectly labelled opcode')
        parsed.append({
            'source_local_seq':len(parsed)+1, 'stage':row['stage'],
            'original_host_frame':frame, 'original_local_V':v,'original_local_H':h,
            'source_guest_PC_context':f'{pc:06X}', 'raw_fetched_opcode_if_fetch':
                f'{op:02X}' if row['stage']=='fetch' else None,
            'source_stack_SP':f'{sp:04X}', 'waiting_for_interrupt':bool(wai),
            'decoded_original_guest_fetch_executed':row['stage']=='fetch'})
    if not parsed:
        raise ValueError('no actual original opcode/NMI source events')
    nmies=[(i,x) for i,x in enumerate(parsed) if x['stage']=='nmi_before']
    if sum(x['stage']=='nmi_pending' for x in parsed) != len(nmies):
        raise ValueError('original NMI wake-pending and before-push populations differ')
    seen_frames = [e['original_host_frame'] for _,e in nmies]
    if seen_frames != sorted(set(seen_frames)):
        raise ValueError('original NMI frame chronology duplicated or reordered')
    missing_frames = sorted(set(range(1017,1026))-set(seen_frames))
    frames=[]
    for i,e in nmies:
        if i == 0 or parsed[i-1]['stage'] != 'nmi_pending':
            raise ValueError('original NMI wake-pending marker missing before actual push')
        pending = parsed[i-1]
        if pending['original_host_frame'] != e['original_host_frame'] or \
           pending['waiting_for_interrupt'] is None or e['waiting_for_interrupt']:
            raise ValueError('original NMI wake flag/host frame source contradiction')
        prior_pc = int(pending['source_guest_PC_context'],16)
        after_pc = int(e['source_guest_PC_context'],16)
        expected_pc = (prior_pc & 0xff0000) | (((prior_pc & 0xffff) + int(pending['waiting_for_interrupt'])) & 0xffff)
        if after_pc != expected_pc:
            raise ValueError('original NMI WAI wake PC advancement contradicted by source')
        before=next((x for x in reversed(parsed[:i]) if x['stage']=='fetch'),None)
        next_nmi=next((j for j in range(i+1,len(parsed))
                       if parsed[j]['stage']=='nmi_pending'),len(parsed))
        after=next((x for x in parsed[i+1:next_nmi] if x['stage']=='fetch'),None)
        frames.append({
            'original_NMI_wake_pending_event':pending,
            'original_NMI_before_push_event':e,
            'original_source_wake_incremented_PC':pending['waiting_for_interrupt'],
            'original_source_wake_pc_before':pending['source_guest_PC_context'],
            'original_source_wake_pc_after':e['source_guest_PC_context'],
            'last_selected_original_opcode_fetch_before_NMI':before,
            'first_selected_original_opcode_fetch_after_NMI':after,
            'all_intervening_unselected_opcode_fetches_observed':False})
    return {
        'schema':'ur-qa01-rf076-original-true-fetched-PC-NMI-order/1',
        'source_observed_nmi_before_marker_count':len(nmies),
        'complete_nine_original_NMI_frames_observed':not missing_frames and len(nmies)==9,
        'missing_original_NMI_frames':missing_frames,
        'source_observed_selected_actual_opcode_fetches':sum(x['stage']=='fetch' for x in parsed),
        'source_events':len(parsed), 'source_NMI_brackets':frames,
        'original_opcode_fetches_unselected_sites_observed':False,
        'original_source_incomplete_witness_can_grant_USA_credit':False,
        'original_native_semantically_aligned_NMI_proven':False,
        'original_native_same_binary_source_epoch_proven':False,
        'first_differing_consumed_stack_byte_proven':False,
        'accepted_USA_events':0,
    }


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('original_log',type=Path)
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    report=inspect(args.original_log.read_text(encoding='utf8'))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print('RF076 true source opcode marker sequence retained; cross-guest NMI phase HOLD')


if __name__ == '__main__':
    main()
