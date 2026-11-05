"""No numpy/GLB dependency: predeclared upper frame stretch constraints."""
import unittest
from tools.art.experimental_upper_frame_stretch import (
    SCALES,SADDLE_MOUNT_HEIGHT,stretch_vertices
)

class AuthoredUpperStretchTests(unittest.TestCase):
    def test_both_scales_preserve_xy_and_transform_only_source_z(self):
        source=((0.,0.,-.02),(.3,.1,1.),(-.25,0,2.27))
        for factor in SCALES:
            one=stretch_vertices(source,factor)
            self.assertEqual(len(one),3)
            for original,changed in zip(source,one):
                self.assertEqual(changed[:2],original[:2])
                self.assertAlmostEqual(changed[2],original[2]*factor)
            self.assertAlmostEqual(SADDLE_MOUNT_HEIGHT*(factor-1),
                                   2.27*(factor-1))
        self.assertEqual(source[2][2],2.27)

    def test_source_rejects_fitted_or_nonfinite_geometry(self):
        src=((0,0,0),(0,0,2))
        for bad in (0,1,1.05,.95,True,float("nan"),"1.04"):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                stretch_vertices(src,bad)
        for invalid in ((),((1,2),),((0,0,float("inf")),),
                        ((0,0,0),(0,0,float("nan"))),None):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                stretch_vertices(invalid,1.04)

if __name__=="__main__":
    unittest.main()
