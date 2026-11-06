"""Front-plane lateral symmetry diagnostic for actual GLB world geometry."""
import unittest
import importlib.util
from types import SimpleNamespace

AVAILABLE = all(importlib.util.find_spec(name) is not None
                for name in ("numpy","scipy","trimesh"))
if AVAILABLE:
    import trimesh
    from tools.art.verify_collar_transition_review import (
        lateral_reflection_error, silver_post_cross_section_centers,
    )


@unittest.skipUnless(AVAILABLE, "optional real GLB geometry dependencies")
class OwnerFrontMirrorTests(unittest.TestCase):
    def build(self, y):
        scene = trimesh.Scene(base_frame="world")
        scene.graph.update(frame_from="world", frame_to="saddle")
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

    def test_actual_silver_mesh_sections_reject_tilt_and_offset(self):
        import numpy as np

        def silver_mesh():
            post=trimesh.creation.cylinder(radius=.06,height=.565,sections=48)
            post.apply_translation([-.22,0,(1.67+2.235)/2])
            return post

        key="fork_and_frame__material_1"
        vertical=SimpleNamespace(geometry={key:silver_mesh()})
        passed=silver_post_cross_section_centers(vertical)
        self.assertEqual(passed["source_heights"],[1.90,2.10])
        for center in passed["xy_centerline_at_each_height"]:
            self.assertAlmostEqual(center[0],-.22,places=4)
            self.assertAlmostEqual(center[1],0,places=4)

        shifted=silver_mesh()
        shifted.apply_translation([.015,0,0])
        with self.assertRaisesRegex(ValueError,"angled or off-centre"):
            silver_post_cross_section_centers(SimpleNamespace(geometry={key:shifted}))

        tilted=silver_mesh()
        shear=np.eye(4)
        shear[0,2]=.02/.565
        shear[0,3]=-shear[0,2]*1.67
        tilted.apply_transform(shear)
        with self.assertRaisesRegex(ValueError,"angled or off-centre"):
            silver_post_cross_section_centers(SimpleNamespace(geometry={key:tilted}))

    def test_detect_lateral_seat_offset_and_reject_pedal_exception(self):
        moved=lateral_reflection_error(self.build(.3),"saddle")
        self.assertGreater(moved["max_nearest_vertex_error"],.3)
        with self.assertRaisesRegex(ValueError,"non-pedal"):
            lateral_reflection_error(self.build(0.),"pedals")
        with self.assertRaisesRegex(ValueError,"non-pedal"):
            lateral_reflection_error(self.build(0.),"unknown")


if __name__=="__main__":
    unittest.main()
