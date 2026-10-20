#!/usr/bin/env python3
"""RF079 actual existing BIT read and BPL input from one real Zoo source epoch.

Read only source-emitted original post-op observations and native paced-bus
return/decoded-opcode records. NO fabricated original-native clock alignment,
no inferred memory read from a saved stack byte, no release credit.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

import qa01_rf076_executed_pc_vs_resume as native_rf076

ORIG='work/zoom-zoo/replay/reference.log'
NATIVE='work/zoom-zoo/replay/native.log'
STRICT_SIDECAR='rf079-native-rf047-strict.log'
ORIG_TAG='QA01RF079ORIG '
FRAMES=(1017,1018)

def require(ok,reason):
    if not ok:
        raise ValueError(reason)

def fields(line,tag):
    require(line.startswith(tag),'source label not at row start')
    body=line[len(tag):]
    pairs=re.findall(r'([A-Za-z][A-Za-z0-9]*)=([^\s]+)',body)
    require(bool(pairs) and
            ' '.join(f'{k}={v}' for k,v in pairs)==body and
            len(dict(pairs))==len(pairs),'source row malformed')
    return dict(pairs)

def inspect(original,native):
    require('QA01RF079ORIG_TRUNCATED' not in original,
            'original post-op source stream overflow')
    nat=native_rf076.parse(native)
    orig=original.splitlines()
    events=[]
    for index,line in enumerate(orig):
        if not line.startswith(ORIG_TAG):
            continue
        v=fields(line,ORIG_TAG)
        require(int(v.get('seq','0'))==len(events)+1,
                'original BIT/BPL ordinal incomplete')
        fr=int(v['f'])
        pc=int(v['before'],16); op=int(v['opcode'],16)
        m=int(v['M']);n=int(v['N']);byte=int(v['Nbyte'],16)
        require(fr in FRAMES and v.get('phase')=='after_real_guest_opcode' and
                (pc,op) in ((0x82D4EE,0x24),(0x82D4F0,0x10)) and
                m==1 and n in (0,1) and n==int(bool(byte&128)),
                'original post-op true M=1 operand or negative flag changed')
        if op==0x10:
            expected=0x82D4EE if n==0 else 0x82D4F2
            require(int(v['after'],16)==expected,
                    'actual original BPL branch landing contradicts N flag')
        events.append((index,v))
    require(events,'no actual original two-frame post-BIT/BPL source evidence')
    out=[]
    for frame in FRAMES:
        original_nmi=[i for i,line in enumerate(orig)
                      if line.startswith(f'QA01RF044ORIGNMI f={frame} ')]
        require(len(original_nmi)==1,'original real frame NMI missing/duplicated')
        orig_after=[e for i,e in events if i>original_nmi[0] and int(e['f'])==frame]
        require(orig_after and orig_after[0]['before'] in ('82D4EE','82D4F0'),
                'original first source-local wait-loop operation after true NMI missing')
        first_bpl=next((e for e in orig_after if e['before']=='82D4F0'),None)
        require(first_bpl is not None,'original post-NMI actual BPL decision absent')
        ns=[e for e in nat if int(e['f'])==frame]
        returns=[i for i,e in enumerate(ns) if e.get('stage')=='handler_return']
        require(len(returns)==1,'native true interrupt handler-return missing/duplicated')
        post=ns[returns[0]+1:]
        candidates=[(i,e) for i,e in enumerate(post)
                    if e.get('stage') in ('bit_real_return','bpl_actual_input')]
        require(bool(candidates),'native real BIT/BPL post-NMI source events missing')
        (readpos,read)=next(((i,e) for i,e in candidates if e['stage']=='bit_real_return'),
                            (-1,{}))
        (bplpos,bpl)=next(((i,e) for i,e in candidates if e['stage']=='bpl_actual_input'),
                          (-1,{}))
        require(readpos>=0 and bplpos>readpos and
                read.get('guestPC')=='82D4EE' and
                bpl.get('guestPC')=='82D4F0' and bpl.get('bitReadSeen')=='1',
                'native real BIT return to next BPL source ordinal join broken')
        actual_addr=int(read.get('addr','-1'),16)
        d=int(read.get('D','-1'),16)
        value=int(read.get('value','-1'),16)
        neg=int(bpl.get('N','-1'))
        require(0<=d<=0xffff and 0<=value<=255 and
                actual_addr==((d+0x57)&0xffff) and
                bpl.get('D')==read.get('D') and neg==int(bool(value&128)),
                'native paced bus actual returned value contradicts BPL N flag')
        before_read=next((e for e in reversed(post[:readpos])
                          if e.get('stage')=='opcode'),None)
        before_bpl=next((e for e in reversed(post[:bplpos])
                         if e.get('stage')=='opcode'),None)
        require(before_read and before_read.get('tier')=='aot' and
                before_read.get('guestPC')=='82D4EE' and
                before_bpl and before_bpl.get('tier')=='aot' and
                before_bpl.get('guestPC')=='82D4F0',
                'native BIT real read or BPL N marker lacked actually executed AOT PC')
        out.append({
            'source_host_frame_label':frame,
            'original_first_selected_post_NMI_opcode_PC':orig_after[0]['before'],
            'original_first_actual_BPL_negative_flag':int(first_bpl['N']),
            'original_first_actual_BPL_guest_landing_PC':first_bpl['after'],
            'native_first_actual_post_NMI_BIT_effective_address':f'{actual_addr:04X}',
            'native_first_actual_post_NMI_BIT_returned_byte':f'{value:02X}',
            'native_first_actual_post_NMI_BIT_returned_byte_negative':neg,
            'native_first_BPL_negative_flag_equal_original':neg==int(first_bpl['N']),
            'native_BPL_take_inferred_from_real_negative_flag':neg==0,
            'same_original_native_guest_instruction_phase_proven':False,
            'source_clock_rebased':False,
        })
    return {
      'schema':'ur-qa01-rf079-real-BIT-return-and-BPL-N-contrast/1',
      'real_original_source_post_op_events':len(events),
      'real_native_qualifying_source_events':len(nat),
      'source_two_frame_brackets_compared':len(out),
      'compared_frames':[1017,1018],
      'real_BPL_N_input_disagreement_count':
          sum(not x['native_first_BPL_negative_flag_equal_original'] for x in out),
      'first_causally_significant_gameplay_divergence_proven':False,
      'semantic_original_native_clock_alignment_proven':False,
      'accepted_USA_events':0,'frames':out,
    }

def case_archive(path):
    raw=path.read_bytes()
    with zipfile.ZipFile(path) as z:
        require(z.testzip() is None,'ZIP CRC failed')
        require(ORIG in z.namelist() and NATIVE in z.namelist(),
                'same-case original/native actual logs absent')
        require(STRICT_SIDECAR in z.namelist(),
                'strict native event sidecar absent: cannot repair mixed stderr after execution')
        orig=z.read(ORIG)
        nat_stderr=z.read(NATIVE)
        nat=z.read(STRICT_SIDECAR)
    strict_lines=nat.decode('utf-8').splitlines()
    require(bool(strict_lines) and
            all(line.startswith('QA01RF047NATIVE seq=') for line in strict_lines),
            'RF047 sidecar contains a non-source line or overflow')
    # A dedicated source stream must never silently erase the separate
    # historical raw-stderr source-integrity failure. Match only complete
    # raw lines byte-for-byte against the isolated source sequence; never
    # extract embedded RF047 records from other logger fragments.
    side_by_seq = {}
    for i, line in enumerate(strict_lines, 1):
        require(line.startswith(f'QA01RF047NATIVE seq={i} '),
                'native strict sidecar sequence not contiguous')
        side_by_seq[i] = line
    raw_matched = 0
    raw_malformed = 0
    for line in nat_stderr.decode('utf-8').splitlines():
        if not line.startswith('QA01RF047NATIVE seq='):
            continue
        match = re.match(r'QA01RF047NATIVE seq=(\\d+) ', line)
        if match is None or int(match.group(1)) not in side_by_seq:
            raw_malformed += 1
        elif line == side_by_seq[int(match.group(1))]:
            raw_matched += 1
        else:
            raw_malformed += 1
    result=inspect(orig.decode('utf-8'),nat.decode('utf-8'))
    result.update({
        'native_raw_stderr_byte_exact_RF047_source_events':raw_matched,
        'native_raw_stderr_malformed_or_mismatched_RF047_prefix_rows':raw_malformed,
        'native_raw_stderr_missing_complete_RF047_source_events':
            len(side_by_seq)-raw_matched,
        'case_zip_sha256':hashlib.sha256(raw).hexdigest(),
        'original_log_sha256':hashlib.sha256(orig).hexdigest(),
        'native_raw_stderr_sha256':hashlib.sha256(nat_stderr).hexdigest(),
        'native_strict_RF047_sidecar_sha256':hashlib.sha256(nat).hexdigest(),
        'native_RF047_dedicated_source_ordinals_verified':True,
        'native_raw_stderr_separately_preserved_unchanged':True,
        'native_stderr_full_RF047_source_continuity_claimed':False
    })
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case-zip',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    result=case_archive(a.case_zip)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('RF079 actual BIT bytes and BPL N compared in two source clocks; gameplay cause HOLD')
if __name__=='__main__':
    main()
