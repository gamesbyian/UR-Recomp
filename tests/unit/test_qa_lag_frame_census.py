"""Game-frame census from the 7E:00C6 vblank-wait counter."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import qa_lag_frame_census as m


def pages(counter_values, menus=None):
    out = []
    for i, c in enumerate(counter_values):
        page = bytearray(131072)
        page[m.COUNTER] = c
        page[m.MENU] = (menus or [0] * len(counter_values))[i]
        out.append(bytes(page))
    return out


class Census(unittest.TestCase):
    def test_counts_decrements_across_the_mod_32_reload(self):
        # 0x02 -> 0x1E is four passes through 0x01, 0x00, reload 0x1F, 0x1E.
        self.assertEqual(m.passes(pages([0x05, 0x02, 0x1E])), [3, 4])

    def test_reports_lag_and_only_differing_windows(self):
        frames = [0, 4, 8, 12]
        result = m.census(frames, {
            "native": pages([0x10, 0x0C, 0x0B, 0x07], [0, 0x84, 0x84, 0x84]),
            "snes9x": pages([0x10, 0x0C, 0x08, 0x04], [0, 0x84, 0xD7, 0xD7]),
        })
        self.assertEqual(result["host_frames"], 12)
        self.assertEqual(result["game_frames"], {"native": 9, "snes9x": 12})
        self.assertEqual(result["lag_frames"], {"native": 3, "snes9x": 0})
        self.assertEqual(result["differing_windows"], [
            {"host_frames": [4, 8], "menu": {"native": 0x84, "snes9x": 0xD7},
             "game_frames": {"native": 1, "snes9x": 4}}])
        self.assertEqual(result["release_gate_credit"], 0)

    def test_rejects_samples_too_sparse_or_impossible_counts(self):
        with self.assertRaisesRegex(ValueError, "period"):
            m.census([0, 40], {"a": pages([0, 0])})
        with self.assertRaisesRegex(ValueError, "impossible"):
            m.census([0, 2], {"a": pages([0x10, 0x0C])})


if __name__ == "__main__":
    unittest.main()
