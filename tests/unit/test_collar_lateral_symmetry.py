"""Front-plane lateral symmetry diagnostic for actual GLB world geometry."""
import unittest
import numpy as np

try:
    import trimesh
    from tools.art.verify_collar_transition_review import lateral_reflection_error
except ImportError:
    trimesh = None


@unittest.skipUnless(trimesh is not None, "optional real GLB geometry dependencies")
class OwnerFrontMirrorTests(unittest.TestCase):
    def build(self, y):
        scene = trimesh.Scene(base_frame="world")
        for i in range(2):
            mesh = trimesh.creation.box(extents=[.24,.2,.32])
            mesh.apply_translation([0,y,0])
            scene.add_geometry(mesh,node_name=f"saddle__material_{i}",
                               geom_name=f"saddle__material_{i}",
                               parent_node_name="saddle")
        return scene

    def test_symmetric_saddle_has_zero_real_glb_mirror_error(self):
        report=lateral_reflection_error(self.build(0.),"saddle")
        self.assertEqual(report["sampled_world_vertices"],16)
        self.assertLess(report["max_nearest_vertex_error"],1e-10)
        self.assertFalse(report["exact_surface_mirror_recovered_1994"])

    def test_detect_lateral_seat_offset_and_reject_pedal_exception(self):
        moved=lateral_reflection_error(self.build(.3),"saddle")
        self.assertGreater(moved["max_nearest_vertex_error"],.3)
        with self.assertRaisesRegex(ValueError,"non-pedal"):
            lateral_reflection_error(self.build(0.),"pedals")
        with self.assertRaisesRegex(ValueError,"non-pedal"):
            lateral_reflection_error(self.build(0.),"unknown")


if __name__=="__main__":
    unittest.main()
