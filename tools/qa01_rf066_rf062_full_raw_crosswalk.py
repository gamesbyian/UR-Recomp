#!/usr/bin/env python3
"""QA01 genuine RF066→RF062 same-input, cross-epoch *raw* image census.

Full 388 retained WRAM/SRAM members from two independently pinned original/
native 2014 Zoom Zoo producer ZIPs. Compare raw bytes, never inferred CPU
reads. Different original AND native ELF binaries mean changed native WRAM
cannot automatically be assigned to RF062 probe overhead.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import stat
import zipfile

SCHEMA = "ur-qa01-rf066-to-rf062-actual-original-native-all-raw-crosswalk/1"
RF066_SHA = "494737bb6a1c422141c40f7175883f212767c3d774ee63fb0ba82add78cb445f"
RF062_SHA = "b8287234d2fe515ee32b19b3d2a9b0e1bb58104b437de3a5cbe2e32e3af093ff"
ROOT = "work/zoom-zoo/replay/"
GUESTS = ("ref", "native")
KINDS = ("wram", "sram")
BYTES = {"wram": 131072, "sram": 8192}
IMAGE_COUNT = 388
GUEST_PAIR_COUNT = 97
MESH_COUNT = 78
CONTROL = ("rom_sha256", "original_movie_sha256", "original_movie_window_sha256",
           "input_sha256", "source_sram_sha256")
SAME_INPUT_FILES = (ROOT + "ref.input", ROOT + "pinned-baldosa.input")
NAME = re.compile(r"work/zoom-zoo/replay/(ref|native)/([A-Za-z0-9-]+)\.(wram|sram)\.bin\Z")


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError(why)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def raw_names(z: zipfile.ZipFile) -> set[str]:
    return {n for n in z.namelist() if NAME.fullmatch(n) is not None}


def audited_zip(path: Path, expected: str, members: int) -> zipfile.ZipFile:
    require(path.is_file() and not path.is_symlink() and sha(path.read_bytes()) == expected,
            "immutable source-original/native ZIP SHA256 mismatch")
    z = zipfile.ZipFile(path)
    info = z.infolist()
    require(len(info) == members and len({x.filename for x in info}) == members
            and z.testzip() is None and
            all(not x.is_dir() and not stat.S_ISLNK(x.external_attr >> 16)
                and x.file_size <= 12_000_000 and
                not x.filename.startswith("/") and ".." not in Path(x.filename).parts
                for x in info),
            "unsafe/duplicate/corrupt/unexpected genuine archived member count")
    return z


def byte_mismatches(original: bytes, new: bytes, *, kind: str) -> list[tuple[int, int, int]]:
    require(kind in BYTES and len(original) == len(new) == BYTES[kind],
            "missing or truncated original/native full memory image")
    return [(i, a, b) for i, (a, b) in enumerate(zip(original, new)) if a != b]


def physical(kind: str, index: int) -> str:
    if kind == "sram":
        return f"SRAM:{index:04X}"
    return f"{'7E' if index < 65536 else '7F'}:{index % 65536:04X}"


def crosswalk(before: zipfile.ZipFile, after: zipfile.ZipFile,
              *, count: int = IMAGE_COUNT) -> dict:
    names0, names1 = raw_names(before), raw_names(after)
    require(names0 == names1 and len(names0) == count and count % 4 == 0,
            "incomplete genuine source/native raw checkpoint population")
    all_tags = {k: set() for k in GUESTS}
    same_image = Counter()
    different_image = Counter()
    different_bytes = Counter()
    addresses = Counter()
    changed = []
    for name in sorted(names0):
        match = NAME.fullmatch(name)
        require(match is not None, "unexpected original/native raw name")
        guest, tag, kind = match.groups()
        all_tags[guest].add((tag, kind))
        old, new = before.read(name), after.read(name)
        deltas = byte_mismatches(old, new, kind=kind)
        identity = guest + "_" + kind
        if deltas:
            different_image[identity] += 1
            different_bytes[identity] += len(deltas)
            observed = [{"address": physical(kind, i),
                         "RF066": f"{a:02X}", "RF062": f"{b:02X}"}
                        for i, a, b in deltas]
            for item in observed:
                addresses[item["address"]] += 1
            changed.append({"member": name, "guest": guest, "type": kind,
                            "unmasked_byte_occurrences": len(deltas),
                            "observed_original_source_epochs": observed})
        else:
            same_image[identity] += 1
    require(all_tags["ref"] == all_tags["native"] and
            sum(1 for tag, kind in all_tags["ref"] if kind == "wram") == count//4 and
            sum(1 for tag, kind in all_tags["ref"] if kind == "sram") == count//4,
            "original/native WRAM/SRAM checkpoint membership not paired")
    keys = [guest+"_"+kind for guest in GUESTS for kind in KINDS]
    return {
        "complete_source_guest_Wram_Sram_archive_members_reopened": count,
        "per_guest_memory_type_identical_image_counts": {
            k: same_image[k] for k in keys},
        "per_guest_memory_type_changed_image_counts": {
            k: different_image[k] for k in keys},
        "per_guest_memory_type_changed_byte_occurrences": {
            k: different_bytes[k] for k in keys},
        "changed_byte_addresses_across_two_source_epochs": dict(sorted(addresses.items())),
        "changed_image_members": changed,
    }


def within_case(z: zipfile.ZipFile) -> dict:
    names = raw_names(z)
    tags = sorted({NAME.fullmatch(n).group(2) for n in names})
    mesh = []
    unequal = 0
    for tag in tags:
        if tag != "race-entered" and re.fullmatch("scene-[0-9]{5}", tag) is None:
            continue
        name0 = ROOT + "ref/" + tag + ".wram.bin"
        name1 = ROOT + "native/" + tag + ".wram.bin"
        require(name0 in names and name1 in names,
                "unpaired race scene raw original/native images")
        mismatches = byte_mismatches(z.read(name0), z.read(name1), kind="wram")
        mesh.append((tag, len(mismatches)))
        unequal += len(mismatches)
    require(len(mesh) == MESH_COUNT, "78 real original/native checkpoint pairs absent")
    return {
        "actual_original_native_race_mesh_pairs": len(mesh),
        "raw_byte_exact_race_mesh_pairs": sum(n == 0 for _, n in mesh),
        "raw_byte_unequal_race_mesh_pairs": sum(n != 0 for _, n in mesh),
        "unmasked_guest_race_mesh_WRAM_byte_occurrences": unequal,
        "first_unequal_checkpoint": next(
            ({"tag": tag, "differing_bytes": n} for tag, n in mesh if n), None),
        "late_sound_pointer_dump_differences": [
            {"relative_frame": int(tag.split("-")[1]),
             "unmasked_WRAM_differences": n}
            for tag, n in mesh
            if tag.startswith("scene-0504")],
    }


def audit(before: Path, after: Path) -> dict:
    with audited_zip(before, RF066_SHA, 411) as old, \
         audited_zip(after, RF062_SHA, 407) as new:
        p0, p1 = [json.loads(z.read("producer-report.json")) for z in (old,new)]
        case0, case1 = [json.loads(z.read("case-result.json")) for z in (old,new)]
        require(p0["name"] == p1["name"] == "zoom-zoo" and
                p0["course_id"] == p1["course_id"] == "course:02" and
                all(p0[k] == p1[k] for k in CONTROL) and
                p0["reference_entry"] == p1["reference_entry"] == 1017 and
                p0["native_entry"] == p1["native_entry"] == 1017,
                "original/native source movie, host origins or controller changed")
        require(all(old.read(n) == new.read(n) for n in SAME_INPUT_FILES),
                "actual original/native guest controller transport changed")
        require(case0["disposition"] == case1["disposition"] == "strict_candidate" and
                case0["release_credit"] == case1["release_credit"] == 0 and
                case0["source_sha"] != case1["source_sha"] and
                p0["reference_core_sha256"] != p1["reference_core_sha256"] and
                p0["native_executable_sha256"] != p1["native_executable_sha256"],
                "not two distinct original/native source instrumentation/binary epochs")
        raw = crosswalk(old,new)
        p0mesh = within_case(old)
        p1mesh = within_case(new)
        for z, receipt, own in ((old,p0mesh,p0),(new,p1mesh,p1)):
            source = json.loads(z.read("qa01-zoo-independent-raw-audit.json"))
            require(source["full_zoo_mesh_rehashed_original_native_128k_pairs"] ==
                    receipt["actual_original_native_race_mesh_pairs"] and
                    source["full_zoo_mesh_exact_pairs"] ==
                    receipt["raw_byte_exact_race_mesh_pairs"] and
                    source["full_zoo_mesh_unmasked_differing_byte_occurrences"] ==
                    receipt["unmasked_guest_race_mesh_WRAM_byte_occurrences"] and
                    own["zoo_race_mesh"]["raw_byte_exact_sample_count"] ==
                    receipt["raw_byte_exact_race_mesh_pairs"] and
                    source["accepted_usa_events"] == 0,
                    "original/native actual raw recomputation contradicts producer receipt")
    return {
        "schema": SCHEMA,
        "earlier_RF066_case_zip_sha256": RF066_SHA,
        "later_RF062_case_zip_sha256": RF062_SHA,
        "original_guest_binary_changed": True,
        "native_guest_binary_changed": True,
        "2014_original_ROM_movie_controller_and_guest_origin_claims_equal": True,
        "both_original_and_native_input_file_bytes_equal_across_epochs": True,
        **raw,
        "earlier_RF066_original_native_race_mesh": p0mesh,
        "later_RF062_original_native_race_mesh": p1mesh,
        "causal_reason_for_cross_epoch_native_stack_or_DP_byte_change_proven": False,
        "instrumentation_on_off_same_binary_family_noninterference_proven": False,
        "original_native_instruction_time_read_parity_proven": False,
        "all_frame_original_native_Wram_parity_proven": False,
        "full_USA_events_accepted": 0,
        "release_QA_gates": 0,
        "adjudication": "HOLD: cross-epoch native WRAM changed; unchanged controls insufficient to attribute cause",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rf066", type=Path, required=True)
    ap.add_argument("--rf062", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    require(not args.output.exists(), "refuse overwrite of independently reviewed result")
    result = audit(args.rf066,args.rf062)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("QA01 real cross-epoch 388-image provenance: native WRAM different; no cause inferred")


if __name__ == "__main__":
    main()
