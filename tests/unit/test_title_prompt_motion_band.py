"""ROM-free pixel-center controls for title reduced-motion isolation.

These small masks deliberately do not claim an original/native or device run.
"""
from __future__ import annotations
import sys
from pathlib import Path
import unittest

try:
    import numpy as np
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
    from verify_title_plate_artifact import prompt_only_motion
except ImportError:
    np = None
    prompt_only_motion = None


@unittest.skipUnless(np is not None and prompt_only_motion is not None,
                     'optional NumPy/Pillow graphics research dependencies')
class TitlePromptMotionBandTests(unittest.TestCase):
    def make_mask(self, height, source_row):
        mask = np.zeros((height, 16), dtype=bool)
        ys = np.flatnonzero(np.floor((np.arange(height) + .5) * 224 / height) == source_row)
        self.assertGreater(len(ys), 0)
        mask[int(ys[0]), 5] = True
        return mask

    def test_real_archive_768p_prompt_band(self):
        mask = np.zeros((768, 16), dtype=bool)
        mask[696:720, 5] = True  # authentic observed bounding rows
        prompt_only_motion(mask, 768)

    def test_real_archive_720p_prompt_band(self):
        mask = np.zeros((720, 16), dtype=bool)
        mask[652:674, 5] = True  # authentic observed bounding rows
        prompt_only_motion(mask, 720)

    def test_rehashed_top_of_title_difference_refused(self):
        for height in (720, 768):
            with self.subTest(height=height):
                mask = self.make_mask(height, 203)
                mask |= self.make_mask(height, 108)
                with self.assertRaisesRegex(ValueError, 'escaped title prompt band'):
                    prompt_only_motion(mask, height)

    def test_bottom_overscan_difference_refused(self):
        for height in (720, 768):
            with self.subTest(height=height):
                with self.assertRaisesRegex(ValueError, 'escaped title prompt band'):
                    prompt_only_motion(self.make_mask(height, 223), height)

    def test_empty_or_invalid_geometry_refused(self):
        mask = np.zeros((720, 16), dtype=bool)
        with self.assertRaisesRegex(ValueError, 'did not change'):
            prompt_only_motion(mask, 720)
        with self.assertRaisesRegex(ValueError, 'invalid.*geometry'):
            prompt_only_motion(mask, 768)


if __name__ == '__main__':
    unittest.main()
