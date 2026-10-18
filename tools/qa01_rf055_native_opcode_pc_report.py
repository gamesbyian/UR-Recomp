#!/usr/bin/env python3
"""RF055: live decoded native LDA [$63],Y site to original-matched bus and writer.

Reject missing, repeated or truncated identities. The genuine RF054 archive
checks source original, immutable USA inputs, complete SPC receiver sequence,
78 unmasked WRAM checkpoints, next Bowl and SRAM before any conclusion.
"""
from __future__ import annotations
import argparse, hashlib, json, zipfile
from pathlib import Path
import qa01_rf054_native_sound_writer_report as rf054

MARK='QA01RF055NATIVEPC '
BUS=rf054.BUS
WRITER=rf054.TAG
LOG=rf054.MAIN
NEEDED=('seq','frame','pc','opcode','operand','master','A','Y','PB','DB','D',
        'ptr63','ptr64','ptr65','scope')

def inspect(log: str) -> dict:
    if 'QA01RF055NATIVEPC_TRUNCATED' in log:
        raise ValueError('RF055 decoded instruction-site observer truncated')
    lines=log.splitlines()
    markers=[(i,rf054.fields(x)) for i,x in enumerate(lines) if x.startswith(MARK)]
    if not markers:
        raise ValueError('RF055 executed decoded native 82:82F0 not observed')
    for j,(_,v) in enumerate(markers,1):
        if any(k not in v for k in NEEDED):
            raise ValueError('RF055 incomplete native decoded opcode-site record')
        if (int(v['seq'])!=j or int(v['frame'])!=6124 or v['pc']!='8282F0'
                or v['opcode']!='B7' or v['operand']!='63'):
            raise ValueError('RF055 incorrect/gapped decoded PC or opcode record')
        if any(c not in '0123456789ABCDEF' for c in
               v['A']+v['Y']+v['PB']+v['ptr63']+v['ptr64']+v['ptr65']):
            raise ValueError('RF055 malformed native source-site register')
    prior=rf054.inspect(log)
    if prior['genuine_late_D0_63_CPU_writer_pair_count']!=1:
        raise ValueError('RF055 predecessor native writer no longer unique')
    rows=[(i,rf054.fields(x)) for i,x in enumerate(lines) if x.startswith(BUS)]
    read_matches=[(i,r) for i,r in rows if r['kind']=='read8' and
                  r['addr']=='11C774' and r['A']=='630D' and r['Y']=='C774' and
                  r['scope']=='Snd_UploadBlockList_82EF_M1X0']
    if len(read_matches)!=1:
        raise ValueError('RF055 source-matched real native bus read missing/ambiguous')
    bi,br=read_matches[0]
    earlier=[(i,m) for i,m in markers if i<bi]
    if not earlier:
        raise ValueError('RF055 decoded source instruction absent before helper')
    mi,site=earlier[-1]
    if any(mi<i<bi for i,_ in rows) or any(
         mi<i<bi and x.startswith(WRITER) and 'kind=writer ' in x
         for i,x in enumerate(lines)):
        raise ValueError('RF055 competing native helper or writer after opcode marker')
    if (site['A'],site['Y'],site['PB'],site['D'],
        site['ptr63'],site['ptr64'],site['ptr65'],site['scope']) != (
         '630D','C774','82','0000','00','00','11',br['scope']):
        raise ValueError('RF055 decoded opcode registers/pointer disagree')
    if not (0<=int(br['master'])-int(site['master'])<=200):
        raise ValueError('RF055 native decoded opcode→helper interval unqualified')
    writers=prior['native_real_paired_writer_context']
    if br['scope']!=writers[0]['scope'] or
        [w['val'] for w in writers]!=['00D0','0063']:
        raise ValueError('RF055 native read to APU writer scope/payload broken')
    return {
        'schema':'rf055-executed-generated-65816-opcode-site-v1',
        'native_decoded_opcode_execution_count':len(markers),
        'source_decoded_guest_instruction':'82:82F0 B7 LDA [$63],Y',
        'native_executed_instruction_site':site,
        'native_actual_ROM_read8':br,
        'native_site_to_real_bus_master_delta':int(br['master'])-int(site['master']),
        'same_native_scope_real_bus_11c774_and_D0_63_writer':True,
        'actual_generated_opcode_site_executed':True,
        'native_AOT_65816_hardware_PC_register_read':False,
        'cross_emulator_CPU_clock_origin_registered':False,
        'sound_samples_or_full_event_parity_proven':False,
        'independently_accepted_complete_USA_events':0,
    }

def report(case:Path,baseline:Path)->dict:
    prior=rf054.report(case,baseline)
    with zipfile.ZipFile(case) as z:
        log=z.read(LOG).decode('utf8','replace')
    out=inspect(log)
    out['RF054_source_native_operand_and_322_true_SPC_reads']=prior[
       'original_11C774_operand_equals_native_effective_ROM_operand_proven']
    out['RF047_full_original_native_controls_equal']=prior[
       'full_RF047_Zoo_Bowl_SRAM_controls_unchanged']
    if not all((out['RF054_source_native_operand_and_322_true_SPC_reads'],
                out['RF047_full_original_native_controls_equal'])):
        raise ValueError('RF055 source/receiver or full controls failed')
    out['case_sha256']=hashlib.sha256(case.read_bytes()).hexdigest()
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('case',type=Path)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    body=json.dumps(report(a.case,a.baseline),indent=2,sort_keys=True)+'\n'
    if a.out:a.out.write_text(body,encoding='utf8')
    else:print(body,end='')
if __name__=='__main__':main()
