"""Guard the source-only two-isolated-finish-pixel arithmetic, geometry and no promotion."""
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
import qa08_two_isolated_finish_pixels as source


class FinishOnePixelTest(unittest.TestCase):
    def test_two_precommitted_target_frames_and_latest_source(self):
        self.assertEqual(source.GUESTS,(3792,3872))
        self.assertEqual(source.NEIGHBOURS,(3776,3808,3856,3888))
        self.assertEqual((source.W,source.H),(256,224))
        self.assertEqual(source.EXPECTED_FULL_EXACT,203)
        self.assertEqual(source.EXPECTED_FULL_WRONG,385373)
        self.assertEqual(len(source.EXPECTED_NATIVE_EXE),64)

    def test_exact_BGRX_green6_only_and_unmasked_neighbor_coordinates(self):
        source_bytes=bytearray(source.W*source.H*4)
        native_bytes=bytearray(source.W*source.H*4)
        x,y=17,31
        at=(y*source.W+x)*4
        # 2014 original B,G,R,X; green6=6-bit 0x42 (RGB5 green=8).
        source_bytes[at:at+4]=bytes((24,66,90,255))
        native_bytes[at:at+4]=bytes((90,66,24,0))
        self.assertEqual(source.original_rgb5(source_bytes,x,y),(90,66,24))
        self.assertEqual(source.native_rgb(native_bytes,x,y),(90,66,24))
        self.assertFalse(any(p["wrong_RGB5"] for p in
            source.neighbourhood(source_bytes,native_bytes,x,y,0)))
        native_bytes[at+1]=57
        patch=source.neighbourhood(source_bytes,native_bytes,x,y,1)
        self.assertEqual(len(patch),9)
        self.assertEqual([p for p in patch if p["wrong_RGB5"]],
                         [next(p for p in patch if p["x"]==x and p["y"]==y)])
        self.assertEqual(patch[4]["original_RGB5_expanded"],[90,66,24])
        self.assertEqual(patch[4]["real_windows_RGB8"],[90,57,24])

    def test_invalid_full_size_or_coordinates_fail_closed(self):
        for a,b,x,y,radius in [
            (b"",bytes(source.W*source.H*4),1,1,1),
            (bytes(source.W*source.H*4),b"",1,1,1),
            (bytes(source.W*source.H*4),bytes(source.W*source.H*4),-1,1,1),
            (bytes(source.W*source.H*4),bytes(source.W*source.H*4),1,1,5),
        ]:
            with self.subTest(x=x,y=y,radius=radius),self.assertRaises(ValueError):
                source.neighbourhood(a,b,x,y,radius)


if __name__=="__main__":
    unittest.main()
