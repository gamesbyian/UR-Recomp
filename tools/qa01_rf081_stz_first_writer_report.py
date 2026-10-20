#!/usr/bin/env python3
"""RF081: strict source-local first common STZ D+$59 writer after NMI.

Consumes one CRC-valid original/native Zoo archive containing real original
S9xSetByte + postdispatch records, genuine native paced byte-write commits
and the independently isolated RF047 sidecar. Never shifts host frames or
subtracts original H/V clock from native master ticks. No QA admission.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

import qa01_rf079_real_bit_bpl_report as rf079
import qa01_rf076_executed_pc_vs_resume as rf076

SCHEMA="ur-qa01-rf081-real-first-common-stz-writer/1"
STAGE_TAG="QA01RF081ORIG "
FRAMES=(1017,1018)

def must(ok,reason):
    if not ok:
        raise ValueError(reason)

def parse(original:str,native:str)->dict:
    must("QA01RF081ORIG_TRUNCATED" not in original,
         "original real STZ writer stream truncated")
    must("QA01RF081NATIVE_STZ_MISSING_WRITE" not in native,
         "native opcode marker had no true paced STZ write")
    # Requires real first BIT/BPL decisions and strict RF047 ordinal stream.
    rf079_witness=rf079.inspect(original,native)
    events=rf076.parse(native)
    original_lines=original.splitlines()
    observed=[]
    for pos,line in enumerate(original_lines):
        if line.startswith(STAGE_TAG):
            row=rf079.fields(line,STAGE_TAG)
            must(int(row.get("seq","0"))==len(observed)+1,
                 "original STZ source ordinal gap/duplicate")
            must(row.get("stage") in ("setbyte_enter","after_stz_opcode") and
                 row.get("phase")=="source_local" and
                 row.get("pc")=="82D4F2" and
                 int(row.get("f","-1")) in FRAMES,
                 "original STZ source label/stage invalid")
            observed.append((pos,row))
    must(observed,"original true STZ setter and completed-opcode records absent")
    rows=[]
    for frame in FRAMES:
        entries=[i for i,line in enumerate(original_lines)
                 if line.startswith(f"QA01RF044ORIGNMI f={frame} ")]
        must(len(entries)==1,"original genuine NMI entry absent/duplicated")
        after=[(i,e) for i,e in observed
               if i>entries[0] and int(e["f"])==frame]
        must(len(after)>=2,"original real post-NMI STZ source event absent")
        (original_set_line,original_set),(original_commit_line,original_commit)=after[:2]
        actual_opcodes=[rf079.fields(line,"QA01RF076ORIGPC ")
                        for line in original_lines[entries[0]+1:original_set_line]
                        if line.startswith("QA01RF076ORIGPC ") and
                        f" f={frame} " in line and
                        "stage=fetch" in line]
        must(bool(actual_opcodes) and
             actual_opcodes[-1].get("actualFetchedPC")=="82D4F2" and
             actual_opcodes[-1].get("fetchedOpcode")=="64",
             "original true fetched STZ 82:D4F2/64 absent before S9xSetByte entry")
        earlier_bpl=[rf079.fields(line,"QA01RF079ORIG ") for line in
                     original_lines[entries[0]+1:original_set_line]
                     if line.startswith("QA01RF079ORIG ") and
                     f" f={frame} " in line and
                     "before=82D4F0 " in line]
        must(earlier_bpl,"original actual post-NMI BPL result before STZ missing")
        original_first_bpl=earlier_bpl[0]
        must(original_first_bpl.get("phase")=="after_real_guest_opcode",
             "original first BPL lacked genuine post-op clock stage")
        ov0=int(original_first_bpl["V"]);oh0=int(original_first_bpl["H"])
        ov1=int(original_set["v"]);oh1=int(original_set["h"])
        original_local_delta=(ov1-ov0)*1364+(oh1-oh0)
        must(original_local_delta>=0,
             "original first BPL to STZ local source clock not monotone")
        must((original_set["stage"],original_commit["stage"])==
             ("setbyte_enter","after_stz_opcode"),
             "original first after-NMI writer ordering invalid")
        d=int(original_set["D"],16)
        addr=int(original_set["addr"],16)
        must(addr==((d+0x59)&0xffff) and int(original_set["value"],16)==0,
             "original STZ actual setter target or written value not D+$59 / zero")
        must(original_commit["D"]==original_set["D"] and
             int(original_commit["addr"],16)==addr and
             int(original_commit["value"],16)==0 and
             original_commit["committed"]=="1",
             "original opcode return did not prove one real committed zero byte")
        must(int(original_set["seq"])+1==int(original_commit["seq"]),
             "original STZ setter-to-commit source ordinal not adjacent")
        original_commit_delta=(int(original_commit["v"])-int(original_set["v"]))*1364+(int(original_commit["h"])-int(original_set["h"]))
        must(original_commit_delta>=0,
             "original STZ setter-to-completion source clock regressed")
        subset=[e for e in events if int(e["f"])==frame]
        interrupt=[i for i,e in enumerate(subset)
                   if e.get("stage")=="handler_return"]
        must(len(interrupt)==1,"native source actual NMI return absent/duplicate")
        post=subset[interrupt[0]+1:]
        native_stz=[(i,e) for i,e in enumerate(post)
                    if e.get("stage")=="stz_real_commit"]
        must(native_stz,"native actual STZ paced writer never returned")
        native_pos,native_write=native_stz[0]
        native_direct_page=int(native_write.get("D","-1"),16)
        native_address=int(native_write.get("addr","-1"),16)
        must(native_direct_page==d and native_address==addr and
             addr<0x2000,
             "original/native first STZ direct page/effective WRAM address differs")
        must(native_write.get("guestPC")=="82D4F2" and
             native_write.get("bank")=="00" and
             int(native_write.get("addr","-1"),16)==
             ((int(native_write.get("D","-1"),16)+0x59)&0xffff) and
             native_write.get("written")=="00" and
             native_write.get("rawAfter")=="00",
             "native true STZ committed value/physical D+$59 target mismatch")
        prior_opcode=next((e for e in reversed(post[:native_pos])
                           if e.get("stage")=="opcode"),None)
        next_opcode=next((e for e in post[native_pos+1:]
                          if e.get("stage")=="opcode"),None)
        must(prior_opcode and prior_opcode.get("tier")=="aot" and
             prior_opcode.get("guestPC")=="82D4F2" and
             next_opcode and next_opcode.get("tier")=="aot" and
             next_opcode.get("guestPC")=="82D4F4",
             "native real paced write not bracketed by actual executed STZ and next opcode")
        prior_bpl=[e for e in post[:native_pos]
                   if e.get("stage")=="bpl_actual_input"]
        must(prior_bpl and int(prior_bpl[0]["seq"])<int(native_write["seq"]),
             "native real first BPL decision did not precede first STZ write")
        must(int(prior_bpl[0]["master"])<=int(prior_opcode["master"])<=
             int(native_write["master"])<=int(next_opcode["master"]),
             "native BPL/STZ commit/next-opcode source master clock regressed")
        native_local_delta=int(native_write["master"])-int(prior_bpl[0]["master"])
        must(native_local_delta>=0,"native BPL pre-op to STZ write local master clock regressed")
        rows.append({
          "source_host_frame_label_only":frame,
          "original_actual_first_STZ_setter":{
              "source_ordinal":int(original_set["seq"]),
              "direct_page":original_set["D"],
              "effective_address":f"{addr:06X}",
              "value_from_actual_S9xSetByte":original_set["value"],
              "source_V":int(original_set["v"]),
              "source_H":int(original_set["h"])},
          "original_true_STZ_dispatch_completed":{
              "source_ordinal":int(original_commit["seq"]),
              "host_physical_RAM_mirror":original_commit["value"],
              "source_V":int(original_commit["v"]),
              "source_H":int(original_commit["h"])},
          "native_true_paced_STZ_committed":{
              "source_ordinal":int(native_write["seq"]),
              "direct_page":native_write["D"],
              "physical_address":native_write["bank"]+native_write["addr"],
              "value_from_actual_cpu_write8_paced":native_write["written"],
              "host_physical_RAM_mirror":native_write["rawAfter"],
              "source_master_cycle":int(native_write["master"])},
          "original_local_vh_ticks_first_BPL_post_execution_to_true_setbyte_entry":
              original_local_delta,
          "native_local_master_ticks_first_BPL_pre_execution_to_true_paced_commit":
              native_local_delta,
          "clock_deltas_have_different_start_end_semantic_stages":True,
          "cross_emulator_subtraction_valid":False,
          "same_emulated_STZ_opcode_and_value":True,
          "same_intrastage_guest_clock_proven":False,
          "post_STZ_gameplay_causality_proven":False
        })
    return {
      "schema":SCHEMA,
      "rf079_real_branch_contrast_precondition":rf079_witness["schema"],
      "strict_native_source_event_count":len(events),
      "real_original_source_STZ_observer_rows":len(observed),
      "frames":rows,
      "real_common_direct_page_STZ_write_count_qualified":len(rows),
      "same_guest_operands_and_committed_zero_values_proven_locally":True,
      "equivalent_original_native_instruction_phase_proven":False,
      "comparable_elapsed_original_native_cycles_proven":False,
      "first_persistent_gameplay_state_divergence_proven":False,
      "accepted_USA_events":0
    }

def inspect_archive(case_zip:Path)->dict:
    case_data=case_zip.read_bytes()
    with zipfile.ZipFile(case_zip) as z:
        must(z.testzip() is None,"case ZIP member CRC mismatch")
        for path in (rf079.ORIG,rf079.NATIVE,rf079.STRICT_SIDECAR):
            must(path in z.namelist(),"source-qualified original/native required file absent")
        orig=z.read(rf079.ORIG)
        stderr=z.read(rf079.NATIVE)
        side=z.read(rf079.STRICT_SIDECAR)
    # Reuse the preexisting strict raw-vs-dedicated-ordinal qualification.
    prev=rf079.case_archive(case_zip)
    report=parse(orig.decode(),side.decode())
    report.update({
       "raw_native_stderr_RF047_ordinal_continuity_assumed":False,
       "native_strict_sidecar_sha256":hashlib.sha256(side).hexdigest(),
       "native_raw_stderr_sha256":hashlib.sha256(stderr).hexdigest(),
       "original_true_log_sha256":hashlib.sha256(orig).hexdigest(),
       "case_archive_sha256":hashlib.sha256(case_data).hexdigest(),
       "previous_two_frame_real_BIT_BPL_read_report_qualified":
           prev["source_two_frame_brackets_compared"]==2
    })
    return report

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case-zip",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    result=inspect_archive(args.case_zip)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("RF081 original/native real STZ source writers qualified; comparable clocks and gameplay cause HOLD")

if __name__=="__main__":
    main()
