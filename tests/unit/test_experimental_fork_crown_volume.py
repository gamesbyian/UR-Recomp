"""Frozen 2026 authored fork crown profile and exception-safe mesh restoration."""
import importlib.util
import unittest

from tools.art.experimental_fork_crown_volume import (
    CROWN_SCALES, CROWN_CENTER_Z, CROWN_HALF_BAND,
    source_stem_x, scale_crown_vertices, temporary_fork_crown_volume,
)


class ForkCrownVolumeTests(unittest.TestCase):
    def test_symmetrical_bounded_fork_crown_scaling_preserves_source_joints(self):
        self.assertEqual(CROWN_SCALES,(.90,1.10))
        self.assertAlmostEqual(CROWN_CENTER_Z-CROWN_HALF_BAND,.86)
        self.assertAlmostEqual(CROWN_CENTER_Z+CROWN_HALF_BAND,1.98)
        tip = source_stem_x(CROWN_CENTER_Z)
        source = (
            (tip+.30,.20,CROWN_CENTER_Z),  # source crown bulge
            (tip-.25,-.17,CROWN_CENTER_Z),
            (tip,0.,CROWN_CENTER_Z),       # centreline unchanged
            (-.35,.18,.86),                # smooth band boundary unchanged
            (-.10,.20,1.98),
            (-.06,.11,2.1),                # saddle clamp higher than band
            (-.05,-.12,.07),               # wheel/hub stays unchanged
        )
        for scale in CROWN_SCALES:
            posed=scale_crown_vertices(source,scale)
            self.assertEqual(len(posed),len(source))
            self.assertAlmostEqual(posed[0][0],tip+.30*scale)
            self.assertAlmostEqual(posed[0][1],.20*scale)
            self.assertAlmostEqual(posed[1][0],tip-.25*scale)
            self.assertAlmostEqual(posed[1][1],-.17*scale)
            self.assertEqual(posed[2],source[2])
            self.assertEqual(posed[3:],source[3:])
            self.assertEqual([row[2] for row in posed],
                             [row[2] for row in source])
        self.assertAlmostEqual(source_stem_x(.83),-.10)
        self.assertAlmostEqual(source_stem_x(1.39),-.17)
        self.assertAlmostEqual(source_stem_x(2.09),-.25)

    def test_source_geometry_rejects_fitted_invalid_or_unbounded_candidates(self):
        point=((0.,0.,1.42),)
        for scale in (1.,.8,1.2,True,None,"1.1",float("nan"),
                      float("inf"),0):
            with self.subTest(scale=scale),self.assertRaises(ValueError):
                scale_crown_vertices(point,scale)
        for invalid in (None,(),((1,2),),((1,2,3,4),),
                        ((float("nan"),0,1.42),),((1,0,float("inf")),)):
            with self.subTest(vertices=invalid),self.assertRaises(ValueError):
                scale_crown_vertices(invalid,1.1)
        for z in (float("nan"),float("inf"),None,"1.42"):
            with self.subTest(z=z),self.assertRaises(ValueError):
                source_stem_x(z)

    @unittest.skipUnless(importlib.util.find_spec("trimesh") and
                         importlib.util.find_spec("numpy"),
                         "real scene requires optional Trimesh/NumPy")
    def test_actual_five_parent_16_material_scene_restores_after_exception(self):
        import numpy as np
        import trimesh
        from tools.art.experimental_direct_drive_phase import PARTS,CHILD_COUNTS

        scene=trimesh.Scene()
        eye=np.eye(4)
        scene.graph.update(frame_to="world_1",frame_from="world",matrix=eye)
        for part in PARTS:
            scene.graph.update(frame_to=part,frame_from="world_1",matrix=eye)
            for index in range(CHILD_COUNTS[part]):
                name=f"{part}__material_{index}"
                if part=="fork_and_frame":
                    mesh=trimesh.creation.icosphere(subdivisions=1,radius=.3)
                    mesh.apply_translation([-.17,0,1.42])
                else:
                    mesh=trimesh.creation.box(extents=(.4,.4,.4))
                mesh.visual.vertex_colors=[(40,99,180,255)]*len(mesh.vertices)
                scene.geometry[name]=mesh
                scene.graph.update(frame_to=name,frame_from=part,
                                   matrix=eye,geometry=name)
        vertices={name:np.asarray(mesh.vertices).copy()
                  for name,mesh in scene.geometry.items()}
        parent={part:np.asarray(scene.graph.get(part)[0]).copy() for part in PARTS}
        for scale in CROWN_SCALES:
            with self.assertRaisesRegex(RuntimeError,"interrupt"):
                with temporary_fork_crown_volume(scene,scale):
                    self.assertFalse(np.array_equal(
                        scene.geometry["fork_and_frame__material_0"].vertices,
                        vertices["fork_and_frame__material_0"]))
                    self.assertTrue(np.array_equal(
                        scene.geometry["saddle__material_0"].vertices,
                        vertices["saddle__material_0"]))
                    raise RuntimeError("interrupt")
            for part in PARTS:
                np.testing.assert_array_equal(scene.graph.get(part)[0],
                                              parent[part])
            for name in vertices:
                np.testing.assert_array_equal(scene.geometry[name].vertices,
                                              vertices[name])


if __name__=="__main__":
    unittest.main()
