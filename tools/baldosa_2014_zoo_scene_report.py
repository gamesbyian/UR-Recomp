#!/usr/bin/env python3
"""Bounded original/native 2014 scene witness, deliberately non-admitting."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

SAMPLES = ("scene-entered", "result-onset-candidate", "result-stable-candidate")


def snapshot(path: Path) -> dict:
    w = path.read_bytes()
    if len(w) != 0x20000:
        raise ValueError(f"{path}: expected 128 KiB WRAM, got {len(w)} bytes")
    u16 = lambda a: int.from_bytes(w[a:a+2], "little")
    return {
        "nmi_handler": f"0x{u16(0x53):04X}",
        "menu": w[0x009F],
        "race_flag": w[0x0313],
        "track_id": w[0x00CE],
        "p1_world_xy": [u16(0x0411), u16(0x0415)],
        "p2_world_xy": [u16(0x0413), u16(0x0417)],
        "p1_stored_contact": u16(0x0E95),
        "p1_checkpoint": u16(0x1199),
        "p1_finish_gate": u16(0x119D),
        "p1_laps_remaining": u16(0x0EF1),
        "race_stopwatch_raw": [w[a] for a in (
            0x0E0F, 0x0E13, 0x0E17, 0x0E1B, 0x0E1F)],
    }


def analyze(original_dir: Path, native_dir: Path, metadata: dict) -> dict:
    observations = {}
    for name, directory in (("original", original_dir), ("native", native_dir)):
        observations[name] = {
            sample: snapshot(directory / f"{sample}.wram.bin")
            for sample in SAMPLES
        }
    different = []
    for sample in SAMPLES:
        reference, candidate = observations["original"][sample], observations["native"][sample]
        for key in reference:
            if reference[key] != candidate[key]:
                different.append({
                    "sample": sample, "field": key,
                    "original": reference[key], "baldosa": candidate[key]})
    full_wram = {}
    for sample in SAMPLES:
        o = (original_dir / f"{sample}.wram.bin").read_bytes()
        n = (native_dir / f"{sample}.wram.bin").read_bytes()
        mismatched = [i for i, (a, b) in enumerate(zip(o, n)) if a != b]
        full_wram[sample] = {
            "guest_wram_bytes_compared": len(o),
            "original_wram_sha256": hashlib.sha256(o).hexdigest(),
            "baldosa_wram_sha256": hashlib.sha256(n).hexdigest(),
            "exact_match": not mismatched,
            "differing_byte_count": len(mismatched),
            "first_byte_offsets": [f"0x{i:05X}" for i in mismatched[:16]],
        }
    initial_good = all(
        rows["scene-entered"]["race_flag"] == 1 and
        rows["scene-entered"]["track_id"] == 1
        for rows in observations.values()
    )
    results = {
        label: (rows["result-onset-candidate"]["menu"] == 0xBC
                and rows["result-stable-candidate"]["menu"] == 0xBC
                and rows["result-stable-candidate"]["track_id"] == 1
                and rows["result-stable-candidate"]["race_flag"] != 1)
        for label, rows in observations.items()
    }
    return {
        "schema_version": 1,
        "source": "2014 original Snes9x archived Zoom Zoo result scene input, independently fresh boot",
        "source_original_result_frame": 8353,
        "source_input": metadata,
        "original_and_baldosa_entered_zoo": initial_good,
        "original_reached_stable_circuit_result_state": results["original"],
        "baldosa_reached_stable_circuit_result_state": results["native"],
        "paired_result_state_candidate": initial_good and all(results.values())
                                          and not different,
        "observed_named_fields_compared": len(SAMPLES) *
                                          len(observations["original"][SAMPLES[0]]),
        "first_semantic_difference": different[0] if different else None,
        "all_sampled_differences": different,
        "raw_whole_wram_snapshots": full_wram,
        "raw_wram_exact_matched_count": sum(r["exact_match"]
                                            for r in full_wram.values()),
        "observations": observations,
        "complete_event_qa_credit": 0,
        "limitation": (
            "No PPU result text or independent time/score equality proven. "
            "A 2014 movie scene is a hypothesis for freshly booted guests, "
            "not the original entire movie execution state. A result-state "
            "candidate is NOT a complete accepted event."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--original", type=Path, required=True)
    p.add_argument("--native", type=Path, required=True)
    p.add_argument("--source-report", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)\n    p.add_argument("--calibration-report", type=Path)
    args = p.parse_args()
    meta = json.loads(args.source_report.read_text(encoding="utf-8"))
    r = analyze(args.original, args.native, meta)\n    if args.calibration_report:\n        r["calibrated_movie_input"] = json.loads(\n            args.calibration_report.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: r[key] for key in (
        "original_and_baldosa_entered_zoo",
        "original_reached_stable_circuit_result_state",
        "baldosa_reached_stable_circuit_result_state",
        "paired_result_state_candidate",
        "first_semantic_difference",\n        "raw_wram_exact_matched_count",
        "complete_event_qa_credit")}))
    return 0 if r["original_and_baldosa_entered_zoo"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
