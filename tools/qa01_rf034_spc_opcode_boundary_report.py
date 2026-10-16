#!/usr/bin/env python3
"""RF034 qualify source-executed original SPC opcode debt vs native port consumer.

Requires complete RF030/RF032/RF033 source witnesses. Independent clock
axes and fractional conversions are reported, never silently synchronized.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
import qa01_rf033_cpu_master_clock_report as rf033

SCHEMA="UR-RF034-EXECUTED-SPC-OPCODE-DEBT-AND-PORT-CONSUMER/1"
O_PREFIX="QA01RF034ORIG "
N_PREFIX="QA01RF034NATIVE "
O_FIELDS={"before","after","debtbefore","debtafter","pcbefore","pcafter","opbefore","opafter","cycbefore","cycafter","value"}
N_FIELDS={"age","target","pc","left","qhead","qtail","value"}
HEX={"pcbefore","pcafter","opbefore","opafter","pc","value"}

def parse(log: str,prefix: str,required:set[str])->list[dict]:
    if prefix.strip()+"_TRUNCATED" in log:
        raise ValueError("RF034 truncated read-only instruction trace")
    result=[]
    for line in log.splitlines():
        if not line.startswith(prefix):
            continue
        row={}
        for token in line[len(prefix):].split():
            if "=" not in token:
                raise ValueError("RF034 malformed witness field")
            k,v=token.split("=",1)
            if k not in required or k in row:
                raise ValueError("RF034 unknown/duplicate field")
            if k in HEX:
                if not re.fullmatch("[0-9A-F]+",v):
                    raise ValueError("RF034 invalid hexadecimal source clock")
                row[k]=int(v,16)
            else:
                if not re.fullmatch("-?[0-9]+",v):
                    raise ValueError("RF034 invalid decimal source clock")
                row[k]=int(v)
        if set(row)!=required:
            raise ValueError("RF034 incomplete source opcode/port record")
        if row["value"]!=0xcc:
            raise ValueError("RF034 source record is not CPU $CC")
        result.append(row)
        if len(result)>128:
            raise ValueError("RF034 unexpected unbounded instruction events")
    if not result:
        raise ValueError("RF034 missing actual original/native SPC opcode boundary")
    return result

def summarize(original_log:str,native_log:str)->dict:
    prior=rf033.summarize(original_log,native_log)
    original=parse(original_log,O_PREFIX,O_FIELDS)
    native=parse(native_log,N_PREFIX,N_FIELDS)
    o=original[0]
    n=native[0]
    if o["before"]!=prior["original_first_cc"]["spc_age_before_cpu_port_execute"] or \
       o["after"]!=prior["original_first_cc"]["spc_age_after_execute_and_write"]:
        raise ValueError("RF034 original opcode state does not bind RF033 true first CPU CC")
    if n["age"]!=prior["native_first_cc"]["stored_port_target"] or \
       n["target"]!=prior["native_first_cc"]["stored_port_target"]:
        raise ValueError("RF034 native queued-port event does not bind first CC target/application")
    if o["after"]-o["before"] != prior["original_first_cc"]["observed_spc_age_increment"]:
        raise ValueError("RF034 original executed SPC age count changed")
    if n["qhead"]>n["qtail"] or n["qtail"]-n["qhead"]>1024:
        raise ValueError("RF034 native port queue state invalid")
    if n["left"]>64:
        raise ValueError("RF034 impossible native SPC opcode cycles remaining")
    if [x["after"] for x in original]!=sorted(x["after"] for x in original) or \
       [x["age"] for x in native]!=sorted(x["age"] for x in native):
        raise ValueError("RF034 re-ordered CPU writer/SPC opcode records")
    return {
        "schema":SCHEMA,
        "original_first_cc":{
            "spc_age_before":o["before"],"spc_age_after":o["after"],
            "spc_clock_debt_before":o["debtbefore"],
            "spc_clock_debt_after":o["debtafter"],
            "spc_pc_before":f"{o['pcbefore']:04X}",
            "spc_pc_after":f"{o['pcafter']:04X}",
            "spc_opcode_number_before":f"{o['opbefore']:02X}",
            "spc_opcode_number_after":f"{o['opafter']:02X}",
            "opcode_cycle_before":o["cycbefore"],
            "opcode_cycle_after":o["cycafter"],
            "actual_spc_ticks_during_source_execute":o["after"]-o["before"],
            "nominal_spc_ticks_requested":prior["original_first_cc"]["original_spc_ticks_predicted_at_cpu_bus_write"],
            "observed_original_cc_writes_in_window":len(original)
        },
        "native_first_cc":{
            "queued_port_application_spc_age":n["age"],
            "stored_target_spc_age":n["target"],
            "spc_pc_at_consumption":f"{n['pc']:04X}",
            "native_opcode_cycles_left_before_port_apply":n["left"],
            "queue_head_at_consumption":n["qhead"],
            "queue_tail_at_consumption":n["qtail"],
            "actual_cc_applies_in_window":len(native)
        },
        "cross_source_absolute_spc_phase_sync_proven":False,
        "source_correct_cpu_port_visibility_fix_proven":False,
        "complete_gameplay_event_credit":0
    }

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-log",type=Path,required=True)
    p.add_argument("--native-log",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():
        p.error("refuse to overwrite immutable RF034 source receipt")
    report=summarize(a.original_log.read_text(encoding="utf8"),
                     a.native_log.read_text(encoding="utf8"))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps(report,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
