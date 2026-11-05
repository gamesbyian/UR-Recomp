"""Saddle contour geometry constraints, with optional real Trimesh rollback."""
import importlib.util
import math
import unittest

from tools.art.experimental_saddle_cup import (
    CUP_OFFSETS, cup_vertices, temporary_saddle_cup,
)


class SaddleCupGeometryTests(unittest.TestCase):
    def test_predeclared_cup_depth_affects_only_center_upper_material(self):
        bounds = (-1., 1., -.2, .6)
        sample = ((-1.,0.,.6), (1.,0.,.6), (0.,0.,-.2),
                  (0.,0.,-.04), (0.,0.,.6), (.5,.25,.6))
        for offset in CUP_OFFSETS:
            changed = cup_vertices(sample,offset,bounds)
            self.assertEqual([row[:2] for row in changed],
                             [row[:2] for row in sample])
            for i in range(4):
                self.assertAlmostEqual(changed[i][2],sample[i][2])
            self.assertAlmostEqual(changed[4][2]-sample[4][2],offset)
            self.assertAlmostEqual(changed[5][2]-sample[5][2],
                                   offset*(1-.5*.5)**2)
        self.assertEqual(cup_vertices(sample,-.08,bounds)[4][2],
                         .6-.08)
        self.assertEqual(cup_vertices(sample,.08,bounds)[4][2],
                         .6+.08)

    def test_common_bounds_make_2026_material_seam_continuous(self):
        bounds = (-1., 1., -.2, .6)
        # The same coincident vertex in the dark body and its top highlight
        # MUST receive exactly the same displacement, not a per-mesh Z ratio.
        dark = ((0.,.15,.5),(-1.,0.,-.2))
        highlight = ((0.,.15,.5),(1.,0.,.6))
        for offset in CUP_OFFSETS:
            self.assertEqual(cup_vertices(dark,offset,bounds)[0],
                             cup_vertices(highlight,offset,bounds)[0])

    def test_rejects_unbounded_or_malformed_sculpt_and_vertex(self):
        valid = ((0.,0.,.6),)
        bounds = (-1.,1.,-.2,.6)
        for value in (0,.01,.1,-.1,True,None,"-.08",float("nan"),
                      float("inf")):
            with self.subTest(offset=value),self.assertRaises(ValueError):
                cup_vertices(valid,value,bounds)
        for limits in ((0.,0.,-.2,.6),(-1.,1.,.3,.3),(-1.,1.,-.2),
                       (-1.,1.,-.2,float("nan")),None):
            with self.subTest(bounds=limits),self.assertRaises(ValueError):
                cup_vertices(valid,-.08,limits)
        for points in ((),None,((0.,0.),),((0.,0.,0.,0.),),
                       ((float("nan"),0.,.4),),((2.,0.,.4),),
                       ((0.,0.,float("inf")),)):
            with self.subTest(points=points),self.assertRaises(ValueError):
                cup_vertices(points,-.08,bounds)

    @unittest.skipUnless(importlib.util.find_spec("numpy") and
                         importlib.util.find_spec("trimesh"),
                         "optional NumPy/Trimesh required")
    def test_actual_synthetic_five_parent_sixteen_material_scene_rolls_back(self):
        import numpy as np
        import trimesh
        from tools.art.experimental_direct_drive_phase import PARTS, CHILD_COUNTS

        scene = trimesh.Scene()
        eye = np.eye(4)
        scene.graph.update(frame_to="world_1",frame_from="world",matrix=eye)
        for part in PARTS:
            transform = eye.copy()
            if part == "saddle":
                transform[2,3] = 3.27
            scene.graph.update(frame_to=part,frame_from="world_1",matrix=transform)
            for i in range(CHILD_COUNTS[part]):
                name = f"{part}__material_{i}"
                # A cuboid has vertices only at its X tips, where this sculpt
                # is deliberately zero. Use real interior vertices for saddle
                # materials so the synthetic GLB exercises nonzero cupping.
                mesh=(trimesh.creation.icosphere(subdivisions=2,radius=.4)
                      if part=="saddle" else
                      trimesh.creation.box(extents=(2.,.4,.8)))
                mesh.visual.vertex_colors=[(48,90,200,255)]*len(mesh.vertices)
                scene.geometry[name] = mesh
                scene.graph.update(frame_to=name,frame_from=part,
                                   matrix=eye,geometry=name)
        prior={name:np.asarray(mesh.vertices).copy()
               for name,mesh in scene.geometry.items()}
        nodes=set(scene.graph.nodes)
        parents={p:np.asarray(scene.graph.get(p)[0]).copy() for p in PARTS}
        for offset in CUP_OFFSETS:
            with self.assertRaisesRegex(RuntimeError,"probe"):
                with temporary_saddle_cup(scene,offset):
                    self.assertFalse(np.array_equal(
                        scene.geometry["saddle__material_0"].vertices,
                        prior["saddle__material_0"]))
                    self.assertTrue(np.array_equal(
                        scene.geometry["tire__material_0"].vertices,
                        prior["tire__material_0"]))
                    raise RuntimeError("probe")
            self.assertEqual(set(scene.graph.nodes),nodes)
            for p in PARTS:
                np.testing.assert_array_equal(scene.graph.get(p)[0],parents[p])
            for name,vertices in prior.items():
                np.testing.assert_array_equal(scene.geometry[name].vertices,vertices)


if __name__=="__main__":
    unittest.main()
