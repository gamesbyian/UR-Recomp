#!/usr/bin/env python3
"""RF043: certify the first Zoo stack divergence from authentic full-WRAM mesh.

Read-only analysis of an immutable original/native case artifact. No masking,
frame retiming, fabricated opcode attribution or USA event admission.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

BASELINE_SHA = "1c21481aff42ab3580f6292d94c3b0f255d71d8c548b688f2f4d00ae4190ebb0"
STACK4 = ("7E:01ED", "7E:01EE", "7E:01EF", "7E:01F0")
STACK2 = ("7E:01EE", "7E:01F1")
SOUND1 = ("7E:0063",)
FIRST_MESH = (0, 1, 2, 4, 8)

def certify(producer: dict) -> dict:
    mesh = producer["zoo_race_mesh"]
    if mesh["mesh_checkpoint_count"] != 78 or mesh["masked_or_excluded_wram_bytes"] != 0:
        raise ValueError("RF043 missing 78 full unmasked WRAM mesh observations")
    if mesh["raw_byte_exact_sample_count"] != 51:
        raise ValueError("RF043 exact sample count drift")
    observations = mesh["samples"]
    if len(observations) != 78:
        raise ValueError("RF043 missing per-frame observations")
    byframe = {}
    address_frames = {}
    nonzero = []
    total = 0
    for sample in observations:
        frame = int(sample["race_relative_frame"])
        if frame in byframe: raise ValueError("RF043 duplicate relative frame")
        diff = sample["original_native_full_wram_byte_difference"]
        if (diff["full_wram_bytes_per_guest"] != 131072 or
                diff["excluded_byte_count"] != 0 or
                not diff["every_byte_compared"]):
            raise ValueError("RF043 masked or truncated WRAM pair")
        details = diff["first_24_differences"]
        if diff["differing_byte_count"] != len(details):
            raise ValueError("RF043 incomplete differing-address list")
        addrs = tuple(e["snes_address"] for e in details)
        for a in addrs: address_frames.setdefault(a, []).append(frame)
        byframe[frame] = {"addresses": addrs, "record": sample}
        total += diff["differing_byte_count"]
        if addrs: nonzero.append(frame)
    if total != 92 or any(f not in byframe for f in FIRST_MESH):
        raise ValueError("RF043 baseline byte count or early sampling changed")
    if byframe[0]["addresses"] or byframe[8]["addresses"]:
        raise ValueError("RF043 source/native entry or +8 not fully WRAM equal")
    if any(byframe[f]["addresses"] != STACK4 for f in (1, 2, 4)):
        raise ValueError("RF043 first Zoo stack divergence identity changed")
    if [f for f in nonzero if tuple(byframe[f]["addresses"]) == STACK4] != [
        1,2,4,32,219,604,840,841,1080,1531,1532,1720,1721,1800,
        2160,2520,2880,3120,3600,4920
    ]:
        raise ValueError("RF043 four-byte stack windows changed")
    if [f for f in nonzero if tuple(byframe[f]["addresses"]) == STACK2] != [
        5034,5035,5036,5037,5038
    ]:
        raise ValueError("RF043 two-byte late stack window changed")
    if [f for f in nonzero if tuple(byframe[f]["addresses"]) == SOUND1] != [5040,5045]:
        raise ValueError("RF043 live sound pointer residual drift")
    if len(nonzero) != 27: raise ValueError("RF043 missing residual frame")
    entry = byframe[0]["record"]
    if (int(entry["original_absolute_host_frame"]) != 1017 or
        int(entry["native_absolute_host_frame"]) != 1017):
        raise ValueError("RF043 first original/native host clock registration changed")
    earliest = byframe[1]["record"]
    if (int(earliest["original_absolute_host_frame"]) != 1018 or
        int(earliest["native_absolute_host_frame"]) != 1018):
        raise ValueError("RF043 first differing host clock changed")
    actual = {}
    for e in earliest["original_native_full_wram_byte_difference"]["first_24_differences"]:
        actual[e["snes_address"]] = [int(e["original_byte"]), int(e["native_byte"])]
    return {
        "schema":"rf043-zoo-first-stack-divergence-source-native-v1",
        "accepted_usa_events":0,
        "source_movie_active_entry_frame": int(mesh["source_original_active_entry_movie_frame"]),
        "reference_and_native_entry_host":1017,
        "first_differing_host":1018,
        "first_differing_relative_frame":1,
        "original_native_entry_full_wram_equal":True,
        "original_native_full_wram_equal_again_at_relative_8":True,
        "first_differing_byte_values":actual,
        "stack_four_byte_mismatch_frames":list(address_frames["7E:01ED"]),
        "late_two_byte_stack_frames":list(address_frames["7E:01F1"]),
        "live_sound_pointer_frames":list(address_frames["7E:0063"]),
        "all_78_unmasked_full_wram_pairs_compared":True,
        "stack_differing_byte_occurrences":90,
        "sound_pointer_differing_byte_occurrences":2,
        "total_unmasked_byte_occurrences":92,
        "next_minimal_source_original_native_opcode_NMI_writer_read_window":{
            "absolute_host_start_inclusive":1017,
            "absolute_host_end_inclusive":1025,
            "first_causal_transition":[1017,1018],
            "stack_addresses":["7E:01ED","7E:01EE","7E:01EF","7E:01F0","7E:01F1"],
            "must_capture":"actual original/native stack writes, subsequent reads, interrupt/NMI pre/post stack state; real CPU opcode PC and SP where available",
            "must_not_infer":"source and native are the same CPU instruction/IRQ tick simply because host frames match"
        },
        "stack_bytes_safe_to_mask":False,
        "source_qualified_last_writer_reader_or_NMI_proven":False,
    }

def receipt(zipfile_path: Path, *, strict_sha: bool=True) -> dict:
    actual = hashlib.sha256(zipfile_path.read_bytes()).hexdigest()
    if strict_sha and actual != BASELINE_SHA:
        raise ValueError("RF043 immutable RF041 source case hash changed")
    with zipfile.ZipFile(zipfile_path) as z:
        data = json.loads(z.read("producer-report.json"))
    out = certify(data)
    out["case_zip_sha256"] = actual
    out["strict_baseline_sha_verified"] = actual == BASELINE_SHA
    return out

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("case_zip",type=Path)
    p.add_argument("--output",type=Path)
    p.add_argument("--allow-other-zip",action="store_true")
    a=p.parse_args()
    result=json.dumps(receipt(a.case_zip,strict_sha=not a.allow_other_zip),sort_keys=True,indent=2)+"\n"
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(result,encoding="utf8")
    else: print(result,end="")
if __name__=="__main__":main()
