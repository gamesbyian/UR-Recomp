"""Bounded non-Dragster ORIGINAL course-entry witness contracts.

Synthetic WRAM is allowed for tool self-tests, never promoted as evidence of a
real race. Production program requires full exact course payload identity.
"""
from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import probe_original_non_dragster_course_entry as probe


def image(case: str, payload: bytes = bytes(range(64))) -> bytes:
    wram = bytearray(probe.WRAM_BYTES)
    wram[probe.COURSE_RAM_OFFSET:probe.COURSE_RAM_OFFSET + len(payload)] = payload
    wram[0x00CE] = probe.CASES[case][1]
    wram[0x0313] = 1
    for addr, word in (
        (0x0411, 1234), (0x0415, 2034),
        (0x0413, 4321), (0x0417, 3045),
        (0x04B7, 0xFFF1), (0x04BB, 0x0010),
        (0x04B9, 0xFFEF), (0x04BD, 0x0020),
        (0x0E95, 0x2024), (0x0E97, 0x1804),
        (0x1199, 0), (0x119B, 2),
        (0x119D, 0), (0x119F, 1),
        (0x0EF1, 2), (0x0EF3, 3), (0x11CF, 64),
    ):
        struct.pack_into("<H", wram, addr, word)
    return bytes(wram)


