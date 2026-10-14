#!/usr/bin/env python3
"""Fail-closed classification of the actually executed QA-01 paired air witness.

This verifies a successful *observation*, not correct racer physics or an
original/native accepted full event. Read-only on the retained Actions ZIP.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ZIP_SHA = "7bc085861183e7667620ad66fb0c7a18f8be7a870afe8c2e4752eb6229cd6c2a"
REPORT_SHA = "de521d7597b274031ba8768aa8f67e2d65938178f2e0e43fa93a1cb7d9497a6a"
EXPECTED_AIR = {
    2579: {"original": [0, 1], "native": [0, 1]},
    2580: {"original": [0, 2], "native": [1, 2]},
    2581: {"original": [0, 0], "native": [0, 0]},
}


def checked(z: zipfile.ZipFile, name: str) -> bytes:
    info = [i for i in z.infolist() if i.filename == name]
    if len(info) != 1 or info[0].is_dir():
        raise ValueError(f"missing or repeated executed artifact file {name}")
    return z.read(info[0])


def classify(blob: bytes, *, verify_zip_hash: bool = True) -> dict:
    import io
    digest = hashlib.sha256(blob).hexdigest()
    if verify_zip_hash and digest != ZIP_SHA:
        raise ValueError("not the exact independently executed pinned artifact")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        report_raw = checked(z, "paired-report.json")
        report_hash = hashlib.sha256(report_raw).hexdigest()
        if verify_zip_hash and report_hash != REPORT_SHA:
            raise ValueError("actual paired report changed")
        report = json.loads(report_raw)
        original_log = checked(z, "original.log").decode("utf-8")
        native_log = checked(z, "native.log").decode("utf-8")
        manifest = json.loads(checked(z, "manifest.json"))
    if (report.get("release_gate_credit") != 0
            or report.get("strict_complete_event_accepted") is not False
            or report.get("paired_guest_relative_entry_offset_calibrated") is not False
            or report.get("both_engine_actual_dump_frame_receipts_verified") is not True
            or report.get("same_executable_as_frontier_witness") is not True
            or report.get("original_wram_snapshots") != 18
            or report.get("native_wram_snapshots") != 18
            or report.get("raw_both_air_at_2580") != {"original": False, "native": True}
            or report.get("active_race_at_2580") != {"original": True, "native": True}
            or manifest.get("seed") != 50036056):
        raise ValueError("source/native provenance or admission changed")
    rows = report.get("read_only_paired_samples")
    if not isinstance(rows, list) or len(rows) != 18:
        raise ValueError("not all 18 original/native paired memory samples present")
    for side, log in (("original", original_log), ("native", native_log)):
        receipt = report["independent_emulator_frame_receipts"][side]
        if receipt.get("transcript_sha256") != hashlib.sha256(log.encode()).hexdigest():
            raise ValueError(side + " actual transcript digest mismatch")
        observed = []
        for frame, tag, suffix in re.findall(
                r"^script f=(\d+) dump ([a-zA-Z0-9-]+) (.+)$", log, re.MULTILINE):
            if tag not in manifest["checkpoints"]:
                continue
            if side == "original":
                if re.fullmatch(r"fb=256x224 RGB565 sram=8192 ppuw=\d+", suffix) is None:
                    raise ValueError("invalid actual original Snes9x script receipt")
            elif suffix != "ok":
                raise ValueError("invalid actual native script receipt")
            observed.append([int(frame), tag])
        if observed != receipt["observed_frame_label_pairs"] or len(observed) != 18:
            raise ValueError(side + " guest dump host receipt falsified")
    triple = []
    for f in (2579, 2580, 2581):
        row = next((x for x in rows if x.get("host_frame_label") ==
                    ("endurance-2580" if f == 2580 else f"qa01-neighbor-{f}")), None)
        if row is None:
            raise ValueError("missing original/native adjacent host state")
        for side in ("original", "native"):
            if row.get(side + "_air_raw") != EXPECTED_AIR[f][side]:
                raise ValueError("real raw air bytes differ from retained source")
            if row.get(side + "_active_race_raw") != 1:
                raise ValueError("not genuine dual active racing")
            if row.get(side + "_progress", {}).get("player1", {}).get("laps_remaining") != 1:
                raise ValueError("not genuine paired on-course progression")
        triple.append({
            "host_frame": f,
            "original_raw_air": row["original_air_raw"],
            "native_raw_air": row["native_air_raw"],
            "original_vertical_velocity": row["original_velocity"][0][1],
            "native_vertical_velocity": row["native_velocity"][0][1],
            "p1_y_original": row["original_xy"][0][1],
            "p1_y_native": row["native_xy"][0][1],
            "p2_y_original": row["original_xy"][1][1],
            "p2_y_native": row["native_xy"][1][1],
            "p1_y_native_minus_original": (row["native_xy"][0][1]
                                          - row["original_xy"][0][1]),
            "p2_y_native_minus_original": (row["native_xy"][1][1]
                                          - row["original_xy"][1][1]),
        })
    return {
        "schema": "UR-QA01-DUAL-AIR-EXECUTED-PAIRED-OBSERVATION/1",
        "executed_run": 38509912672,
        "artifact_id": 11869806880,
        "zip_sha256": digest,
        "paired_report_sha256": report_hash,
        "actual_emulator_receipts": True,
        "source_native_same_host_frame_2580_raw_both_air_parity": False,
        "original_native_raw_air_discrepancy_at_2580": True,
        "neighbor_three_frame_samples": triple,
        "source_native_event_entry_phase_equivalence_proven": False,
        "physical_airborne_semantics_proven": False,
        "strict_complete_event_accepted": False,
        "complete_event_credit": 0,
        "interpretation": "P1 original 0 vs native 1 at 7E:0545 on exactly host 2580, "
                          "while P2 matches 2 at 7E:0547. P1 vertical velocity "
                          "is original 0 vs native 19 at that host frame; P1 Y "
                          "original 857 vs native 858, persisting at 2581 even "
                          "after the provisional P1 air byte resets. At 2580 "
                          "P2 Y original 863 vs native 862, returning to the "
                          "same Y 864 at 2581. This is a small genuine "
                          "raw-state divergence, not a proved airborne collision/"
                          "physics cause, CPU phase equivalence or any accepted course."
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    result = classify(a.artifact.read_bytes())
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"raw_discrepancy": result["original_native_raw_air_discrepancy_at_2580"],
                      "complete_event_credit": 0}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
