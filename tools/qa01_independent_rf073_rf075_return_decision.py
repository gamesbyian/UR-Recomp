#!/usr/bin/env python3
"""Independently cross-qualify two genuine but DIFFERENT NMI evidence epochs.

RF073: original/native source-authentic 9 live NMI brackets from RF054 ZIP.
RF075: compiled/interpreted RTI source ABI proven in a separate pinned
immutable source-contract ZIP. Never equate the independent original/native
CPU clocks, compiled emitter semantics with executed opcode fetches, or
different guest binary epochs. ROM bytes are neither needed nor copied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import qa01_rf073_native_nmi_brackets as rf073
import qa01_rf075_native_rti_source_contract as rf075

SCHEMA = "ur-qa01-independent-rf073-rf075-static-live-NMI-decision/1"
SOURCE_ABI_ZIP_SHA256 = "b199009e3c7c924e0bd6a7d1842311296ce0bcc2afd8137b9980e1863db54e39"
SOURCE_ABI_MEMBER = "pinned-native-interpreted-rti-source-contract.json"
NMI_ZIP_SHA256 = rf073.ARCHIVE_SHA256


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def read_source_abi(path: Path) -> dict:
    require(sha256(path.read_bytes()) == SOURCE_ABI_ZIP_SHA256,
            "RF075 genuine source contract archive identity changed")
    with zipfile.ZipFile(path) as z:
        require(z.namelist() == [SOURCE_ABI_MEMBER] and z.testzip() is None,
                "RF075 exact single-source receipt archive incomplete or corrupt")
        obj = json.loads(z.read(SOURCE_ABI_MEMBER))
    return qualify_source_abi(obj)


def qualify_source_abi(obj: dict) -> dict:
    needed = {
        "schema": "ur-qa01-rf075-original-source-native-RTI-ABI-static-contract/1",
        "pinned_upstream_snesrecomp": rf075.UPSTREAM,
        "pinned_all_five_unmodified_source_blobs_verified": True,
        "compiled_RTI_guest_status_load_count": 1,
        "compiled_RTI_guest_saved_PC_load_count": 0,
        "compiled_RTI_guest_saved_PB_load_count": 0,
        "compiled_RTI_guest_PC_PB_discarded_by_stack_advance": True,
        "compiled_RTI_returns_via_host_C_control_flow": True,
        "interpreted_RTI_stacked_status_PC_PB_restored": True,
        "interrupt_push_writes_actual_provided_resume_PC_bytes": True,
        "host_interrupt_push_before_dispatch_before_scheduler_resume_update": True,
        "any_such_guest_stack_rewrite_actually_observed": False,
        "original_native_equivalent_interruption_instruction_phase_proven": False,
        "native_actual_fetched_opcode_pc_proven": False,
        "first_actually_consumed_differing_byte_proven": False,
        "all_gameplay_frames_equal": False,
        "accepted_USA_events": 0,
        "accepted_Windows_QA_gates": 0,
    }
    for key, value in needed.items():
        require(type(obj.get(key)) is type(value) and obj[key] == value,
                "RF075 genuine source ABI claim changed: " + key)
    identity = {p: git for _, (p, git) in rf075.FILES.items()}
    require(obj.get("exact_upstream_source_git_blobs") == identity,
            "RF075 genuine source compiler/runtime five Git blob identities differ")
    return obj


def decide(native_receipt: dict, abi: dict) -> dict:
    qualify_source_abi(abi)
    require(native_receipt["schema"] == rf073.SCHEMA and
            native_receipt["exact_authenticated_RF054_zip_sha256"] == NMI_ZIP_SHA256 and
            native_receipt["native_RF047_event_count"] == 2741 and
            native_receipt["authentic_native_NMI_frame_count"] == 9 and
            native_receipt["native_compiled_NMI_brackets_with_one_actual_status_helper_read"] == 9 and
            native_receipt["native_saved_PC_or_PB_helper_reads_between_push_and_compiled_RTI"] == 0 and
            native_receipt["original_native_same_intra_frame_semantic_phase_proven"] is False and
            native_receipt["source_original_native_NMI_saved_PC_low_differences"] == 4,
            "RF073 actual historical original/native NMI coverage or status changed")
    brackets = native_receipt["brackets"]
    require([row["native_frame"] for row in brackets] == list(rf073.FRAMES),
            "RF073 nine original/native frame brackets missing or reordered")
    frames = []
    for row in brackets:
        original = bytes.fromhex(row["original_post_real_NMI_raw_5_stack_bytes"])
        native = bytes.fromhex(row["native_after_push_raw_4_bytes"])
        require(len(original) == 5 and len(native) == 4 and
                original[0] == native[0] == 0x26 and
                original[3] == native[3] == 0x82 and
                native[1:3] == bytes.fromhex("EED4") and
                row["native_true_status_stack_helper_read_value"] == "0026" and
                row["original_native_intra_frame_semantic_phase_proven_equal"] is False,
                "RF073 original/native true stack byte bracket cannot be qualified")
        src_pc = (original[3] << 16) | (original[2] << 8) | original[1]
        native_saved_pc = (native[3] << 16) | (native[2] << 8) | native[1]
        require(src_pc in (0x82D4EE, 0x82D4F0) and native_saved_pc == 0x82D4EE and
                row["original_native_PC_low_byte_differ_in_paired_host_frame"] is
                    (src_pc != native_saved_pc),
                "RF073 source/native host-frame PC observation counterexample changed")
        frames.append({
            "host_frame_label": row["native_frame"],
            "original_observed_saved_PC_24": f"{src_pc:06X}",
            "native_actual_after_push_saved_PC_24": f"{native_saved_pc:06X}",
            "host_frame_snapshot_PC_low_bytes_differ": src_pc != native_saved_pc,
            "native_compiled_RTI_true_status_helper_value": "26",
            "native_compiled_RTI_saved_PC_PB_guest_loads_by_pinned_source": 0,
            "native_compiled_RTI_continuation_is_scheduler_owned": True,
            "native_actual_fetched_resume_opcode_PC_observed_here": False,
            "same_semantic_interrupt_stage_original_native_qualified": False,
            "same_original_native_guest_binary_epoch_for_RF073_and_RF075": False,
        })
    require(sum(row["host_frame_snapshot_PC_low_bytes_differ"] for row in frames)==4,
            "RF073 four host-frame original/native saved-PC discrepancies changed")
    return {
        "schema": SCHEMA,
        "RF073_live_original_native_Zoo_case_zip_sha256": NMI_ZIP_SHA256,
        "RF075_exact_source_contract_archive_sha256": SOURCE_ABI_ZIP_SHA256,
        "RF075_pinned_native_codegen_source_commit": rf075.UPSTREAM,
        "historical_native_NMI_actual_handler_status_reads": len(frames),
        "historical_native_saved_PC_PB_helper_reads_during_compiled_RTI": 0,
        "pinned_compiled_native_RTI_guest_saved_PC_PB_load_count": 0,
        "pinned_interpreted_RTI_restores_saved_PC_PB": True,
        "original_native_host_frame_saved_PC_low_differences": 4,
        "native_saved_PC_PB_discrepancy_directly_changes_compiled_RTI_target_proven": False,
        "conditional_future_failure_if_scheduler_PC_differs_from_architectural_PC": True,
        "conditional_future_failure_if_stack_return_modified_in_game": True,
        "same_binary_original_native_NMI_phase_qualified": False,
        "actual_guest_stack_return_rewritten_in_real_Uniracers_proven": False,
        "actual_scheduler_resume_equal_to_original_interrupted_fetch_PC_proven": False,
        "true_native_architectural_RTI_fetch_PC_observed_here": False,
        "no_instruction_time_guest_memory_byte_masks_or_clock_adjustments": True,
        "accepted_USA_events": 0,
        "accepted_Windows_QA_gates": 0,
        "adjudication": "HOLD: static compiled return semantics + separately observed native NMI cannot establish original/native execution-phase or gameplay divergence",
        "required_next_single_case": [
            "one exact source ROM/2014 original movie/input and compiled original/native executable pair",
            "same semantic original/native NMI before-push PC and 5 raw stack bytes",
            "native scheduler resume assignment versus independently decoded interrupted fetched guest opcode PC",
            "first native RTI status and actual PC/PB returned values or demonstrated compiled ABI skip",
            "real original source getter-entry and returned values plus first observed stack overwrite",
            "continuous unmasked original/native full-race memory and exact Windows earned cold disk witness",
        ],
        "frame_label_observations_not_joinable_across_guest_clocks": frames,
    }


def audit(native_case: Path, source_contract: Path) -> dict:
    native = rf073.authenticated_case(native_case)
    contract = read_source_abi(source_contract)
    result = decide(native, contract)
    result["RF073_native_executable_sha256"] = native["native_executable_sha256"]
    result["RF073_original_core_sha256"] = native["original_core_sha256"]
    result["RF073_original_movie_sha256"] = native["original_movie_sha256"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rf054-case", type=Path, required=True)
    parser.add_argument("--rf075-source-contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.rf054_case, args.rf075_source_contract)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2)+"\n")
    print("Independent nine RF073 native brackets + pinned RF075 compiled RTI ABI: HOLD, 0/45")


if __name__ == "__main__":
    main()
