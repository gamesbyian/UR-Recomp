"""Real mesh-independent tests for frozen saddle shape ablation."""
import unittest
from tools.art.experimental_saddle_span import SADDLE_SPANS,span_vertices

class SourceSaddleSpanTests(unittest.TestCase):
    def test_source_mesh_local_x_only_and_exact_authored_pivot(self):
        original=((-1.0,-.2,.05),(-.2,0,.2),(.8,.1,.3))
        for span in SADDLE_SPANS:
            changed=span_vertices(original,span)
            self.assertEqual(len(changed),len(original))
            for a,b in zip(original,changed):
                self.assertAlmostEqual(b[0],a[0]*span)
                self.assertEqual(b[1:],a[1:])
        self.assertEqual(original[0][0],-1.)
    def test_disallows_paint_camera_and_unbounded_shape_fits(self):
        for factor in (0,1.,.8,1.2,True,None,"1.1",float("nan")):
            with self.subTest(factor=factor),self.assertRaises(ValueError):
                span_vertices(((1,0,1),),factor)
        for pts in ((),None,((1,2),),((1,2,3,4),),
                    ((float("inf"),0,1),),((1,0,float("nan")),)):
            with self.subTest(pts=pts),self.assertRaises(ValueError):
                span_vertices(pts,1.1)

if __name__=="__main__":
    unittest.main()
