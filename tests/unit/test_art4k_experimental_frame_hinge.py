"""ROM-free controls for the optional original-five-parent GLB axle hinge."""
import io
import math
import tempfile
import unittest
from pathlib import Path
from tools.art.experimental_frame_hinge import rotation_y, pitch_scene, process


class PureHingeControls(unittest.TestCase):
    def test_degree_matrix(self):
        self.assertEqual(rotation_y(0), ((1.,0.,0.,0.),(0.,1.,0.,0.),
                                          (0.,0.,1.,0.),(0.,0.,0.,1.)))
        positive = rotation_y(3)
        self.assertAlmostEqual(positive[0][2], math.sin(math.radians(3)))
        self.assertAlmostEqual(positive[2][0], -positive[0][2])

    def test_invalid_angles_fail_closed(self):
        for val in (-46, 46, float("nan"), float("inf"), True, "3", None):
            with self.subTest(val=val), self.assertRaises(ValueError):
                rotation_y(val)


try:
    import numpy as np
    import trimesh
except ImportError:
    np = trimesh = None


@unittest.skipUnless(np is not None and trimesh is not None, "optional offline numpy/trimesh")
class SceneHingeControls(unittest.TestCase):
    def fixture(self):
        scene = trimesh.Scene()
        parents = {"tire": (0,0,1),"rim_and_hub": (0,0,1),
                   "pedals": (0,0,1),"fork_and_frame": (0,0,1),
                   "saddle": (.04,0,3.27)}
        counts = {"tire":2,"rim_and_hub":5,"pedals":3,"fork_and_frame":4,"saddle":2}
        for name, xyz in parents.items():
            matrix = np.eye(4)
            matrix[:3,3] = xyz
            scene.graph.update(frame_to=name, frame_from="world", matrix=matrix)
            for i in range(counts[name]):
                scene.add_geometry(trimesh.creation.box(extents=(.1,.1,.1)),
                    node_name=f"{name}__material_{i}",
                    geom_name=f"{name}__material_{i}", parent_node_name=name)
        return scene

    def test_active_frame_only_preserves_wheel_and_all_material_geometry(self):
        scene = self.fixture()
        before = {p: scene.graph.get(p)[0].copy() for p in
                  ("tire","rim_and_hub","pedals","fork_and_frame","saddle")}
        geometry = {k:(v.vertices.copy(),v.faces.copy()) for k,v in scene.geometry.items()}
        record = pitch_scene(scene, 3)
        self.assertEqual(record["source_wheel_axle_pivot_world_xyz"],[0.,0.,1.])
        for name in ("tire","rim_and_hub","pedals"):
            np.testing.assert_array_equal(scene.graph.get(name)[0],before[name])
        np.testing.assert_allclose(scene.graph.get("fork_and_frame")[0][:3,3],
                                   [0,0,1],atol=1e-10)
        self.assertGreater(scene.graph.get("saddle")[0][0,3],
                           before["saddle"][0,3]+.10)
        for k,mesh in scene.geometry.items():
            np.testing.assert_array_equal(mesh.vertices,geometry[k][0])
            np.testing.assert_array_equal(mesh.faces,geometry[k][1])
        rerender=trimesh.load(file_obj=io.BytesIO(scene.export(file_type="glb")),
                              file_type="glb",force="scene",process=False)
        self.assertEqual(len(rerender.graph.nodes_geometry),16)
        self.assertEqual(len(rerender.graph.nodes),22)

    def test_large_source_family_pose_keeps_axle_and_children(self):
        scene = self.fixture()
        before = scene.graph.get("saddle")[0].copy()
        record = pitch_scene(scene, -40)
        saddle = scene.graph.get("saddle")[0]
        fork = scene.graph.get("fork_and_frame")[0]
        self.assertEqual(record["moving_parent_parts"], ["fork_and_frame", "saddle"])
        np.testing.assert_allclose(fork[:3,3], [0,0,1], atol=1e-9)
        self.assertLess(saddle[0,3], before[0,3]-1.0)
        self.assertEqual(len(scene.graph.nodes_geometry), 16)

    def test_zero_hinge_noop(self):
        scene=self.fixture()
        before={p:scene.graph.get(p)[0].copy() for p in
                ("tire","rim_and_hub","pedals","fork_and_frame","saddle")}
        pitch_scene(scene,0)
        for p,T in before.items():
            np.testing.assert_allclose(scene.graph.get(p)[0],T,atol=1e-12,rtol=0)

    def test_missing_material_or_bad_source_pivots_refused(self):
        scene=self.fixture()
        matrix=scene.graph.get("pedals")[0].copy()
        matrix[0,3]=.1
        scene.graph.update(frame_to="pedals",frame_from="world",matrix=matrix)
        with self.assertRaisesRegex(ValueError,"pivots"):
            pitch_scene(scene,3)
        scene=self.fixture()
        scene.delete_geometry("tire__material_0")
        with self.assertRaisesRegex(ValueError,"sixteen"):
            pitch_scene(scene,3)

    def test_source_hash_mismatch_and_existing_outputs_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/"src.glb"
            output=root/"out.glb"
            receipt=root/"receipt.json"
            source.write_bytes(b"invalid GLB")
            with self.assertRaisesRegex(ValueError,"SHA-pinned"):
                process(source,3,output,receipt)
            self.assertFalse(output.exists())
            output.write_bytes(b"existing")
            with self.assertRaises(FileExistsError):
                process(source,3,output,receipt)
            self.assertEqual(output.read_bytes(),b"existing")


if __name__ == "__main__":
    unittest.main()
