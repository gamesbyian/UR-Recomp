"""Player-visible blank-screen census from per-frame framebuffers."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa_blank_screen_census as m


def fb(level: int) -> bytes:
    return bytes([level, level, level, 0]) * (256 * 224)


class BlankCensus(unittest.TestCase):
    def test_brightness_uses_the_brightest_channel(self):
        self.assertEqual(m.brightness(fb(0)), 0)
        self.assertEqual(m.brightness(bytes([0, 0, 200, 0]) * 1000), 200)
        with self.assertRaises(ValueError):
            m.brightness(b"\x00" * 7)

    def test_dark_runs_are_inclusive_and_split_by_bright_frames(self):
        frames = list(range(10, 20))
        values = [0, 0, 50, 50, 0, 0, 0, 50, 1, 2]
        self.assertEqual(m.dark_runs(frames, values), [[10, 11], [14, 16], [18, 19]])

    def test_census_pairs_runs_and_reports_length_deltas(self):
        frames = list(range(0, 12))
        ref = [50, 0, 0, 0, 50, 50, 50, 0, 0, 50, 50, 50]
        nat = [50, 0, 0, 0, 0, 0, 50, 50, 0, 0, 0, 50]
        result = m.census(frames, {"bsnes": ref, "native": nat}, "bsnes")
        self.assertEqual(result["dark_frames"], {"bsnes": 5, "native": 8})
        self.assertEqual(
            [(r["reference"], r["other"], r["length_delta"])
             for r in result["paired_against_reference"]["native"]],
            [([1, 3], [1, 5], 2), ([7, 8], [8, 10], 1)])
        self.assertEqual(result["release_gate_credit"], 0)
        self.assertFalse(result["original_native_parity_claimed"])

    def test_unmatched_reference_run_is_reported_not_dropped(self):
        rows = m.pair_runs([[5, 6]], [[10, 12]])
        self.assertEqual(rows, [{"reference": [5, 6], "other": None, "length_delta": None}])


if __name__ == "__main__":
    unittest.main()
