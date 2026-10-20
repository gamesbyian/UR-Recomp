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
        "source_identity_matches":True,
        "same_binaries":True,
        "runtime_RF062_logging_noninterference_supported":False,
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
            "all_other_native_lines_byte_equal_after_strict_host_metadata":False},
        "actual_supplied_input_sha256":{"original":"a"*64,"native":"b"*64},
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
    host={
        "strict_existing_native_source_comparator_nonRF062_passed":False,
        "single_host_video_totals_seconds_field_only_qualified":True,
        "same_simulations_and_presentations_off_on":[6460,6460],
        "actual_host_video_elapsed_seconds_off_on":["109.566","109.591"],
        "all_other_native_guest_trace_rows_equal_after_host_only_metadata":True,
        "RF062_direct_logged_rows_excluded":10,
        "guest_CPU_Wram_or_audio_equivalence_beyond_samples_proven":False,
    }
    return a,raw,native,report,{"original":"a"*64,"native":"b"*64},host


class BoundedObservationsRemainDistinct(unittest.TestCase):
    def test_real_classification_contract_keeps_no_wrapper_or_event_credit(self):
        result=gate.classify(*fixture())
        self.assertTrue(result[
            "helper_address_register_master_clock_sequence_unchanged_under_logging"])
        self.assertFalse(result["RF062_read_wrapper_replacement_noninterference_proven"])
        self.assertFalse(result["existing_native_logging_strict_full_log_comparator_passed"])
        self.assertTrue(result["bounded_native_guest_trace_equal_after_only_exact_host_metric"])
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
            ("source_identity_not_qualified",0,("source_identity_matches",),False),
            ("same_binary_identity_not_qualified",0,("same_binaries",),False),
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
            ("rf066_exact_mesh_forged",1,("earlier_RF066_original_native_race_mesh",
                                         "raw_byte_exact_race_mesh_pairs"),52),
            ("rf062_exact_mesh_forged",1,("later_RF062_original_native_race_mesh",
                                         "raw_byte_exact_race_mesh_pairs"),47),
            ("rf066_unmasked_difference_forged",1,("earlier_RF066_original_native_race_mesh",
                                                  "unmasked_guest_race_mesh_WRAM_byte_occurrences"),91),
            ("rf062_unmasked_difference_forged",1,("later_RF062_original_native_race_mesh",
                                                  "unmasked_guest_race_mesh_WRAM_byte_occurrences"),103),

            ("forged_same_executable",1,("native_guest_binary_changed",),False),
            ("forged_cause",1,("causal_reason_for_cross_epoch_native_stack_or_DP_byte_change_proven",),True),
            ("native_read_missing",2,("frame_6124_real_helper_read_count",),654),
            ("native_return_forgery",2,("native_read_rows",4,"native_returned_byte"),"D1"),
            ("wrong_guest_origin",3,("native_entry",),1019),
            ("different_ROM",3,("rom_sha256",),"0"*64),
            ("wrong_original_controller",4,("original",),"0"*64),
            ("wrong_native_controller",4,("native",),"0"*64),
            ("forged_strict_verifier_pass",0,("runtime_RF062_logging_noninterference_supported",),True),
            ("host_video_total_unqualified",5,("single_host_video_totals_seconds_field_only_qualified",),False),
            ("host_elapsed_off_forged",5,("actual_host_video_elapsed_seconds_off_on",),["109.567","109.591"]),
            ("host_elapsed_on_forged",5,("actual_host_video_elapsed_seconds_off_on",),["109.566","109.590"]),
            ("host_guest_trace_changed",5,("all_other_native_guest_trace_rows_equal_after_host_only_metadata",),False),
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


    def test_exact_one_native_terminal_host_wallclock_statistic_only(self):
        off = (b"[host +109.676s] video totals: simulations=6460 "
               b"presentations=6460 seconds=109.566\n")
        direct = b"".join(
            b"QA01RF062NATIVE seq=" + str(i).encode() +
            b" f=6124 executedPC=8282F0 value=D0\n" for i in range(1,11))
        on = direct + (b"[host +109.698s] video totals: simulations=6460 "
                       b"presentations=6460 seconds=109.591\n")
        result=gate.independently_qualify_terminal_host_walltime(off,on)
        self.assertFalse(result["strict_existing_native_source_comparator_nonRF062_passed"])
        self.assertTrue(result["all_other_native_guest_trace_rows_equal_after_host_only_metadata"])
        self.assertEqual(result["RF062_direct_logged_rows_excluded"],10)
        self.assertEqual(result["actual_host_video_elapsed_seconds_off_on"],
                         ["109.566","109.591"])

    def test_modified_simulations_guest_data_and_unqualified_metadata_fail(self):
        off = (b"[host +109.676s] video totals: simulations=6460 "
               b"presentations=6460 seconds=109.566\n")
        direct = b"".join(
            b"QA01RF062NATIVE seq=" + str(i).encode() +
            b" f=6124 executedPC=8282F0 value=D0\n" for i in range(1,11))
        on = direct + (b"[host +109.698s] video totals: simulations=6460 "
                       b"presentations=6460 seconds=109.591\n")
        for variant, other in (
            ("changed_simulations",on.replace(b"simulations=6460",b"simulations=6459")),
            ("changed_presentations",on.replace(b"presentations=6460",b"presentations=6461")),
            ("new_native_guest_bus_record",b"QA01RF054NATIVEBUS addr=11C774 value=D1\n"+on),
            ("missing_final_newline",on.rstrip(b"\n")),
            ("invalid_time",on.replace(b"109.591",b"not-time")),
            ("identical_host_elapsed_secs",on.replace(b"109.591",b"109.566")),
            ("duplicated_host_totals",on + on.splitlines(keepends=True)[-1]),
        ):
            with self.subTest(variant=variant),self.assertRaises(ValueError):
                gate.independently_qualify_terminal_host_walltime(off,other)

    def test_missing_whole_native_binary_archive_not_accepted(self):
        items=list(copy.deepcopy(fixture()))
        items[0]["independently_reopened_compiled_binaries"]=None
        with self.assertRaisesRegex(ValueError,"compiled executable provenance"):
            gate.classify(*items)


if __name__=="__main__":
    unittest.main()
