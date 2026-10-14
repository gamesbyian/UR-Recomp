"""QA-01 original-source raw $009F text/restore crosswalk, no guest runs."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_result_field_restore_contract as m


class OriginalResultTextRestoreContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank80 = m.BANK80.read_text(encoding="utf-8")
        cls.bank83 = m.BANK83.read_text(encoding="utf-8")
        cls.ram = m.RAM.read_text(encoding="utf-8")

    def test_pinned_source_operand_and_two_store_odd_word_layout(self):
        r = m.report(self.bank80, self.bank83, self.ram)
        self.assertEqual(r["schema"], m.SCHEMA)
        self.assertEqual(r["raw_result_signature_address"], "7E:009F")
        self.assertEqual(r["source_catalogue_symbol"], "wTextPos")
        self.assertEqual(r["source_catalogue_symbol_width_bytes"], 2)
        self.assertEqual(r["source_text_initializer_load_immediate"], "80:A18E")
        self.assertEqual(r["source_text_initializer_store"], "80:A190")
        self.assertEqual(r["archived_bank80_direct_restore_callsite"], "80:9A3F")
        self.assertEqual(r["source_save_direct_page_call_before"], "80:9A27")
        self.assertEqual(r["source_video_reset_call_before_restore"], "80:9A37")
        self.assertEqual(r["source_input_or_setup_call_before_restore"], "80:9A3A")
        self.assertIs(r["original_result_boundary_executed_this_callsite_proven"], False)
        self.assertEqual(r["source_restore_loop_entry"], "83:987D")
        self.assertEqual(r["source_restore_word_writer"], "83:988A")
        self.assertEqual(r["source_restore_loop_branch"], "83:9890")
        self.assertEqual(r["restore_word_writes_per_execution"], 207)
        self.assertEqual(r["restore_total_bytes_if_Wram_DBR"], 414)
        self.assertEqual(r["restore_byte_range_if_Wram_DBR"],
                         ["7E:0000", "7E:019D"])
        self.assertEqual(r["text_position_field_restore_owners"], [
            {
                "byte_offset_hex": "7E:009F",
                "indexed_word_start": "7E:009E",
                "word_byte_index": 1,
                "loop_iteration_one_based": 80,
            },
            {
                "byte_offset_hex": "7E:00A0",
                "indexed_word_start": "7E:00A0",
                "word_byte_index": 0,
                "loop_iteration_one_based": 81,
            },
        ])
        for key in (
            "observed_0x84_to_0x16_proves_actual_scene_change",
            "observed_0x84_to_0x16_proves_83_988A_executed",
            "source_operand_proves_DBR_Wram_at_runtime",
            "cpu_beam_frame_phase_original_native_aligned",
        ):
            self.assertIs(r[key], False, key)
        self.assertEqual(r["complete_usa_events_strict_admitted"], 0)

    def test_noncontiguous_byte_spans_fail_closed_at_restore_bounds(self):
        for offset, word, idx in (
            (0x0, "7E:0000", 1),
            (0x9E, "7E:009E", 80),
            (0x9F, "7E:009E", 80),
            (0xA0, "7E:00A0", 81),
            (0x19C, "7E:019C", 207),
            (0x19D, "7E:019C", 207),
        ):
            with self.subTest(offset=offset):
                obj = m.write_owner(offset)
                self.assertEqual(obj["indexed_word_start"], word)
                self.assertEqual(obj["loop_iteration_one_based"], idx)
                self.assertEqual(obj["word_byte_index"], offset & 1)
        for bad in (-1, 0x19E, 0x19F, 0x200):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "outside"):
                    m.write_owner(bad)

    def test_missing_changed_or_duplicated_static_source_instructions_rejected(self):
        for tag, bank80, bank83 in (
            ("restore_caller", self.bank80.replace(
                "80/9A3F: 22 7D 98 83  JSR $83987D",
                "80/9A3F: 22 94 98 83  JSR $839894"), self.bank83),
            ("missing_text", self.bank80.replace(
                "80/A190: 85 9F        STA $9F", "80/A190: 85 9E        STA $9E"), self.bank83),
            ("source_immediate", self.bank80.replace(
                "80/A18E: A9 84        LDA #$84",
                "80/A18E: A9 83        LDA #$83"), self.bank83),
            ("restore_writer", self.bank80, self.bank83.replace(
                "83/988A: 9D 00 00     STA $0000,X",
                "83/988A: 9D 02 00     STA $0002,X")),
            ("loop_branch", self.bank80, self.bank83.replace(
                "83/9890: 10 F4        BPL $9886",
                "83/9890: 10 F2        BPL $9884")),
            ("duplicate", self.bank80, self.bank83 +
             "\n83/988A: 9D 00 00     STA $0000,X\n"),
        ):
            with self.subTest(tag=tag):
                with self.assertRaisesRegex(ValueError, "missing, duplicate or rewritten"):
                    m.report(bank80, bank83, self.ram)

    def test_width_and_symbol_provenance_rejected_if_changed(self):
        with self.assertRaisesRegex(ValueError, "two-byte text position"):
            m.report(self.bank80, self.bank83,
                     self.ram.replace("7E009F wTextPos                 2",
                                      "7E009F wTextPos                 1"))
        # SEP placed between the source REP and final RTL would invalidate
        # unconditional 16-bit per-store analysis despite unchanged opcodes.
        modified = self.bank83.replace(
            "83/988D: E8           INX",
            "83/988B: E2 20        SEP #$20\n"
            "83/988D: E8           INX")
        with self.assertRaisesRegex(ValueError, "accumulator width"):
            m.report(self.bank80, modified, self.ram)


if __name__ == "__main__":
    unittest.main()
