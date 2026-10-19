#!/usr/bin/env python3
"""QA01 exact independent raw-memory noninterference across RF064 -> RF066.

Reopen and compare EVERY actual original/native WRAM+SRAM image retained in
two exact source-authentic ZIPs. No interpolation or event acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

SCHEMA = "ur-qa01-rf064-rf066-all-retained-raw-crosswalk/1"
RF064_SHA = "7891a24124c67f414e9b00ed2bb1dbe2e59e4a2b6c50b558e920c25d885e63ea"
RF066_SHA = "494737bb6a1c422141c40f7175883f212767c3d774ee63fb0ba82add78cb445f"
RAW_ROOT = "work/zoom-zoo/replay/"
PINNED_IMAGES = 388
PINNED_RAW_BYTES = 27017216
W_SIZE, S_SIZE = 131072, 8192
INPUT_IDENTITY = (
    "rom_sha256", "original_movie_sha256", "source_sram_sha256",
    "input_sha256", "original_movie_window_sha256", "native_executable_sha256",
)
CONTROL_INPUT = (
    "controller_movie_window_sha256", "reference_supplied_input_sha256",
    "native_supplied_input_sha256", "reference_supplied_input_bytes",
    "native_supplied_input_bytes",
)


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def raw_names(z: zipfile.ZipFile) -> set[str]:
    return {name for name in z.namelist() if name.startswith(RAW_ROOT)
            and (name.endswith(".wram.bin") or name.endswith(".sram.bin"))}


def compare_images(before: zipfile.ZipFile, after: zipfile.ZipFile,
                   *, required_count: int) -> dict:
    names_before, names_after = raw_names(before), raw_names(after)
    require(names_before == names_after and
            len(names_before) == required_count and required_count > 0,
            "original/native memory image coverage changed or is incomplete")
    count_bytes = 0
    same_guest: dict[str, int] = {}
    for name in sorted(names_before):
        size = W_SIZE if name.endswith(".wram.bin") else S_SIZE
        old, new = before.read(name), after.read(name)
        require(len(old) == len(new) == size,
                "raw retained original/native WRAM/SRAM size changed")
        require(old == new,
                "RF066 genuine original/native raw memory diverged at " + name)
        count_bytes += size
        guest = name[len(RAW_ROOT):].split("/", 1)[0]
        require(guest in ("ref", "native"),
                "unknown original/native raw guest label")
        same_guest[guest] = same_guest.get(guest, 0) + 1
    require(same_guest.get("ref") == same_guest.get("native") ==
            required_count // 2, "unpaired original/native memory population")
    return {"retained_original_native_raw_image_count": required_count,
            "reopened_actual_memory_bytes": count_bytes,
            "byte_differences_between_RF064_and_RF066": 0,
            "per_guest_identical_image_counts": same_guest}


def checked_zip(path: Path, sha: str) -> zipfile.ZipFile:
    require(digest(path.read_bytes()) == sha, "wrong exact source-authentic ZIP")
    z = zipfile.ZipFile(path)
    infos = z.infolist()
    require(len(infos) <= 1000 and
            len(infos) == len(set(entry.filename for entry in infos)) and
            all(not x.is_dir() and not x.filename.startswith("/") and
                ".." not in Path(x.filename).parts and x.file_size <= 2_000_000
                for x in infos) and z.testzip() is None,
            "unsafe, duplicate or corrupt source-authentic ZIP member")
    return z


def audit(before: Path, after: Path) -> dict:
    with checked_zip(before, RF064_SHA) as a, checked_zip(after, RF066_SHA) as b:
        pa, pb = json.loads(a.read("producer-report.json")), json.loads(
            b.read("producer-report.json"))
        require(pa.get("name") == pb.get("name") == "zoom-zoo" and
                all(pa.get(key) == pb.get(key) for key in INPUT_IDENTITY),
                "source ROM, SMV, guest controller stream or native ELF changed")
        ca, cb = (p["qa01_capture_ab_control"] for p in (pa, pb))
        require(all(ca.get(key) == cb.get(key) for key in CONTROL_INPUT) and
                not ca.get("capturing_continuous_frames") and
                not cb.get("capturing_continuous_frames") and
                ca.get("repository_source_sha") != cb.get("repository_source_sha") and
                pa.get("reference_core_sha256") != pb.get("reference_core_sha256"),
                "not distinct source-instrumentation epochs sharing original inputs")
        for key in ("reference_entry", "native_entry", "comparison",
                    "zoo_race_mesh", "zoo_next_bowl_handoff",
                    "source_terminal_followthrough", "reference", "native"):
            require(pa.get(key) == pb.get(key),
                    "different game result or source/native sampled state: " + key)
        samples = compare_images(a, b, required_count=PINNED_IMAGES)
        require(samples["reopened_actual_memory_bytes"] == PINNED_RAW_BYTES,
                "incomplete genuine 27 MB original/native memory replay")
        qa, qb = (
            json.loads(z.read("qa01-zoo-independent-raw-audit.json"))
            for z in (a, b))
        require(all(q["full_zoo_mesh_rehashed_original_native_128k_pairs"] == 78 and
                    q["full_zoo_mesh_exact_pairs"] == 51 and
                    q["full_zoo_mesh_nonexact_pairs"] == 27 and
                    q["full_zoo_mesh_unmasked_differing_byte_occurrences"] == 92
                    for q in (qa, qb)) and
                pa["zoo_race_mesh"]["raw_byte_exact_sample_count"] == 51 and
                pb["zoo_race_mesh"]["raw_byte_exact_sample_count"] == 51,
                "independent 78-point race baseline changed between original guest epochs")
        return {
            "schema": SCHEMA, "rf064_case_zip_sha256": RF064_SHA,
            "rf066_case_zip_sha256": RF066_SHA,
            "source_code_sha_changed": True,
            "compiled_original_core_sha_changed": True,
            "native_compiled_elf_and_supplied_controller_inputs_unchanged": True,
            "exact_reported_original_native_game_semantics_unchanged": True,
            **samples,
            "actual_original_stack_getset_read_entries_proven": False,
            "whole_course_continuous_frame_equality_proven": False,
            "original_native_actual_CPU_joypad_reads_proven": False,
            "exact_windows_release_candidate_proven": False,
            "accepted_USA_events": 0, "release_QA_gates": 0,
            "adjudication": "HOLD",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rf064", type=Path, required=True)
    parser.add_argument("--rf066", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.rf064, args.rf066)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("RF064→RF066 actual raw images re-opened; zero complete event credit")


if __name__ == "__main__":
    main()
