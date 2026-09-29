from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from controller_input import ControllerRun, load_controller_runs, masks_at


class ControllerInputTests(unittest.TestCase):
    def test_legacy_three_field_rows_mean_player_one_only(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "input.txt"
            p.write_text("0:2:080\n", encoding="utf-8")
            self.assertEqual(
                load_controller_runs(p),
                [ControllerRun(0, 2, 0x080, 0)],
            )

    def test_four_field_rows_preserve_both_players(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "input.txt"
            p.write_text("0:3:080:040\n3:2:000:001\n", encoding="utf-8")
            runs = load_controller_runs(p)
            self.assertEqual(masks_at(runs, 1), (0x080, 0x040))
            self.assertEqual(masks_at(runs, 3), (0, 0x001))
            self.assertEqual(masks_at(runs, 5), (0, 0))

    def test_cross_player_overlap_is_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "input.txt"
            p.write_text("0:4:080:000\n2:4:000:040\n", encoding="utf-8")
            runs = load_controller_runs(p)
            self.assertEqual(masks_at(runs, 2), (0x080, 0x040))

    def test_same_player_overlap_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "input.txt"
            p.write_text("0:4:080:000\n3:2:001:000\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "player-1"):
                load_controller_runs(p)

    def test_zero_zero_row_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "input.txt"
            p.write_text("0:1:000:000\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "no controller input"):
                load_controller_runs(p)


if __name__ == "__main__":
    unittest.main()
