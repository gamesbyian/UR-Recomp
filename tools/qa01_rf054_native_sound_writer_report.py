#!/usr/bin/env python3
"""RF054: actual native CPU publication versus ROM mapping or bus read provenance.

Read one genuine archived source-qualified USA Zoo ZIP, never invent a CPU
opcode or reinterpret a RomPtr mapping request as a dereference. Always check
RF053 true 322/322 SPC receiver sequence, RF050 original LDA→APU publication
and strict unchanged original/native Zoo/Bowl/SRAM/witness identities.
"""
from __future__ import annotations
import argparse, hashlib, json, zipfile
from pathlib import Path
import qa01_rf053_real_spc_receiver_sequence_parity as rf053

TAG="QA01RF054NATIVE "
BUS="QA01RF054NATIVEBUS "
MAIN="work/zoom-zoo/replay/native.log"

def fields(line:str)->dict:
    record={}
    for p in line.split()[1:]:
        if "=" in p:
            k,v=p.split("=",1)
            if not k or k in record: raise ValueError("RF054 duplicate/empty recorder field")
            record[k]=v
    return record

def inspect(log:str)->dict:
    if "QA01RF054NATIVE_TRUNCATED" in log or "QA01RF054NATIVEBUS_TRUNCATED" in log:
        raise ValueError("RF054 native CPU writer or data observer truncated")
    lines=log.splitlines()
    stages=[(n,fields(line)) for n,line in enumerate(lines) if line.startswith(TAG)]
    bus=[(n,fields(line)) for n,line in enumerate(lines) if line.startswith(BUS)]
    kinds=("writer","rom-map")
    separate={}
    for label in kinds:
        selected=[(i,x) for i,x in stages if x.get("kind")==label]
        for seq,(index,row) in enumerate(selected,1):
            needed=("seq","frame","master","addr","val","PB","DB","D","Y","A","dp63","dp64","dp65","scope")
            if any(k not in row for k in needed):
                raise ValueError("RF054 incomplete actual/native mapping or writer identity")
            if int(row["seq"])!=seq or int(row["frame"])!=6124:
                raise ValueError("RF054 native stage ordinal/frame invalid")
            if any(c not in "0123456789ABCDEF" for c in row["addr"]):
                raise ValueError("RF054 malformed native address")
            if label=="rom-map" and (int(row["addr"],16)>>16 not in (0x10,0x11,0x12,0x13)):
                raise ValueError("RF054 ROM mapping observation outside bank scope")
            if label=="writer" and int(row["addr"],16) not in (0x2142,0x2143):
                raise ValueError("RF054 CPU writer observation outside actual sound registers")
        separate[label]=selected
    if len(separate["writer"])<2:
        raise ValueError("RF054 actual native AOT CPU sound publication absent")
    for index,row in bus:
        needed=("kind","seq","frame","master","addr","A","Y","D","dp63","dp64","dp65","scope")
        if any(k not in row for k in needed):
            raise ValueError("RF054 actual native CPU helper observation incomplete")
        if int(row["seq"])<=0 or int(row["frame"])!=6124 or row["kind"] not in ("read8","read16"):
            raise ValueError("RF054 real native CPU helper read identity invalid")
        try:
            bus_address=int(row["addr"],16)
        except ValueError as exc:
            raise ValueError("RF054 actual bus physical address malformed") from exc
        if bus_address>>16 not in (0x10,0x11,0x12,0x13):
            raise ValueError("RF054 actual bus helper read outside qualified ROM bank")
    if [int(x["seq"]) for _,x in bus]!=list(range(1,len(bus)+1)):
        raise ValueError("RF054 native bus read rows lost or duplicated")
    if any(int(b[1]["master"])<int(a[1]["master"]) for a,b in zip(bus,bus[1:])):
        raise ValueError("RF054 native CPU true helper master clock regressed")
    writers=separate["writer"]
    candidate=[]
    for (i,x),(j,y) in zip(writers,writers[1:]):
        if (x["addr"],x["val"],y["addr"],y["val"])!=("002143","00D0","002142","0063"):
            continue
        candidate.append((i,j,x,y))
    if len(candidate)!=1:
        raise ValueError("RF054 genuine native late D0/63 CPU publication pair absent/nonunique")
    wi,wj,w0,w1=candidate[0]
    if int(w1["master"])<int(w0["master"]):
        raise ValueError("RF054 actual native writer source clock regressed")
    before=[x for i,x in separate["rom-map"] if i<wi]
    near=[x for x in before if int(w0["master"])-int(x["master"])>=0
          and int(w0["master"])-int(x["master"])<=20000]
    helper=[x for i,x in bus if i<wi and 0<=int(w0["master"])-int(x["master"])<=20000]
    return {
      "schema":"rf054-actual-native-65816-sound-writer-context-v1",
      "native_actual_cpu_port_writer_count":len(writers),
      "native_ROM_pointer_mapping_request_count":len(separate["rom-map"]),
      "native_actual_CPU_ROM_bus_helper_read_count":len(bus),
      "genuine_late_D0_63_CPU_writer_pair_count":len(candidate),
      "native_real_paired_writer_context":[w0,w1],
      "native_late_pair_separate_master_clocks":[int(w0["master"]),int(w1["master"])],
      "mapping_requests_prior_to_writer_20000_master_clock_window":near[-24:],
      "actual_read_helper_invocations_prior_to_writer_20000_master_clock_window":helper[-24:],
      "native_ROM_pointer_mapping_is_not_proof_of_dereference":True,
      "native_CPU_helper_read_call_is_real_but_not_necessarily_the_last_LDA":True,
      "native_compiled_65816_instruction_PC_proven":False,
      "original_11C774_operand_equals_native_effective_ROM_operand_proven":False,
      "source_native_CPU_APU_publication_clock_registered":False,
      "USA_full_course_event_credit":0,
    }

def report(case:Path,baseline:Path)->dict:
    prior=rf053.one_case(case,baseline)
    if not prior["native_true_schedule_apply_SPC_receiver"]["native_actual_port_write_apply_receiver_chain_verified"]:
        raise ValueError("RF054 native SPC receiver and queue chain no longer source qualified")
    with zipfile.ZipFile(case) as z:
        native=z.read(MAIN).decode("utf8","replace")
    result=inspect(native)
    result["real_original_native_exact_SPC_receiver_match_count"]=prior["original_real_spc_read_count"]
    result["real_native_SPC_receiver_unique_position"]=prior["native_read_window_zero_based_match_start"]
    result["full_RF047_Zoo_Bowl_SRAM_controls_unchanged"]=prior["all_RF047_Zoo_Bowl_terminal_producer_controls_equal"]
    result["frozen_experiment_source_sha"]=prior["source_exact_guest_sha"]
    result["case_sha256"]=hashlib.sha256(case.read_bytes()).hexdigest()
    result["baseline_sha256"]=hashlib.sha256(baseline.read_bytes()).hexdigest()
    return result

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case",type=Path)
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    out=json.dumps(report(a.case,a.baseline),sort_keys=True,indent=2)+"\n"
    if a.out:a.out.write_text(out,encoding="utf8")
    else:print(out,end="")
if __name__=="__main__":main()
