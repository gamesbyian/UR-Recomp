#!/usr/bin/env python3
"""Historical source-evidence cross-check; never a release gate positive."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa_independent_source_evidence_disposition as qa


def reports():
    return (
        json.loads(qa.WRITER.read_text(encoding="utf-8")),
        json.loads(qa.FADE.read_text(encoding="utf-8")),
    )


class IndependentOriginalNativeEvidenceDisposition(unittest.TestCase):
    def test_actual_retained_research_contract_has_zero_release_credit(self):
        original, fade = reports()
        output = qa.audit(original, fade)
        self.assertEqual(output["original_source_writer_instructions_crosschecked"], 18)
        self.assertEqual(output["original_source_opcode_records_crosschecked"], 55)
        self.assertEqual(output["original_channel5_source_descriptors_crosschecked"], 6)
        self.assertEqual(output["same_absolute_host_brightness_steps"], 7)
        # Matching brightness is never a hash-identical PPU register image.
        self.assertEqual(output["full_original_native_ppu_register_hash_matches"], 0)
        self.assertEqual(output["current_release_gate_credit_from_these_files"], 0)
        self.assertFalse(output["source_native_same_input_final_pixels_verified"])
        self.assertFalse(output["source_native_complete_course_accepted_from_these_files"])

    def test_forged_original_source_opcode_and_descriptor_are_rejected(self):
        original, fade = reports()
        variants = []
        for field, value in (
            ("original_independently_executed_writer_PCs", 17),
            ("native_channel5_mode1_CGADSUB_COLDATA_pairs_strictly_accepted", False),
            ("full_original_native_same_input_frame_parity_proven", True),
            ("original_opcode_archive_zip_SHA256", "00"),
        ):
            bad = copy.deepcopy(original)
            bad[field] = value
            variants.append(bad)
        bad = copy.deepcopy(original)
        bad["original_executed_65816_writer_PC_and_WRAM_target"][0]["WRAM"] = "7E:2099"
        variants.append(bad)
        bad = copy.deepcopy(original)
        bad["original_executed_65816_writer_PC_and_WRAM_target"][1]["ROM_instruction_hex"] = "8F86207E"
        variants.append(bad)
        bad = copy.deepcopy(original)
        bad["original_table_triplets"][3]["coldata"] = "FF"
        variants.append(bad)
        bad = copy.deepcopy(original)
        bad["original_source_opcode_sequence"][3]["original_PC"] = (
            bad["original_source_opcode_sequence"][2]["original_PC"]
        )
        variants.append(bad)
        for bad in variants:
            with self.subTest(changed=repr(bad)[-90:]):
                with self.assertRaises(ValueError):
                    qa.audit(bad, fade)

    def test_forged_fade_phase_and_source_claims_are_rejected(self):
        original, fade = reports()
        variants = []
        for field, value in (
            ("seven_brightness_steps_exact_absolute_host_aligned", False),
            ("source_gameplay_finish_instruction_identified", True),
            ("original_native_race_return_fade_result_complete_event_strict_equal", True),
            ("approved_usa_events", 1),
            ("source_result_menu_onset_guest_relative", 5162),
        ):
            bad = copy.deepcopy(fade)
            bad["interpretation"][field] = value
            variants.append(bad)
        bad = copy.deepcopy(fade)
        bad["fade_brightness_steps"][2]["native_absolute_host"] += 1
        variants.append(bad)
        bad = copy.deepcopy(fade)
        bad["fade_brightness_steps"][1]["ppu_brightness"] = 12
        variants.append(bad)
        bad = copy.deepcopy(fade)
        bad["first_persistent_ppu_blank"]["native_absolute_host"] -= 2
        variants.append(bad)
        bad = copy.deepcopy(fade)
        bad["fade_brightness_steps"][4]["original_ppu_regs_sha256"] = "bad"
        variants.append(bad)
        for bad in variants:
            with self.subTest(changed=repr(bad)[-90:]):
                with self.assertRaises(ValueError):
                    qa.audit(original, bad)


if __name__ == "__main__":
    unittest.main()
