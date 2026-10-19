#!/usr/bin/env python3
"""RF059 audit of the immutable authentic original/native Bowl source run.

Read two *exact* archived producer ZIPs; no emulation, no frame/input shifts.
All 64 raw historical movie, fresh original and native images must be wholly
identical. Only instrumented Snes9x executable SHA and precisely known
additive diagnostic metadata may differ from the earlier source case.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile
from pathlib import Path
import qa01_rf059_original_scene_writer_report as original

CASE_SHA="b5854c0c8290b989bac9e7ec81a59d7552c06d7f5e06568eb4e6f3483d3a3db0"
BASE_SHA="c2262b40e43b4e167cbdf291623b0e34207561187e103af39eca7a46fa4b0edc"
NEW_CORE_SHA="a9e0bc5bb49c627fdcf67425b603f0d3e73a526cabaaf0db0b3dccc445451ff3"
OLD_CORE_SHA="0182cfc3446e5a2c1d00453928b857b3d1d9c23148486c7339c895c4facc25c5"
DIAGNOSTIC_KEY="bounded_dragster_to_zoo_diagnostic_without_full_event_parity"

def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
def images(z:zipfile.ZipFile)->dict[str,bytes]:
    return {n:z.read(n) for n in z.namelist()
            if n.startswith(("bowl/replay/ref/","bowl/replay/native/","bowl/source/"))
            and n.endswith((".wram.bin",".sram.bin"))}

def certify_producer(case:dict,baseline:dict)->None:
    if case.get("reference_core_sha256")!=NEW_CORE_SHA or baseline.get("reference_core_sha256")!=OLD_CORE_SHA:
        raise ValueError("RF059 actual reference core rebuild SHA256 not source-authenticated")
    c=case.get("comparison");b=baseline.get("comparison")
    if (not isinstance(c,dict) or not isinstance(b,dict)
        or DIAGNOSTIC_KEY in b or c.get(DIAGNOSTIC_KEY) is not False
        or {k:v for k,v in c.items() if k!=DIAGNOSTIC_KEY}!=b):
        raise ValueError("RF059 non-qualifying original/native full producer comparison drift")
    if "dragster_next_zoo_handoff" in baseline or case.get("dragster_next_zoo_handoff","missing") is not None:
        raise ValueError("RF059 unrelated additive Dragster handoff metadata not exactly None")
    permitted={"reference_core_sha256","comparison","dragster_next_zoo_handoff"}
    if (set(case)!=(set(baseline)|{"dragster_next_zoo_handoff"})
        or any(v!=baseline[k] for k,v in case.items() if k not in permitted)):
        raise ValueError("RF059 original/natural source ROM, controller, SRAM or Bowl outcome changed")

def certify_images(a:dict[str,bytes],b:dict[str,bytes])->dict:
    if set(a)!=set(b) or len(a)!=64:
        raise ValueError("RF059 missing original/native/historical 64 whole images")
    for name,data in b.items():
        expected=131072 if name.endswith(".wram.bin") else 8192
        if len(data)!=expected or len(a[name])!=expected:
            raise ValueError("RF059 incomplete full WRAM/SRAM image")
        if data!=a[name]:
            raise ValueError("RF059 actual entire guest WRAM/SRAM diverged: "+name)
    return {"raw_original_native_historical_whole_images_equal":64,
            "excluded_or_masked_guest_bytes":0}

def certify_archive(actual:Path,reference:Path)->dict:
    if sha(actual)!=CASE_SHA or sha(reference)!=BASE_SHA:
        raise ValueError("RF059 exact independent original/native case ZIP SHA256 wrong")
    with zipfile.ZipFile(actual) as z,zipfile.ZipFile(reference) as b:
        if len(z.namelist())!=84 or len(b.namelist())!=78:
            raise ValueError("RF059 source guest record artifacts incomplete")
        actual_report=json.loads(z.read("bowl-report.json"))
        baseline_report=json.loads(b.read("bowl-report.json"))
        certify_producer(actual_report,baseline_report)
        guest=certify_images(images(z),images(b))
        parsed=original.inspect(z.read("bowl/replay/reference.log").decode("utf8","replace"))
        archived=json.loads(z.read("rf059-executed-scene-state-WRAM.json"))
        if parsed!=archived or parsed["actual_source_65816_opcode_interval_mutation_count"]!=24:
            raise ValueError("RF059 producer's actual source opcode evidence changed")
        actual_hand=json.loads(z.read("bowl-independent-raw-audit.json"))
        previous=json.loads(b.read("bowl-independent-raw-audit.json"))
        actual_producer_sha=hashlib.sha256(z.read("bowl-report.json")).hexdigest()
        prior_producer_sha=hashlib.sha256(b.read("bowl-report.json")).hexdigest()
        if (actual_hand.get("producer_sha256")!=actual_producer_sha or
            previous.get("producer_sha256")!=prior_producer_sha or
            {k:v for k,v in actual_hand.items() if k!="producer_sha256"} !=
            {k:v for k,v in previous.items() if k!="producer_sha256"}):
            raise ValueError("RF059 independent raw audit differs beyond its authenticated parent producer SHA")
    return {
        "schema":"rf059-genuine-2014-USA-Bowl-original-CPU-scene-setup-whole-archive-audit-v1",
        "original_source_replay_sha256":CASE_SHA,
        "independent_original_baseline_sha256":BASE_SHA,
        **guest,
        "entire_source_ROM_movie_controller_SRAM_and_Bowl_report_equal_except_two_additions_and_core_sha":True,
        "actual_true_original_CPU_opcode_boundary_rows":parsed["actual_source_65816_opcode_interval_mutation_count"],
        "actual_original_65816_source_handoff_frames":parsed["actual_source_CPU_frames_at_handoff"],
        "first_and_last_real_original_CPU_writers_by_address":
            {key:{"first":parsed["actual_CPU_scene_change_first_by_address"][key],
                  "last":parsed["actual_CPU_scene_change_last_by_address"][key]}
             for key in parsed["actual_memory_change_candidate_address_census"]},
        "source_native_CPU_clock_epoch_registered":False,
        "single_transition_causal_CPU_branch_proven":False,
        "independent_USA_complete_events_accepted":0,
    }
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("actual_RF059_ZIP",type=Path)
    p.add_argument("--baseline",required=True,type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    payload=json.dumps(certify_archive(a.actual_RF059_ZIP,a.baseline),indent=2,sort_keys=True)+"\n"
    if a.out:a.out.write_text(payload,encoding="utf8")
    else:print(payload,end="")
if __name__=="__main__":main()
