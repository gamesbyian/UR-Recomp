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

def report(case:Path,rf047_baseline:Path)->dict:
    with zipfile.ZipFile(case) as z:
        orig=z.read(REF).decode("utf8","replace")
    audit=analyze(orig)
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
