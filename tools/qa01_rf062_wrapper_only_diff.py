#!/usr/bin/env python3
"""Strict RF062 native AOT generated-source substitution diff, not gameplay QA.

Exactly one compiled C read site may change: original paced byte -> a wrapper
that itself calls original cpu_read8_paced once. No other generated unit or
unmatched M/X variant can change. ROM-free checks precede genuine replay.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

MARK = "UR_QA01_RF062_DIRECT_PC_8282F0"
PAT = re.compile(
    r"(ur_rf062_read8_pc_8282f0)\((cpu,[^\n;]+)\); /\* "
    + MARK + r" \*/"
)


def check(baseline: Path, wrapped: Path) -> dict:
    def files(root: Path) -> dict[str, bytes]:
        if not root.is_dir():
            raise ValueError("genuine emitted C root missing")
        return {
            str(p.relative_to(root)): p.read_bytes()
            for p in sorted(root.rglob("*"))
            if p.is_file() and p.suffix in (".c",".h")
        }
    a,b=files(baseline),files(wrapped)
    if not a or set(a)!=set(b):
        raise ValueError("generated file population drift")
    changed=[p for p in a if a[p]!=b[p]]
    if len(changed)!=1 or not changed[0].endswith(".c"):
        diagnostics=[{
            "file":p,
            "baseline_sha256":hashlib.sha256(a[p]).hexdigest(),
            "wrapped_sha256":hashlib.sha256(b[p]).hexdigest(),
            "rf062_marker_count":b[p].count(MARK.encode()),
            "rf062_wrapper_function_call_count":b[p].count(
                b"ur_rf062_read8_pc_8282f0("),
            "baseline_bytes":len(a[p]),"wrapped_bytes":len(b[p]),
        } for p in changed]
        raise ValueError(
            "expected exactly one generated live C source changed: "+
            json.dumps({"total_changed":len(changed),
                        "first_changed":diagnostics[:20]},
                        sort_keys=True,separators=(",",":")))
    src_old=a[changed[0]].decode("utf8")
    src_new=b[changed[0]].decode("utf8")
    sites=list(PAT.finditer(src_new))
    if len(sites)!=1 or src_old.count("ur_rf062_read8_pc_8282f0")!=0:
        raise ValueError("missing or duplicated native RF062 read substitution")
    rewritten=PAT.sub(r"cpu_read8_paced(\2);",src_new)
    if rewritten!=src_old:
        raise ValueError("native code changed beyond one original paced read")
    from qa01_rf062_verify_live_generated import audit
    live=audit(wrapped)
    if live["source_provenance"]["direct_original_8282F0_real_bus_read_callsites"]!=1:
        raise ValueError("not exactly one actual M1X0 decoded opcode read")
    return {
        "schema":"ur-qa01-rf062-wrapper-only-generated-c-diff/1",
        "only_one_live_generated_c_file_changed":True,
        "changed_generated_file":changed[0],
        "original_generated_file_sha256":hashlib.sha256(a[changed[0]]).hexdigest(),
        "wrapped_generated_file_sha256":hashlib.sha256(b[changed[0]]).hexdigest(),
        "only_delta":"one cpu_read8_paced to one ur_rf062_read8_pc_8282f0 call; source CPU/guest clocks not inferred",
        "source_guest_rom_execution_or_noninterference_proven":False,
        "accepted_USA_events":0
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline",type=Path)
    p.add_argument("wrapped",type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    report=check(args.baseline,args.wrapped)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("Exactly one genuine generated sound AOT read substituted; no gameplay credit")


if __name__=="__main__":
    main()
