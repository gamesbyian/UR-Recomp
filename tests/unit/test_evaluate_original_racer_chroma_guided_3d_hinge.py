"""ROM-free controls for source-painted 2D to authored 3D hinge matching."""
import math
import unittest
from tools.art.evaluate_original_racer_chroma_guided_3d_hinge import (
    ANGLES,source_selected_angle,painted_axis_from_mask,spin_frame,
)

class ChromaGuidedHingeTests(unittest.TestCase):
    def test_grid_uses_fixed_degree_bounds_without_silhouette_oracle(self):
        self.assertEqual(ANGLES,tuple(range(-45,46,5)))
        source={a:float(-a) for a in ANGLES}
        self.assertEqual(source_selected_angle(40.,source),-40)
        self.assertEqual(source_selected_angle(-25.,source),25)
        self.assertEqual(source_selected_angle(0.,source),0)
        for problem in (float("nan"),float("inf"),True,"41",None):
            with self.subTest(problem=problem),self.assertRaises(ValueError):
                source_selected_angle(problem,source)
        with self.assertRaises(ValueError):
            source_selected_angle(30.,{0:0.})

    def test_source_painted_pixel_axis_is_signed_and_pixel_aspect_adjusted(self):
        try:
            import numpy as np
        except ImportError:
            self.skipTest("optional NumPy")
        image=np.zeros((64,64),dtype=bool)
        for y in range(10,40):
            # Painted frame leaning right from top to bottom.
            image[y,20+(y-10)//3]=True
        observed=painted_axis_from_mask(image)
        self.assertGreater(observed,0.)
        image=np.fliplr(image)
        self.assertLess(painted_axis_from_mask(image),0.)
        with self.assertRaises(ValueError):
            painted_axis_from_mask(np.zeros((64,64),dtype=bool))

    def test_unexpected_source_hinge_angles_fail_closed(self):
        for angle in (-46,46,3.,5.5,"5",True,None):
            with self.subTest(angle=angle),self.assertRaises(ValueError):
                spin_frame(None,angle)


if __name__=="__main__":
    unittest.main()
