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
        (0x0E95, 0x2024), (0x0E97, 0x1804),
        (0x0EF1, 2), (0x11CF, 64),
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
        self.assertEqual(row["p1_laps_remaining"], 2)
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
        self.assertEqual(probe.SAMPLES, (0, 1, 2, 4, 8, 16))


if __name__ == "__main__":
    unittest.main()
