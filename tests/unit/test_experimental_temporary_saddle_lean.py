"""Actual 2026 GLB saddle mount pitch, no new mesh or guessed source joints."""
import math
import unittest
from tools.art.experimental_temporary_saddle_lean import (
    saddle_local_y_matrix,temporary_saddle_pitch,
)

try:
    import numpy as np
    import trimesh
except ImportError:
    np=trimesh=None


@unittest.skipUnless(np is not None and trimesh is not None,"optional GLB deps")
class TemporarySaddleLeanTests(unittest.TestCase):
    def make_scene(self):
        scene=trimesh.Scene()
        sizes={"tire":2,"rim_and_hub":5,"fork_and_frame":4,"pedals":3,"saddle":2}
        for part,n in sizes.items():
            pose=np.eye(4);pose[:3,3]=[0.,0.,2.3 if part=="saddle" else 1.]
            scene.graph.update(frame_to=part,frame_from=scene.graph.base_frame,
                               matrix=pose)
            for i in range(n):
                name=f"{part}__material_{i}"
                scene.add_geometry(trimesh.creation.box(extents=(.1,.1,.1)),
                                   geom_name=name,node_name=name,
                                   parent_node_name=part)
        return scene

    def test_mount_pivot_rotates_only_saddle_then_restores(self):
        scene=self.make_scene()
        before={part:scene.graph.get(part)[0].copy()
                for part in ("tire","rim_and_hub","fork_and_frame","pedals","saddle")}
        mesh={name:np.asarray(obj.vertices).copy()
              for name,obj in scene.geometry.items()}
        with temporary_saddle_pitch(scene,15.):
            a=scene.graph.get("saddle")[0]
            self.assertAlmostEqual(a[0,0],math.cos(math.radians(15)),places=9)
            np.testing.assert_allclose(a[:3,3],before["saddle"][:3,3],atol=1e-9,rtol=0)
            for part in before:
                if part!="saddle":
                    np.testing.assert_array_equal(scene.graph.get(part)[0],before[part])
            with self.assertRaises(ValueError):
                with temporary_saddle_pitch(scene,40):pass
        for part,old in before.items():
            np.testing.assert_allclose(scene.graph.get(part)[0],old,atol=1e-9,rtol=0)
        for name,obj in scene.geometry.items():
            np.testing.assert_array_equal(obj.vertices,mesh[name])
        with temporary_saddle_pitch(scene,-15.):
            self.assertAlmostEqual(scene.graph.get("saddle")[0][0,2],
                                   -math.sin(math.radians(15)),places=9)
        for part,old in before.items():
            np.testing.assert_allclose(scene.graph.get(part)[0],old,atol=1e-9,rtol=0)

    def test_invalid_angle_or_missing_source_hierarchy(self):
        for bad in (-31,31,True,None,float("nan"),float("inf")):
            with self.subTest(value=bad),self.assertRaises(ValueError):
                saddle_local_y_matrix(bad)
        scene=trimesh.Scene()
        with self.assertRaises(ValueError):
            with temporary_saddle_pitch(scene,15):pass


if __name__=="__main__":unittest.main()
