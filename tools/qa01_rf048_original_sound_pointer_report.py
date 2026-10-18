#!/usr/bin/env python3
"""RF048: fail-closed source/native sound-pointer read reports for exact Zoo ZIP.

The original Snes9x ICPU.Frame and native host frame are *different clocks*.
A pointer reconstructed from Snes9x's WRAM mirror is read-only observer
material, not an additional genuine bus access or automatic equivalence.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

SOURCE = "work/zoom-zoo/replay/reference.log"
NATIVE = "work/zoom-zoo/replay/native.log"
TARGET_FRAMES = ((6056, "C773", 6057, "C774"),
                 (6061, "D0B3", 6062, "D0B4"))
ORIG_TAG = "QA01RF048ORIGPTR "
NATIVE_TAG = "QA01RF037NATIVEPTR "

def _fields(line: str) -> dict:
    tokens = line.split()
    result = {}
    for token in tokens[1:]:
        if "=" in token:
            key, value = token.split("=", 1)
            if not key or key in result:
                raise ValueError("duplicate or missing observer field")
            result[key] = value
    return result

def classify(original: str, native: str) -> dict:
    if "QA01RF048ORIGPTR_TRUNCATED" in original:
        raise ValueError("truncated original RF048 pointer observation")
    if "QA01RF037NATIVEPTR_TRUNCATED" in native:
        raise ValueError("truncated native RF037 pointer observer")
    orows = [_fields(line) for line in original.splitlines()
             if line.startswith(ORIG_TAG)]
    if not orows:
        raise ValueError("source RF048 original opcode observer did not execute")
    for row in orows:
        required = ("count", "frame", "v", "h", "dp_base", "dp_slot",
                    "mirror", "raw_ptr", "y", "effective_candidate",
                    "a0", "a1", "target")
        if any(k not in row for k in required):
            raise ValueError("incomplete original RF048 actual opcode row")
        if row["mirror"] not in ("0","1") or row["target"] not in ("0","1"):
            raise ValueError("invalid original raw mirror classification")
        if row["target"]=="1" and row["mirror"]!="1":
            raise ValueError("original pointer target cannot be outside WRAM mirror")
        for name in ("dp_base", "dp_slot", "raw_ptr", "y", "effective_candidate","a0","a1"):
            if any(c not in "0123456789ABCDEF" for c in row[name]):
                raise ValueError("invalid original source address/value")
        candidate=int(row["effective_candidate"],16)&0xffff
        actual_indexed=(row["mirror"]=="1" and
                        (0xC770<=candidate<=0xC779 or
                         0xD0B0<=candidate<=0xD0B9))
        if ("indexed_target" in row and
            row["indexed_target"]!=str(int(actual_indexed))):
            raise ValueError("RF048 claimed indexed target disagrees with recorded original address")
    counts=[int(row["count"]) for row in orows]
    if counts!=sorted(set(counts)):
        raise ValueError("original source opcode event ordinal regress/duplicate")
    nrows = [_fields(line) for line in native.splitlines()
             if line.startswith(NATIVE_TAG)]
    required_n=("frame","bank","addr","width","val","scope")
    selected=[]
    for row in nrows:
        if any(k not in row for k in required_n):
            raise ValueError("incomplete actual native pointer read")
        if row["bank"]=="00" and row["addr"]=="0063" and row["width"]=="2":
            selected.append(row)
    pairs=[]
    for pre,old,post,new in TARGET_FRAMES:
        before=[row for row in selected if int(row["frame"])==pre]
        after=[row for row in selected if int(row["frame"])==post]
        if not before or not after:
            raise ValueError(f"missing real native pointer read at {pre}/{post}")
        if before[-1]["val"]!=old or after[0]["val"]!=new:
            raise ValueError(f"native exact pointer-consumer boundary differs at {pre}/{post}")
        pairs.append({
            "native_host_last_frame":pre, "native_last_bus_helper_read":old,
            "native_host_next_frame":post, "native_first_bus_helper_read":new,
            "native_old_scope":before[-1]["scope"],
            "native_new_scope":after[0]["scope"],
            "native_actual_helper_read_covered":True,
            "source_original_host_frame_equivalence_proven":False,
        })
    # The original 82:82CE clears the base pointer before LDA [$63],Y.
    # A matching physical effective-address *candidate* may therefore occur
    # while raw_ptr is zero. Never conflate these independent observations.
    target=[row for row in orows if row["target"]=="1"]
    indexed=[row for row in orows if row["mirror"]=="1" and
             (0xC770 <= (int(row["effective_candidate"],16)&0xffff) <= 0xC779 or
              0xD0B0 <= (int(row["effective_candidate"],16)&0xffff) <= 0xD0B9)]
    per_frame=Counter(int(row["frame"]) for row in orows)
    per_target=Counter(int(row["frame"]) for row in target)
    return {
        "schema":"rf048-original-indexed-sound-first-consumer-v1",
        "original_executed_opcode_rows":len(orows),
        "original_recorded_source_frames":{str(k):v for k,v in sorted(per_frame.items())},
        "original_target_raw_pointer_rows":len(target),
        "original_target_raw_pointer_source_frames":{str(k):v for k,v in sorted(per_target.items())},
        "original_first_candidate_rows":target[:12],
        "original_indexed_effective_candidate_rows":len(indexed),
        "original_indexed_effective_source_frames":
            {str(k):v for k,v in sorted(Counter(int(row["frame"]) for row in indexed).items())},
        "original_indexed_effective_candidate_examples":indexed[:12],
        "original_raw_WRAM_mirror_is_not_actual_second_bus_read":True,
        "native_verified_boundary_read_pairs":pairs,
        "source_original_internal_frame_equals_native_host_proven":False,
        "original_effective_pointer_vs_native_consumer_proven":False,
        "original_native_SPC_publication_causality_proven":False,
        "source_window_coverage":"indexed_candidate_observed" if indexed else "sparse_source_samples_no_indexed_target",
        "complete_USA_event_credit":0,
    }

def report(case:Path,baseline:Path|None=None)->dict:
    data=case.read_bytes()
    with zipfile.ZipFile(case) as z:
        original=z.read(SOURCE).decode("utf8","replace")
        native=z.read(NATIVE).decode("utf8","replace")
        p=json.loads(z.read("producer-report.json"))
        c=json.loads(z.read("case-result.json"))
    mesh=p["zoo_race_mesh"]
    if (mesh["mesh_checkpoint_count"]!=78 or
        mesh["masked_or_excluded_wram_bytes"]!=0 or
        mesh["raw_byte_exact_sample_count"]!=51 or
        c["release_credit"]!=0 or c["disposition"]!="strict_candidate"):
        raise ValueError("RF048 source-qualified immutable unmasked Zoo control changed")
    out=classify(original,native)
    out.update(case_outer_zip_sha256=hashlib.sha256(data).hexdigest(),
               case_source_sha=c["source_sha"],actual_WM_pairs=78,
               exact_WM_pairs=51,admitted_events=0)
    if baseline:
        with zipfile.ZipFile(baseline) as z:
            old=json.loads(z.read("producer-report.json"))
        for key in ("zoo_race_mesh","zoo_next_bowl_handoff","source_terminal_followthrough"):
            if p[key]!=old[key]:
                raise ValueError("RF048 changed strict existing RF047 source/native course control "+key)
        out["unchanged_RF047_Zoo_Bowl_and_full_WM_controls"]=True
        out["baseline_case_zip_sha256"]=hashlib.sha256(baseline.read_bytes()).hexdigest()
    return out

def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case",type=Path)
    parser.add_argument("--baseline",type=Path)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    body=json.dumps(report(args.case,args.baseline),indent=2,sort_keys=True)+"\n"
    if args.output:args.output.write_text(body,encoding="utf8")
    else:print(body,end="")
if __name__=="__main__":
    main()
