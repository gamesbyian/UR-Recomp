"""H26 source-free whole-block-shift false-positive on QA06 block checker."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2] / "tools"))
from qa06_source_shift_negative import qa06_source_free_shift_admission
from qa06_original_block_consistency import verify_blocks
from qa06_raster_roi_reference import source_pixel_at_host_coordinate


class WholeBlockShiftLimitation(unittest.TestCase):
    def test_wrong_source_pixel_shift_still_passes_block_checker(self):
        result = qa06_source_free_shift_admission(
            verify_blocks, source_pixel_at_host_coordinate)
        self.assertEqual(result['host'], [512,448])
        self.assertEqual(result['source'], [256,224])
        self.assertGreater(result['shifted_host_byte_differences'], 200000)
        self.assertTrue(result['clean_block_consistency_passes'])
        self.assertTrue(result['wrong_one_source_pixel_shift_also_passes'])
        self.assertTrue(result['requires_independently_pinned_source_frame_for_pixel_fidelity'])
        self.assertFalse(result['physical_capture'])
        self.assertFalse(result['art_approval'])
        self.assertFalse(result['release_credit'])


if __name__=='__main__':
    unittest.main()
