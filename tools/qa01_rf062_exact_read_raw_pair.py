#!/usr/bin/env python3
"""Pair actual RF062 native read with independent original and raw frame labels.

This is a source-bound research *crosswalk*, not a claim that the differently
originated guest frame clocks or script dumps are CPU-instruction synchronous.
The genuine RF062 decoder/bus proof is rederived from the source ZIP + immutable
original RF054 baseline by qa01_rf062_sound_pc_report.report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

import qa01_rf062_sound_pc_report as sound_replay
import qa01_verify_frame_capture as raw_audit

SCHEMA = "ur-qa01-rf062-native-read-original-raw-frame-crosswalk/1"
FRAME_DIR = "work/zoom-zoo/replay/qa01-frame-evidence/"
ROM_DP_BYTES = (0x63, 0x64, 0x65, 0x69, 0x1ED, 0x1EE, 0x1EF, 0x1F0, 0x1F1)


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError(why)


def correlate(sound: dict, fingerprint: dict, independent: dict,
              retained: Path) -> dict:
    """Reopen both *whole frame* memories around actual guest frame 6124."""
    require(sound.get("schema") == "ur-qa01-rf062-source-opcode-direct-native-bus/1"
            and sound.get("actual_native_decoder_bound_read_count") == 10
            and sound.get("actual_source_and_native_11C774_consumed_byte_same") is True
            and sound.get("actual_native_opcode_pc") == "8282F0"
            and sound.get("original_native_clock_epochs_equivalent") is False
            and sound.get("complete_USA_events_accepted") == 0,
            "sound opcode/source proof absent, misidentified or overpromoted")
    target = [x for x in sound.get("native_reads", [])
              if x.get("native_physical_operand") == "11C774"]
    require(len(target) == 1
            and target[0].get("source_opcode_guest_PC") == "8282F0"
            and target[0].get("native_real_returned_byte") == "D0"
            and target[0].get("independent_rf054_real_helper_ordinal") == 492,
            "native actual read at 82:82F0 is absent or not source-bound")
    require(fingerprint.get("schema") == "ur-qa01-frame-fingerprint/1"
            and fingerprint.get("accepted_USA_events") == 0,
            "unqualified frame fingerprint/source event credit")
    identity, coverage = fingerprint["source_identity"], fingerprint["coverage"]
    require(identity.get("observation_phase") == "post-script-dump"
            and identity.get("masked_wram_bytes") == 0
            and identity.get("masked_sram_bytes") == 0,
            "wrong/masked original-native script-dump observation phase")
    require(coverage.get("continuous_at_declared_frame_phase") is True
            and coverage.get("between_frame_opcode_semantics_proven") is False
            and type(coverage.get("start")) is int
            and type(coverage.get("end")) is int
            and coverage.get("end") - coverage.get("start") + 1 ==
                coverage.get("required_frames") ==
                coverage.get("observed_native_frames") ==
                coverage.get("observed_original_frames"),
            "missing original/native frame continuity")
    require(len(fingerprint.get("rows", [])) == coverage["required_frames"],
            "frame row population missing")
    require(independent.get("schema") ==
                "ur-qa01-independent-frame-capture-audit/1"
            and independent.get("source_memory_bytes_independently_recomputed_for_retained_frames") is True
            and independent.get("whole_race_opcode_equivalence_proven") is False
            and independent.get("complete_USA_events_accepted") == 0
            and independent.get("source_sha") == identity.get("source_sha"),
            "independent raw-source verifier missing or overpromoted")
    rederived = raw_audit.verify(fingerprint, retained)
    for key in ("verified_raw_frames", "verified_raw_files",
                "verified_differing_byte_occurrences",
                "digest_only_equal_frames_not_independently_reopened",
                "fingerprint_report_canonical_sha256",
                "retained_raw_manifest_canonical_sha256",
                "source_sha"):
        require(rederived.get(key) == independent.get(key),
                "original/native independently recomputed raw bytes changed: " + key)
    require(identity.get("rom_sha256") == "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"
            and identity.get("movie_sha256") == "06dce29e9d36997fc2a1fac4bab72180ab6c8096366cfcf05780c1b2dea4b442",
            "raw captures not on original 2014 retail ROM/movie")
    result = {}
    for guest in ("original", "native"):
        origin = identity.get(guest + "_frame_origin")
        require(type(origin) is int, "missing independent actual guest frame origin")
        relative = 6124 - origin
        require(coverage["start"] <= relative <= coverage["end"],
                "no guest-specific relative offset for authentic sound execution frame")
        row = fingerprint["rows"][relative - coverage["start"]]
        require(row.get("relative_frame") == relative
                and row.get(guest + "_actual_host_frame") == 6124,
                "raw guest frame 6124 was not actually recorded")
        path = retained / f"{guest}-relative-{relative:06d}-wram.bin"
        require(path.is_file() and not path.is_symlink(),
                "genuine sound guest frame omitted from retained full raw memory")
        data = path.read_bytes()
        require(len(data) == 131072, "not a full physical 128KiB WRAM image")
        image_sha = hashlib.sha256(data).hexdigest()
        require(image_sha == row["types"]["wram"][guest + "_sha256"],
                "genuine original/native frame memory does not match fingerprint")
        result[guest] = {
            "guest_original_host_frame": 6124,
            "guest_relative_frame": relative,
            "frame_origin": origin,
            "full_Wram_sha256": image_sha,
            "actual_Wram_bytes_at_post_script_dump": {
                f"7E:{off:04X}": f"{data[off]:02X}" for off in ROM_DP_BYTES
            },
        }
    return {
        "schema": SCHEMA,
        "original_immutable_RF054_sound_opcode_attested": True,
        "native_real_CPU_read_pc": "82:82F0",
        "native_read_actual_address": "11:C774",
        "native_real_returned_byte": "D0",
        "native_bus_master_local": target[0]["native_independent_CPU_master"],
        "reopened_raw_images_each_guest_at_its_own_host_frame": result,
        "original_native_relative_frame_offsets_same": (
            result["original"]["guest_relative_frame"] ==
            result["native"]["guest_relative_frame"]),
        "raw_memory_observation_phase": "post-script-dump",
        "raw_sample_at_exact_CPU_bus_instruction_instant_proven": False,
        "original_native_instruction_clock_alignment_proven": False,
        "actual_guest_CPU_joypad_poll_equivalence_proven": False,
        "first_consumed_differing_original_native_Wram_byte_proven": False,
        "accepted_USA_events": 0,
    }



def validate_case_provenance(sound: dict, fingerprint: dict,
                             case: dict, producer: dict) -> None:
    """Require one real case for opcode, original source and raw host origins."""
    identity = fingerprint.get("source_identity", {})
    evidence = case.get("evidence", {})
    require(case.get("source_sha") == sound.get("candidate_source_sha") ==
                identity.get("source_sha"),
            "source identity differs between opcode and raw evidence")
    require(identity.get("rom_sha256") == evidence.get("rom_sha256") ==
                producer.get("rom_sha256") and
            identity.get("movie_sha256") == evidence.get("movie_sha256") ==
                producer.get("original_movie_sha256"),
            "ROM/movie differs between actual source/native run and raw evidence")
    require(identity.get("input_sha256") ==
                evidence.get("original_movie_window_sha256") ==
                producer.get("original_movie_window_sha256"),
            "input window identity differs between actual CPU trace and raw frames")
    require(type(evidence.get("reference_entry_frame")) is int and
            type(evidence.get("native_entry_frame")) is int and
            evidence["reference_entry_frame"] ==
                identity.get("original_frame_origin") and
            evidence["native_entry_frame"] ==
                identity.get("native_frame_origin"),
            "real original/native race-entry origins do not match captured raw")


def report(candidate: Path, baseline: Path, expected_sha: str | None = None) -> dict:
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if expected_sha is not None:
        require(digest == expected_sha, "candidate case archive SHA256 changed")
    # Reexecute the existing, source-binary/ROM/movie/CPU-bus-checked sound
    # producer audit instead of accepting someone else's asserted report.
    sound = sound_replay.report(candidate, baseline)
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        with zipfile.ZipFile(candidate) as z:
            names = z.namelist()
            case = json.loads(z.read("case-result.json"))
            producer = json.loads(z.read("producer-report.json"))
            require(len(names) == len(set(names)), "duplicate case ZIP members")
            require(FRAME_DIR + "fingerprints.json" in names
                    and FRAME_DIR + "independent-review.json" in names,
                    "no genuine continuous paired raw frame report")
            fps = json.loads(z.read(FRAME_DIR + "fingerprints.json"))
            audit = json.loads(z.read(FRAME_DIR + "independent-review.json"))
            # Matching per-run provenance is an independently unit-tested
            # *positive requirement*, never inherited from a prior experiment.
            validate_case_provenance(sound, fps, case, producer)
            for x in fps.get("raw_retained_members", []):
                member = x.get("member", "")
                require(type(member) is str and
                        Path(member).name == member and
                        member and ".." not in Path(member).parts,
                        "unsafe retained raw source member")
                name = FRAME_DIR + "retained/" + member
                require(name in names and
                        z.getinfo(name).file_size in (8192, 131072),
                        "missing full original/native WRAM/SRAM ZIP member")
                (directory / member).write_bytes(z.read(name))
        result = correlate(sound, fps, audit, directory)
    result["actual_case_archive_sha256"] = digest
    result["immutable_rf054_baseline_zip_sha256"] = sound["baseline_zip_sha256"]
    result["case_source_sha"] = sound["candidate_source_sha"]
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--expect-sha256")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = report(args.candidate, args.baseline, args.expect_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("RF062 actual native 82:82F0 + genuine original RF054 + two raw host6124 frames; USA HOLD")


if __name__ == "__main__":
    main()
