"""ROM-free negative acceptance tests for four distinct RF062 evidence sources."""
from __future__ import annotations
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
import qa01_rf062_evidence_factorization as gate


def fixture():
    a={
        "schema":"ur-qa01-rf062-same-executable-logging-ab/1",
        "authenticated_evidence_archive_sha256":gate.AB_ZIP,
        "zip_archive_raw_byte_reopened":True,
        "runtime_RF062_logging_noninterference_supported":True,
        "wrapper_replacement_noninterference_proven":False,
        "USA_events_accepted":0,
        "native_real_sound_helper_count_off_on":[655,655],
        "native_sound_helper_matching_ordered_observations":655,
        "native_actual_RF054_address_and_register_rows_equal":True,
        "native_actual_RF054_CPU_master_clocks_equal":True,
        "original_native_whole_mesh_and_followthrough_equal":True,
        "rf062_actual_native_read_count_off_on":[0,10],
        "original_qualified_source_log_path_differences":{
            "source_nonpath_log_equality_proven":True},
        "native_complete_nonRF062_log_metadata_limited_comparison":{
            "all_other_native_lines_byte_equal_after_strict_host_metadata":True},
        "independently_reopened_compiled_binaries":{
            "binary_artifact_SHA256":gate.AB_BINARY_ZIP,
            "actual_native_binary_SHA256":gate.TARGET_NATIVE_BINARY,
            "all_three_emulator_tool_binaries_rehashed":True},
    }
    raw={
        "schema":gate.epochs.SCHEMA,
        "earlier_RF066_case_zip_sha256":gate.epochs.RF066_SHA,
        "later_RF062_case_zip_sha256":gate.epochs.RF062_SHA,
        "complete_source_guest_Wram_Sram_archive_members_reopened":388,
        "both_original_and_native_input_file_bytes_equal_across_epochs":True,
        "original_guest_binary_changed":True,
        "native_guest_binary_changed":True,
        "per_guest_memory_type_changed_image_counts":{
            "ref_wram":0,"ref_sram":0,"native_wram":15,"native_sram":0},
        "per_guest_memory_type_changed_byte_occurrences":{
            "ref_wram":0,"ref_sram":0,"native_wram":77,"native_sram":0},
        "causal_reason_for_cross_epoch_native_stack_or_DP_byte_change_proven":False,
        "instrumentation_on_off_same_binary_family_noninterference_proven":False,
        "full_USA_events_accepted":0,"release_QA_gates":0,
        "earlier_RF066_original_native_race_mesh":{
            "raw_byte_exact_race_mesh_pairs":51,
            "unmasked_guest_race_mesh_WRAM_byte_occurrences":92},
        "later_RF062_original_native_race_mesh":{
            "raw_byte_exact_race_mesh_pairs":46,
            "unmasked_guest_race_mesh_WRAM_byte_occurrences":104},
    }
    native={"source_bound_native_read_count":10,
            "frame_6124_real_helper_read_count":655,
            "native_read_rows":[{"native_read_address":"11C770",
                                 "native_returned_byte":"00"} for _ in range(10)]}
    native["native_read_rows"][4]={
        "native_read_address":"11C774","native_returned_byte":"D0"}
    report={"native_executable_sha256":gate.TARGET_NATIVE_BINARY,
            "rom_sha256":gate.PINNED_ROM,
            "reference_entry":1017,"native_entry":1017}
    return a,raw,native,report


class BoundedObservationsRemainDistinct(unittest.TestCase):
    def test_real_classification_contract_keeps_no_wrapper_or_event_credit(self):
        result=gate.classify(*fixture())
        self.assertTrue(result[
            "helper_address_register_master_clock_sequence_unchanged_under_logging"])
        self.assertFalse(result["RF062_read_wrapper_replacement_noninterference_proven"])
        self.assertFalse(result["historical_656_vs_655_missing_helper_attributed_to_logging"])
        self.assertEqual(result[
            "historical_RF066_to_instrumented_RF062_78_mesh_exact"],[51,46])
        self.assertEqual(result[
            "historical_RF066_to_instrumented_RF062_78_mesh_unmasked_byte_differences"],
            [92,104])
        self.assertEqual(result["full_USA_events_accepted"],0)
        self.assertEqual(result["release_QA_gates"],0)

    def test_unsafe_promotions_and_missing_positive_proof_fail(self):
        experiments=(
            ("changed_native_emu_binary",0,("independently_reopened_compiled_binaries",
                                            "actual_native_binary_SHA256"),"0"*64),
            ("helper_count_off_changes",0,("native_real_sound_helper_count_off_on",),[656,655]),
            ("logging_master_clock_changes",0,("native_actual_RF054_CPU_master_clocks_equal",),False),
            ("falsely_certified_wrapper",0,("wrapper_replacement_noninterference_proven",),True),
            ("no_original_log_control",0,("original_qualified_source_log_path_differences",
                                          "source_nonpath_log_equality_proven"),False),
            ("raw_image_population_missing",1,("complete_source_guest_Wram_Sram_archive_members_reopened",),387),
            ("native_stack_delta_omitted",1,("per_guest_memory_type_changed_byte_occurrences",
                                             "native_wram"),0),
            ("forged_same_executable",1,("native_guest_binary_changed",),False),
            ("forged_cause",1,("causal_reason_for_cross_epoch_native_stack_or_DP_byte_change_proven",),True),
            ("native_read_missing",2,("frame_6124_real_helper_read_count",),654),
            ("native_return_forgery",2,("native_read_rows",4,"native_returned_byte"),"D1"),
            ("wrong_guest_origin",3,("native_entry",),1019),
            ("different_ROM",3,("rom_sha256",),"0"*64),
        )
        for name,index,path,value in experiments:
            with self.subTest(name=name):
                arguments=list(copy.deepcopy(fixture()))
                member=arguments[index]
                for key in path[:-1]:
                    member=member[key]
                member[path[-1]]=value
                with self.assertRaises(ValueError):
                    gate.classify(*arguments)

    def test_missing_whole_native_binary_archive_not_accepted(self):
        items=list(copy.deepcopy(fixture()))
        items[0]["independently_reopened_compiled_binaries"]=None
        with self.assertRaisesRegex(ValueError,"binary"):
            gate.classify(*items)


if __name__=="__main__":
    unittest.main()
