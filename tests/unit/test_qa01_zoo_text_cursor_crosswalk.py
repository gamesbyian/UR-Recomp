"""QA-01 Zoo source opcode changes vs native helper attempts, zero release credit."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_zoo_text_cursor_crosswalk as c


class ZooTextCursorCrosswalk(unittest.TestCase):
    def setUp(self):
        self.original = (
            "ZOOPCWRITE f=6760 v=240 pc=83988A addr=009F old=84 new=16\n"
            "ZOOPCWRITE f=6766 v=139 pc=80C49E addr=009F old=16 new=22\n"
            "ZOOPCWRITE f=6766 v=140 pc=80C5B2 addr=009F old=22 new=23\n"
            "ZOOPCWRITE f=6766 v=141 pc=80C5B2 addr=009F old=23 new=24\n"
            "ZOOPCWRITE f=6766 v=142 pc=80C5B2 addr=009F old=24 new=BC\n")
        self.native = (
            "f6767   00:009F=0022 w2 Text_CmdSetPos_M0X0\n"
            "f6767   00:009F=0023 w2 Text_DrawLoop_C3F7_M1X0\n"
            "f6767   00:009F=0023 w2 Text_CmdSetPos_M0X0\n"
            "f6767   00:009F=0024 w2 Text_DrawLoop_C3F7_M1X0\n"
            "f6767   00:009F=00BC w2 Text_DrawLoop_C3F7_M1X0\n")
        self.src_host = ("script f=1604 dump scene-entered fb=256x224 RGB565 "
                         "sram=8192 ppuw=4\n")
        self.nat_host = "script f=1606 dump scene-entered ok\n"
        for frame in (5160, 5161, 5162, 5163):
            self.src_host += (f"script f={1604+frame} dump boundary-{frame:05d} "
                              "fb=256x224 RGB565 sram=8192 ppuw=4\n")
            self.nat_host += (
                f"script f={1606+frame} dump boundary-{frame:05d} ok\n")

    def analyze(self, **changes):
        d = dict(original_log=self.original, native_log=self.native,
                 original_host_log=self.src_host, native_host_log=self.nat_host)
        d.update(changes)
        return c.analyze(**d)

    def test_source_changes_match_native_mutating_attempts_only(self):
        v = self.analyze()
        self.assertEqual((v["original_painted_byte_mutations_after_reset"],
                          v["native_cpu_helper_write_attempts"],
                          v["native_mutating_attempts_after_deduplication"]), (4, 5, 4))
        self.assertEqual(v["native_idempotent_write_attempts"], [
            {"attempt_index": 2, "value": "23",
             "native_scope": "Text_CmdSetPos_M0X0"}])
        self.assertTrue(v["observed_mutating_cursor_values_exact_same_order"])
        self.assertTrue(v["both_last_cursor_values_bc"])
        self.assertEqual(v["source_changed_value_sequence_sha256"],
                         v["native_mutating_value_sequence_sha256"])
        self.assertEqual(v["source_cursor_reset"]["pc"], "83:988A")
        self.assertEqual(v["original_attested_boundary_dump_hosts"][5162], 6766)
        self.assertEqual(v["native_attested_boundary_dump_hosts"][5162], 6768)
        self.assertFalse(v["cpu_frame_and_ppu_phase_equivalence_proven"])
        self.assertFalse(v["guest_relative_full_result_onset_equivalent"])
        self.assertFalse(v["exact_executed_38500427634_log_pair_verified"])
        self.assertEqual(v["qa01_complete_event_credit"], 0)

    def test_changed_native_value_is_not_mistaken_for_two_noop_duplicates(self):
        v = self.analyze(native_log=self.native.replace(
            "f6767   00:009F=0024", "f6767   00:009F=0025"))
        self.assertFalse(v["observed_mutating_cursor_values_exact_same_order"])
        self.assertEqual(v["first_observed_value_disagreement"], 2)
        self.assertEqual(v["qa01_complete_event_credit"], 0)

    def test_missing_source_change_and_unqualified_reset_fail(self):
        with self.assertRaisesRegex(ValueError, "missing/unattributed writer"):
            self.analyze(original_log=self.original.replace(
                "ZOOPCWRITE f=6766 v=141 pc=80C5B2 addr=009F old=23 new=24\n", ""))

    def test_bad_guest_receipts_fail_without_inferred_host_retiming(self):
        for altered in (
            self.src_host.replace("script f=6766 dump boundary-05162",
                                  "script f=6765 dump boundary-05162"),
            self.src_host + "script f=6766 dump boundary-05162 "
                            "fb=256x224 RGB565 sram=8192 ppuw=4\n",
        ):
            with self.subTest(altered=altered[-100:]),self.assertRaises(ValueError):
                self.analyze(original_host_log=altered)

    def test_malformed_source_or_native_rejected(self):
        with self.assertRaisesRegex(ValueError, "malformed original"):
            self.analyze(original_log=self.original.replace(
                "addr=009F old=22 new=23", "addr=009F old=xx new=23"))
        with self.assertRaisesRegex(ValueError, "malformed native"):
            self.analyze(native_log=self.native.replace(
                "00:009F=0023 w2", "00:009F=ZZZZ w2"))
        with self.assertRaisesRegex(ValueError, "cursor reset drifted"):
            self.analyze(original_log=self.original.replace(
                "addr=009F old=84 new=16", "addr=009F old=84 new=15"))


if __name__ == "__main__":
    unittest.main()
