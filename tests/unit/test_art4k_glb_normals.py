"""ART-4K GLB normals must match source-derived float32 mesh shading."""
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

GUARD = Path(__file__).resolve().parents[2] / "tools/art/glb_roundtrip_guard.py"
spec = importlib.util.spec_from_file_location("glb_roundtrip_guard", GUARD)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@unittest.skipUnless(np is not None and trimesh is not None, "optional numpy/trimesh")
class SourceNormalIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "candidate.glb"
        self.scene = trimesh.Scene()
        self.report = {"source_pose_transform": np.eye(4).tolist(), "components": []}
        for i, name in enumerate(("tire", "rim_and_hub", "fork_and_frame", "pedals", "saddle")):
            parent = np.eye(4)
            parent[2, 3] = i + 1
            self.scene.graph.update(frame_to=name, frame_from=self.scene.graph.base_frame,
                                    matrix=parent)
            mesh = (trimesh.creation.icosphere(subdivisions=2) if i == 1
                    else trimesh.creation.box())
            rgba = [20 + i, 40 + i, 60 + i, 255]
            mesh.visual.vertex_colors = np.asarray(rgba, dtype=np.uint8)
            child = name + "__material_0"
            module.bind_source_normals(mesh)
            self.scene.add_geometry(mesh, node_name=child, geom_name=child,
                                    parent_node_name=name)
            self.report["components"].append({
                "name": name, "pivot_translation": [0, 0, i + 1],
                "material_count": 1, "triangles": len(mesh.faces),
                "materials": [{"node": child, "triangles": len(mesh.faces),
                               "rgba": rgba,
                               "geometry_sha256": module.geometry_signature(mesh),
                               "normals_sha256": module.normal_signature(mesh, source=True)}],
            })
        self.write_scene()

    def write_scene(self):
        self.path.write_bytes(self.scene.export(file_type="glb"))

    def test_source_normals_survive_actual_glb_roundtrip(self):
        result = module.validate_glb_roundtrip(self.path, self.report)
        self.assertEqual(result["validated_parts"], 5)
        self.assertEqual(result["validated_material_meshes"], 5)

    def test_inverted_glb_normals_rejected_without_geometry_change(self):
        mesh = self.scene.geometry["tire__material_0"]
        original_geometry = module.geometry_signature(mesh)
        mesh.vertex_normals = -mesh.vertex_normals
        self.assertEqual(module.geometry_signature(mesh), original_geometry)
        self.write_scene()
        with self.assertRaisesRegex(ValueError, "normal digest changed"):
            module.validate_glb_roundtrip(self.path, self.report)

    def test_changed_unit_normals_rejected_without_geometry_change(self):
        mesh = self.scene.geometry["rim_and_hub__material_0"]
        normals = mesh.vertex_normals.copy()
        mesh.vertex_normals = normals[:, [1, 2, 0]]
        self.write_scene()
        with self.assertRaisesRegex(ValueError, "normal digest changed"):
            module.validate_glb_roundtrip(self.path, self.report)

    def test_missing_serialized_normal_accessor_rejected(self):
        # Trimesh can synthesize normals when glTF omits NORMAL; the receipt
        # must inspect actual GLB attributes, not this reconstructed fallback.
        mesh = self.scene.geometry["tire__material_0"]
        mesh._cache.clear()
        self.write_scene()
        with self.assertRaisesRegex(ValueError, "NORMAL accessor"):
            module.validate_glb_roundtrip(self.path, self.report)

    def test_missing_normal_signature_fails_closed(self):
        del self.report["components"][0]["materials"][0]["normals_sha256"]
        with self.assertRaisesRegex(ValueError, "normal digest changed"):
            module.validate_glb_roundtrip(self.path, self.report)

    def test_normal_signature_preserves_face_order_invariance(self):
        mesh = self.scene.geometry["tire__material_0"].copy()
        expected = module.normal_signature(mesh)
        normals = mesh.vertex_normals.copy()
        mesh.faces = mesh.faces[::-1]
        mesh.vertex_normals = normals
        self.assertEqual(module.normal_signature(mesh), expected)


if __name__ == "__main__":
    unittest.main()
