#!/usr/bin/env python3
"""Independently separate RF062 runtime logging from cross-epoch/native wrapper effects.

Reopens FOUR immutable genuine ZIP archives: RF066 and RF062 full raw Zoo,
the same-native-binary logging ON/OFF case, and its compiled guest binaries.
May certify bounded *runtime logging* noninterference only. An unexecuted
wrapper-substitution comparison and a cross-binary WRAM change are different
scientific questions and MUST stay unproved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import qa01_rf062_same_binary_ab as logging_ab
import qa01_rf066_rf062_full_raw_crosswalk as epochs
import qa01_rf062_real_read_raw_archive as reads

SCHEMA = "ur-qa01-rf062-distinct-controls-runtime-logging-versus-cross-epoch/1"
AB_ZIP = "b94660b8ffb0cfb1cd35ec9fe3a3c1c8c6b44a46d865272b8cfdad2e62078cbd"
AB_BINARY_ZIP = "83233faded8aa546025f59abe50c9ba29f109250f5bcafb2e20cdb5d7780bc37"
TARGET_NATIVE_BINARY = "31790cd408950ef20153031b5633f4045aa753368f6b94170ece607b5950a53a"
PINNED_ROM = "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478"


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError(why)


def classify(ab: dict, cross: dict, executed: dict, report: dict,
             actual_case_inputs: dict[str, str]) -> dict:
    """Pure strict evidence judgment, exercised by adversarial ROM-free tests."""
    compiled = ab.get("independently_reopened_compiled_binaries")
    require(ab.get("schema") == logging_ab.SCHEMA and
            ab.get("authenticated_evidence_archive_sha256") == AB_ZIP and
            ab.get("zip_archive_raw_byte_reopened") is True and
            ab.get("runtime_RF062_logging_noninterference_supported") is True and
            ab.get("wrapper_replacement_noninterference_proven") is False and
            ab.get("USA_events_accepted") == 0 and
            ab.get("native_real_sound_helper_count_off_on") == [655,655] and
            ab.get("native_sound_helper_matching_ordered_observations") == 655 and
            ab.get("native_actual_RF054_address_and_register_rows_equal") is True and
            ab.get("native_actual_RF054_CPU_master_clocks_equal") is True and
            ab.get("original_native_whole_mesh_and_followthrough_equal") is True and
            ab.get("rf062_actual_native_read_count_off_on") == [0,10] and
            ab.get("original_qualified_source_log_path_differences",{})
              .get("source_nonpath_log_equality_proven") is True and
            ab.get("native_complete_nonRF062_log_metadata_limited_comparison",{})
              .get("all_other_native_lines_byte_equal_after_strict_host_metadata") is True,
            "genuine runtime logging on/off no longer has identical bounded source/native observations")
    require(type(compiled) is dict and
            compiled.get("binary_artifact_SHA256") == AB_BINARY_ZIP and
            compiled.get("actual_native_binary_SHA256") == TARGET_NATIVE_BINARY and
            compiled.get("all_three_emulator_tool_binaries_rehashed") is True,
            "original/native compiled executable provenance for logging A/B differs")
    require(cross.get("schema") == epochs.SCHEMA and
            cross.get("earlier_RF066_case_zip_sha256") == epochs.RF066_SHA and
            cross.get("later_RF062_case_zip_sha256") == epochs.RF062_SHA and
            cross.get("complete_source_guest_Wram_Sram_archive_members_reopened") == 388 and
            cross.get("both_original_and_native_input_file_bytes_equal_across_epochs") is True and
            cross.get("original_guest_binary_changed") is True and
            cross.get("native_guest_binary_changed") is True and
            cross.get("per_guest_memory_type_changed_image_counts") ==
              {"ref_wram":0,"ref_sram":0,"native_wram":15,"native_sram":0} and
            cross.get("per_guest_memory_type_changed_byte_occurrences") ==
              {"ref_wram":0,"ref_sram":0,"native_wram":77,"native_sram":0} and
            cross.get("causal_reason_for_cross_epoch_native_stack_or_DP_byte_change_proven") is False and
            cross.get("instrumentation_on_off_same_binary_family_noninterference_proven") is False and
            cross.get("full_USA_events_accepted") == 0 and
            cross.get("release_QA_gates") == 0,
            "full native memory cross-epoch data missing or causality falsely upgraded")
    require(report.get("native_executable_sha256") == TARGET_NATIVE_BINARY and
            report.get("native_executable_sha256") == compiled["actual_native_binary_SHA256"] and
            report.get("rom_sha256") == PINNED_ROM and
            report.get("reference_entry") == 1017 and
            report.get("native_entry") == 1017,
            "true RF062 native 82:82F0 case not bound to same logging A/B binary")
    require(type(actual_case_inputs) is dict and
            set(actual_case_inputs) == {"original","native"} and
            ab.get("actual_supplied_input_sha256") == actual_case_inputs and
            all(type(value) is str and len(value) == 64
                for value in actual_case_inputs.values()),
            "logging native executable shares RF062 but supplied original/native controller bytes differ")
    require(executed.get("source_bound_native_read_count") == 10 and
            executed.get("frame_6124_real_helper_read_count") == 655 and
            executed["native_read_rows"][4]["native_returned_byte"] == "D0" and
            executed["native_read_rows"][4]["native_read_address"] == "11C774",
            "actual RF062 native 82:82F0 helper census/return changed")
    return {
        "schema": SCHEMA,
        "source_actual_RF066_case_SHA256": epochs.RF066_SHA,
        "source_actual_RF062_case_SHA256": epochs.RF062_SHA,
        "source_same_native_binary_logging_ab_case_SHA256": AB_ZIP,
        "source_reopened_emulator_binaries_SHA256": AB_BINARY_ZIP,
        "same_actual_native_binary_SHA256_in_RF062_and_logging_ab": TARGET_NATIVE_BINARY,
        "original_native_supplied_guest_input_SHA256_same_in_RF062_and_logging_ab":
            actual_case_inputs,
        "logging_toggle_native_helper_counts_off_on": [655,655],
        "real_native_8282F0_direct_read_counts_off_on": [0,10],
        "real_native_operand_11C774_returned": "D0",
        "helper_address_register_master_clock_sequence_unchanged_under_logging": True,
        "guest_mesh_and_successor_samples_unchanged_under_logging": True,
        "historical_RF066_to_instrumented_RF062_78_mesh_exact": [
            cross["earlier_RF066_original_native_race_mesh"]["raw_byte_exact_race_mesh_pairs"],
            cross["later_RF062_original_native_race_mesh"]["raw_byte_exact_race_mesh_pairs"]],
        "historical_RF066_to_instrumented_RF062_78_mesh_unmasked_byte_differences": [
            cross["earlier_RF066_original_native_race_mesh"]["unmasked_guest_race_mesh_WRAM_byte_occurrences"],
            cross["later_RF062_original_native_race_mesh"]["unmasked_guest_race_mesh_WRAM_byte_occurrences"]],
        "different_binary_episodes_native_Wram_changed_files":15,
        "different_binary_episodes_native_Wram_changed_bytes":77,
        "historical_656_vs_655_missing_helper_attributed_to_logging":False,
        "different_binary_epoch_native_Wram_change_cause_proven":False,
        "RF062_read_wrapper_replacement_noninterference_proven":False,
        "native_unmodified_noninstrumented_guest_instruction_parity_proven":False,
        "first_source_native_differing_consumed_byte_proven":False,
        "full_USA_events_accepted":0,
        "release_QA_gates":0,
        "adjudication":"HOLD: runtime logging alone is bounded nonperturbing; same-binary-family wrapper substitution and native/source gameplay remain unresolved",
    }


def audit(rf066: Path, rf062: Path, ab_case: Path, ab_binaries: Path) -> dict:
    # All three source-episode case ZIPs and the original/native compiled
    # binary archive must be checked against their published immutable pins.
    cross = epochs.audit(rf066,rf062)
    logging = logging_ab.archived(ab_case,AB_ZIP,ab_binaries,AB_BINARY_ZIP)
    with epochs.audited_zip(rf062, epochs.RF062_SHA, 407) as z:
        report = json.loads(z.read("producer-report.json"))
        executed = reads.observed_native_reads(
            z.read(reads.NATIVE).decode("utf-8"))
        actual_inputs = {
            guest: hashlib.sha256(z.read(
                "work/zoom-zoo/replay/" + path)).hexdigest()
            for guest,path in (("original","ref.input"),
                               ("native","pinned-baldosa.input"))
        }
    return classify(logging,cross,executed,report,actual_inputs)


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("rf066","rf062","ab-case","ab-binaries","output"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    require(not a.output.exists(),"refuse overwrite of reviewed evidence")
    result=audit(a.rf066,a.rf062,a.ab_case,a.ab_binaries)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("QA01 real RF062 logging positive distinct from wrapper substitution unknown; 0/45")


if __name__ == "__main__":
    main()
