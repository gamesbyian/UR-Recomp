#!/usr/bin/env python3
"""RF046: exact early Zoo checkpoint ↔ preceding ORIGINAL NMI pre/post match.

This establishes a byte correspondence, NOT native instruction/NMI phase
equivalence, absence of readers, gameplay correctness or release acceptance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

CASE_SHA = "84d6906af7ebfe0dee3f77fb90b4c4f50400fc7c45add3e586f14035daf15357"
SOURCE_LOG = "work/zoom-zoo/replay/reference.log"
EARLY = (1, 2, 4)
FOUR_STACK_FRAMES = (1,2,4,32,219,604,840,841,1080,1531,1532,1720,
                     1721,1800,2160,2520,2880,3120,3600,4920)
EXPECTED_ORIGINAL_NMI_SHAPE_COUNTS = {
    "26F0D482": 1, "26EED482": 4, "27F0D482": 10, "27EED482": 5
}
ADDRESSES = tuple(f"7E:{a:04X}" for a in range(0x01ED, 0x01F1))
NMI_RE = re.compile(
    r"^QA01RF044ORIGNMI f=(\d+) f1=(\d+) pc=([A-F0-9]{6}) "
    r"S0=([A-F0-9]{4}) S1=([A-F0-9]{4}) "
    r"old=([A-F0-9]{10}) new=([A-F0-9]{10})$"
)

def nmis_from_log(source_log: str) -> dict[int, dict]:
    if "QA01RF044ORIGNMI_TRUNCATED" in source_log:
        raise ValueError("RF046 original NMI trace truncated")
    records: dict[int, dict] = {}
    for raw in source_log.splitlines():
        if not raw.startswith("QA01RF044ORIGNMI "):
            continue
        m = NMI_RE.fullmatch(raw)
        if not m:
            raise ValueError("RF046 malformed source NMI row")
        frame, postframe, pc, s0, s1, old, new = m.groups()
        f = int(frame)
        if f in records or int(postframe) != f or s0 != "01F0" or s1 != "01EC":
            raise ValueError("RF046 duplicate/frame-crossing/unexpected original NMI")
        records[f] = {"frame": f, "interrupted_pc": pc,
                      "SP_before": s0, "SP_after": s1,
                      "before_stack_01ED_01F0": old[:8],
                      "after_stack_01ED_01F0": new[:8],
                      "before_01F1": old[8:], "after_01F1": new[8:]}
    if list(records) != list(range(1017, 1026)):
        raise ValueError("RF046 incomplete original nine-frame NMI census")
    return records

def compare(producer: dict, case: dict, original_log: str) -> dict:
    nmis = nmis_from_log(original_log)
    mesh = producer["zoo_race_mesh"]
    if (mesh["mesh_checkpoint_count"] != 78 or
        len(mesh["samples"]) != 78 or
        mesh["raw_byte_exact_sample_count"] != 51 or
        mesh["masked_or_excluded_wram_bytes"] != 0 or
        case["release_credit"] != 0 or
        case["disposition"] != "strict_candidate"):
        raise ValueError("RF046 immutable unmasked control mesh missing")
    if "QA01RF044ORIGBUS_TRUNCATED" in original_log:
        raise ValueError("RF046 original bus recorder truncated")
    if sum(s["original_native_full_wram_byte_difference"]["differing_byte_count"]
           for s in mesh["samples"]) != 92:
        raise ValueError("RF046 unmasked WRAM total drift")
    byframe = {}
    for s in mesh["samples"]:
        relative = int(s["race_relative_frame"])
        if relative in byframe:
            raise ValueError("RF046 duplicated checkpoint frame")
        byframe[relative] = s
    for rel in (0, 8):
        if rel not in byframe or byframe[rel][
                "original_native_full_wram_byte_difference"]["differing_byte_count"] != 0:
            raise ValueError("RF046 entry or +8 whole-WRAM equality missing")
    # The other 17 four-byte checkpoint images have the same status + PC
    # + program-bank *shape*, but lack RF044 executed NMI rows; do not
    # elevate them to source bus/NMI timing evidence.
    shape_counts: dict[str, int] = {}
    shape_samples = []
    for rel in FOUR_STACK_FRAMES:
        if rel not in byframe:
            raise ValueError("RF046 four-byte stack checkpoint missing")
        diff = byframe[rel]["original_native_full_wram_byte_difference"]
        entries = diff["first_24_differences"]
        if (diff["differing_byte_count"] != 4 or
            len(entries) != 4 or
            tuple(e["snes_address"] for e in entries) != ADDRESSES):
            raise ValueError("RF046 20-frame four-byte stack distribution drift")
        value = "".join(f"{int(e['original_byte']):02X}" for e in entries)
        if not (value[:2] in ("26", "27") and
                value[2:4] in ("EE", "F0") and value[4:] == "D482"):
            raise ValueError("RF046 original stack return-PC shaped bytes drift")
        shape_counts[value] = shape_counts.get(value, 0) + 1
        shape_samples.append({"relative_frame":rel,
                              "checkpoint_original_return_stack_image":value,
                              "actual_source_NMI_at_this_frame_observed": rel in EARLY})
    if shape_counts != EXPECTED_ORIGINAL_NMI_SHAPE_COUNTS:
        raise ValueError("RF046 original 20-frame status/PC shape census drift")
    comparisons = []
    for rel in EARLY:
        if rel not in byframe:
            raise ValueError("RF046 early source/native checkpoint absent")
        s = byframe[rel]
        host_o, host_n = (int(s[k]) for k in
            ("original_absolute_host_frame", "native_absolute_host_frame"))
        if host_o != 1017 + rel or host_n != 1017 + rel:
            raise ValueError("RF046 original/native checkpoint host clocks changed")
        nmi = nmis[host_o - 1]
        d = s["original_native_full_wram_byte_difference"]
        if d["differing_byte_count"] != 4:
            raise ValueError("RF046 early first four-byte difference incomplete")
        diffs = d["first_24_differences"]
        if len(diffs) != 4 or tuple(x["snes_address"] for x in diffs) != ADDRESSES:
            raise ValueError("RF046 wrong actual stack mismatch address")
        orig = "".join(f"{int(x['original_byte']):02X}" for x in diffs)
        native = "".join(f"{int(x['native_byte']):02X}" for x in diffs)
        if orig != nmi["after_stack_01ED_01F0"] or native != nmi["before_stack_01ED_01F0"]:
            raise ValueError("RF046 pre/post-NMI correspondence not reproduced")
        comparisons.append({
            "relative_frame": rel,
            "original_checkpoint_host": host_o,
            "native_checkpoint_host": host_n,
            "preceding_original_NMI_host": host_o - 1,
            "original_NMI_interrupted_pc": nmi["interrupted_pc"],
            "original_NMI_before_stack_01ED_01F0": nmi["before_stack_01ED_01F0"],
            "original_NMI_after_stack_01ED_01F0": nmi["after_stack_01ED_01F0"],
            "checkpoint_original_stack_01ED_01F0": orig,
            "checkpoint_native_stack_01ED_01F0": native,
            "original_checkpoint_equals_preceding_source_NMI_post": True,
            "native_checkpoint_equals_preceding_source_NMI_pre": True,
        })
    return {
        "schema": "rf046-first-zoo-NMI-prepost-crossphase-match-v1",
        "source_original_all_twenty_four_byte_stack_shapes": shape_samples,
        "source_original_twenty_four_byte_image_histogram": shape_counts,
        "later_frames_have_executed_source_NMI_proven": False,
        "exact_early_checkpoint_NMI_matches": comparisons,
        "original_NMI_nine_frame_census_count": len(nmis),
        "original_NMI_first_host": min(nmis),
        "original_NMI_last_host": max(nmis),
        "entry_full_Wram_bytes_equal": True,
        "entire_Wram_equal_again_at_relative_frame_8": True,
        "all_78_full_unmasked_128KiB_pair_controls_present": True,
        "all_real_unmasked_byte_difference_occurrences": 92,
        "native_actual_NMI_instruction_phase_from_correspondence_proven": False,
        "original_physical_bus_writer_reader_proven": False,
        "native_saved_return_PC_correctness_proven": False,
        "differing_stack_bytes_never_consumed_proven": False,
        "no_masking_or_exclusion_authorized": True,
        "complete_USA_events_admitted": 0,
    }

def report(path: Path) -> dict:
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if sha != CASE_SHA:
        raise ValueError("RF046 source-pinned RF044 archive SHA mismatch")
    with zipfile.ZipFile(path) as z:
        result = compare(json.loads(z.read("producer-report.json")),
                         json.loads(z.read("case-result.json")),
                         z.read(SOURCE_LOG).decode("utf8", "replace"))
    result["rf044_genuine_case_zip_sha256"] = sha
    return result

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("case_zip", type=Path)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    result = json.dumps(report(a.case_zip), indent=2, sort_keys=True) + "\n"
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(result, encoding="utf8")
    else:
        print(result, end="")

if __name__ == "__main__":
    main()
