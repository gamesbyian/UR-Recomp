"""Actual full-triangle radial test, mandatory in isolated real-art model CI."""
import unittest

try:
    import numpy as np
    import trimesh
except ModuleNotFoundError:
    np=trimesh=None

if np is not None and trimesh is not None:
    from tools.art.verify_rotating_axle_bearing_review import (
        projected_triangle_origin_radius,
    )


@unittest.skipUnless(np is not None and trimesh is not None,
                     "requires isolated original geometry/GLB dependencies")
class ShaftTriangleSurfaceTests(unittest.TestCase):
    def test_triangle_interior_can_hit_shaft_without_any_vertex_inside(self):
        # Three projected vertices all outside a .065 drive shaft, but
        # the entire source triangle still covers the central rotation axis.
        points = np.array([[.12,0.,0.],
                           [-.06,0.,.10392304845],
                           [-.06,0.,-.10392304845]])
        faces = np.array([[0,1,2]])
        self.assertGreater(np.linalg.norm(points[:,(0,2)],axis=1).min(),.065)
        self.assertAlmostEqual(projected_triangle_origin_radius(points,faces),0.0)

    def test_triangle_edge_can_intersect_shaft_without_near_vertices(self):
        points = np.array([[.065,0.,-.08],[.065,0.,.08],[.2,0.,.12]])
        self.assertAlmostEqual(
            projected_triangle_origin_radius(points,[[0,1,2]]),.065)

    def test_annular_facets_and_degenerate_projection(self):
        points=np.array([[.071,0.,0.],[.071,1.,0.],[.073,0.,.05],
                         [.073,1.,.05]])
        self.assertGreater(
            projected_triangle_origin_radius(points,[[0,1,2],[1,3,2]]),.0655)
        points=np.array([[.08,0.,0.],[.08,1.,0.],[.08,2.,0.]])
        self.assertAlmostEqual(
            projected_triangle_origin_radius(points,[[0,1,2]]),.08)

    def test_refuse_invalid_or_missing_source_surfaces(self):
        for vertices, faces in (
            ([[0,0,0]], []), ([[0,0,0]], [[0,1,2]]),
            ([[float("nan"),0,0],[1,0,0],[0,0,1]],[[0,1,2]]),
        ):
            with self.assertRaises(ValueError):
                projected_triangle_origin_radius(vertices,faces)


if __name__=="__main__":
    unittest.main()
