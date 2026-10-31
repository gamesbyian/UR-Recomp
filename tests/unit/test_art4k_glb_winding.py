"""ART-4K GLB integrity: opposite triangle winding must not pass the receipt."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

try:
    import numpy as np
    import trimesh
except ImportError:
    np = None
    trimesh = None

GUARD = Path(__file__).resolve().parents[2] / "tools" / "art" / "glb_roundtrip_guard.py"
spec = importlib.util.spec_from_file_location("glb_roundtrip_guard", GUARD)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@unittest.skipUnless(np is not None and trimesh is not None, "optional numpy/trimesh")
class OrientedMaterialDigestTests(unittest.TestCase):
    def test_cyclic_vertex_rotation_and_face_order_remain_equivalent(self):
        mesh = trimesh.creation.box()
        cyclic = mesh.copy()
        cyclic.faces = cyclic.faces[:, [1, 2, 0]]
        reordered = mesh.copy()
        reordered.faces = reordered.faces[::-1]
        self.assertEqual(module.geometry_signature(mesh), module.geometry_signature(cyclic))
        self.assertEqual(module.geometry_signature(mesh), module.geometry_signature(reordered))

    def test_reversed_normals_change_signature_despite_watertightness(self):
        mesh = trimesh.creation.box()
        inverted = mesh.copy()
        inverted.faces = inverted.faces[:, [0, 2, 1]]
        self.assertTrue(mesh.is_watertight)
        self.assertTrue(inverted.is_watertight)
        self.assertEqual(len(mesh.faces), len(inverted.faces))
        self.assertNotEqual(module.geometry_signature(mesh), module.geometry_signature(inverted))
        self.assertLess(float(np.mean(np.sum(mesh.face_normals * inverted.face_normals, axis=1))), -0.99)

    def test_serialized_glb_with_reversed_winding_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidate.glb"
            scene = trimesh.Scene()
            report = {"source_pose_transform": np.eye(4).tolist(), "components": []}
            for i, name in enumerate(("tire", "rim_and_hub", "fork_and_frame", "pedals", "saddle")):
                transform = np.eye(4)
                transform[2, 3] = i + 1
                scene.graph.update(frame_to=name, frame_from=scene.graph.base_frame,
                                   matrix=transform)
                mesh = trimesh.creation.box()
                rgba = [40 + i, 80 + i, 120 + i, 255]
                mesh.visual.vertex_colors = np.array(rgba, dtype=np.uint8)
                child = f"{name}__material_0"
                scene.add_geometry(mesh, node_name=child, geom_name=child,
                                   parent_node_name=name)
                report["components"].append({
                    "name": name, "pivot_translation": [0, 0, i + 1],
                    "material_count": 1, "triangles": len(mesh.faces),
                    "materials": [{"node": child, "triangles": len(mesh.faces),
                                   "rgba": rgba,
                                   "geometry_sha256": module.geometry_signature(mesh),
                                   "normals_sha256": module.normal_signature(mesh, source=True)}],
                })
            path.write_bytes(scene.export(file_type="glb"))
            self.assertEqual(module.validate_glb_roundtrip(path, report),
                             {"validated_parts": 5, "validated_material_meshes": 5,
                              "validated_triangles": 60})
            corrupted = scene.geometry["tire__material_0"]
            corrupted.faces = corrupted.faces[:, [0, 2, 1]]
            path.write_bytes(scene.export(file_type="glb"))
            with self.assertRaisesRegex(ValueError, "geometry digest changed"):
                module.validate_glb_roundtrip(path, report)


if __name__ == "__main__":
    unittest.main()
