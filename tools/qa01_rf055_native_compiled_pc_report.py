#!/usr/bin/env python3
"""RF055: join real generated PC stamp to native CPU bus/port and SPC receipt.

Read one immutable genuine Zoo case. All instruction PC rows are executed
generated-C sites, never inferred from a C function scope or byte payload.
Require contiguous F0/read/F2/port3/F6/port2 chains; no masked/state
rewrites or cross-domain clock assumptions.
"""
from __future__ import annotations
import argparse,json,zipfile
from pathlib import Path
import qa01_rf054_native_sound_writer_report as rf054

PC="QA01RF055NATIVEPC "
BUS="QA01RF054NATIVEBUS "
WRITER="QA01RF054NATIVE kind=writer "
PATH="work/zoom-zoo/replay/native.log"
EXPECTED=("8282F0","8282F2","8282F6")
SCOPE="Snd_UploadBlockList_82EF_M1X0"

def inspect(log:str,expected_transfers:int|None=None)->dict:
    if "QA01RF055NATIVEPC_TRUNCATED" in log or (
            "QA01RF054NATIVE_TRUNCATED" in log or
            "QA01RF054NATIVEBUS_TRUNCATED" in log):
        raise ValueError("RF055 source-native executed witness truncated")
    items=[]
    for line in log.splitlines():
        kind = ("pc" if line.startswith(PC) else
                "bus" if line.startswith(BUS) else
                "writer" if line.startswith(WRITER) else None)
        if kind:
            record=rf054.fields(line)
            if record.get("frame")!="6124" or (
                    kind=="pc" and record.get("pc") not in EXPECTED):
                raise ValueError("RF055 guest PC/frame provenance invalid")
            if record.get("scope")!=SCOPE:
                raise ValueError("RF055 generated instruction changed owning scope")
            items.append((kind,record))
    if not items or len(items)%6:
        raise ValueError("RF055 incomplete executed opcode/bus/writer groups")
    count=len(items)//6
    if expected_transfers is not None and count!=expected_transfers:
        raise ValueError("RF055 actual native transfers count changed")
    witnesses=[]
    previous_master=None
    for i in range(count):
        group=items[i*6:i*6+6]
        if [k for k,_ in group]!=["pc","bus","pc","writer","pc","writer"]:
            raise ValueError(f"RF055 guest opcode and actual CPU bus ordering changed at {i}")
        p0,b,p1,w0,p2,w1=[row for _,row in group]
        if [p0["pc"],p1["pc"],p2["pc"]]!=list(EXPECTED):
            raise ValueError("RF055 incorrect emitted per-instruction guest PC")
        for row in (p0,b,p1,w0,p2,w1):
            needed=("master","A","Y","D","dp63","dp64","dp65","scope","frame")
            if any(k not in row for k in needed):
                raise ValueError("RF055 actual native CPU context incomplete")
        if b.get("kind")!="read8" or w0.get("addr")!="002143" or w1.get("addr")!="002142":
            raise ValueError("RF055 missing actual real ROM operand/port publication")
        if (int(b.get("seq","0"))!=i+1 or int(w0.get("seq","0"))!=2*i+1 or
                int(w1.get("seq","0"))!=2*i+2):
            raise ValueError("RF055 CPU bus/port ordinal sequence interrupted")
        masters=[int(x["master"]) for x in (p0,b,p1,w0,p2,w1)]
        if masters!=sorted(masters) or (
                previous_master is not None and masters[0]<previous_master):
            raise ValueError("RF055 native instruction/CPU publication clock regression")
        previous_master=masters[-1]
        if len({x["Y"] for x in (p0,b,p1,w0,p2,w1)})!=1:
            raise ValueError("RF055 native Y changed within witnessed upload transfer")
        if (p0["A"]!=b["A"] or p1["A"]!=w0["A"] or p2["A"]!=w1["A"]):
            raise ValueError("RF055 executed instruction A differs from actual CPU read/write")
        if any(x["dp65"]!="11" or x["dp63"]!="00" or x["dp64"]!="00"
               for x in (p0,b,p1,w0,p2,w1)):
            raise ValueError("RF055 source pointer bytes differ within upload")
        if int(b.get("addr","0"),16)!=0x110000+int(b["Y"],16):
            raise ValueError("RF055 actual bus effective operand violates DP indexed address")
        if (int(w0.get("val","0"),16)!=(int(w0["A"],16)&0xff) or
                int(w1.get("val","0"),16)!=(int(w1["A"],16)&0xff)):
            raise ValueError("RF055 actual CPU published value not equal accumulator low byte")
        if b["addr"]=="11C774":
            witnesses.append({"transaction_index_zero_based":i,
                              "guest_opcode_PCs":list(EXPECTED),
                              "native_CPU_master_clocks":masters,
                              "native_65816_A_at_opcode_entries":[p0["A"],p1["A"],p2["A"]],
                              "actual_ROM_operand":b["addr"],
                              "actual_port3_value":w0["val"],
                              "actual_port2_value":w1["val"],
                              "native_AOT_scope":SCOPE})
    if len(witnesses)!=1 or witnesses[0]["actual_port3_value"]!="00D0" or (
            witnesses[0]["actual_port2_value"]!="0063"):
        raise ValueError("RF055 source matched late 11:C774 CPU opcode chain absent/ambiguous")
    return {
        "schema":"rf055-executed-generated-65816-instruction-pc-v1",
        "exact_native_compiled_transfer_count":count,
        "executed_instruction_PC_records":count*3,
        "genuine_native_CPU_bus_helper_records":count,
        "genuine_native_CPU_port_publication_records":count*2,
        "all_transfer_instruction_bus_and_publication_orders_verified":True,
        "unique_source_matched_11C774_to_D0_63_executed_PC_chain":witnesses[0],
        "original_native_absolute_CPU_SP_C_clock_phase_proven":False,
        "all_frame_CPU_and_APU_equivalence_proven":False,
        "event_admission_credit":0,
    }

