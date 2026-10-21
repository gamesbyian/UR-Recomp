"""RF081 same-source sequence-gap audit, not cross-source instruction parity.

Each side's sequence numbers are local and may count different event kinds.
The apparent next opcode marker cannot be interpreted as the first executed
opcode at an equivalent original/native instruction phase.
"""
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile
import json
import re

ARCHIVE_SHA256='df35ddcd8e87bd6664e4e01fe6cbc91fabef6b45292d92564bdab92214bcff37'


def analyze_records(original, native):
    a=original.get('source_NMI_brackets') if type(original) is dict else None
    b=native.get('native_frames') if type(native) is dict else None
    if type(a) is not list or type(b) is not list or len(a)!=9 or len(b)!=9:
        raise ValueError('missing source-local NMI populations')
    rows=[]
    last_original_seq = -1
    last_native_seq = -1
    for o,n in zip(a,b):
        try:
            pending=o['original_NMI_wake_pending_event']
            before=o['original_NMI_before_push_event']
            fetch=o['first_selected_original_opcode_fetch_after_NMI']
            native_first=n['first_observed_target_opcode_after_handler_before_next_NMI']
            original_seq=[pending['source_local_seq'],before['source_local_seq'],fetch['source_local_seq']]
            native_seq=[n['native_entry_seq'],n['native_compiled_handler_return_seq'],native_first['seq']]
            frame=fetch['original_host_frame']
            if (type(frame) is not int or type(native_first['frame']) is not int or
                    type(n['native_NMI_frame_label']) is not int or
                    frame!=native_first['frame'] or frame!=n['native_NMI_frame_label'] or
                    any(type(event.get('original_host_frame')) is not int or
                        event['original_host_frame'] != frame for event in (pending,before)) or
                    # A re-pinned receipt must preserve original local wake PC/stack identity.
                    o.get('original_source_wake_incremented_PC') is not False or
                    o.get('original_source_wake_pc_before') != fetch.get('source_guest_PC_context') or
                    o.get('original_source_wake_pc_after') != fetch.get('source_guest_PC_context') or
                    any(event.get('source_guest_PC_context') != fetch.get('source_guest_PC_context')
                        for event in (pending,before)) or
                    any(event.get('source_stack_SP') != fetch.get('source_stack_SP')
                        for event in (pending,before)) or
                    re.fullmatch('[0-9A-F]{4}', fetch.get('source_stack_SP','')) is None or
                    re.fullmatch('[0-9A-F]{6}', fetch.get('source_guest_PC_context','')) is None or
                    re.fullmatch('[0-9A-F]{6}', native_first.get('decoded_guest_opcode_PC','')) is None or
                    any(type(x) is not int for x in original_seq+native_seq) or
                    not(original_seq[0]<original_seq[1]<original_seq[2]) or
                    not(native_seq[0]<native_seq[1]<native_seq[2]) or
                    pending.get('stage') != 'nmi_pending' or
                    before.get('stage') != 'nmi_before' or
                    fetch.get('stage') != 'fetch' or
                    fetch.get('decoded_original_guest_fetch_executed') is not True or
                    pending.get('decoded_original_guest_fetch_executed') is not False or
                    before.get('decoded_original_guest_fetch_executed') is not False or
                    native_first.get('actual_guest_emitter_tier') != 'aot' or
                    o['all_intervening_unselected_opcode_fetches_observed'] is not False or
                    n['original_native_interrupt_instruction_phase_qualified'] is not False or
                    n['scheduler_PC_is_independently_proven_fetched_interrupt_target'] is not False):
                raise ValueError('noncomparable or malformed source-local ordering')
        except (KeyError, TypeError, IndexError) as exc:
            raise ValueError('incomplete NMI event') from exc
        if original_seq[0] <= last_original_seq:
            raise ValueError('reused/nonmonotonic original source-local sequence across frames')
        last_original_seq = original_seq[2]
        if native_seq[0] <= last_native_seq:
            raise ValueError('reused/nonmonotonic native source-local sequence across frames')
        last_native_seq = native_seq[2]
        rows.append({'host_frame_label':frame,
                     'original_pending_to_before_push_seq_gap':original_seq[1]-original_seq[0],
                     'original_before_push_to_selected_fetch_seq_gap':original_seq[2]-original_seq[1],
                     'native_entry_to_compiled_return_seq_gap':native_seq[1]-native_seq[0],
                     'native_return_to_observed_opcode_seq_gap':native_seq[2]-native_seq[1],
                     'unselected_original_fetches_observed':False,
                     'same_instruction_phase_proven':False})
    if [r['host_frame_label'] for r in rows] != list(range(1017,1026)):
        raise ValueError('unexpected RF081 frame population')
    return {'schema':'rf081-nmi-source-local-sequence-gaps/1','rows':rows,
            'original_native_seq_comparable':False,
            'actual_rts_operand_consumption_observed':False,
            'first_causal_divergence_proven':False,'release_gate_credit':0,
            'decision':'HOLD_MISSING_SAME_EPOCH_BUS_OPERANDS'}


def analyze_archive(raw):
    if type(raw) is not bytes or sha256(raw).hexdigest()!=ARCHIVE_SHA256:
        raise ValueError('wrong RF081 archive')
    with ZipFile(BytesIO(raw)) as z:
        if z.testzip() is not None or len(z.namelist())!=len(set(z.namelist())):
            raise ValueError('ambiguous archive')
        return analyze_records(json.loads(z.read('rf076-original-fetch.json')),
                               json.loads(z.read('rf076-native-opcode-vs-scheduler.json')))
