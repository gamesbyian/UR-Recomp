"""Independent real BGRX original vs P7 RGBA A/B source comparison."""
import unittest
from tools.qa08_premath_full263_native_source_ab import census,pixels,PIXELS,HEADER
class TestAB(unittest.TestCase):
    def test_byte_order_exact_and_nonexact(self):
        ref=bytes((8,16,24,0))*PIXELS
        same=HEADER+bytes((24,16,8,255))*PIXELS
        wrong=HEADER+bytes((32,16,8,255))*PIXELS
        a=census(ref,same,same)
        self.assertEqual(a["original_baseline_wrong"],0)
        self.assertEqual(a["experimental_wrong"],0)
        b=census(ref,wrong,same)
        self.assertEqual(b["corrected"],PIXELS)
        self.assertEqual(b["newly_wrong"],0)
        c=census(ref,same,wrong)
        self.assertEqual(c["newly_wrong"],PIXELS)
    def test_no_cropped_or_forged_pixel_buffer(self):
        with self.assertRaisesRegex(ValueError,"uncropped"):
            pixels(b"")
        with self.assertRaisesRegex(ValueError,"cropped"):
            census(b"",HEADER+b"\x00"*(PIXELS*4),HEADER+b"\x00"*(PIXELS*4))
if __name__=="__main__":unittest.main()
