#!/usr/bin/env python3
"""RF055: fail-closed SPC receiver read-stage cadence of authentic RF052 Zoo.

Only analyzes saved original/native true SPC PC/port/value reads and immutable
RF047 controls through merged RF053. No guest replay, emulator phase assumption,
queue change or new gameplay approval.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,zipfile
from pathlib import Path
import qa01_rf053_real_spc_receiver_sequence_parity as rf053

def rows(src: str, tag: str) -> list[dict]:
    return [rf053.fields(line) for line in src.splitlines() if line.startswith(tag)]

def precise_cadence(original: list[dict], native: list[dict]) -> dict:
    if len(original)!=322 or len(native)!=322:
        raise ValueError('RF055 receiver cadence must be exactly 322 actual matched reads')
    source_ages=[int(x['age']) for x in original]
    native_ages=[int(x['clock']) for x in native]
    source_minus_native=[a-b for a,b in zip(source_ages,native_ages)]
    cycles=[]
    for q in range(107):
        j=q*3
        group=original[j:j+4]
        native_group=native[j:j+4]
        if [(r['spcpc'],r['port']) for r in group]!=[
            ('1521','2'),('1525','3'),('1527','2'),('1521','2')]:
            raise ValueError('RF055 source receiver cycle PC/port order diverged')
        if [(r['pc'],r['port']) for r in native_group]!=[
            ('1521','2'),('1525','3'),('1527','2'),('1521','2')]:
            raise ValueError('RF055 native receiver cycle PC/port order diverged')
        if [(x['port'],x['val']) for x in group]!=[
            (x['port'],x['val']) for x in native_group]:
            raise ValueError('RF055 original/native receiver values diverged')
        x=[source_ages[k+1]-source_ages[k] for k in range(j,j+3)]
        y=[native_ages[k+1]-native_ages[k] for k in range(j,j+3)]
        if x != [5,3,18] or y != [5,4,17]:
            raise ValueError('RF055 observed SPC receiver stage interval changed')
        if sum(x)!=26 or sum(y)!=26:
            raise ValueError('RF055 packet cycle no longer identical in local ticks')
        if source_minus_native[j:j+4]!=[23,23,22,23]:
            raise ValueError('RF055 original/native stage offset is not 23/23/22')
        cycles.append((tuple(x),tuple(y)))
    assert len(cycles)==107
    pc_phase=collections.defaultdict(collections.Counter)
    for a,b,d in zip(original,native,source_minus_native):
        if (a['spcpc'],a['port'],a['val'])!=(b['pc'],b['port'],b['val']):
            raise ValueError('RF055 original/native executed SPC read values/PC differ')
        pc_phase[a['spcpc']][d]+=1
    expected={'1521':{23:108},'1525':{23:107},'1527':{22:107}}
    if {k:dict(v) for k,v in pc_phase.items()}!=expected:
        raise ValueError('RF055 actual read-PC phase histogram changed')
    return {
      'schema':'rf055-true-spc700-receiver-instruction-stage-cadence-v1',
      'executed_source_SPC_receiver_reads':len(original),
      'executed_native_SPC_receiver_reads_matched':len(native),
      'verified_complete_three_read_cycles':len(cycles),
      'source_actual_read_PC_port_order':['1521/F6','1525/F7','1527/F6'],
      'source_inter_read_local_SPC_cycle_intervals':[5,3,18],
      'native_inter_read_local_SPC_cycle_intervals':[5,4,17],
      'source_complete_three_read_packet_local_cycles':26,
      'native_complete_three_read_packet_local_cycles':26,
      'source_minus_native_read_stage_offset_by_PC':{
          k:{str(offset):count for offset,count in sorted(hist.items())}
          for k,hist in sorted(pc_phase.items())},
      'source_minus_native_322_read_offsets_exact_period_23_23_22':True,
      'identical_read_PC_port_value_for_each_executed_read':True,
      'per_loop_local_tick_drift_observed':False,
      'equal_CPU_clock_origins_or_global_phase_proven':False,
      'SMP_opcode_bus_access_instants_or_audio_PCM_parity_proven':False,
      'complete_USA_event_credit':0
    }

def case_report(case:Path,baseline:Path)->dict:
    prev=rf053.one_case(case,baseline)
    with zipfile.ZipFile(case) as z:
        source=z.read(rf053.ORIG).decode('utf8','replace')
        native=z.read(rf053.NATIVE).decode('utf8','replace')
    aligned=rf053.exact_alignment(source,native,expected_count=322)
    original=rows(source,rf053.SOURCE_TAG)
    reads=[r for r in rows(native,rf053.NATIVE_TAG) if r['kind']=='spc-read']
    pos=aligned['native_read_window_zero_based_match_start']
    out=precise_cadence(original,reads[pos:pos+322])
    out['native_true_receiver_alignment_unique_start']=pos
    out['native_true_receiver_window_size']=len(reads)
    out['RF047_all_full_Zoo_Bowl_SRAM_controls_equal']=prev[
        'all_RF047_Zoo_Bowl_terminal_producer_controls_equal']
    out['frozen_original_native_input_provenance_equal']=prev[
        'USA_source_ROM_movie_input_SRAM_identical_to_RF047']
    out['original_native_case_zip_sha256']=hashlib.sha256(case.read_bytes()).hexdigest()
    return out

def compare_cases(a:Path,b:Path,baseline:Path)->dict:
    first=case_report(a,baseline)
    second=case_report(b,baseline)
    keys=('verified_complete_three_read_cycles',
          'source_inter_read_local_SPC_cycle_intervals',
          'native_inter_read_local_SPC_cycle_intervals',
          'source_minus_native_read_stage_offset_by_PC',
          'source_minus_native_322_read_offsets_exact_period_23_23_22')
    if any(first[k]!=second[k] for k in keys):
        raise ValueError('RF055 independent RF052 source/native replay receiver cadence changed')
    return {'schema':'rf055-two-frozen-original-native-replays-same-SPC-receiver-cadence-v1',
            'case_A':first,'case_B':second,
            'two_independent_genuine_replays_replicate_107_identical_26_tick_read_cycles':True,
            'complete_USA_events_accepted':0}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('case',type=Path)
    p.add_argument('--baseline',required=True,type=Path)
    p.add_argument('--compare',type=Path)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    value=compare_cases(a.case,a.compare,a.baseline) if a.compare else case_report(a.case,a.baseline)
    s=json.dumps(value,sort_keys=True,indent=2)+'\n'
    if a.out:a.out.write_text(s,encoding='utf8')
    else:print(s,end='')
if __name__=='__main__':main()
