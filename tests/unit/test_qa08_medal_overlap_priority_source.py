"""Adversarial original VRAM/native OAM priority composition contracts."""
import unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_medal_overlap_priority_source as q


class OverlapSourceTest(unittest.TestCase):
    def test_exact_same_two_frames_five_positions_and_reverse_slot_precedence(self):
        self.assertEqual(q.ROWS,((207,91,112,None),(205,115,113,None),
                                 (205,139,114,None),(225,96,97,99),(225,120,96,98)))
        self.assertEqual(q.EXPECTED,(0,4,6,14,14))
        for slot,under in ((97,99),(96,98)):
            self.assertLess(slot,under)
    def test_foreign_input_sources_rejected_before_pixel_attribution(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td:
            p=Path(td)/"fake.zip"
            p.write_bytes(b"not source-authenticated")
            with self.assertRaisesRegex(ValueError,"unverified"):
                q.read_source(p,p,p)


if __name__=="__main__":
    unittest.main()
