"""ROM-free source-local selected-PC census controls; no causal parity."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from rf081_selected_pc_candidate_census import classify_records, census


def observations():
    original = {
        "original_native_semantically_aligned_NMI_proven": False,
        "first_differing_consumed_stack_byte_proven": False,
        "source_NMI_brackets": [],
    }
    native = {
        "actual_guest_fetch_at_saved_scheduler_NMI_PC_proven": False,
        "first_differing_consumed_byte_proven": False,
        "native_frames": [],
    }
    for index, frame in enumerate(range(1017, 1026)):
        original["source_NMI_brackets"].append({
            "all_intervening_unselected_opcode_fetches_observed": False,
            "first_selected_original_opcode_fetch_after_NMI": {
                "original_host_frame": frame,
                "source_guest_PC_context": "82D4F0",
                "raw_fetched_opcode_if_fetch": "10",
                "stage": "fetch",
                "decoded_original_guest_fetch_executed": True,
            },
        })
        native["native_frames"].append({
            "native_NMI_frame_label": frame,
            "original_native_interrupt_instruction_phase_qualified": False,
            "first_observed_target_opcode_after_handler_before_next_NMI": {
                "frame": frame,
                "decoded_guest_opcode_PC": "82D4EE" if index < 4 else "82D4F0",
                "actual_guest_emitter_tier": "aot",
            },
        })
    return original, native


class SelectedPCCandidateTests(unittest.TestCase):
    def test_candidate_counts_not_causal_verdict(self):
        result = classify_records(*observations())
        self.assertEqual((result["selected_pc_mismatch_labels"],
                          result["selected_pc_match_labels"]), (4, 5))
        self.assertEqual(result["release_gate_credit"], 0)
        self.assertFalse(result["first_causal_divergence_proven"])
        self.assertFalse(result["complete_event_equivalence_proven"])
        self.assertTrue(all(not row["semantic_phase_aligned"] for row in result["frames"]))

    def test_selected_original_fetch_stage_is_explicit(self):
        # Reject a same-frame selected PC from an opcode-adjacent
        # interrupt observation masquerading as the actual source fetch.
        for stage in (None, "nmi_pending", "nmi_before", "opcode", 1):
            original, native = observations()
            original["source_NMI_brackets"][0][
                "first_selected_original_opcode_fetch_after_NMI"]["stage"] = stage
            with self.subTest(stage=stage), self.assertRaisesRegex(
                    ValueError, "not comparable"):
                classify_records(original, native)

    def test_native_frame_swap_refused(self):
        original, native = observations()
        native["native_frames"][0], native["native_frames"][1] = (
            native["native_frames"][1], native["native_frames"][0])
        with self.assertRaisesRegex(ValueError, "frame label"):
            classify_records(original, native)

    def test_unqualified_source_phase_cannot_be_promoted(self):
        original, native = observations()
        original["original_native_semantically_aligned_NMI_proven"] = True
        with self.assertRaisesRegex(ValueError, "status changed"):
            classify_records(original, native)

    def test_missing_fetch_and_invalid_pc_lexemes_refused(self):
        for value in (None, {}, {"original_host_frame": 1017,
                                 "source_guest_PC_context": "82d4f0",
                                 "raw_fetched_opcode_if_fetch": "10",
                                 "decoded_original_guest_fetch_executed": True}):
            original, native = observations()
            original["source_NMI_brackets"][0]["first_selected_original_opcode_fetch_after_NMI"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                classify_records(original, native)

    def test_selected_fetch_completeness_claim_refused(self):
        original, native = observations()
        original["source_NMI_brackets"][0]["all_intervening_unselected_opcode_fetches_observed"] = True
        with self.assertRaisesRegex(ValueError, "not comparable"):
            classify_records(original, native)

    def test_mutated_or_unpinned_archive_refused(self):
        with self.assertRaisesRegex(ValueError, "SHA"):
            census(b"not the genuine RF081 archive")


if __name__ == "__main__":
    unittest.main()
