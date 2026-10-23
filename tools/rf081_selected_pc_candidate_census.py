#!/usr/bin/env python3
"""Exact RF081 selected-PC candidate census; NEVER a first-divergence verdict.

A selected original fetch after NMI and a native post-return opcode marker
are not guaranteed to be the first executed instruction at the same semantic
phase. The matched host frame label is merely an indexing aid. This audit
preserves that missingness and forbids release or causal promotion.
"""
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile
import json
import re

ARCHIVE_SHA256 = 'df35ddcd8e87bd6664e4e01fe6cbc91fabef6b45292d92564bdab92214bcff37'
ORIGINAL = 'rf076-original-fetch.json'
NATIVE = 'rf076-native-opcode-vs-scheduler.json'
HEX6 = re.compile(r'[0-9A-F]{6}\Z')
HEX2 = re.compile(r'[0-9A-F]{2}\Z')


def classify_records(original, native):
    if type(original) is not dict or type(native) is not dict:
        raise ValueError('invalid RF081 source records')
    a = original.get('source_NMI_brackets')
    b = native.get('native_frames')
    if type(a) is not list or type(b) is not list or len(a) != 9 or len(b) != 9:
        raise ValueError('incomplete nine-frame NMI bracket population')
    if (original.get('original_native_semantically_aligned_NMI_proven') is not False or
            native.get('actual_guest_fetch_at_saved_scheduler_NMI_PC_proven') is not False or
            original.get('first_differing_consumed_stack_byte_proven') is not False or
            native.get('first_differing_consumed_byte_proven') is not False):
        raise ValueError('source qualification status changed; independent review required')
    rows = []
    seen = set()
    for old, new in zip(a, b):
        if type(old) is not dict or type(new) is not dict:
            raise ValueError('invalid NMI bracket entry')
        old_fetch = old.get('first_selected_original_opcode_fetch_after_NMI')
        new_fetch = new.get('first_observed_target_opcode_after_handler_before_next_NMI')
        if type(old_fetch) is not dict or type(new_fetch) is not dict:
            raise ValueError('missing selected source fetch')
        frame = old_fetch.get('original_host_frame')
        if (type(frame) is not int or frame in seen or
                type(new_fetch.get('frame')) is not int or frame != new_fetch['frame'] or
                type(new.get('native_NMI_frame_label')) is not int or frame != new['native_NMI_frame_label']):
            raise ValueError('host frame label mismatch or duplication')
        seen.add(frame)
        original_pc = old_fetch.get('source_guest_PC_context')
        native_pc = new_fetch.get('decoded_guest_opcode_PC')
        if (type(original_pc) is not str or not HEX6.fullmatch(original_pc) or
                type(native_pc) is not str or not HEX6.fullmatch(native_pc) or
                type(old_fetch.get('raw_fetched_opcode_if_fetch')) is not str or
                not HEX2.fullmatch(old_fetch['raw_fetched_opcode_if_fetch']) or
                old_fetch.get('decoded_original_guest_fetch_executed') is not True or
                old_fetch.get('stage') != 'fetch' or
                new_fetch.get('actual_guest_emitter_tier') != 'aot' or
                old.get('all_intervening_unselected_opcode_fetches_observed') is not False or
                new.get('original_native_interrupt_instruction_phase_qualified') is not False):
            raise ValueError('selected fetch evidence not comparable')
        # Sequence numbers are local to each logger. Verify ordering within
        # each provenance stream, never compare their numeric values as
        # equivalent original/native instruction phases.
        original_before = old.get('original_NMI_before_push_event')
        first_seq = original_before.get('source_local_seq') if type(original_before) is dict else None
        selected_seq = old_fetch.get('source_local_seq')
        return_seq = new.get('native_compiled_handler_return_seq')
        native_selected_seq = new_fetch.get('seq')
        if (any(type(v) is not int for v in
                (first_seq, selected_seq, return_seq, native_selected_seq)) or
                first_seq < 0 or return_seq < 0 or
                selected_seq <= first_seq or native_selected_seq <= return_seq):
            raise ValueError('source-local selected marker order invalid')
        rows.append({'host_frame_label':frame,'original_selected_pc':original_pc,
                     'native_observed_pc':native_pc,'selected_pc_equal':original_pc == native_pc,
                     'original_source_local_gap':selected_seq-first_seq,
                     'native_source_local_gap':native_selected_seq-return_seq,
                     'semantic_phase_aligned':False,'actual_rts_operand_pair_observed':False})
    if sorted(seen) != list(range(1017,1026)):
        raise ValueError('unexpected RF081 NMI frame population')
    differing = sum(not r['selected_pc_equal'] for r in rows)
    return {'schema':'rf081-selected-pc-candidate-census/1',
            'selected_pc_mismatch_labels':differing,
            'selected_pc_match_labels':len(rows)-differing,
            'frames':rows,'first_causal_divergence_proven':False,
            'complete_event_equivalence_proven':False,'release_gate_credit':0,
            'decision':'HOLD_SOURCE_PHASE_UNQUALIFIED'}


def census(raw):
    if type(raw) is not bytes or sha256(raw).hexdigest() != ARCHIVE_SHA256:
        raise ValueError('RF081 archive SHA mismatch')
    with ZipFile(BytesIO(raw)) as z:
        if z.testzip() is not None or len(z.namelist()) != len(set(z.namelist())):
            raise ValueError('corrupt/ambiguous RF081 ZIP')
        return classify_records(json.loads(z.read(ORIGINAL)),json.loads(z.read(NATIVE)))
