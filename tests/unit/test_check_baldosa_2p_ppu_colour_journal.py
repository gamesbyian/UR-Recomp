"""Adversarial genuine SNES PPU raster journal evidence contracts (QA-08)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import check_baldosa_2p_ppu_colour_journal as qa
from tools.check_baldosa_wide_single_slot_source import HEADER


class Original2PColourRegisterJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.stock = root / "ur-baldosa-ws342-002208.pam"
        self.log = root / "native.log"
        self.reference = root / "stock.crc"
        self.candidate = root / "read-only-journal.crc"
        self.raw_original = bytes((10, 20, 30, 0)) * (342 * 224)
        self.stock.write_bytes(HEADER + self.raw_original)
        for p in (self.reference, self.candidate):
            p.write_bytes(b"1234ABCD\n" * 2473)
        self.trace = {
            "armed": 1, "have_completed": 1,
            "completed": {
                "count": 3, "dropped": 0,
                "base": {"cgadsub": "0x13"},
                "entries": [
                    {"l": 43, "r": "0x2132", "v": "0x2D"},
                    {"l": 45, "r": "0x2131", "v": "0x10"},
                    {"l": 159, "r": "0x210D", "v": "0x38"},
                ],
            },
            "recording": {
                "count": 1, "dropped": 0,
                "base": {"cgadsub": "0x00"},
                "entries": [{"l": 225, "r": "0x2130", "v": "0x02"}],
            },
        }
        self.flush()

    def flush(self):
        self.log.write_text(
            "UR_QA08_PPU_COLOUR_JOURNAL guest=2208 guest_unchanged=1 "
            "cgadsub=10 cgwsel=20 fixed15=01AD raster=" +
            json.dumps(self.trace, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    def read(self):
        return qa.parse_record(self.log.read_text().strip())

    def test_real_journal_extracts_colour_register_lines_without_causal_claim(self):
        record = self.read()
        self.assertEqual(record["status"],
                         "native-original-2p-postgo-PPU-register-journal-observed")
        self.assertEqual(record["sampled_after_render_registers"]["CGADSUB"],
                         "0x10")
        self.assertEqual(record["sampled_after_render_registers"]["CGWSEL"],
                         "0x20")
        self.assertEqual(record["sampled_after_render_registers"]["fixed_R5"],
                         13)
        self.assertEqual(record["field_register_journals"]["completed"]
                         ["colour_register_write_count"], 2)
        self.assertEqual(record["field_register_journals"]["recording"]
                         ["colour_register_write_examples_bounded"][0]
                         ["register"], "CGWSEL")
        self.assertFalse(record["PPU_registers_per_racer_pixel_or_line_proven"])
        completed = record["field_register_journals"]["completed"]
        timeline = completed["cgadsub_scanline_tag_chronology"]
        self.assertEqual(timeline["cgadsub_write_count"], 1)
        self.assertEqual(timeline["line_tag_intervals_after_last_same_line_write"], [
            {"first_scanline_tag": 0, "last_scanline_tag": 44, "cgadsub": "0x13"},
            {"first_scanline_tag": 45, "last_scanline_tag": 261, "cgadsub": "0x10"},
        ])
        self.assertFalse(timeline["tag_to_original_output_y_calibrated"])
        self.assertFalse(timeline["effective_per_pixel_colour_math_proven"])
        self.assertFalse(record["native_scanline_tag_to_final_PPU_row_alignment_proven"])
        self.assertFalse(record["remastered_HD_art_approved"])
        beam = completed["beam_order_colour_knowledge"]
        self.assertTrue(completed["legacy_numeric_tag_order_is_not_beam_field_order"])
        self.assertEqual(beam["visible_line_tag_intervals_after_same_line_final_write"][0]["first_visible_line_tag"], 0)
        self.assertEqual(beam["visible_line_tag_intervals_after_same_line_final_write"][-1]["last_visible_line_tag"], 223)
        self.assertIsNone(beam["visible_line_tag_intervals_after_same_line_final_write"][0]["cgwsel"])
        self.assertFalse(beam["source_colour_math_operand_per_pixel_proven"])

    def test_valid_source_has_zero_colour_writes_without_invented_addition(self):
        self.trace["completed"]["entries"] = []
        self.trace["completed"]["count"] = 0
        self.trace["recording"]["entries"] = []
        self.trace["recording"]["count"] = 0
        self.flush()
        record = self.read()
        self.assertEqual(record["field_register_journals"]["completed"]
                         ["colour_register_write_count"], 0)
        self.assertFalse(record["PPU_registers_per_racer_pixel_or_line_proven"])

    def test_multiple_same_tag_writes_retained_in_journal_order(self):
        self.trace["completed"]["entries"].insert(
            2, {"l": 45, "r": "0x2131", "v": "0x1A"})
        self.trace["completed"]["entries"].insert(
            3, {"l": 46, "r": "0x2131", "v": "0x0E"})
        self.trace["completed"]["count"] = 5
        self.flush()
        timeline = (self.read()["field_register_journals"]["completed"]
                    ["cgadsub_scanline_tag_chronology"])
        self.assertEqual(timeline["cgadsub_write_count"], 3)
        self.assertEqual(timeline["same_scanline_rewrites"], 1)
        self.assertEqual(
            [x["native_scanline_tag"] for x in
             timeline["cgadsub_writes_in_original_journal_order"]], [45, 45, 46])
        self.assertEqual(timeline["line_tag_intervals_after_last_same_line_write"], [
            {"first_scanline_tag": 0, "last_scanline_tag": 44, "cgadsub": "0x13"},
            {"first_scanline_tag": 45, "last_scanline_tag": 45, "cgadsub": "0x1A"},
            {"first_scanline_tag": 46, "last_scanline_tag": 261, "cgadsub": "0x0E"},
        ])

    def test_no_writes_retain_entire_262_tag_baseline(self):
        self.trace["completed"]["count"] = 0
        self.trace["completed"]["entries"] = []
        self.flush()
        timeline = (self.read()["field_register_journals"]["completed"]
                    ["cgadsub_scanline_tag_chronology"])
        self.assertEqual(timeline["cgadsub_write_count"], 0)
        self.assertEqual(timeline["line_tag_intervals_after_last_same_line_write"], [
            {"first_scanline_tag": 0, "last_scanline_tag": 261, "cgadsub": "0x13"}
        ])

    def test_native_journal_bool_coercions_and_duplicate_keys_rejected(self):
        self.trace["completed"]["entries"][0]["l"] = True
        self.flush()
        with self.assertRaisesRegex(ValueError, "scanline"):
            self.read()
        self.trace["completed"]["entries"][0]["l"] = 43
        # The recording field has exactly ONE entry: True == 1 is
        # accepted by ordinary Python equality unless types are checked.
        self.trace["recording"]["count"] = True
        self.flush()
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.read()
        self.trace["recording"]["count"] = 1
        self.trace["armed"] = True
        self.flush()
        with self.assertRaisesRegex(ValueError, "not armed/completed"):
            self.read()
        self.trace["armed"] = 1
        self.trace["completed"]["dropped"] = False
        self.flush()
        with self.assertRaisesRegex(ValueError, "dropped"):
            self.read()
        self.trace["completed"]["dropped"] = 0
        self.flush()
        duplicate = self.log.read_text().replace(
            '"armed":1', '"armed":1,"armed":1')
        with self.assertRaisesRegex(ValueError, "duplicate native PPU"):
            qa.parse_record(duplicate)

    def test_unarmed_or_no_completed_field_fails(self):
        self.trace["have_completed"] = 0
        self.flush()
        with self.assertRaisesRegex(ValueError, "not armed/completed"):
            self.read()

    def test_dropped_field_entries_or_wrong_count_fail_closed(self):
        self.trace["completed"]["dropped"] = 1
        self.flush()
        with self.assertRaisesRegex(ValueError, "dropped"):
            self.read()
        self.trace["completed"]["dropped"] = 0
        self.trace["completed"]["count"] = 4
        self.flush()
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.read()

    def test_impossible_scanline_or_guest_frame_rejected(self):
        self.trace["completed"]["entries"][0]["l"] = 310
        self.flush()
        with self.assertRaisesRegex(ValueError, "invalid original PPU"):
            self.read()
        self.trace["completed"]["entries"][0]["l"] = 43
        self.flush()
        raw = self.log.read_text().replace("guest=2208", "guest=1888")
        with self.assertRaisesRegex(ValueError, "exact genuine guest2208"):
            qa.parse_record(raw)

    def test_fake_NON_ppu_register_or_unquantized_write_rejected(self):
        self.trace["completed"]["entries"][0]["r"] = "0x420B"
        self.flush()
        with self.assertRaisesRegex(ValueError, "non-PPU address"):
            self.read()
        self.trace["completed"]["entries"][0]["r"] = "0x2132"
        self.trace["completed"]["entries"][0]["v"] = "0x1ZZ"
        self.flush()
        with self.assertRaisesRegex(ValueError, "invalid original PPU"):
            self.read()

    def test_native_baselines_required_only_with_explicit_opt_in(self):
        digest = hashlib.sha256(self.raw_original).hexdigest()
        with patch.object(qa, "EXPECTED_STOCK_SHA256", digest):
            with self.assertRaisesRegex(ValueError, "baselines missing"):
                qa.verify(self.stock, self.log, self.reference, self.candidate,
                          require_colour_field_baselines=True)
            self.trace["completed"]["base"].update(
                cgwsel="0x02", fixed15="0x296D")
            self.trace["recording"]["base"].update(
                cgwsel="0x04", fixed15="0x001F")
            self.flush()
            result = qa.verify(self.stock, self.log, self.reference, self.candidate,
                               require_colour_field_baselines=True)
        for name in ("completed", "recording"):
            report = result["field_register_journals"][name]["beam_order_colour_knowledge"]
            self.assertTrue(report["baseline_cgwsel_known"])
            self.assertTrue(report["baseline_fixed_colour_known"])

    def test_exact_stock_and_full_crc_run_can_pass_synthetic_structure(self):
        digest = hashlib.sha256(self.raw_original).hexdigest()
        with patch.object(qa, "EXPECTED_STOCK_SHA256", digest):
            result = qa.verify(self.stock, self.log, self.reference, self.candidate)
        self.assertEqual(result["full_native_guest_CRC_entries_equal"], 2473)
        self.assertEqual(result["full_original_342x224_RGBA_SHA256"], digest)

    def test_changed_original_or_crcs_cannot_revalidate(self):
        with self.assertRaisesRegex(ValueError, "stock Original"):
            qa.verify(self.stock, self.log, self.reference, self.candidate)
        digest = hashlib.sha256(self.raw_original).hexdigest()
        self.candidate.write_bytes(b"BAD_CRC\n" * 2473)
        with patch.object(qa, "EXPECTED_STOCK_SHA256", digest):
            with self.assertRaisesRegex(ValueError, "streams differ"):
                qa.verify(self.stock, self.log, self.reference, self.candidate)

    def test_duplicate_or_failed_journal_is_not_accepted(self):
        self.log.write_text(self.log.read_text() * 2)
        digest = hashlib.sha256(self.raw_original).hexdigest()
        with patch.object(qa, "EXPECTED_STOCK_SHA256", digest):
            with self.assertRaisesRegex(ValueError, "not exactly one"):
                qa.verify(self.stock, self.log, self.reference, self.candidate)


if __name__ == "__main__":
    unittest.main()
