#!/usr/bin/env python3
"""RF050 exact original late S9xAPUWritePort receipt, no clock conflation.

Reuses real RF049 original opcode/STA and RF048 native DP63+DP65 evidence.
Late original APU records are selected by observed source age/V/H, NOT ICPU.Frame
(which is local to a different Snes9x translation unit). An identical D0/63
pair elsewhere in source/native prefix cannot be assigned to this opcode.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from collections import Counter
import hashlib
import json
import zipfile
import qa01_rf049_sound_operand_report as rf049

TAG="QA01RF050ORIGAPU "
REF="work/zoom-zoo/replay/reference.log"
def parse(line:str)->dict:
    fields={}
    for token in line.split()[1:]:
        if "=" in token:
            k,v=token.split("=",1)
            if not k or k in fields:raise ValueError("duplicate/missing RF050 log key")
            fields[k]=v
    return fields

def analyze(original:str)->dict:
    if "QA01RF050ORIGAPU_TRUNCATED" in original:
        raise ValueError("late original APU publication recorder truncated")
    rows=[parse(line) for line in original.splitlines() if line.startswith(TAG)]
    for i,row in enumerate(rows,1):
        for k in ("seq","age","v","h","port","val"):
            if k not in row:raise ValueError("RF050 real original APU record missing field "+k)
        if int(row["seq"])!=i:
            raise ValueError("RF050 late original APU sequence lost/duplicated")
        if int(row["v"])!=159 or not 850<=int(row["h"])<=1200:
            raise ValueError("RF050 real original APU CPU beam gate invalid")
        if not 104200000<=int(row["age"])<=106500000:
            raise ValueError("RF050 original SPC-age gate invalid")
        if row["port"] not in ("2","3") or len(row["val"])!=2 or any(
            c not in "0123456789ABCDEF" for c in row["val"]):
            raise ValueError("RF050 original CPU port/value invalid")
    if any(int(rows[i+1]["age"])<int(rows[i]["age"]) for i in range(len(rows)-1)):
        raise ValueError("RF050 source original SPC age regressed")
    pairs=[]
    for i in range(len(rows)-1):
        first,second=rows[i],rows[i+1]
        if (first["port"],first["val"],second["port"],second["val"])!=("3","D0","2","63"):
            continue
        pairs.append({
            "sequence":[int(first["seq"]),int(second["seq"])],
            "source_spc_ages":[int(first["age"]),int(second["age"])],
            "source_cpu_beams":[int(first["h"]),int(second["h"])],
            "between_port_publications_source_spc_ticks":
                int(second["age"])-int(first["age"]),
            "source_publication_real_S9xAPUWritePort":True,
            "source_frame_6124_attested_by_APU_hook":False,
        })
    return {
        "schema":"rf050-late-source-port-publication-v1",
        "late_original_real_apu_port_rows":len(rows),
        "late_original_source_apu_age_range":
            [int(rows[0]["age"]),int(rows[-1]["age"])] if rows else None,
        "late_original_port_record_counts":
            {p:sum(row["port"]==p for row in rows) for p in ("2","3")},
        "source_original_V159_H850_to_H1200_APU_candidates":rows[:100],
        "late_source_real_D0_63_adjacent_port_pairs":pairs,
        "source_original_CPU_frame_not_available_inside_apu_cpp":True,
        "identical_port_bytes_alone_dont_link_to_RF049_LDA":True,
        "source_native_clock_axes_registered":False,
        "original_vs_native_SPC_receiver_parity_proven":False,
        "USA_complete_events_admitted":0,
    }

def source_instruction_publication_link(original:str)->dict:
    """Bind real APU records only when within the executed LDA->STA log segment.

    RF050 runs in S9xAPUWritePort after the real port write; RF049 prints
    after the same 65816 opcode. No ICPU.Frame variable is imported into
    apu.cpp. The authoritative original stream's contiguous instruction
    ordering is an independent linkage discriminator.
    """
    lines=original.splitlines()
    ld=[(i,parse(line)) for i,line in enumerate(lines)
        if line.startswith("QA01RF049LDA ") and "ea=11C774" in line]
    st=[(i,parse(line)) for i,line in enumerate(lines)
        if line.startswith("QA01RF049STA ") and "target=1" in line]
    if len(ld)!=1 or len(st)!=2 or not(ld[0][0]<st[0][0]<st[1][0]):
        raise ValueError("RF050 source LDA/STA instruction-boundary identity missing")
    windows=[(ld[0][0],st[0][0],3,"D0"),(st[0][0],st[1][0],2,"63")]
    events=[]
    for before,after,port,value in windows:
        rows=[(i,parse(line)) for i,line in enumerate(lines[before+1:after],before+1)
              if line.startswith(TAG)]
        if len(rows)>1:raise ValueError("multiple source APU publications between one original opcode pair")
        if not rows:
            events.append({"preceding_source_log_line":before,
                           "source_STA_completion_log_line":after,
                           "real_APU_publication_captured_inside_instruction":False,
                           "missing_coverage_is_not_no_publication":True})
            continue
        line_idx,row=rows[0]
        if (row.get("port"),row.get("val"))!=(str(port),value):
            raise ValueError("intervening original APU port/value does not match actual STA")
        events.append({"preceding_source_log_line":before,
                       "real_original_APU_publication_log_line":line_idx,
                       "source_STA_completion_log_line":after,
                       "real_APU_publication_captured_inside_instruction":True,
                       "source_SPC_age":int(row["age"]),
                       "source_CPU_V":int(row["v"]),
                       "source_CPU_H":int(row["h"]),
                       "port":port,"value":value})
    return {
       "late_original_11C774_instruction":ld[0][1],
       "late_original_STA_source_row_numbers":[x[0] for x in st],
       "source_original_STA_to_actual_APU_publications":events,
       "both_real_port_publications_inside_original_instruction_segments":
           all(x["real_APU_publication_captured_inside_instruction"] for x in events),
       "native_host_clock_registered":False,
       "SPC_receiver_ack_for_late_original_publication_proven":False,
    }

def report(case:Path,rf047_baseline:Path)->dict:
    with zipfile.ZipFile(case) as z:
        orig=z.read(REF).decode("utf8","replace")
    audit=analyze(orig)
    audit["original_instruction_to_live_APU_source_order"]=source_instruction_publication_link(orig)
    prior=rf049.report(case,rf047_baseline)
    audit["source_full_operand_census"]={
        k:prior[k] for k in
        ("genuine_original_82F0_LDA_count","exact_original_full_operand_13C774",
         "exact_original_full_operand_13D0B4",
         "source_true_LDA_followed_by_STA_2143_and_STA_2142",
         "source_vs_native_host_epoch_registered")
    }
    audit["all_RF047_original_native_unmasked_Zoo_Bowl_SRAM_controls_unchanged"]=bool(
        prior["source_guest_controls"].get("unchanged_RF047_Zoo_Bowl_and_full_WM_controls"))
    audit["case_zip_sha256"]=hashlib.sha256(case.read_bytes()).hexdigest()
    audit["RF047_baseline_zip_sha256"]=hashlib.sha256(rf047_baseline.read_bytes()).hexdigest()
    audit["frozen_research_source_sha"]=prior["source_guest_controls"]["case_source_sha"]
    return audit

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case",type=Path)
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    text=json.dumps(report(a.case,a.baseline),indent=2,sort_keys=True)+"\n"
    if a.output:a.output.write_text(text,encoding="utf8")
    else:print(text,end="")
if __name__=="__main__":main()
