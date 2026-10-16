#!/usr/bin/env python3
"""RF033 strict source-original/native 65816->SPC master-clock conversion receipt.

Extends (never replaces) qualified RF030/RF032 original/native transport logs.
No cross-emulator phase synchronization, no inferred opcode correction and no
complete event credit.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
import qa01_rf032_native_port_target_report as rf032

SCHEMA = "UR-RF033-ORIGINAL-NATIVE-CPU-MASTER-TO-SPC-CLOCK/1"
O_PREFIX = "QA01RF033ORIG "
N_PREFIX = "QA01RF033NATIVE "
O_KEYS = {"before","after","h","v","ref","rem","num","den","predicted","value"}
N_KEYS = {"age","guest","master","frame","framestart","extended","valid","value","pc"}


def read_lines(log: str, prefix: str, fields: set[str]) -> list[dict]:
    if prefix.strip() + "_TRUNCATED" in log:
        raise ValueError("RF033 source CPU clock observer truncated")
    result = []
    for line in log.splitlines():
        if not line.startswith(prefix):
            continue
        row = {}
        for field in line[len(prefix):].split():
            if "=" not in field:
                raise ValueError("malformed RF033 CPU clock field")
            k,v = field.split("=",1)
            if k not in fields or k in row or not v:
                raise ValueError("missing/duplicate/unrecognized RF033 clock field")
            if k in {"pc","value"}:
                if not re.fullmatch("[0-9A-F]+",v):
                    raise ValueError("invalid hex RF033 clock field")
                row[k]=int(v,16)
            else:
                if not re.fullmatch("[0-9]+",v):
                    raise ValueError("invalid decimal RF033 clock field")
                row[k]=int(v)
        if set(row)!=fields:
            raise ValueError("incomplete original/native RF033 clock witness")
        result.append(row)
        if len(result)>128:
            raise ValueError("RF033 unexpected unbounded CPU writer trace")
    if not result:
        raise ValueError("missing executed original/native RF033 CPU first CC writer")
    if [x["after" if prefix==O_PREFIX else "age"] for x in result] != sorted(x["after" if prefix==O_PREFIX else "age"] for x in result):
        raise ValueError("reordered executed original/native RF033 CPU events")
    return result

def summarize(original_log: str, native_log: str) -> dict:
    evidence = rf032.summarize(original_log,native_log)
    original = read_lines(original_log,O_PREFIX,O_KEYS)
    native = read_lines(native_log,N_PREFIX,N_KEYS)
    o=next((x for x in original if x["value"]==0xcc),None)
    n=next((x for x in native if x["value"]==0xcc),None)
    if o is None or n is None:
        raise ValueError("missing real CC at CPU bus")
    if o["after"]!=evidence["original_cpu_first_cc_echo_age"]-38:
        # original CPU's first CC at +546 and its actual echo read at +584
        # are independently required by RF030 but not fixed by synthetic timing.
        # Do not rely on the 38-cycle gap: use RF030's actual first writer.
        import qa01_ipl_echo_report as rf030
        source=rf030.summarize(original_log,native_log)
        if o["after"]!=source["original_ipl_first_cc"]["cpu_write_age"]:
            raise ValueError("original CPU source clock differs from actual first CC write")
    if n["age"]!=evidence["native_first_cc_schedule"]["port_clock"] or n["guest"]!=evidence["native_first_cc_schedule"]["guest_cycle"]:
        raise ValueError("native AOT CPU clock does not bind executed queue schedule")
    if not o["den"] or not o["num"] or o["rem"]>=o["den"]:
        raise ValueError("original SPC ratio numerator/denominator/remainder invalid")
    if o["predicted"]<0 or o["before"]>o["after"]:
        raise ValueError("impossible original CPU/SPC conversion chronology")
    if n["extended"] not in (0,1) or n["valid"] not in (0,1):
        raise ValueError("invalid native frame clock mode")
    if n["frame"]<1 or n["master"]<n["framestart"]:
        raise ValueError("native master clock outside active frame")
    return {
        "schema":SCHEMA,
        "status":"executed_original_native_cpu_writer_conversion_observation",
        "original_first_cc":{
            "spc_age_before_cpu_port_execute":o["before"],
            "spc_age_after_execute_and_write":o["after"],
            "cpu_master_within_scanline":o["h"],
            "cpu_beam_v":o["v"],
            "original_spc_reference_time":o["ref"],
            "original_spc_fraction_remainder":o["rem"],
            "original_spc_ratio_numerator":o["num"],
            "original_spc_ratio_denominator":o["den"],
            "original_spc_ticks_predicted_at_cpu_bus_write":o["predicted"],
            "observed_spc_age_increment":o["after"]-o["before"]
        },
        "native_first_cc":{
            "apu_port_clock_when_cpu_bus_write_queued":n["age"],
            "guest_apu_cycle_at_cpu_write":n["guest"],
            "cpu_master_cycles":n["master"],
            "cpu_frame":n["frame"],
            "apu_frame_start_master":n["framestart"],
            "cpu_master_offset_in_frame":n["master"]-n["framestart"],
            "extended_frame_clock_enabled":bool(n["extended"]),
            "apu_frame_time_valid":bool(n["valid"]),
            "spc_pc_at_cpu_write":f"{n['pc']:04X}",
            "stored_port_target":evidence["native_first_cc_schedule"]["stored_target_cycle"],
            "queue_apply_minus_target_cycles":evidence["native_first_cc_apply"]["applied_minus_stored_target_cycle"],
            "native_spc_echo_to_cpu_poll_cycles":evidence["native_cpu_first_cc_echo_read"]["echo_to_cpu_observation_spc_cycles"]
        },
        "independent_original_native_master_clock_domains_phase_identical_proven":False,
        "all_cpu_spc_instruction_ticks_or_audio_samples_proven":False,
        "usa_complete_event_acceptance_credit":0
    }

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-log",type=Path,required=True)
    p.add_argument("--native-log",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():
        p.error("refuse to overwrite immutable executed RF033 source clock receipt")
    result=summarize(a.original_log.read_text(encoding="utf8"),a.native_log.read_text(encoding="utf8"))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
