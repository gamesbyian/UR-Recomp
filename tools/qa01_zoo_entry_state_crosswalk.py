#!/usr/bin/env python3
"""QA-01: source/native Zoo guest entry, exact pre-restore state and residue.

Reuses the *executed* independently booted 2014 source/movie artifact, not
synthetic emulator state or retimed inputs. This is a bounded state inspection:
it never certifies a complete original/native event or CPU/NMI synchronization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import qa01_zoo_restore_anchored_phase as prior

SHA = "d5ec65c672736fa45f01214134db8598baa840f106729bd2c04ffb8949f1d039"
SCHEMA = "UR-QA01-ZOO-EXACT-ENTRY-AND-RESTORE-PHASE-STATE/1"
SIZES = {"wram": 131072, "vram": 65536, "cgram": 512}
ENTRY_BYTES = {
    0x01ED: (0x87, 0x41),
    0x01EE: (0x7F, 0x02),
    0x2000: (0x03, 0x04),
    0x2004: (0x80, 0x40),
}
# Source original relative frame -> native = original - 1, with independently
# attested original/native scene entry hosts 1604/1606. These are *not*
# instructions to change the input phase or comparator.
EXPECTED_RESIDUES = {
    5158: (4, 0, 8),
    5159: (4, 0, 8),
    5160: (5, 0, 8),
    5161: (5, 0, 8),
    5162: (13, 0, 0),
    5163: (13, 0, 0),
}
SOURCE_RESTORE_OPCODE = prior.SOURCE_OPCODES["restore"]
NATIVE_RESTORE_STORE = prior.NATIVE_STORES["restore"]


def hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def changed(left: bytes, right: bytes) -> list[dict]:
    if len(left) != len(right):
        raise ValueError("comparing incomplete original/native guest memory")
    return [{"offset": i, "original": a, "native": b}
            for i, (a, b) in enumerate(zip(left, right)) if a != b]


def evaluate(states: dict, *, entries: dict, frame_receipts: dict) -> dict:
    """Make only source-verified narrow claims; synthetic tests earn no QA credit."""
    if entries != {"original": 1604, "native": 1606}:
        raise ValueError("original/native independently reported scene entry drifted")
    if set(states) != {"original", "native"}:
        raise ValueError("one original/native guest missing")
    for side in ("original", "native"):
        for label in ("entry", 5156, 5157, 5158, 5159, 5160, 5161, 5162, 5163):
            obj = states[side].get(label)
            if obj is None or set(obj) != set(SIZES):
                raise ValueError("missing full guest memory snapshot " + str(label))
            for memory, size in SIZES.items():
                if len(obj[memory]) != size:
                    raise ValueError("incomplete guest " + memory + " " + str(label))
        if frame_receipts[side] != {
                f: entries[side] + f for f in range(5156, 5164)}:
            raise ValueError("actual original/native guest script frame receipts drifted")
    old, new = states["original"], states["native"]
    if (old["entry"]["vram"] != new["entry"]["vram"] or
            old["entry"]["cgram"] != new["entry"]["cgram"]):
        raise ValueError("source-original/native entry PPU guest memory diverged")
    differences = changed(old["entry"]["wram"], new["entry"]["wram"])
    if {d["offset"]: (d["original"], d["native"]) for d in differences} != ENTRY_BYTES:
        raise ValueError("source-original/native exact entry difference surface drifted")
    for side, sample in (("original", old["entry"]), ("native", new["entry"])):
        raw = sample["wram"]
        if (raw[0x009F], raw[0x00CE], raw[0x0313]) != (0, 1, 1):
            raise ValueError(side + " entry source qualifier drifted")

    first = old[5157]
    second = new[5156]
    for memory in SIZES:
        if first[memory] != second[memory]:
            raise ValueError("previously exact source-native 197120-byte sample diverged")
    for side, data in (("original", first), ("native", second)):
        w = data["wram"]
        if (w[0x009F], w[0x00CE], w[0x0313], w[0x0EF1],
                w[0x1199], w[0x119D]) != (0x84, 0, 1, 0, 1, 1):
            raise ValueError(side + " exact pre-restore guest semantics drifted")

    rows = []
    for oframe, expected in EXPECTED_RESIDUES.items():
        nframe = oframe - 1
        src, dst = old[oframe], new[nframe]
        mismatches = {k: changed(src[k], dst[k]) for k in SIZES}
        counts = tuple(len(mismatches[k]) for k in SIZES)
        if counts != expected:
            raise ValueError("source-native aligned residual byte counts drifted")
        if any(not 0x01DB <= d["offset"] <= 0x01F4
               for d in mismatches["wram"]):
            raise ValueError("original/native WRAM residual outside observed scratch window")
        if any(not 0xD8 <= d["offset"] <= 0xDF
               for d in mismatches["cgram"]):
            raise ValueError("original/native CGRAM residual outside observed palette window")
        rows.append({
            "original_scene_relative_frame": oframe,
            "native_scene_relative_frame": nframe,
            "original_absolute_host_frame": frame_receipts["original"][oframe],
            "native_absolute_host_frame": frame_receipts["native"][nframe],
            "original_minus_native_absolute_host": -1,
            "difference_count_by_memory": dict(zip(SIZES, counts)),
            "guest_wram_residual_offsets": [d["offset"] for d in mismatches["wram"]],
            "guest_cgram_residual_offsets": [d["offset"] for d in mismatches["cgram"]],
        })

    return {
        "schema": SCHEMA,
        "original_entry_absolute_host": entries["original"],
        "native_entry_absolute_host": entries["native"],
        "entry_source_original_native_wram_differences": differences,
        "entry_vram_and_cgram_identical": True,
        "entry_candidate_7e2000_and_7e2004_owner_verified": False,
        "exact_matched_pair": {
            "original_guest_relative": 5157,
            "native_guest_relative": 5156,
            "original_host": frame_receipts["original"][5157],
            "native_host": frame_receipts["native"][5156],
            "memory_classes": dict(SIZES),
            "total_identical_bytes": sum(SIZES.values()),
            "sha256_each_memory_class": {
                kind: hash_bytes(first[kind]) for kind in SIZES},
            "source_native_guest_memory_byte_exact": True,
        },
        "adjacent_aligned_residuals": rows,
        "source_original_native_cpu_nmi_scanline_synchronized": False,
        "scene_entry_predicate_source_cpu_authority_proven": False,
        "original_native_event_terminal_phase_equivalent": False,
        "release_complete_event_credit": 0,
        "next_discriminator": (
            "Trace independently verified original/native producer of 7E:2000/"
            "7E:2004 and the initial 7E:0313==01 scene entry, then guest finish/"
            "return scheduling. Exact memory on one offset pair is not a global "
            "rephase, controller remedy or complete-event pass."
        ),
    }


def analyze(archive: Path, *, expected_sha256: str | None = SHA) -> dict:
    blob = archive.read_bytes()
    digest = hash_bytes(blob)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("not the exact executed original/native source artifact")
    with ZipFile(archive) as z:
        host_entries, frame_receipts, states = {}, {}, {}
        for side in ("original", "native"):
            raw_log = prior.read(z, prior.HOST_LOGS[side]).decode("utf-8")
            host_entries[side], frame_receipts[side] = prior.receipts(
                raw_log, side)
            trace = prior.read(z, prior.TRACE_LOGS[side]).decode("utf-8")
            prior.unique_trace(trace, SOURCE_RESTORE_OPCODE if side == "original"
                               else NATIVE_RESTORE_STORE)
            states[side] = {}
            for label in ("entry", *range(5156, 5164)):
                tag = "scene-entered" if label == "entry" else f"boundary-{label:05d}"
                samples = {}
                for memory in SIZES:
                    filename = f"{prior.DIRS[side]}/{tag}.{memory}.bin"
                    samples[memory] = prior.read(z, filename)
                states[side][label] = samples
        result = evaluate(states, entries=host_entries, frame_receipts=frame_receipts)
    result["original_native_executed_workflow"] = prior.SOURCE_RUN
    result["source_actions_artifact_id"] = prior.SOURCE_ARTIFACT
    result["artifact_zip_sha256"] = digest
    result["source_artifact_sha256_verified"] = digest == SHA
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifact", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    report = analyze(args.artifact)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "source_artifact_sha256_verified": report["source_artifact_sha256_verified"],
        "identical_memory_bytes": report["exact_matched_pair"]["total_identical_bytes"],
        "original_native_event_terminal_phase_equivalent": False,
        "release_complete_event_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
