#!/usr/bin/env python3
"""RF076 producer-side chronology of actual native RF047 emitted opcode markers.

An emitted AOT instruction marker is a guest-executed decoded site if observed
in the real log. This reporter never substitutes a scheduler ring PC, saved
NMI stack PC, stale IPC, or host-frame label for an executed instruction.
RF074's independent scheduler ring verifier remains a separate prerequisite.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TAG = 'QA01RF047NATIVE seq='
RECORD = re.compile(r'QA01RF047NATIVE seq=(\d+) (.*)$')
FIELDS = re.compile(r'([A-Za-z][A-Za-z0-9]*)=([^\s]+)')
FRAMES = tuple(range(1017, 1026))
MARKER_PCS = {0x82D4EE, 0x82D4F0, 0x82D4F2, 0x82D4F4, 0x82D4F5,
              0x8282F0, 0x8282F2, 0x8282F6}
STAGES = ('entry', 'resume_origin', 'after_push', 'compiled_rti', 'handler_return')


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def parse(raw: str) -> list[dict]:
    require('QA01RF047NATIVE_TRUNCATED' not in raw, 'RF047 native event stream truncated')
    events = []
    for line in raw.splitlines():
        if TAG not in line:
            continue
        require(line.count(TAG) == 1, 'RF047 events mixed on a single line')
        match = RECORD.fullmatch(line[line.index(TAG):])
        require(match is not None, 'RF047 record truncated or malformed')
        parts = FIELDS.findall(match.group(2))
        require(parts and ' '.join(f'{k}={v}' for k, v in parts) == match.group(2),
                'RF047 tokens malformed')
        item = dict(parts)
        require(len(parts) == len(item), 'RF047 duplicate keys')
        seq = int(match.group(1))
        require(seq == len(events) + 1, 'RF047 sequence incomplete')
        try:
            frame = int(item['f'])
            master = int(item['master'])
        except (KeyError, ValueError) as exc:
            raise ValueError('RF047 native source frame/master missing') from exc
        require(frame in FRAMES and master >= 0, 'RF047 native event outside bounded clock')
        item['seq'] = seq
        events.append(item)
    require(events, 'RF047 native source event stream absent')
    return events


def inspect(raw: str) -> dict:
    events = parse(raw)
    bounds = []
    for frame in FRAMES:
        stage = [(i, e) for i, e in enumerate(events)
                 if int(e['f']) == frame and e.get('stage') in STAGES]
        require(tuple(e['stage'] for _, e in stage) == STAGES,
                f'RF076 NMI stage bracket incomplete or reordered frame={frame}')
        (entry_idx, entry), (_, origin), (_, push), (_, rti), (return_idx, done) = stage
        require(origin.get('sourceFound') == origin.get('originMatches') == '1',
                f'RF076 unresolved scheduler ring provenance frame={frame}')
        require(origin.get('resume') == entry.get('resume') == push.get('resume')
                == done.get('resume') == origin.get('newPC'),
                f'RF076 scheduler/push identity mismatch frame={frame}')
        require(entry.get('S') == '01F0' and push.get('S') == '01EC'
                and rti.get('S') == done.get('S') == '01F0',
                f'RF076 native NMI stack phase changed frame={frame}')
        bounds.append((frame, entry_idx, return_idx, entry, origin, done))
    opcodes = []
    for i, e in enumerate(events):
        if e.get('stage') != 'opcode':
            continue
        pc = e.get('guestPC', '')
        require(re.fullmatch(r'[0-9A-Fa-f]{6}', pc) is not None
                and int(pc, 16) in MARKER_PCS and e.get('tier') in ('aot', 'interp'),
                'RF076 opcode event missing qualified decoded PC/tier')
        opcodes.append((i, e))
    result = []
    for position, (frame, entry_idx, return_idx, entry, origin, done) in enumerate(bounds):
        next_entry = bounds[position + 1][1] if position + 1 < len(bounds) else len(events)
        prior = [e for i, e in opcodes if i < entry_idx]
        after = [e for i, e in opcodes if return_idx < i < next_entry]
        during = [e for i, e in opcodes if entry_idx < i < return_idx]
        def capture(e):
            return None if e is None else {'seq': e['seq'], 'frame': int(e['f']),
                'native_master': int(e['master']), 'decoded_guest_opcode_PC': e['guestPC'],
                'actual_guest_emitter_tier': e['tier']}
        result.append({
            'native_NMI_frame_label': frame,
            'native_entry_seq': entry['seq'],
            'native_compiled_handler_return_seq': done['seq'],
            'scheduler_saved_resume_PC': origin['resume'],
            'last_observed_target_opcode_before_NMI': capture(prior[-1] if prior else None),
            'NMI_handler_target_opcode_markers': [capture(e) for e in during],
            'first_observed_target_opcode_after_handler_before_next_NMI':
                capture(after[0] if after else None),
            'post_return_target_opcode_marker_population': len(after),
            'scheduler_PC_equals_first_observed_post_return_target_opcode':
                bool(after and int(after[0]['guestPC'], 16) == int(origin['resume'], 16)),
            'original_native_interrupt_instruction_phase_qualified': False,
            'scheduler_PC_is_independently_proven_fetched_interrupt_target': False,
        })
    return {
        'schema': 'ur-qa01-rf076-native-executed-pc-vs-scheduler-chronology/1',
        'native_event_count': len(events),
        'native_opcode_target_event_count': len(opcodes),
        'native_NMI_brackets': len(result),
        'native_frames': result,
        'all_possible_guest_opcode_fetches_traced': False,
        'actual_guest_fetch_at_saved_scheduler_NMI_PC_proven': False,
        'same_semantic_phase_original_native_proven': False,
        'first_differing_consumed_byte_proven': False,
        'accepted_USA_events': 0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('native_log', type=Path)
    ap.add_argument('--out', required=True, type=Path)
    args = ap.parse_args()
    report = inspect(args.native_log.read_text(encoding='utf8'))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print('RF076 actual native decoded target-site chronology observed; cross-guest first divergence HOLD')


if __name__ == '__main__':
    main()
