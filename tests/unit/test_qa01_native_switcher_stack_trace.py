"""QA-01 native Switcher read-only stack scope contracts and fail-closed guards."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa01_native_switcher_stack_gate as gate
import qa01_native_switcher_stack_report as report


class NativeStackGuardTests(unittest.TestCase):
    def test_source_marker_unique_and_disposable_gate_not_guest_mutation(self):
        original = "a\n" + gate.MARKER + "    if (g_wlog_addr_n++ >= g_wlog_addr_cap) return;\n"
        patched = gate.patch(original)
        self.assertIn(gate.STAMP, patched)
        self.assertEqual(patched.count(gate.MARKER), 1)
        self.assertEqual(patched.count("g_wlog_addr_n++"), 1)
        self.assertIn("UR_QA_NATIVE_STACK_FIRST", patched)
        self.assertIn("UR_QA_NATIVE_STACK_LAST", patched)
        self.assertIn("b - a <= 64", patched)
        self.assertIn("snes_frame_counter", patched)
        self.assertLess(patched.index("snes_frame_counter < ur_qa_stack_first"),
                        patched.index("g_wlog_addr_n++"))
        with self.assertRaisesRegex(ValueError, "already installed"):
            gate.patch(patched)
        with self.assertRaisesRegex(ValueError, "absent or ambiguous"):
            gate.patch("bogus")
        with self.assertRaisesRegex(ValueError, "absent or ambiguous"):
            gate.patch(gate.MARKER * 2)

    def test_native_address_write_attempts_are_not_original_change_events(self):
        rows = [
            "f5778   00:01F1=F4 w1 Res_LoadToVram A=0000 X=0000 Y=0000 S=01F2 D=0000 DB=00 M=1 Xf=0 IPC=FFFFFF p34=000000\n",
            "f5778   00:01F0=FBF4 w2 another_scope A=0000 X=0000 Y=0000 S=01F2 D=0000 DB=00 M=1 Xf=0 IPC=000000\n",
            "f5782   80:01DD=11 w1 actual_scope via=DMA A=0000 X=0000 Y=0000 S=01EF D=0000 DB=00 M=1 Xf=0 IPC=FFFFFF\n",
        ]
        result = report.summarize(rows)
        self.assertEqual(result["schema"], report.SCHEMA)
        self.assertEqual(result["native_guest_wram_write_attempts"], 4)
        self.assertEqual(result["counts_by_address"],
                         {"7E:01DD": 1, "7E:01F0": 1, "7E:01F1": 2})
        self.assertEqual(result["counts_by_native_host_frame"], {5778: 3, 5782: 1})
        self.assertEqual(result["counts_by_address_generated_or_interpreter_scope"]
                         ["7E:01F1"]["Res_LoadToVram"], 1)
        self.assertEqual(result["first_five_observed_writes_per_address"]
                         ["7E:01DD"][0]["native_cpu_sp"], "01EF")
        self.assertTrue(result["no_direct_guest_wram_values_or_complete_memory_dumps"])
        self.assertEqual(result["complete_event_release_credit"], 0)

    def test_wrong_memory_frame_context_and_empty_logs_rejected(self):
        good = ("f5782 00:01F1=FB w1 tiny_scope A=0 S=01F2 IPC=FFFFFF\n")
        for bad in [
            "", "arbitrary string", good.replace("f5782", "f5792"),
            good.replace("f5782", "f5760"),
            good.replace("00:01F1", "81:01F1"),
            good.replace(" S=01F2", ""),
            good.replace(" IPC=FFFFFF", ""),
            good.replace("w1", "w3"),
            good.replace("01F1=FB", "01F1=FFFF"),
        ]:
            with self.subTest(bad=bad[:40]):
                with self.assertRaises(ValueError):
                    report.summarize(bad.splitlines(keepends=True))
        with self.assertRaisesRegex(ValueError, "escaped the frame or memory scope"):
            report.summarize([good, good.replace("f5782", "f5779")])
        with self.assertRaisesRegex(ValueError, "budget exceeded"):
            old_limit = report.MAX_EVENTS
            try:
                report.MAX_EVENTS = 2
                report.summarize([good] * 3)
            finally:
                report.MAX_EVENTS = old_limit

    def test_genuine_independent_full_memory_offset_pair_required(self):
        pair = {
            "name": "switcher", "course_id": "course:04",
            "rom_sha256": report.EXPECTED_ROM_SHA,
            "original_movie_sha256": report.EXPECTED_MOVIE_SHA,
            "reference_entry": 1079, "native_entry": 1081,
            "comparison": {
                "terminal_result_guest_frame": {
                    "reference_relative": 4704, "native_relative": 4702,
                },
                "terminal_result_frame_matched": False,
            },
            "switcher_same_host_penultimate": {
                "schema": "UR-QA01-SWITCHER-PENULTIMATE-SAME-HOST/1",
                "original_absolute_host": 5782, "native_absolute_host": 5782,
                "result_absolute_host": 5783, "same_host_named_guest_fields_equal": True,
            },
            "switcher_same_host_full_memory_offsets": {
                "schema": "UR-QA01-SWITCHER-5782-FULL-GUEST-OFFSETS/1",
                "original_host_frame": 5782, "native_host_frame": 5782,
                "original_movie_input_modified": False,
                "release_complete_event_credit": 0,
                "memory_classes": {
                    "wram": {
                        "different_byte_offsets": report.EXPECTED_DIFFS,
                        "offsets_truncated": False,
                    },
                    "vram": {"different_byte_count": 0},
                    "cgram": {"different_byte_count": 0},
                },
            },
        }
        approved = report.validate_paired_guest_report(pair)
        self.assertEqual(approved["complete_event_release_credit"], 0)
        self.assertFalse(approved["original_native_result_relative_frame_parity"])
        import copy
        for tamper in [
            lambda x: x["comparison"]["terminal_result_guest_frame"].update(native_relative=4704),
            lambda x: x["switcher_same_host_full_memory_offsets"]["memory_classes"]["wram"]
                .update(different_byte_offsets=[]),
            lambda x: x["switcher_same_host_full_memory_offsets"]["memory_classes"]["vram"]
                .update(different_byte_count=1),
            lambda x: x.update(original_movie_sha256="different"),
            lambda x: x["switcher_same_host_penultimate"]
                .update(same_host_named_guest_fields_equal=False),
        ]:
            altered = copy.deepcopy(pair)
            tamper(altered)
            with self.assertRaises(ValueError):
                report.validate_paired_guest_report(altered)


if __name__ == "__main__":
    unittest.main()
