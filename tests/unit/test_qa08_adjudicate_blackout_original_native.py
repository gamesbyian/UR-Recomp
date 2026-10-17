"""Authentic original/native black PPU full-geometry source checker."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_adjudicate_blackout_original_native as q

class BlackoutRealSourceTest(unittest.TestCase):
    def test_pinned_three_sources_and_sparse_frame_controls(self):
        self.assertEqual(q.PIXELS,57344)
        self.assertEqual(q.SCENES[4016],54709)
        self.assertEqual(q.SCENES[4000],0)
        self.assertEqual(q.SCENES[4048],0)
        self.assertEqual(q.SCENES[4032],296)
        self.assertEqual(len(q.SCENES),8)
        self.assertEqual(q.actual_pixels(bytes(4*q.PIXELS),q.P7+bytes(4*q.PIXELS)),0)
        with self.assertRaises(ValueError):
            q.actual_pixels(bytes(4*q.PIXELS-1),q.P7+bytes(4*q.PIXELS))
        with self.assertRaises(ValueError):
            q.actual_pixels(bytes(4*q.PIXELS),bytes(4*q.PIXELS))
        self.assertIn("original_callback_equals_native_guest_minus_one_no_temporal_search",
                      (ROOT/"tools/qa08_adjudicate_blackout_original_native.py").read_text())
        self.assertNotIn("forcepoke(",(
            ROOT/"tools/qa08_adjudicate_blackout_original_native.py").read_text())

if __name__=="__main__":
    unittest.main()
