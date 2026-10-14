#!/usr/bin/env python3
"""Source-pinned executed Zoo full WRAM/VRAM/CGRAM pre-return frame crosswalk.

An observational bounded check on an already-executed original Snes9x/native
artifact. Equal memory at a sampled guest-relative frame is not an assertion
of CPU/NMI phase, complete-event parity or equal subsequent frame timing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile

SOURCE_RUN = 38500427634
SOURCE_ARTIFACT = 11866136501
SOURCE_ZIP_SHA256 = "d5ec65c672736fa45f01214134db8598baa840f106729bd2c04ffb8949f1d039"
FRAMES = ("scene-entered", "boundary-04700", "boundary-04800",
          "boundary-05000", "boundary-05100", "boundary-05155",
          "boundary-05156")
SIZES = {"wram": 131072, "vram": 65536, "cgram": 512}
SIDES = {"original": ("original-boundary", "original-boundary.log", 1604),
         "native": ("native-boundary/dump", "native-boundary/log.txt", 1606)}
DUMP = re.compile(r"^script f=(\d+) dump ([\w-]+) (.+)$", re.MULTILINE)
ORIGINAL_FORMAT = re.compile(
    r"fb=256x224 RGB565 sram=8192 ppuw=\d+(?: \(truncated\))?")
SCHEMA = "UR-QA01-ZOO-PRERETURN-GENUINE-BULK-PARITY/1"


def sha(buf: bytes) -> str:
    return hashlib.sha256(buf).hexdigest()


def member(z: ZipFile, name: str) -> bytes:
    found = [x for x in z.infolist() if x.filename == name]
    if len(found) != 1 or found[0].is_dir():
        raise ValueError("missing, duplicate or invalid guest artifact member: " + name)
    if ((found[0].external_attr >> 16) & 0o170000) == 0o120000:
        raise ValueError("symlink in genuine source/native evidence: " + name)
    return z.read(found[0])


def actual_ticks(log: str, side: str, expected_entry: int) -> dict:
    observed = {}
    for frame, label, detail in DUMP.findall(log):
        if label not in FRAMES:
            continue
        if ((ORIGINAL_FORMAT.fullmatch(detail) is None) if side == "original"
                else (detail != "ok")):
            raise ValueError(side + " invalid emulator frame receipt: " + label)
        observed.setdefault(label, []).append(int(frame))
    entry = observed.get("scene-entered", [])
    if len(entry) != 1 or entry[0] != expected_entry:
        raise ValueError(side + " actual guest scene-entry fingerprint changed")
    result = {}
    for label in FRAMES:
        expected = (expected_entry if label == "scene-entered"
                    else expected_entry + int(label.removeprefix("boundary-")))
        values = observed.get(label, [])
        if len(values) != 1 or values[0] != expected:
            raise ValueError(side + " duplicate, missing or mistimed guest receipt: " + label)
        result[label] = values[0]
    return result


def analyze(artifact: Path, expected_sha: str | None = SOURCE_ZIP_SHA256) -> dict:
    raw = artifact.read_bytes()
    archive_sha = sha(raw)
    if expected_sha is not None and archive_sha != expected_sha:
        raise ValueError("unqualified executed original/native artifact identity")
    histories = {}
    with ZipFile(artifact) as z:
        for side, (prefix, log_path, guest_entry) in SIDES.items():
            actual_log = member(z, log_path)
            frames = actual_ticks(actual_log.decode("utf-8"), side, guest_entry)
            data = {}
            for label in FRAMES:
                images = {}
                for mem, size in SIZES.items():
                    buf = member(z, f"{prefix}/{label}.{mem}.bin")
                    if len(buf) != size:
                        raise ValueError(f"{side} {label}: incorrect {mem} guest size")
                    images[mem] = buf
                data[label] = images
            histories[side] = {
                "actual_script_host_ticks": frames,
                "host_log_sha256": sha(actual_log),
                "guest_images": data,
            }
    rows = []
    for label in FRAMES:
        row = {"guest_label": label}
        for mem in SIZES:
            a = histories["original"]["guest_images"][label][mem]
            b = histories["native"]["guest_images"][label][mem]
            row[mem] = {
                "bytes_sampled": len(a),
                "different_byte_count": sum(x != y for x, y in zip(a, b)),
                "original_sha256": sha(a),
                "native_sha256": sha(b),
            }
        row["all_three_memory_classes_exact"] = all(
            row[mem]["different_byte_count"] == 0 for mem in SIZES)
        row["original_host_tick"] = histories["original"][
            "actual_script_host_ticks"][label]
        row["native_host_tick"] = histories["native"][
            "actual_script_host_ticks"][label]
        rows.append(row)

    by_label = {row["guest_label"]: row for row in rows}
    exact = [row["guest_label"] for row in rows
             if row["all_three_memory_classes_exact"]]
    old = by_label["boundary-05155"]
    next_ = by_label["boundary-05156"]
    return {
        "schema": SCHEMA,
        "original_native_workflow_run": SOURCE_RUN,
        "artifact_id": SOURCE_ARTIFACT,
        "zip_sha256": archive_sha,
        "historical_executed_artifact_identity_pinned":
            archive_sha == SOURCE_ZIP_SHA256,
        "original_host_log_sha256": histories["original"]["host_log_sha256"],
        "native_host_log_sha256": histories["native"]["host_log_sha256"],
        "separate_original_native_scene_host_tick": {
            side: histories[side]["actual_script_host_ticks"]["scene-entered"]
            for side in SIDES},
        "memory_classes_bytes": SIZES,
        "paired_guest_relative_rows": rows,
        "all_197120_wram_vram_cgram_bytes_identical_at":
            exact,
        "source_wram_match_and_transient_vram_at_5155": (
            old["wram"]["different_byte_count"] == 0
            and old["vram"]["different_byte_count"] > 0
            and old["cgram"]["different_byte_count"] == 0),
        "next_sample_vram_match_and_wram_mismatch_at_5156": (
            next_["vram"]["different_byte_count"] == 0
            and next_["wram"]["different_byte_count"] > 0),
        "original_native_guest_cpu_nmi_beam_phase_equal_proven": False,
        "original_native_complete_event_accepted": False,
        "release_complete_usa_event_credit": 0,
        "scope": ("Observed genuine original/native full WRAM/VRAM/CGRAM "
                  "at fixed scene-relative ticks, not an instruction-level "
                  "execution trace. Do not infer correctness between samples."),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    d = analyze(a.artifact)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(d, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "all_three_exact_at": d["all_197120_wram_vram_cgram_bytes_identical_at"],
        "source_wram_match_and_transient_vram_at_5155":
            d["source_wram_match_and_transient_vram_at_5155"],
        "release_complete_usa_event_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
