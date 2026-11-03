"""ROM-free mathematical and optional synthetic GLB tests of one-rig coupled motion."""
import math
import unittest

from tools.art.experimental_continuous_five_parent_pose import (
    parameters, apply_scene, build, DRIVE, FRAME, PARTS, CHILD_COUNTS, SCHEMA,
)
from tools.art.experimental_direct_drive_phase import rotation as drive_rotation
from tools.art.experimental_frame_hinge import rotation_y as frame_rotation

try:
    import numpy as np
    import trimesh
except ImportError:
    np = None
    trimesh = None


class ContinuousParentPoseTests(unittest.TestCase):
    def test_angles_have_explicit_bounds_and_no_nonfinite_or_boolean_values(self):
        self.assertEqual(parameters(0, 0), (0., 0.))
        self.assertEqual(parameters(-360, -45), (-360., -45.))
        self.assertEqual(parameters(360, 45), (360., 45.))
        for a, b in ((361, 0), (-361, 0), (0, 46), (0, -46),
                     (float("nan"), 0), (0, float("inf")),
                     (True, 0), (0, False), ("25", 0)):
            with self.subTest(a=a, b=b):
                with self.assertRaisesRegex(ValueError, "finite"):
                    parameters(a, b)

    def test_drive_and_frame_are_opposite_sign_conventions_with_closed_turn(self):
        a = drive_rotation(25)
        b = frame_rotation(-25)
        for row1, row2 in zip(a, b):
            for x, y in zip(row1, row2):
                self.assertAlmostEqual(x, y, places=12)
        for i, row in enumerate(drive_rotation(360)):
            for j, val in enumerate(row):
                self.assertAlmostEqual(val, 1 if i == j else 0, places=12)

    @unittest.skipUnless(np is not None and trimesh is not None, "optional trimesh/numpy")
    def test_synthetic_sixteen_mesh_scene_two_controls_keep_coupled_parts(self):
        scene = trimesh.Scene()
        # A translated axle catches accidental world-origin rotations.
        axle = np.eye(4)
        axle[:3, 3] = [2.0, -3.0, 4.0]
        for part in PARTS:
            initial = axle.copy()
            if part == "fork_and_frame":
                initial[:3, 3] += [0, 0, 0.3]
            if part == "saddle":
                initial[:3, 3] += [0, 0, 0.7]
            scene.graph.update(frame_to=part, frame_from="world", matrix=initial)
            for i in range(CHILD_COUNTS[part]):
                node = f"{part}__material_{i}"
                cube = trimesh.creation.box(extents=(0.1, 0.2, 0.3))
                scene.add_geometry(cube, node_name=node, geom_name=node,
                                   parent_node_name=part)
        self.assertEqual(len(scene.graph.nodes_geometry), 16)
        old_mesh = {
            k: (np.array(v.vertices, copy=True), np.array(v.faces, copy=True))
            for k, v in scene.geometry.items()
        }
        before = {p: np.array(scene.graph.get(p)[0], copy=True) for p in PARTS}
        output = apply_scene(scene, 35, 14)
        self.assertEqual(output["schema"], SCHEMA)
        self.assertEqual(output["rotated_drive_parts"], list(DRIVE))
        self.assertEqual(output["rotated_upper_frame_parts"], list(FRAME))
        tire = scene.graph.get("tire")[0]
        for part in DRIVE:
            self.assertTrue(np.allclose(scene.graph.get(part)[0], tire))
        # Upper-frame parts share a rotation relative to the same original axle.
        for part in FRAME:
            self.assertFalse(np.allclose(scene.graph.get(part)[0], before[part]))
        self.assertTrue(np.allclose(scene.graph.get("tire")[0][:3, 3], [2, -3, 4]))
        for k, (vertices, faces) in old_mesh.items():
            self.assertTrue(np.array_equal(scene.geometry[k].vertices, vertices))
            self.assertTrue(np.array_equal(scene.geometry[k].faces, faces))
        self.assertFalse(output["original_3d_geometry_recovered"])
        self.assertFalse(output["owner_likeness_approved"])
        # Absolute control should not accumulate A into B or fail to return
        # to the SHA-bound source rest geometry when neutral is requested.
        apply_scene(scene, -25, 7)
        apply_scene(scene, 0, 0)
        for p in PARTS:
            self.assertTrue(np.allclose(scene.graph.get(p)[0], before[p],
                                        atol=1e-8, rtol=0))
        # An external writer cannot silently invalidate that cached source.
        scene.graph.update(frame_to="tire", frame_from="world", matrix=np.eye(4))
        with self.assertRaisesRegex(ValueError, "externally changed"):
            apply_scene(scene, 20, 4)

    @unittest.skipUnless(np is not None and trimesh is not None, "optional trimesh/numpy")
    def test_reject_bad_source_scene_hierarchy_and_unauthenticated_glb(self):
        scene = trimesh.Scene()
        with self.assertRaisesRegex(ValueError, "canonical"):
            apply_scene(scene, 0, 0)
        with self.assertRaisesRegex(ValueError, "SHA-pinned"):
            build(b"glTF" + bytes(40), 0, 0)


if __name__ == "__main__":
    unittest.main()
