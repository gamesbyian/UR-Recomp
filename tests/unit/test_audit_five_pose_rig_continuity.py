"""ROM-free controls for source-owned five-GLB part continuity analysis."""
from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from tools.art.audit_five_pose_rig_continuity import (
    POSES, PARTS, SCHEMA, geometry_fingerprint, glb_structure,
    summarize_components, np, trimesh,
)


def study():
    result = {}
    for i, pose in enumerate(POSES):
        result[pose] = {
            part+"__material_0": {
                "local_mesh_sha256": ((part[0] if part != "pedals" else str(i)) * 64),
                "triangle_count": (120 + i * 2) if part == "pedals" else 120,
            }
            for part in PARTS
        }
    return result


class PartContinuityContractTests(unittest.TestCase):
    def test_shared_parts_and_dynamic_pedals_are_not_conflated(self):
        result = summarize_components(study())
        self.assertEqual(result["component_count"], 5)
        self.assertEqual(result["exact_local_mesh_reused_component_count"], 4)
        self.assertEqual(result["pose_dependent_local_mesh_component_count"], 1)
        self.assertEqual(result["pose_dependent_triangle_topology_component_count"], 1)
        self.assertTrue(result["components"]["tire__material_0"]["local_mesh_identical_across_poses"])
        self.assertFalse(result["components"]["pedals__material_0"]["local_mesh_identical_across_poses"])

    def test_missing_pose_and_swapped_component_fails_closed(self):
        incomplete = study()
        incomplete.pop("stunt")
        with self.assertRaisesRegex(ValueError,"five named"):
            summarize_components(incomplete)
        incomplete = study()
        incomplete["stunt"].pop("saddle__material_0")
        with self.assertRaisesRegex(ValueError,"component set"):
            summarize_components(incomplete)

    def test_invalid_triangle_count_or_sha_fails_closed(self):
        bad = study()
        bad["upright"]["tire__material_0"]["triangle_count"] = 0
        with self.assertRaisesRegex(ValueError,"local mesh metric"):
            summarize_components(bad)
        bad = study()
        bad["wheelie"]["pedals__material_0"]["local_mesh_sha256"] = "bad"
        with self.assertRaisesRegex(ValueError,"local mesh metric"):
            summarize_components(bad)

    def test_missing_canonical_parent_material_group_is_rejected(self):
        bad = study()
        for pose in POSES:
            bad[pose] = {k:v for k,v in bad[pose].items() if not k.startswith("saddle__")}
        with self.assertRaisesRegex(ValueError,"five part parent"):
            summarize_components(bad)

    def test_glb_json_reads_real_animation_and_skin_counts(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/"synthetic.glb"
            doc = {"asset":{"version":"2.0"},"animations":[{}],"skins":[{}],
                   "meshes":[{},{}],"nodes":[{},{},{}]}
            json_bytes = json.dumps(doc).encode()
            json_bytes += b" " * ((-len(json_bytes)) % 4)
            # GLB header + JSON chunk; binary blob is deliberately absent.
            raw = b"glTF"+struct.pack("<II",2,20+len(json_bytes))+struct.pack(
                "<I4s",len(json_bytes),b"JSON")+json_bytes
            path.write_bytes(raw)
            self.assertEqual(glb_structure(path),{
                "animations":1,"skins":1,"meshes":2,"nodes":3})
            path.write_bytes(raw[:-1])
            with self.assertRaisesRegex(ValueError,"version, chunk"):
                glb_structure(path)

    @unittest.skipUnless(np is not None and trimesh is not None,
                         "optional 3D inspection packages unavailable")
    def test_actual_synthetic_mesh_local_fingerprinting(self):
        mesh=trimesh.creation.box(extents=[1,1,1])
        h1=geometry_fingerprint(mesh)
        moved=mesh.copy()
        moved.apply_translation([1,0,0])
        self.assertNotEqual(h1,geometry_fingerprint(moved))
        self.assertEqual(h1,geometry_fingerprint(mesh.copy()))


if __name__ == "__main__":
    unittest.main()
