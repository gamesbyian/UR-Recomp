"""Freeze manual-inspired 2026 spoke blade geometry and full source rollback."""
import importlib.util
import math
import unittest

from tools.art.experimental_spoke_blade_volume import (
    BLADE_WIDTH_FACTOR,ORIGINAL_RADIAL_OFFSET_DEGREES,
    SOURCE_GL_B_VERTEX_COUNT,SOURCE_GL_B_FACE_COUNT,
    SPOKE_SET_COUNT,UNMODIFIED_ROOT_RADIUS,
    wider_blade_vertices,temporary_wider_spoke_blades,
)


class ManualSpokeBladeVolumeTests(unittest.TestCase):
    def test_exact_source_spoke_count_root_and_wider_planar_blades(self):
        self.assertEqual(SPOKE_SET_COUNT,8)
        self.assertEqual(ORIGINAL_RADIAL_OFFSET_DEGREES,11)
        self.assertEqual(BLADE_WIDTH_FACTOR,2.)
        self.assertEqual((SOURCE_GL_B_VERTEX_COUNT,SOURCE_GL_B_FACE_COUNT),
                         (1788,3572))
        theta=math.radians(11)
        radius=.7
        spread=.02
        p=(radius*math.sin(theta+spread),-.025,radius*math.cos(theta+spread))
        base=(radius*math.sin(theta),-.025,radius*math.cos(theta))
        root=(.05,-.04,.04)
        source=(root,base,p,(0,0,0))
        result=wider_blade_vertices(source)
        self.assertEqual(result[0],root)
        self.assertEqual(result[3],source[3])
        self.assertAlmostEqual(result[1][0],base[0],12)
        self.assertAlmostEqual(result[1][2],base[2],12)
        self.assertEqual(result[2][1],p[1])
        self.assertAlmostEqual(math.hypot(result[2][0],result[2][2]),
                               radius,12)
        self.assertGreater(math.hypot(result[2][0]-base[0],
                                      result[2][2]-base[2]),
                           math.hypot(p[0]-base[0],p[2]-base[2]))
        for factor in (0.9,1.,1.5,2.5,True,float("nan"),None,"2.0"):
            with self.subTest(factor=factor),self.assertRaises(ValueError):
                wider_blade_vertices(source,factor)
        for candidate in ([],[(1,2)],[(1,2,3,4)],[(0,float("inf"),1)],
                          [(float("nan"),0,1)]):
            with self.subTest(candidate=candidate),self.assertRaises(ValueError):
                wider_blade_vertices(candidate)

    def test_exact_real_glb_numeric_receipt_is_nonshipping_and_source_bound(self):
        import json
        from pathlib import Path
        source=Path(__file__).resolve().parents[2]
        record=json.loads((source/"analysis/data/racer-art4k-2026-source-glb-blade-spoke-volume-20261105.json").read_text(encoding="utf-8"))
        self.assertEqual(record["schema"],
                         "UR-ART4K-2026-REAL-GLB-PRINT-INSPIRED-SPOKE-VOLUME/1")
        self.assertEqual(record["source_2026_upright_GLb_sha256"],
                         "d83a39b805107eb309d3f56db8d5aeb77f435038170005fd5d15c0c45ed4c94a")
        self.assertEqual(record["original_source_GLb_byte_count"],639132)
        self.assertEqual(record["original_rim_spoke_material_node"],"rim_and_hub__material_2")
        self.assertEqual(record["original_fixed_spoke_count"],8)
        self.assertEqual(record["source_spoke_vertices"],1788)
        self.assertEqual(record["source_spoke_faces"],3572)
        self.assertEqual(record["changed_original_vertices_over_1e_5_model_units"],1264)
        self.assertAlmostEqual(record["max_vertex_displacement_model_units"],0.01811738)
        self.assertAlmostEqual(record["original_spoke_mesh_signed_volume_model_units3"],0.015428575,9)
        self.assertAlmostEqual(record["proposed_spoke_mesh_signed_volume_model_units3"],0.019122291,9)
        self.assertAlmostEqual(record["changed_spoke_mesh_volume_percent"],23.940743,5)
        self.assertTrue(record["original_source_2026_spoke_mesh_watertight_after_deformation"])
        self.assertTrue(record["original_2026_model_vertex_arrays_restored_exactly"])
        self.assertFalse(record["original_1994_3D_mesh_camera_spoke_count_or_rig_recovered"])
        self.assertFalse(record["owner_2026_character_likeness_approved"])
        self.assertFalse(record["shipping_art_approved"])

    @unittest.skipUnless(importlib.util.find_spec("numpy") and
                         importlib.util.find_spec("trimesh"),
                         "optional real GLB mesh geometry requires NumPy/Trimesh")
    def test_sixteen_real_part_material_graph_reverts_on_exception(self):
        import numpy as np
        import trimesh
        from tools.art.experimental_direct_drive_phase import PARTS,CHILD_COUNTS
        scene=trimesh.Scene()
        eye=np.eye(4)
        scene.graph.update(frame_to="source_root",frame_from="world",matrix=eye)
        for part in PARTS:
            scene.graph.update(frame_to=part,frame_from="source_root",matrix=eye)
            for index in range(CHILD_COUNTS[part]):
                name=f"{part}__material_{index}"
                if name=="rim_and_hub__material_2":
                    theta=math.radians(11)
                    pts=np.asarray([
                        [.68*math.sin(theta+.03),-.02,.68*math.cos(theta+.03)],
                        [.68*math.sin(theta-.03),-.02,.68*math.cos(theta-.03)],
                        [.04,0,.04],
                    ],dtype=float)[np.arange(SOURCE_GL_B_VERTEX_COUNT)%3]
                    faces=np.arange(SOURCE_GL_B_FACE_COUNT*3).reshape(-1,3)
                    faces=faces%SOURCE_GL_B_VERTEX_COUNT
                    mesh=trimesh.Trimesh(vertices=pts,faces=faces,process=False)
                    mesh.visual.vertex_colors=np.tile(
                        [184,204,217,255],(SOURCE_GL_B_VERTEX_COUNT,1))
                else:
                    mesh=trimesh.creation.box(extents=(.1,.1,.1))
                    mesh.visual.vertex_colors=np.tile(
                        [28,89,222,255],(len(mesh.vertices),1))
                scene.geometry[name]=mesh
                scene.graph.update(frame_to=name,frame_from=part,
                                   matrix=eye,geometry=name)
        before={name:(np.asarray(m.vertices).copy(),np.asarray(m.faces).copy(),
                      np.asarray(m.visual.vertex_colors).copy())
                for name,m in scene.geometry.items()}
        parents={p:np.asarray(scene.graph.get(p)[0]).copy() for p in PARTS}
        with self.assertRaisesRegex(RuntimeError,"interrupt"):
            with temporary_wider_spoke_blades(scene):
                self.assertFalse(np.array_equal(
                    scene.geometry["rim_and_hub__material_2"].vertices,
                    before["rim_and_hub__material_2"][0]))
                self.assertTrue(np.array_equal(
                    scene.geometry["fork_and_frame__material_0"].vertices,
                    before["fork_and_frame__material_0"][0]))
                raise RuntimeError("interrupt")
        for p in PARTS:
            np.testing.assert_array_equal(scene.graph.get(p)[0],parents[p])
        for name,mesh in scene.geometry.items():
            for actual,original in zip(
                    (mesh.vertices,mesh.faces,mesh.visual.vertex_colors),before[name]):
                np.testing.assert_array_equal(actual,original)


if __name__=="__main__":
    unittest.main()
