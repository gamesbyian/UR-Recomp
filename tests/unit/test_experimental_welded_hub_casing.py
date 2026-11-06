"""One connected 2026 authored dark housing, retaining original 1994 art veto."""
import math
import unittest

from tools.art.experimental_welded_hub_casing import (
    RING_COUNT,WELDED_VERTICES,WELDED_FACES,
    welded_source_hub_casing,assert_closed_positive_one_solid,
)

def cylinder_source_vertices():
    n=50
    return tuple((.086*math.cos(2*math.pi*i/n),y,
                  .086*math.sin(2*math.pi*i/n))
                 for y in (-.21,.21) for i in range(n))

class WeldedSourceDarkHubTopologyTests(unittest.TestCase):
    def test_real_2026_sleeve_cross_section_welds_to_authored_dark_casing(self):
        vertices,faces=welded_source_hub_casing(cylinder_source_vertices())
        self.assertEqual((RING_COUNT,len(vertices),len(faces)),(58,234,464))
        volume=assert_closed_positive_one_solid(vertices,faces)
        self.assertAlmostEqual(volume,.0749600518095,places=8)
        self.assertAlmostEqual(min(p[0] for p in vertices),-.30,places=10)
        self.assertAlmostEqual(max(p[0] for p in vertices),.22,places=10)
        self.assertAlmostEqual(min(p[2] for p in vertices),-.37,places=10)
        self.assertAlmostEqual(max(p[2] for p in vertices),.27,places=10)
        self.assertAlmostEqual(min(p[1] for p in vertices),-.21,places=10)
        self.assertAlmostEqual(max(p[1] for p in vertices),.38,places=10)
        self.assertGreater(volume,.06592)
        self.assertLess(volume,.06592+.00973313)
        # Exact original 2026 chamfer corners are retained by angular registry.
        corners=[(-.26,-.37),(.18,-.37),(.22,-.33),(.22,.23),
                 (.18,.27),(-.26,.27),(-.30,.23),(-.30,-.33)]
        housing=vertices[2*RING_COUNT:3*RING_COUNT]
        for corner in corners:
            self.assertTrue(any(math.hypot(p[0]-corner[0],p[2]-corner[1])<1e-10
                                for p in housing),corner)
        self.assertEqual((vertices,faces),welded_source_hub_casing(cylinder_source_vertices()))

    def test_fail_closed_on_altered_original_source_cylinder_and_bad_mesh(self):
        source=cylinder_source_vertices()
        for wrong in (source[:-1],
                      source[:-1]+((0.,0.,0.),),
                      tuple((x,y,z*1.5) for x,y,z in source),
                      tuple((x,y+.01,z) for x,y,z in source)):
            with self.subTest(n=len(wrong)),self.assertRaises(ValueError):
                welded_source_hub_casing(wrong)
        vertices,faces=welded_source_hub_casing(source)
        with self.assertRaises(ValueError):
            assert_closed_positive_one_solid(vertices,faces[:-1])
        with self.assertRaises(ValueError):
            assert_closed_positive_one_solid(vertices,(faces[0],)+faces[1:-1])
        wrong=list(vertices);wrong[0]=wrong[1]
        with self.assertRaises(ValueError):
            assert_closed_positive_one_solid(tuple(wrong),faces)

    def test_real_trimesh_one_closed_component_if_optional_installed(self):
        try:
            import trimesh
        except ImportError:
            self.skipTest("trimesh optional, original 2026 GLB CI validates separately")
        vertices,faces=welded_source_hub_casing(cylinder_source_vertices())
        shape=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
        self.assertTrue(shape.is_watertight)
        self.assertTrue(shape.is_winding_consistent)
        self.assertEqual(shape.euler_number,2)
        # Full connectivity, one shell and reverse winding are independently
        # checked without optional NetworkX in assert_closed_positive_one_solid.
        self.assertAlmostEqual(shape.volume,assert_closed_positive_one_solid(vertices,faces),places=9)

if __name__=="__main__":
    unittest.main()
