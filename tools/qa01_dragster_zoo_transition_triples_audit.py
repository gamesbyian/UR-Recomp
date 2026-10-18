#!/usr/bin/env python3
"""ROM-free authentic 2014 Dragster→Zoo original/native WRAM transition audit.

Reads immutable original Actions ZIP bytes only. Three captured guest-frame
displacement is an observed diagnostic, NOT CPU/SPC/controller retiming,
whole-event equivalence, memory masking or a release admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, BadZipFile

ARCHIVE_SHA256 = "f036f80d72000b05a5c2edb42152eb433b89fa44c5fc36238ccc73bd143e2947"
PRODUCER_SHA256 = "be912d6dbcfe5d3f4c3c12ce6c00b44b649eb5d679b6ee07a4382872112d1936"
OFFSETS = (304,308,312,314,315,316,317,318,319,320,321,324,328,336)
TRIPLE_WINDOWS = ((314,315,317,318),(315,316,318,319),
                  (316,317,319,320),(317,318,320,321))
CANDIDATE_SRAM_OFFSET = 0x0E6B


def require(condition: bool, why: str) -> None:
    if not condition:
        raise ValueError(why)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def mutations(first: bytes, second: bytes) -> set[tuple[int,int,int]]:
    """Full original 128KiB address, actual old byte and actual new byte."""
    require(len(first) == len(second) == 131072, "incomplete 128KiB guest mutation images")
    return {(i, x, y) for i,(x,y) in enumerate(zip(first,second)) if x != y}


def sram_correspondences(wram_original: bytes, wram_native: bytes,
                         sram_original: bytes, sram_native: bytes) -> tuple[int,int,int]:
    """Count all genuine mismatches and their non-exempt candidate value match."""
    require(len(wram_original) == len(wram_native) == 131072 and
            len(sram_original) == len(sram_native) == 8192,
            "wrong authentic guest WRAM or battery extent")
    mismatches = [i for i,(a,b) in enumerate(zip(wram_original,wram_native))
                  if a != b]
    seen = sum(i+CANDIDATE_SRAM_OFFSET < 8192 and
               wram_original[i] == sram_original[i+CANDIDATE_SRAM_OFFSET] and
               wram_native[i] == sram_native[i+CANDIDATE_SRAM_OFFSET]
               for i in mismatches)
    battery = sum(a != b for a,b in zip(sram_original,sram_native))
    return len(mismatches), battery, seen


def audit(path: Path) -> dict:
    require(path.is_file() and not path.is_symlink(), "missing original Actions archive")
    require(digest(path.read_bytes()) == ARCHIVE_SHA256,
            "original ZIP SHA-256 differs from provider-verified source")
    try:
        with ZipFile(path) as z:
            names = z.namelist()
            require(len(names) == len(set(names)) == 69,
                    "unexpected or duplicate authentic source artifact members")
            raw_report = z.read("dragster-report.json")
            require(digest(raw_report) == PRODUCER_SHA256,
                    "actual original source producer SHA-256 differs")
            report = json.loads(raw_report)
            source = report.get("original_source_event") or {}
            comparison = report.get("comparison") or {}
            handoff = report.get("dragster_next_zoo_handoff") or {}
            clocks = comparison.get("terminal_result_guest_frame") or {}
            boundaries = handoff.get("entry_brackets") or {}
            require(report.get("name") == "dragster" and
                    report.get("course_id") == "course:01" and
                    report.get("native_backend") == "pinned-baldosa" and
                    report.get("original_movie_sha256") ==
                        "06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442" and
                    source.get("original_entry_frame") == 794 and
                    source.get("original_result_frame") == 2874 and
                    handoff.get("original_movie_zoo_entry_frame") == 3190 and
                    handoff.get("original_movie_zoo_entry_relative_to_dragster_result") == 316 and
                    handoff.get("release_complete_usa_event_credit") == 0,
                    "not authentic historical Dragster→Zoo original source event")
            require(clocks.get("reference_relative") == 2081 and
                    clocks.get("native_relative") == 2079 and
                    report.get("reference_entry") == 945 and
                    report.get("native_entry") == 945 and
                    boundaries.get("original",{}).get("exact_adjacent_onset_offset") == 315 and
                    boundaries.get("native",{}).get("exact_adjacent_onset_offset") == 318,
                    "actual original/native result and next-event clocks altered")
            rows = handoff.get("samples")
            require(isinstance(rows,list) and len(rows) == len(OFFSETS),
                    "incomplete original/native source-relative observation population")
            wrams = {}
            signatures = []
            per_frame = []
            for offset,row in zip(OFFSETS,rows):
                require(row.get("offset_from_respective_dragster_result") == offset,
                        "source-derived original/native sample clock misregistered")
                memory = {}
                for side,guest,elapsed in (
                    ("ref","original",2081), ("native","native",2079)):
                    claim = (row.get("fresh_guests") or {}).get(guest) or {}
                    require(claim.get("host_frame") == 945+elapsed+offset,
                            "observed actual guest host frame contradicts source")
                    memory[side] = {}
                    for kind,length in (("wram",131072),("sram",8192)):
                        name = f"dragster/replay/{side}/dragster-next-zoo-{offset}.{kind}.bin"
                        info = z.getinfo(name)
                        require(info.file_size == length,
                                "truncated or oversized original guest image: "+name)
                        data = z.read(info)
                        require(len(data) == length and
                                digest(data) == claim.get("full_"+kind+"_sha256") and
                                claim.get("full_"+kind+"_bytes") == length,
                                "original guest image SHA or size differs: "+name)
                        memory[side][kind] = data
                    wrams[side,offset] = memory[side]["wram"]
                original,native = memory["ref"],memory["native"]
                wdiff,sdiff,mapped = sram_correspondences(
                    original["wram"],native["wram"],
                    original["sram"],native["sram"])
                expected = row.get("unmasked_full_original_native_wram_difference") or {}
                require(wdiff == expected.get("differing_byte_count") and
                        expected.get("original_wram_sha256") == digest(original["wram"]) and
                        expected.get("native_wram_sha256") == digest(native["wram"]) and
                        row.get("full_original_native_sram_pair_equal") is (sdiff == 0),
                        "source producer unmasked original/native WRAM or SRAM disagrees")
                signatures.append([(i,original["sram"][i],native["sram"][i])
                                  for i in range(8192)
                                  if original["sram"][i] != native["sram"][i]])
                per_frame.append({
                    "result_relative_offset":offset,
                    "original_host_frame":945+2081+offset,
                    "native_host_frame":945+2079+offset,
                    "unmasked_128k_wram_different_byte_count":wdiff,
                    "unmasked_8k_sram_different_byte_count":sdiff,
                    "wram_value_correspondence_at_sram_plus_0x0E6B":mapped,
                    "remaining_real_unmasked_wram_differences":wdiff-mapped})
            require(len(signatures[0]) == 13 and
                    all(signature == signatures[0] for signature in signatures),
                    "13 original/native static SRAM differing-byte values changed")
            temporal = []
            for original0,original1,native0,native1 in TRIPLE_WINDOWS:
                a = mutations(wrams["ref",original0],wrams["ref",original1])
                b = mutations(wrams["native",native0],wrams["native",native1])
                temporal.append({
                    "original_guest_result_relative_frames":[original0,original1],
                    "native_guest_result_relative_frames":[native0,native1],
                    "same_address_old_new_mutations":len(a&b),
                    "original_mutation_triples":len(a),
                    "native_mutation_triples":len(b),
                    "original_only_mutation_triples":len(a-b),
                    "native_only_mutation_triples":len(b-a),
                    "frames_shifted_for_gameplay_or_input":False,
                })
            require([x["same_address_old_new_mutations"] for x in temporal] ==
                    [636,221,147,195], "original archive transition triples no longer agree")
            return {
                "schema":"UR-QA01-DRAGSTER-ZOO-AUTHENTIC-TRIPLE-WITNESS/1",
                "source_run_id":39174631932,
                "artifact_id":12154480620,
                "original_archive_sha256":ARCHIVE_SHA256,
                "original_report_sha256":PRODUCER_SHA256,
                "original_movie_dragster_result_relative_frames":2080,
                "fresh_original_dragster_result_relative_frames":2081,
                "fresh_native_dragster_result_relative_frames":2079,
                "next_zoo_source_original_native_relative_frames":[316,315,318],
                "original_native_full_memory_files_sha256_checked":len(OFFSETS)*4,
                "per_sample_unmasked_differences":per_frame,
                "persistent_unmasked_sram_value_differences":[
                    {"offset":f"0x{i:04X}","original":a,"native":b}
                    for i,a,b in signatures[0]],
                "candidate_sram_byte_offset":"0x0E6B",
                "candidate_sram_copy_direction_or_writer_proven":False,
                "cross_guest_three_frame_sampled_mutation_fingerprint":temporal,
                "controller_source_movie_file_and_guest_consumption_proven":False,
                "all_unsampled_gameplay_frames_or_cpu_spc_clocks_proven":False,
                "accepted_usa_complete_events":0,
                "release_quality_gates":0,
            }
    except (BadZipFile,KeyError,json.JSONDecodeError) as exc:
        raise ValueError("missing/corrupt real Dragster source ZIP member") from exc


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-archive",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    try:
        result=audit(args.original_archive)
    except (OSError,ValueError,TypeError) as exc:
        p.exit(2,"QA01_DRAGSTER_SOURCE_TRIPLES_INVALID: "+str(exc)+"\n")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("All genuine Dragster original/native images rehashed; USA admissions 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
