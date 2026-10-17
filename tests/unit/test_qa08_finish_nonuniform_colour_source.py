"""Adversarial tests for source colour-only LUT impossibility."""
import unittest
from tools.qa08_finish_nonuniform_colour_source import pixel, targets, diagnose
from tools.qa08_result_grey_phase_archive_check import PIXELS
class ColourSourceTests(unittest.TestCase):
    def test_BGRX_and_RGBA_bit_mapping(self):
        self.assertEqual(pixel(bytes([56,48,40,255]),0,True),0x14c7)
        self.assertEqual(pixel(bytes([32,48,56,255]),0,False),0x10c7)
    def test_cropped_or_zero_forgery_rejected(self):
        with self.assertRaisesRegex(ValueError,"cropped"):
            targets(b"",b"",0x10c6)
        a=bytes(PIXELS*4)
        with self.assertRaisesRegex(ValueError,"source census drift"):
            diagnose({3680:a,4064:a,1856:a},
                     {3680:a,4064:a,1856:a})
    def test_adjacent_original_targets_not_a_function_of_native_colour(self):
        by_native={0x10c6:{0x14e7,0x10c6}}
        self.assertEqual(len(by_native[0x10c6]),2)

    def test_full_RGB8_transfer_rejects_cropped_and_ambiguous_target(self):
        from tools.qa08_finish_nonuniform_colour_source import rgb8_finish_transfer, FINISH_FIELDS
        a=bytes(PIXELS*4)
        with self.assertRaisesRegex(ValueError,"cropped"):
            rgb8_finish_transfer({f:b"" for f in FINISH_FIELDS},
                                 {f:a for f in FINISH_FIELDS})
        # Same true native RGB8 input, conflicting original normalised RGB5.
        orig={f:a for f in FINISH_FIELDS}
        nat={f:a for f in FINISH_FIELDS}
        modified=bytearray(a)
        modified[2]=40
        orig[3664]=bytes(modified)
        with self.assertRaisesRegex(ValueError,"not source-deterministic"):
            rgb8_finish_transfer(orig,nat)
if __name__=="__main__":unittest.main()
