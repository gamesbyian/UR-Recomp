#!/usr/bin/env python3
"""RF051: source-identity-bound original late SPC receiver/native guest window.

Neither source SPC age nor Snes9x CPU frame is equated to Baldosa native
portClock or host frame. Reuses exact RF050 instruction-port and RF049 original
LDA/STA validators and all unchanged RF047 case comparators.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
import qa01_rf050_late_port_publication_report as rf050

ORIGINAL="work/zoom-zoo/replay/reference.log"
NATIVE="work/zoom-zoo/replay/native.log"
O_TAG="QA01RF051ORIGSPC "
N_TAG="QA01RF051NATIVE "

def fields(line:str)->dict:
    out={}
    for fragment in line.split()[1:]:
        if "=" in fragment:
            k,v=fragment.split("=",1)
            if not k or k in out:raise ValueError("duplicate RF051 source/guest field")
            out[k]=v
    return out

def analyze(original:str,native:str)->dict:
    if "QA01RF051ORIGSPC_TRUNCATED" in original:
        raise ValueError("original late F6/F7 window truncated")
    if "QA01RF051NATIVE_TRUNCATED" in native:
        raise ValueError("native later-port receiver window truncated")
    o=[fields(l) for l in original.splitlines() if l.startswith(O_TAG)]
    n=[fields(l) for l in native.splitlines() if l.startswith(N_TAG)]
    for i,row in enumerate(o,1):
        for k in ("ordinal","age","v","h","pc","opcode","cycle","debt","port","val"):
            if k not in row:raise ValueError("missing genuine original SMP receiver field "+k)
        if int(row["ordinal"])!=i:raise ValueError("original F6/F7 read ordinal gap")
        age=int(row["age"])
        if not 104485120<=age<=104485800:
            raise ValueError("original SPC receiver age outside qualified window")
        if row["port"] not in ("2","3"):
            raise ValueError("original receiver port not F6/F7")
        if len(row["val"])!=2 or any(c not in "0123456789ABCDEF" for c in row["val"]):
            raise ValueError("original F6/F7 value not hex byte")
    if any(int(o[i]["age"])>int(o[i+1]["age"]) for i in range(len(o)-1)):
        raise ValueError("original SPC local age regressed")
    for i,row in enumerate(n,1):
        for k in ("ordinal","kind","frame","clock","target","pc","port","val","queue"):
            if k not in row:raise ValueError("missing native receiver/queue field "+k)
        if int(row["ordinal"])!=i:raise ValueError("native queue observation ordinal gap")
        if row["kind"] not in ("schedule","apply","spc-read"):
            raise ValueError("native queue/receive kind unknown")
        if not 6110<=int(row["frame"])<=6140:
            raise ValueError("native frame outside qualified window")
        if not 104300000<=int(row["clock"])<=104900000:
            raise ValueError("native local portClock outside window")
        if row["port"] not in ("2","3"):
            raise ValueError("native receiver port invalid")
        if len(row["val"])!=2 or any(c not in "0123456789ABCDEF" for c in row["val"]):
            raise ValueError("native receiver value invalid")
        if int(row["queue"])<0:raise ValueError("native queue depth negative")
    if any(int(n[i]["clock"])>int(n[i+1]["clock"]) for i in range(len(n)-1)):
        raise ValueError("native local portClock regressed")
    # Two source APU publications independently witnessed by RF050, never
    # derived from a matching native port-value pair.
    link=rf050.source_instruction_publication_link(original)
    if not link["both_real_port_publications_inside_original_instruction_segments"]:
        raise ValueError("RF051 original late sender itself not independently qualified")
    sent=link["source_original_STA_to_actual_APU_publications"]
    if [(x["port"],x["value"]) for x in sent]!=[(3,"D0"),(2,"63")]:
        raise ValueError("RF051 late original sender bytes changed")
    source_after=[]
    for row in o:
        age=int(row["age"]); port=int(row["port"])
        publication=sent[0] if port==3 else sent[1]
        if age>=publication["source_SPC_age"]:
            source_after.append({
              "source_SPC_age":age,
              "original_SPC_PC":row["pc"],
              "original_source_SPC_port":port,
              "observed_value":row["val"],
              "matches_last_original_late_CPU_write":row["val"]==publication["value"],
              "source_local_ticks_after_publication":age-publication["source_SPC_age"],
              "source_same_guest_but_not_native_clock":True,
            })
    native_summary={}
    for k in ("schedule","apply","spc-read"):
        subset=[row for row in n if row["kind"]==k]
        native_summary[k]={
          "count":len(subset),
          "by_port":{str(p):sum(row["port"]==str(p) for row in subset) for p in (2,3)},
          "first_records":subset[:15],
        }
    return {
      "schema":"rf051-original-late-spc-and-native-guest-receiver-v1",
      "original_real_late_APU_sender":sent,
      "original_real_late_SPC_F6_F7_reads":len(o),
      "original_read_age_first_last":[int(o[0]["age"]),int(o[-1]["age"])] if o else None,
      "original_late_incoming_SPC_reads_after_sender":source_after[:150],
      "original_late_incoming_SPC_after_sender_count":len(source_after),
      "original_matching_value_read_after_sender_count":sum(x["matches_last_original_late_CPU_write"] for x in source_after),
      "original_receipt_absence_is_only_source_window_missingness":not bool(source_after),
      "native_later_port_observations":len(n),
      "native_clock_first_last":[int(n[0]["clock"]),int(n[-1]["clock"])] if n else None,
      "native_queue_apply_receiver_census":native_summary,
      "native_window_is_not_original_port_ordinal_alignment":True,
      "source_SPC_age_equals_native_portClock_proven":False,
      "source_original_frame_equals_native_host_frame_proven":False,
      "end_to_end_original_native_SPC_delivery_parity_proven":False,
      "USA_full_course_event_acceptance":0,
    }

def report(case:Path,baseline:Path)->dict:
    with zipfile.ZipFile(case) as z:
        original=z.read(ORIGINAL).decode("utf8","replace")
        native=z.read(NATIVE).decode("utf8","replace")
    out=analyze(original,native)
    prior=rf050.report(case,baseline)
    if not prior["all_RF047_original_native_unmasked_Zoo_Bowl_SRAM_controls_unchanged"]:
        raise ValueError("genuine original/native Zoo controls changed")
    out["rf050_instruction_APU_source_link_confirmed"]=prior[
        "original_instruction_to_live_APU_source_order"]["both_real_port_publications_inside_original_instruction_segments"]
    out["source_RF049_full_original_operand_count"]=prior["source_full_operand_census"]["genuine_original_82F0_LDA_count"]
    out["case_zip_sha256"]=hashlib.sha256(case.read_bytes()).hexdigest()
    out["reference_RF047_case_zip_sha256"]=hashlib.sha256(baseline.read_bytes()).hexdigest()
    out["source_executed_commit"]=prior["frozen_research_source_sha"]
    out["unmasked_mesh_and_Zoo_Bowl_SRAM_unchanged"]=True
    return out

def main()->None:
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("case",type=Path)
    a.add_argument("--baseline",type=Path,required=True)
    a.add_argument("--out",type=Path)
    q=a.parse_args()
    body=json.dumps(report(q.case,q.baseline),indent=2,sort_keys=True)+"\n"
    if q.out:q.out.write_text(body,encoding="utf8")
    else:print(body,end="")
if __name__=="__main__":main()
