"""ROM-free mathematical guards for the actual five-source-GLB pedal census."""
import unittest

# The general tooling suite intentionally stays dependency-free. Run the same
# full, unskipped checks inside the already-installed OpenSCAD rig venv, where
# all real GLBs are also available. Never silently replace these libraries
# with mocked geometry or relax the actual source/mesh assertions.
try:
    import numpy as np
    import scipy
    import trimesh
except ModuleNotFoundError:
    np = scipy = trimesh = None

if np is not None and scipy is not None and trimesh is not None:
    from tools.art.verify_source_pedal_pose_sweep import (
        bidirectional_nearest, rigid_crank_cloud, sided_cloud,
        translated_platform, verify_source_pedalling,
    )


@unittest.skipUnless(np is not None and scipy is not None and trimesh is not None,
                     "real-GLB unit cases require the isolated art rig dependencies")
class FivePosePedalMathTests(unittest.TestCase):
    def fixture(self):
        vertices = np.array([
            [0.2, 0.4, 0.2], [0.3, 0.4, 0.2], [0.2, 0.4, 0.3],
            [-0.2, -0.4, -0.2], [-0.3, -0.4, -0.2], [-0.2, -0.4, -0.3],
        ])
        mesh = trimesh.Trimesh(vertices=vertices,
                              faces=[[0, 1, 2], [3, 5, 4]],
                              process=False)
        return mesh

    def test_bidirectional_matches_permuted_vertices(self):
        a = np.array([[.1, .2, .3], [.3, .2, .1]])
        self.assertEqual(bidirectional_nearest(a, a[::-1])[
            "maximum_nearest_vertex_distance"], 0)
        self.assertGreater(bidirectional_nearest(a, a + [.01, 0, 0])[
            "maximum_nearest_vertex_distance"], .009)
        with self.assertRaises(ValueError):
            bidirectional_nearest(a, np.array([[float("nan"), 0, 1]]))
        with self.assertRaises(ValueError):
            bidirectional_nearest(np.empty((0, 3)), a)

    def test_sided_cloud_and_crossing_face_fail_closed(self):
        mesh = self.fixture()
        self.assertEqual(len(sided_cloud(mesh, 1)), 3)
        self.assertEqual(len(sided_cloud(mesh, -1)), 3)
        mesh.faces[0] = [0, 1, 3]
        with self.assertRaisesRegex(ValueError, "triangle bridges"):
            sided_cloud(mesh, 1)
        mesh.faces[0] = [0, 1, 2]
        mesh.vertices[0, 1] = 0.
        with self.assertRaisesRegex(ValueError, "crosses spindle"):
            sided_cloud(mesh, 1)

    def test_opposing_orbits_preserve_platform_orientation_and_y(self):
        source = self.fixture()
        for theta in (0, 18, 44, 88, 120, 150, 360, 720):
            for side in (-1, 1):
                a = sided_cloud(source, side)
                b = translated_platform(a, 18, theta, side)
                self.assertTrue(np.array_equal(a[:, 1], b[:, 1]))
                self.assertTrue(np.allclose(a[:, 0] - a[0, 0],
                                            b[:, 0] - b[0, 0]))
                self.assertTrue(np.allclose(a[:, 2] - a[0, 2],
                                            b[:, 2] - b[0, 2]))
                self.assertTrue(np.array_equal(source.vertices, self.fixture().vertices))
        with self.assertRaises(ValueError):
            translated_platform(np.ones((2, 3)), float("nan"), 18, 1)
        with self.assertRaises(ValueError):
            translated_platform(np.ones((2, 3)), 18, 88, 0)

    def test_rigid_rod_rotation_vs_openscad_retriangulation_is_not_conflated(self):
        x = np.array([[1., 0., 0.], [-1., 0., 0.]])
        actual = rigid_crank_cloud(x, 90)
        self.assertTrue(np.allclose(actual, [[0, 0, 1], [0, 0, -1]], atol=1e-12))
        with self.assertRaises(ValueError):
            rigid_crank_cloud(x, float("inf"))

    def test_unapproved_original_source_input_fails_before_missing_receipts(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "unreviewed.scad"
            p.write_text("// unsupported alternative")
            with self.assertRaisesRegex(ValueError, "canonical source-locked"):
                verify_source_pedalling(p, Path(tmp))


if __name__ == "__main__":
    unittest.main()
