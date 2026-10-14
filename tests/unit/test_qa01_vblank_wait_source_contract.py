"""Original USA two-edge VBlank wait / cursor-animation contract (no emulator)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_vblank_wait_source_contract as m


class VBlankWaitSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank80 = m.BANK80.read_text(encoding="utf-8")
        cls.ram = m.RAM.read_text(encoding="utf-8")

    def test_exact_original_wait_edges_and_counter_writer(self):
        out = m.report(self.bank80, self.ram)
        self.assertEqual(out["schema"], m.SCHEMA)
        self.assertEqual(out["wait_entry_pc"], "80:FAC9")
        self.assertEqual(out["wait_first_hvbjoy_read_pc"], "80:FACD")
        self.assertEqual(out["wait_for_vblank_clear_branch_pc"], "80:FAD0")
        self.assertEqual(out["wait_second_hvbjoy_read_pc"], "80:FAD6")
        self.assertEqual(out["wait_for_vblank_set_branch_pc"], "80:FAD9")
        self.assertEqual(out["after_second_edge_call_pc"], "80:FADB")
        self.assertEqual(out["counter_decrement_pc"], "80:FAE2")
        self.assertEqual(out["counter_wrap_value"], 31)
        self.assertEqual(out["counter_symbol"], "wCursorAnimTimer")
        self.assertEqual(out["counter_symbol_width_bytes"], 1)
        self.assertEqual(out["animation_output_writer_pcs"],
                         ["80:FAF6", "80:FAF9"])
        self.assertEqual(out["animation_output_addresses"],
                         ["7E:0BDE", "7E:0BFE"])
        self.assertEqual(out["full_usa_events_accepted_by_this_check"], 0)

    def test_fail_closed_on_changed_edge_polarity_poll_or_frame_counter(self):
        cases = (
            ("first_branch", "80/FAD0: 30 F7        BMI $FAC9",
             "80/FAD0: 10 F7        BPL $FAC9"),
            ("second_branch", "80/FAD9: 10 F7        BPL $FAD2",
             "80/FAD9: 30 F7        BMI $FAD2"),
            ("first_poll", "80/FACD: AD 12 42     LDA $4212",
             "80/FACD: AD 11 42     LDA $4211"),
            ("second_poll", "80/FAD6: AD 12 42     LDA $4212",
             "80/FAD6: AD 11 42     LDA $4211"),
            ("counter", "80/FAE2: C6 C6        DEC $C6",
             "80/FAE2: C6 C8        DEC $C8"),
            ("counter_wrap", "80/FAE6: A9 1F        LDA #$1F",
             "80/FAE6: A9 0F        LDA #$0F"),
            ("output", "80/FAF9: 8D FE 0B     STA $0BFE",
             "80/FAF9: 8D FD 0B     STA $0BFD"),
        )
        for tag, before, after in cases:
            with self.subTest(tag=tag):
                self.assertIn(before, self.bank80)
                with self.assertRaisesRegex(ValueError, "opcode"):
                    m.report(self.bank80.replace(before, after), self.ram)

    def test_duplicate_opcode_rejected(self):
        doubled = self.bank80 + "\n80/FACD: AD 12 42     LDA $4212\n"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            m.report(doubled, self.ram)

    def test_counter_symbol_must_match_pinned_ram_map(self):
        symbol = "7E00C6 wCursorAnimTimer         1"
        self.assertIn(symbol, self.ram)
        for altered in ("7E00C6 wCursorAnimTimer         2",
                        "7E00C6 wGameFrameTimer          1"):
            with self.subTest(altered=altered):
                with self.assertRaisesRegex(ValueError, "cursor counter"):
                    m.report(self.bank80, self.ram.replace(symbol, altered))

    def test_source_contract_never_proclaims_cpu_nmi_or_guest_parity(self):
        out = m.report(self.bank80, self.ram)
        for key in (
            "counter_is_universal_guest_simulation_frame_clock_proven",
            "counter_is_unmodified_by_other_routines_proven",
            "actual_original_wait_pc_executed_in_rf014_proven",
            "actual_native_wait_pc_executed_in_rf014_proven",
            "native_beam_model_causes_rf014_proven",
            "cpu_nmi_beam_sample_phase_correspondence_proven",
        ):
            self.assertIs(out[key], False, key)


if __name__ == "__main__":
    unittest.main()
