#!/usr/bin/env python3
"""RF077 source-local original/native NMI RTI consumers in ONE case ZIP.

Compares observed returned operands only within each guest's own NMI phase.
Never equates a host-frame label with aligned guest instruction phase, or
skipped native PC/PB reads with a proven gameplay-causal divergence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ORIG = 'work/zoom-zoo/replay/reference.log'
NATIVE = 'work/zoom-zoo/replay/native.log'
FRAMES = tuple(range(1017, 1026))
HEX = re.compile(r'^[0-9a-fA-F]+$')
ORIG_NMI = 'QA01RF044ORIGNMI '
ORIG_GET = 'QA01RF066ORIGCONSUMED '
NAT_TAG = 'QA01RF047NATIVE seq='
STAGES = ('entry', 'resume_origin', 'after_push', 'compiled_rti', 'handler_return')

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def fields(line, tag):
    require(line.startswith(tag), 'source label not at row start: '+tag)
    body = line[len(tag):]
    pairs = re.findall(r'([A-Za-z][A-Za-z0-9]*)=([^\s]+)', body)
    require(bool(pairs) and ' '.join(f'{k}={v}' for k,v in pairs)==body,
            'malformed source fields: '+tag)
    result = dict(pairs)
    require(len(result)==len(pairs), 'duplicate source field: '+tag)
    return result

def parse(original, native):
    for text, tag in ((original, 'QA01RF044ORIGBUS_TRUNCATED'),
                      (original, 'QA01RF066ORIGCONSUMED_TRUNCATED'),
                      (native, 'QA01RF047NATIVE_TRUNCATED')):
        require(tag not in text, 'source stream truncated: '+tag)
    orig_lines = original.splitlines()
    nat_events = []
    for line in native.splitlines():
        if NAT_TAG not in line:
            continue
        require(line.count(NAT_TAG)==1, 'native event double-spliced')
        e = fields(line[line.index(NAT_TAG):], 'QA01RF047NATIVE ')
        require(int(e.get('seq','0'))==len(nat_events)+1,
                'native source ordinal gap/reorder')
        nat_events.append(e)
    require(nat_events, 'native source events absent')
    orig_nmis = []
    for pos, line in enumerate(orig_lines):
        if not line.startswith(ORIG_NMI):
            continue
        row = fields(line, ORIG_NMI)
        if int(row['f']) in FRAMES:
            orig_nmis.append((pos, row))
    require(tuple(int(x['f']) for _,x in orig_nmis)==FRAMES,
            'nine original true NMI entries missing/duplicate/reordered')
    rows = []
    for number, ((at, orig)) in enumerate(orig_nmis):
        frame = FRAMES[number]
        limit = orig_nmis[number+1][0] if number+1 < len(FRAMES) else len(orig_lines)
        pulls = [fields(line, ORIG_GET) for line in orig_lines[at+1:limit]
                 if line.startswith(ORIG_GET)]
        require(len(pulls)>=3, f'original actual RTI getter absent frame={frame}')
        pulls = pulls[:3]
        require([(x.get('kind'),x.get('base'),x.get('width')) for x in pulls] ==
                [('pullB','01ED','1'), ('pullW','01EE','2'), ('pullB','01F0','1')],
                f'original stack RTI getter sequence changed frame={frame}')
        require(all(x.get('f')==str(frame) and
                    x.get('phase')=='post_real_stack_getter_return' for x in pulls),
                'original post-GET operand qualification missing')
        require(all(int(pulls[i+1]['seq'])>int(pulls[i]['seq']) for i in (0,1)),
                'original stack getter ordinal did not advance')
        stack = orig.get('new','')
        require(len(stack)==10 and bool(HEX.fullmatch(stack)),
                'original real NMI stack snapshot missing')
        status = int(stack[:2],16)
        pc = int(stack[2:4],16) | (int(stack[4:6],16)<<8)
        bank = int(stack[6:8],16)
        require([int(x['returned'],16) for x in pulls]==[status, pc, bank] and
                int(orig['pc'],16)==(bank<<16)|pc and
                orig.get('S0')=='01F0' and orig.get('S1')=='01EC',
                f'original consumed P/PC/PB did not match real push frame={frame}')
        nat = [x for x in nat_events if x.get('f')==str(frame)]
        stages = [(i,x) for i,x in enumerate(nat) if x.get('stage') in STAGES]
        require(tuple(x['stage'] for i,x in stages)==STAGES,
                f'native complete NMI bracket missing frame={frame}')
        (_,entry),(_,origin),(_,push),(_,rti),(_,done) = stages
        require(origin.get('sourceFound')==origin.get('originMatches')=='1' and
                origin.get('phase')=='before_real_interrupt_push' and
                origin.get('kind') in ('set','restore') and
                origin.get('resume')==entry.get('resume')==push.get('resume')==done.get('resume'),
                f'native source scheduler provenance not bound to push frame={frame}')
        require(entry.get('S')=='01F0' and push.get('S')=='01EC' and
                rti.get('S')==done.get('S')=='01F0',
                f'native compiled RTI SP incorrect frame={frame}')
        ns = push.get('stack','')
        require(len(ns)==8 and bool(HEX.fullmatch(ns)),
                'native physical after-push NMI stack missing')
        reads = [x for x in nat[stages[2][0]+1:stages[3][0]]
                 if x.get('stage')=='read']
        require(len(reads)==1 and reads[0].get('addr')=='01ED' and
                reads[0].get('width')=='1' and
                int(reads[0].get('value','-1'),16)==int(ns[:2],16),
                f'native compiled RTI status real getter mismatch frame={frame}')
        rows.append({
            'source_host_frame_label':frame,
            'original_saved_PC':f'{bank:02X}{pc:04X}',
            'native_scheduler_saved_PC':origin['resume'],
            'original_actual_returned_status':f'{status:02X}',
            'original_actual_returned_PC':f'{pc:04X}',
            'original_actual_returned_PB':f'{bank:02X}',
            'original_real_getter_return_sequences':[int(x['seq']) for x in pulls],
            'native_actual_status_read_sequence':int(reads[0]['seq']),
            'native_compiled_rti_sequence':int(rti['seq']),
            'native_actual_saved_PC_PB_getter_count_inside_NMI_bracket':0,
            'saved_PC_differs_between_source_local_NMI_phases':
                int(origin['resume'],16)!=(bank<<16|pc),
            'same_guest_instruction_phase_proven':False,
        })
    return {
        'schema':'ur-qa01-rf077-same-case-actual-NMI-RTI-consumers/1',
        'original_nmi_stack_getter_brackets':len(rows),
        'native_compiled_status_only_brackets':len(rows),
        'actual_stack_saved_PC_value_differs_on_same_host_label_count':
            sum(x['saved_PC_differs_between_source_local_NMI_phases'] for x in rows),
        'different_original_and_native_RTI_memory_consumption_proven_within_own_guest_phase':True,
        'first_causally_significant_gameplay_divergence_proven':False,
        'same_original_native_interrupt_instruction_phase_proven':False,
        'source_binary_epoch_authenticated_by_external_receipts_only':True,
        'actual_original_fetch_PC_proven_by_this_report':False,
        'accepted_USA_events':0,'per_frame':rows,
    }

def inspect(archive):
    raw = archive.read_bytes()
    with zipfile.ZipFile(archive) as z:
        require(z.testzip() is None, 'corrupted ZIP member CRC')
        require(ORIG in z.namelist() and NATIVE in z.namelist(),
                'real original/native one-case raw logs missing')
        orig, nat = z.read(ORIG), z.read(NATIVE)
    report = parse(orig.decode('utf-8'), nat.decode('utf-8'))
    report.update({
        'case_zip_sha256':hashlib.sha256(raw).hexdigest(),
        'original_raw_log_sha256':hashlib.sha256(orig).hexdigest(),
        'native_raw_log_sha256':hashlib.sha256(nat).hexdigest(),
    })
    return report

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--case-zip',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    opts = ap.parse_args()
    result = inspect(opts.case_zip)
    opts.out.parent.mkdir(parents=True,exist_ok=True)
    opts.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('RF077 genuine status/PC/PB RTI consumption qualified; cross-guest causality HOLD')

if __name__=='__main__':
    main()
