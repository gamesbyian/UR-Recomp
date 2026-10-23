"""H26 original NMI wake-coherence regressions, adapted to merged RF081 source.

ROM-free synthetic nine-frame evidence. These tests do not prove that original
and native executed the same bus instruction or earn an original/native gate.
"""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from rf081_nmi_sequence_gaps import analyze_records


def observations():
    original, native = {"source_NMI_brackets": []}, {"native_frames": []}
    for i, frame in enumerate(range(1017, 1026)):
        base = 10 + i * 10
        pc, sp = "009A2B", "01F0"
        original["source_NMI_brackets"].append({
            "original_source_wake_incremented_PC": False,
            "original_source_wake_pc_before": pc,
            "original_source_wake_pc_after": pc,
            "all_intervening_unselected_opcode_fetches_observed": False,
            "original_NMI_wake_pending_event": {
                "source_local_seq": base, "original_host_frame": frame,
                "source_guest_PC_context": pc, "source_stack_SP": sp,
                "stage": "nmi_pending", "decoded_original_guest_fetch_executed": False},
            "original_NMI_before_push_event": {
                "source_local_seq": base + 1, "original_host_frame": frame,
                "source_guest_PC_context": pc, "source_stack_SP": sp,
                "stage": "nmi_before", "decoded_original_guest_fetch_executed": False},
            "first_selected_original_opcode_fetch_after_NMI": {
                "source_local_seq": base + 3, "original_host_frame": frame,
                "source_guest_PC_context": pc, "source_stack_SP": sp,
                "stage": "fetch", "decoded_original_guest_fetch_executed": True},
        })
        native["native_frames"].append({
            "native_entry_seq": base + 4,
            "native_compiled_handler_return_seq": base + 5,
            "native_NMI_frame_label": frame,
            "original_native_interrupt_instruction_phase_qualified": False,
            "scheduler_PC_is_independently_proven_fetched_interrupt_target": False,
            "first_observed_target_opcode_after_handler_before_next_NMI": {
                "seq": base + 7, "frame": frame,
                "decoded_guest_opcode_PC": "009A2C",
                "actual_guest_emitter_tier": "aot"},
        })
    return original, native


class WakeCoherenceH26(unittest.TestCase):
    def setUp(self):
        self.original, self.native = observations()

    def test_nine_frames_remain_a_noncausal_hold(self):
        result = analyze_records(self.original, self.native)
        self.assertEqual(len(result["rows"]), 9)
        self.assertEqual(result["decision"], "HOLD_MISSING_SAME_EPOCH_BUS_OPERANDS")
        self.assertFalse(result["original_native_seq_comparable"])
        self.assertFalse(result["actual_rts_operand_consumption_observed"])
        self.assertFalse(result["first_causal_divergence_proven"])
        self.assertEqual(result["release_gate_credit"], 0)

    def test_wake_pc_before_and_after_must_match_fetch(self):
        for field in ("original_source_wake_pc_before", "original_source_wake_pc_after"):
            with self.subTest(field=field):
                old = copy.deepcopy(self.original)
                old["source_NMI_brackets"][0][field] = "000000"
                with self.assertRaises(ValueError):
                    analyze_records(old, self.native)

    def test_pending_and_before_push_pc_must_match_fetch(self):
        for stage in ("original_NMI_wake_pending_event", "original_NMI_before_push_event"):
            with self.subTest(stage=stage):
                old = copy.deepcopy(self.original)
                old["source_NMI_brackets"][0][stage]["source_guest_PC_context"] = "000000"
                with self.assertRaises(ValueError):
                    analyze_records(old, self.native)

    def test_pending_and_before_push_stack_must_match_fetch(self):
        for stage in ("original_NMI_wake_pending_event", "original_NMI_before_push_event"):
            with self.subTest(stage=stage):
                old = copy.deepcopy(self.original)
                old["source_NMI_brackets"][0][stage]["source_stack_SP"] = "01EF"
                with self.assertRaises(ValueError):
                    analyze_records(old, self.native)

    def test_incremented_wake_or_noncanonical_stack_is_refused(self):
        old = copy.deepcopy(self.original)
        old["source_NMI_brackets"][0]["original_source_wake_incremented_PC"] = True
        with self.assertRaises(ValueError):
            analyze_records(old, self.native)
        old = copy.deepcopy(self.original)
        old["source_NMI_brackets"][0]["first_selected_original_opcode_fetch_after_NMI"]["source_stack_SP"] = "1F0"
        with self.assertRaises(ValueError):
            analyze_records(old, self.native)

    def test_duplicate_source_local_sequence_is_not_progress(self):
        for side in ("original", "native"):
            with self.subTest(side=side):
                old, new = copy.deepcopy(self.original), copy.deepcopy(self.native)
                if side == "original":
                    old["source_NMI_brackets"][1]["original_NMI_wake_pending_event"]["source_local_seq"] = 13
                else:
                    new["native_frames"][1]["native_entry_seq"] = 17
                with self.assertRaises(ValueError):
                    analyze_records(old, new)


if __name__ == "__main__":
    unittest.main()
