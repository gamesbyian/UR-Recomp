"""ROM-free adversarial QA for source-pinned RTI ABI vs nine live NMI brackets."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_independent_rf073_rf075_return_decision as qa


def pinned_contract():
    return {
        "schema": "ur-qa01-rf075-original-source-native-RTI-ABI-static-contract/1",
        "pinned_upstream_snesrecomp": qa.rf075.UPSTREAM,
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
        "exact_upstream_source_git_blobs": {path: blob
            for _, (path, blob) in qa.rf075.FILES.items()},
    }


def nine_brackets():
    b=[]
    for i,frame in enumerate(qa.rf073.FRAMES):
        low="F0" if i<4 else "EE"
        b.append({
            "native_frame": frame,
            "original_post_real_NMI_raw_5_stack_bytes":f"26{low}D48226",
            "native_after_push_raw_4_bytes":"26EED482",
            "native_true_status_stack_helper_read_value":"0026",
            "original_native_intra_frame_semantic_phase_proven_equal":False,
            "original_native_PC_low_byte_differ_in_paired_host_frame":i<4,
        })
    return {
        "schema":qa.rf073.SCHEMA,
        "exact_authenticated_RF054_zip_sha256":qa.NMI_ZIP_SHA256,
        "native_RF047_event_count":2741,
        "authentic_native_NMI_frame_count":9,
        "native_compiled_NMI_brackets_with_one_actual_status_helper_read":9,
        "native_saved_PC_or_PB_helper_reads_between_push_and_compiled_RTI":0,
        "original_native_same_intra_frame_semantic_phase_proven":False,
        "source_original_native_NMI_saved_PC_low_differences":4,
        "brackets":b,
    }


class IndependentNmiArchitecturalDecision(unittest.TestCase):
    def test_all_nine_live_brackets_hypothesis_remains_source_bound_and_hold(self):
        receipt=qa.decide(nine_brackets(),pinned_contract())
        self.assertEqual(receipt["historical_native_NMI_actual_handler_status_reads"],9)
        self.assertEqual(receipt["pinned_compiled_native_RTI_guest_saved_PC_PB_load_count"],0)
        self.assertEqual(receipt["original_native_host_frame_saved_PC_low_differences"],4)
        self.assertFalse(receipt["native_saved_PC_PB_discrepancy_directly_changes_compiled_RTI_target_proven"])
        self.assertFalse(receipt["same_binary_original_native_NMI_phase_qualified"])
        self.assertFalse(receipt["actual_guest_stack_return_rewritten_in_real_Uniracers_proven"])
        self.assertEqual(receipt["accepted_USA_events"],0)
        self.assertEqual(receipt["accepted_Windows_QA_gates"],0)
        self.assertEqual([x["original_observed_saved_PC_24"] for x in
                          receipt["frame_label_observations_not_joinable_across_guest_clocks"]],
                         ["82D4F0"]*4 + ["82D4EE"]*5)

    def test_missing_untrusted_or_mutated_upstream_blobs_refused(self):
        for key, mutation in (
            ("compiled_RTI_guest_status_load_count",0),
            ("compiled_RTI_guest_saved_PC_load_count",1),
            ("compiled_RTI_guest_saved_PB_load_count",1),
            ("pinned_all_five_unmodified_source_blobs_verified",False),
            ("any_such_guest_stack_rewrite_actually_observed",True),
            ("original_native_equivalent_interruption_instruction_phase_proven",True),
            ("accepted_USA_events",1),
            ("compiled_RTI_returns_via_host_C_control_flow",False),
        ):
            obj=pinned_contract()
            obj[key]=mutation
            with self.subTest(key=key),self.assertRaisesRegex(
                    ValueError,"RF075 genuine source ABI"):
                qa.decide(nine_brackets(),obj)
        x=pinned_contract()
        x["exact_upstream_source_git_blobs"]["runner/src/cpu_state.h"]="0"*40
        with self.assertRaisesRegex(ValueError,"Git blob identities"):
            qa.qualify_source_abi(x)

    def test_unqualified_guest_clock_or_missing_native_frame_refused(self):
        baseline=nine_brackets()
        mutations=(
            lambda v: v["brackets"].pop(),
            lambda v: v.update(source_original_native_NMI_saved_PC_low_differences=3),
            lambda v: v.update(native_saved_PC_or_PB_helper_reads_between_push_and_compiled_RTI=1),
            lambda v: v.update(original_native_same_intra_frame_semantic_phase_proven=True),
            lambda v: v["brackets"][0].update(native_frame=1026),
            lambda v: v["brackets"][0].update(native_true_status_stack_helper_read_value="0027"),
            lambda v: v["brackets"][0].update(original_post_real_NMI_raw_5_stack_bytes="26EED48226"),
            lambda v: v["brackets"][0].update(original_native_PC_low_byte_differ_in_paired_host_frame=False),
            lambda v: v["brackets"][0].update(original_native_intra_frame_semantic_phase_proven_equal=True),
            lambda v: v["brackets"][0].update(native_after_push_raw_4_bytes="26F0D482"),
        )
        for i, mutate in enumerate(mutations):
            case=copy.deepcopy(baseline)
            mutate(case)
            with self.subTest(i=i), self.assertRaises(ValueError):
                qa.decide(case,pinned_contract())

    def test_wrong_source_contract_zip_sha_refuses_even_perfect_looking_json(self):
        with tempfile.TemporaryDirectory() as folder:
            fake=Path(folder)/"source-abi.zip"
            with zipfile.ZipFile(fake,"w") as z:
                z.writestr(qa.SOURCE_ABI_MEMBER,json.dumps(pinned_contract()))
            with self.assertRaisesRegex(ValueError,"archive identity"):
                qa.read_source_abi(fake)

    def test_false_static_claim_cannot_piggyback_on_a_real_nmi_archive(self):
        obj=pinned_contract()
        obj["compiled_RTI_guest_saved_PC_load_count"] = 1
        obj["compiled_RTI_guest_PC_PB_discarded_by_stack_advance"] = False
        with self.assertRaises(ValueError):
            qa.decide(nine_brackets(),obj)


if __name__ == "__main__":
    unittest.main()