class NonDragsterCourseEntryTests(unittest.TestCase):
    def test_exact_original_menu_routes(self):
        zoo = probe.original_menu_script("zoom-zoo")
        jumps = probe.original_menu_script("jumps")
        for text in (zoo, jumps):
            self.assertTrue(text.startswith("until 009F == D7"))
            self.assertNotIn("poke ", text)
            self.assertIn("until 009F == 16 1200", text)
            self.assertIn("until 0313 == 01 1800", text)
            self.assertEqual(text.count("dump race-entered"), 1)
            self.assertEqual(text.count("dump race-plus-"), len(probe.SAMPLES) - 1)
            self.assertEqual(text.count("quit"), 1)
        self.assertIn("until 009B == 01 600", zoo)
        self.assertNotIn("until 009B == 02 600", zoo)
        self.assertIn("until 009B == 02 600", jumps)
        self.assertEqual(jumps.count("press down 2"), 3)
        self.assertEqual(zoo.count("press down 2"), 1)
        with self.assertRaises(probe.CourseEntryEvidenceError):
            probe.original_menu_script("dragster")

    def test_strict_full_course_identity_and_track(self):
        original = bytes(range(64))
        row = probe.sample_state(image("zoom-zoo"), "zoom-zoo", original)
        self.assertEqual(row["p1_x"], 1234)
        self.assertEqual(row["p1_speed_x"], -15)
        self.assertEqual(row["p1_contact_stored"], 0x2024)
        self.assertEqual(row["p2_contact_stored"], 0x1804)
        self.assertEqual((row["p2_speed_x"], row["p2_speed_y"]), (-17, 32))
        self.assertEqual((row["p1_next_checkpoint"], row["p1_finish_gate"],
                          row["p1_laps_remaining"]), (0, 0, 2))
        self.assertEqual((row["p2_next_checkpoint"], row["p2_finish_gate"],
                          row["p2_laps_remaining"]), (2, 1, 3))
        self.assertEqual(row["timer_minutes_raw"], 0)
        self.assertEqual(row["timer_tenths_raw"], 0)
        buf = bytearray(image("zoom-zoo"))
        buf[probe.COURSE_RAM_OFFSET + 11] ^= 1
        buf[probe.COURSE_RAM_OFFSET + 12] ^= 1
        probe.sample_state(bytes(buf), "zoom-zoo", original)
        buf[probe.COURSE_RAM_OFFSET + 20] ^= 1
        with self.assertRaisesRegex(probe.CourseEntryEvidenceError, "not fully installed"):
            probe.sample_state(bytes(buf), "zoom-zoo", original)
        with self.assertRaisesRegex(probe.CourseEntryEvidenceError, "not active"):
            probe.sample_state(image("zoom-zoo"), "jumps", original)
        with self.assertRaisesRegex(probe.CourseEntryEvidenceError, "128 KiB"):
            probe.sample_state(bytes(buf[:-1]), "zoom-zoo", original)

    def test_report_comparison_preserves_exact_first_event_divergence(self):
        a = [{"relative_frame": frame, "p1_x": 100, "p1_y": 200}
             for frame in probe.SAMPLES]
        b = [dict(row) for row in a]
        self.assertIsNone(probe.first_difference(a, b))
        b[3]["p1_y"] = 208
        diff = probe.first_difference(a, b)
        self.assertEqual(diff["relative_frame"], 4)
        self.assertEqual(diff["fields"], ["p1_y"])
        self.assertEqual(diff["reference_values"]["p1_y"], 200)
        self.assertEqual(diff["native_values"]["p1_y"], 208)
        b[3]["relative_frame"] = 7
        with self.assertRaisesRegex(probe.CourseEntryEvidenceError, "do not align"):
            probe.first_difference(a, b)
        with self.assertRaisesRegex(probe.CourseEntryEvidenceError, "incomplete"):
            probe.first_difference(a[:-1], a)

    def test_phantom_checkpoint_finish_or_p2_lap_fails_at_first_bounded_frame(self):
        # A guest can appear to handle identically while its race progression
        # state differs. This checks the actual paired sampling path, not a
        # hand-built dictionary with hypothetical field names.
        decoded = bytes(range(64))
        reference = [
            {"relative_frame": frame, **probe.sample_state(
                image("zoom-zoo"), "zoom-zoo", decoded)}
            for frame in probe.SAMPLES
        ]
        native = [dict(row) for row in reference]
        bad = bytearray(image("zoom-zoo"))
        struct.pack_into("<H", bad, 0x1199, 1)  # P1 checkpoint credit
        struct.pack_into("<H", bad, 0x119D, 1)  # P1 finish gate
        struct.pack_into("<H", bad, 0x0EF3, 2)  # P2 lap credit
        native[4] = {"relative_frame": 8, **probe.sample_state(
            bytes(bad), "zoom-zoo", decoded)}
        self.assertEqual(reference[4]["p1_x"], native[4]["p1_x"])
        self.assertEqual(reference[4]["p2_x"], native[4]["p2_x"])
        self.assertEqual(reference[4]["p1_contact_stored"],
                         native[4]["p1_contact_stored"])
        self.assertEqual(reference[4]["p2_contact_stored"],
                         native[4]["p2_contact_stored"])
        difference = probe.first_difference(reference, native)
        self.assertEqual(difference["relative_frame"], 8)
        self.assertEqual(difference["fields"], [
            "p1_finish_gate", "p1_next_checkpoint", "p2_laps_remaining"
        ])
        self.assertEqual(difference["reference_values"],
                         {"p1_finish_gate": 0, "p1_next_checkpoint": 0,
                          "p2_laps_remaining": 3})
        self.assertEqual(difference["native_values"],
                         {"p1_finish_gate": 1, "p1_next_checkpoint": 1,
                          "p2_laps_remaining": 2})

    def test_stunt_course_records_raw_progress_without_asserting_race_lap_rules(self):
        # Jumps is a timed stunt event, not a circuit; its raw register
        # values are useful parity signals but cannot prove race-lap rules.
        row = probe.sample_state(image("jumps"), "jumps", bytes(range(64)))
        self.assertEqual((row["p1_next_checkpoint"], row["p1_finish_gate"],
                          row["p2_next_checkpoint"], row["p2_finish_gate"]),
                         (0, 0, 2, 1))

    def test_zero_snapshot_can_never_prove_loaded_course(self):
        # The decoded stream must be fully present, not a mostly-zero,
        # high-scoring best-match against an inactive WRAM buffer.
        original = bytes(range(64))
        with self.assertRaisesRegex(probe.CourseEntryEvidenceError, "not fully installed"):
            probe.sample_state(
                image("jumps", bytes(64)), "jumps", original,
            )

    def test_real_case_ids_match_canonical_stream_and_event_types(self):
        self.assertEqual(probe.CASES["zoom-zoo"], (2, 1, 0, 1, "circuit-a"))
        self.assertEqual(probe.CASES["jumps"], (13, 12, 2, 2, "stunt"))
        self.assertEqual(probe.SAMPLES, (0, 1, 2, 4, 8, 16, 32, 64))


if __name__ == "__main__":
    unittest.main()
