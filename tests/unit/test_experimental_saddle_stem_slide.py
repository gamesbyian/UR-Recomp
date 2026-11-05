"""Dependency-free synthetic control of the 2026 saddle stem displacement."""
import unittest
from tools.art.experimental_saddle_stem_slide import (
    SOURCE_STEM_UNIT,ALLOWED_STROKES,translate_parent_local_world
)

ID=((1.,0.,0.,0.),(0.,1.,0.,0.),(0.,0.,1.,0.),(0.,0.,0.,1.))
Q=((0.,0.,1.,0.),(0.,1.,0.,0.),(-1.,0.,0.,0.),(0.,0.,0.,1.))

def at(x,y,z,rotation=ID):
    return tuple(tuple(rotation[i][j] if j!=3 else (x,y,z)[i]
                       for j in range(4)) for i in range(3))+((0.,0.,0.,1.),)

class SaddleTranslationTests(unittest.TestCase):
    def test_original_mount_moves_in_parent_stem_direction_not_local_saddle(self):
        a=at(.04,0,3.27)
        for stroke in ALLOWED_STROKES:
            result=translate_parent_local_world(a,ID,stroke)
            self.assertEqual(tuple(row[:3] for row in result[:3]),
                             tuple(row[:3] for row in a[:3]))
            for k in range(3):
                self.assertAlmostEqual(result[k][3]-a[k][3],
                                       SOURCE_STEM_UNIT[k]*stroke)
        q=translate_parent_local_world(a,Q,.12)
        self.assertAlmostEqual(q[0][3]-a[0][3],SOURCE_STEM_UNIT[2]*.12)
        self.assertAlmostEqual(q[2][3]-a[2][3],-SOURCE_STEM_UNIT[0]*.12)

    def test_fails_closed_for_arbitrary_stroke_and_corrupted_real_glb(self):
        for v in (0.,.14,-.13,True,"0.12",None,float("nan")):
            with self.subTest(v=v),self.assertRaises(ValueError):
                translate_parent_local_world(ID,ID,v)
        reflected=((-1.,0,0,0),(0,1.,0,0),(0,0,1.,0),(0,0,0,1))
        shear=((1.,.1,0,0),(0,1.,0,0),(0,0,1.,0),(0,0,0,1))
        bad=at(0,float("inf"),0)
        for matrix in (reflected,shear,bad,((0.,),),True):
            with self.subTest(m=matrix),self.assertRaises(ValueError):
                translate_parent_local_world(matrix,ID,.12)
            with self.subTest(parent=matrix),self.assertRaises(ValueError):
                translate_parent_local_world(ID,matrix,.12)

if __name__=="__main__":
    unittest.main()
