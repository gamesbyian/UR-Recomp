"""Short synthetic integrity controls for ART-4K staged GLB publication."""
from __future__ import annotations

import copy
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
class GlbRoundtripGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "model.glb"
        self.scene = trimesh.Scene()
        self.report = {"source_pose_transform": np.eye(4).tolist(), "components": []}
        for i, name in enumerate(("tire", "rim_and_hub", "fork_and_frame", "pedals", "saddle")):
            transform = np.eye(4)
            transform[2, 3] = float(i + 1)
            self.scene.graph.update(frame_to=name, frame_from=self.scene.graph.base_frame,
                                    matrix=transform)
            mesh = trimesh.creation.box()
            rgba = [20 + i, 40 + i, 60 + i, 255]
            mesh.visual.vertex_colors = np.array(rgba, dtype=np.uint8)
            child = name + "__material_0"
            self.scene.add_geometry(mesh, node_name=child, geom_name=child,
                                    parent_node_name=name)
            self.report["components"].append({"name": name, "pivot_translation": [0, 0, i + 1],
                "material_count": 1, "triangles": len(mesh.faces),
                "materials": [{"node": child, "triangles": len(mesh.faces), "rgba": rgba}]})
        self.write_scene()

    def write_scene(self):
        self.path.write_bytes(self.scene.export(file_type="glb"))

    def test_complete_scene_passes(self):
        self.assertEqual(module.validate_glb_roundtrip(self.path, self.report),
                         {"validated_parts": 5, "validated_material_meshes": 5,
                          "validated_triangles": 60})

    def test_missing_material_node_rejected(self):
        self.scene.delete_geometry("tire__material_0")
        self.write_scene()
        with self.assertRaisesRegex(ValueError, "node set|geometry nodes|mesh names"):
            module.validate_glb_roundtrip(self.path, self.report)

    def test_detached_material_rejected(self):
        self.scene.graph.update(frame_to="tire__material_0",
                                frame_from=self.scene.graph.base_frame,
                                matrix=np.eye(4), geometry="tire__material_0")
        self.write_scene()
        with self.assertRaisesRegex(ValueError, "detached"):
            module.validate_glb_roundtrip(self.path, self.report)

    def test_wrong_parent_transform_rejected(self):
        self.scene.graph.update(frame_to="tire", frame_from=self.scene.graph.base_frame,
                                matrix=np.eye(4))
        self.write_scene()
        with self.assertRaisesRegex(ValueError, "transform changed"):
            module.validate_glb_roundtrip(self.path, self.report)

    def test_wrong_color_rejected(self):
        self.scene.geometry["tire__material_0"].visual.vertex_colors = [255, 0, 0, 255]
        self.write_scene()
        with self.assertRaisesRegex(ValueError, "color changed"):
            module.validate_glb_roundtrip(self.path, self.report)

    def test_wrong_triangle_receipt_rejected(self):
        receipt = copy.deepcopy(self.report)
        receipt["components"][0]["materials"][0]["triangles"] += 1
        with self.assertRaisesRegex(ValueError, "triangle count changed"):
            module.validate_glb_roundtrip(self.path, receipt)

    def test_duplicate_receipt_node_rejected(self):
        receipt = copy.deepcopy(self.report)
        receipt["components"][1]["materials"][0]["node"] = "tire__material_0"
        with self.assertRaisesRegex(ValueError, "duplicate material nodes"):
            module.validate_glb_roundtrip(self.path, receipt)


if __name__ == "__main__":
    unittest.main()
