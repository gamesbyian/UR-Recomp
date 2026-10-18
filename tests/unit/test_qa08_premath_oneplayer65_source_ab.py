"""Source exact 1P 2014 BGRX / current Win32 P7 RGBA pixel verifier."""
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"tools"))
from tools.qa08_premath_oneplayer65_source_ab import PIXELS,HEADER,census,FRAMES
class QA08OneplayerSource(unittest.TestCase):
    def test_65_original_source_frames(self):
        self.assertEqual(len(FRAMES),65)
        self.assertEqual((FRAMES[0],FRAMES[-1]),(2177,2241))
    def test_rgb5_bgrx_and_rgba_pixel_identity(self):
        old=bytes((16,24,32,0))*PIXELS
        exact=HEADER+bytes((32,24,16,255))*PIXELS
        broken=HEADER+bytes((40,24,16,255))*PIXELS
        self.assertEqual(census(old,exact),0)
        self.assertEqual(census(old,broken),PIXELS)
    def test_no_cropped_or_bad_source(self):
        with self.assertRaisesRegex(ValueError,"actual complete"):
            census(b"",b"")
if __name__=="__main__":unittest.main()