def local_cpu_master_intervals(source:str,native:str,
                               expected_original:int=16,
                               expected_native:int=656)->dict:
    """Compare only same-CPU publication gaps, never absolute CPU/SPC axes.

    The original's H/V beam timestamps and the native CPU master counter
    measure local 65816 master-clock intervals. Same pair payload identity
    alone does not calibrate their origins or the SPC queue schedule.
    """
    original=[rf054.fields(s) for s in source.splitlines()
              if s.startswith("QA01RF050ORIGAPU ")]
    native_writers=[rf054.fields(s) for s in native.splitlines()
                    if s.startswith(WRITER)]
    original_gaps=[]
    for a,b in zip(original,original[1:]):
        if a.get("port")=="3" and b.get("port")=="2":
            original_gaps.append((int(b["v"])-int(a["v"]))*1364+
                                 int(b["h"])-int(a["h"]))
    native_gaps=[]
    for a,b in zip(native_writers,native_writers[1:]):
        if a.get("addr")=="002143" and b.get("addr")=="002142":
            native_gaps.append(int(b["master"])-int(a["master"]))
    if len(original_gaps)!=expected_original or len(native_gaps)!=expected_native:
        raise ValueError("RF055 native/original real publication pair census changed")
    if set(original_gaps)!={50} or set(native_gaps)!={50}:
        raise ValueError("RF055 original/native intra-CPU master interval regression")
    return {
        "original_real_port3_to_port2_master_interval_count":len(original_gaps),
        "native_real_port3_to_port2_master_interval_count":len(native_gaps),
        "original_and_native_all_local_master_intervals":50,
        "interval_is_not_absolute_cpu_or_spc_clock_alignment":True,
    }

def report(case:Path,baseline:Path)->dict:
    prior=rf054.report(case,baseline)
    if prior["real_original_native_exact_SPC_receiver_match_count"]!=322 or (
            not prior["full_RF047_Zoo_Bowl_SRAM_controls_unchanged"]):
        raise ValueError("RF055 real RF054/SPC controls changed")
    with zipfile.ZipFile(case) as z:
        log=z.read(PATH).decode("utf8","replace")
        source=z.read("work/zoom-zoo/replay/reference.log").decode("utf8","replace")
    out=inspect(log,expected_transfers=656)
    out["source_native_65816_master_interval_parity"]=local_cpu_master_intervals(
        source,log)
    out["original_real_SPC_PC_port_byte_sequence_unique_match_count"]=322
    out["original_native_full_RF047_controls_unchanged"]=True
    out["source_exact_guest_sha"]=prior["frozen_experiment_source_sha"]
    out["case_sha256"]=prior["case_sha256"]
    out["baseline_sha256"]=prior["baseline_sha256"]
    return out

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case",type=Path)
    p.add_argument("--baseline",required=True,type=Path)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    body=json.dumps(report(args.case,args.baseline),indent=2,sort_keys=True)+"\n"
    if args.out:args.out.write_text(body,encoding="utf8")
    else:print(body,end="")
if __name__=="__main__":main()
