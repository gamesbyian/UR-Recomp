"""Dependency-free GLB NORMAL backing-byte checks for the ART-4K source guard."""
from __future__ import annotations

import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parents[2] / "tools/art/glb_roundtrip_guard.py"
spec = importlib.util.spec_from_file_location("glb_roundtrip_guard", GUARD)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SerializedNormalBufferTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "candidate.glb"
        self.gltf = {
            "asset": {"version": "2.0"},
            "buffers": [{"byteLength": 72}],
            "bufferViews": [
                {"buffer": 0, "byteOffset": 0, "byteLength": 36},
                {"buffer": 0, "byteOffset": 36, "byteLength": 36},
            ],
            "accessors": [
                {"bufferView": 0, "componentType": 5126, "type": "VEC3", "count": 3},
                {"bufferView": 1, "componentType": 5126, "type": "VEC3", "count": 3},
            ],
            "meshes": [{"name": "tire__material_0", "primitives": [
                {"attributes": {"POSITION": 0, "NORMAL": 1}}
            ]}],
        }

    def write(self):
        payload = json.dumps(self.gltf, separators=(",", ":")).encode("utf-8")
        payload += b" " * ((-len(payload)) % 4)
        binary = bytearray(b"\0" * self.gltf["buffers"][0]["byteLength"])
        if len(binary) >= 88:
            struct.pack_into("<H", binary, 72, 0)
            struct.pack_into("<3f", binary, 76, -1.0, 0.0, 0.0)
        total = 20 + len(payload) + 8 + len(binary)
        self.path.write_bytes(
            struct.pack("<4sIIII", b"glTF", 2, total, len(payload), 0x4E4F534A)
            + payload + struct.pack("<II", len(binary), 0x004E4942) + binary
        )

    def assert_rejected(self):
        self.write()
        with self.assertRaisesRegex(ValueError, "NORMAL accessor"):
            module.require_explicit_glb_normals(self.path, {"tire__material_0"})

    def test_valid_explicit_normal_storage(self):
        self.write()
        module.require_explicit_glb_normals(self.path, {"tire__material_0"})

    def test_missing_buffer_view_rejected(self):
        self.gltf["accessors"][1].pop("bufferView")
        self.assert_rejected()

    def test_out_of_range_buffer_view_rejected(self):
        self.gltf["accessors"][1]["bufferView"] = 99
        self.assert_rejected()

    def test_short_view_rejected(self):
        self.gltf["bufferViews"][1]["byteLength"] = 24
        self.assert_rejected()

    def test_out_of_bin_view_rejected(self):
        self.gltf["bufferViews"][1]["byteOffset"] = 60
        self.assert_rejected()

    def test_invalid_stride_rejected(self):
        self.gltf["bufferViews"][1]["byteStride"] = 8
        self.assert_rejected()

    def test_invalid_bin_chunk_rejected(self):
        self.write()
        raw = bytearray(self.path.read_bytes())
        json_size = struct.unpack_from("<I", raw, 12)[0]
        struct.pack_into("<I", raw, 20 + json_size + 4, 0)
        self.path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "BIN chunk"):
            module.require_explicit_glb_normals(self.path, {"tire__material_0"})

    def add_valid_sparse_override(self, accessor_index):
        # A real in-bounds sparse index/value pair. Its glTF semantics
        # override the dense accessor even if a loader ignores the override.
        self.gltf["buffers"][0]["byteLength"] = 88
        self.gltf["bufferViews"].extend([
            {"buffer": 0, "byteOffset": 72, "byteLength": 2},
            {"buffer": 0, "byteOffset": 76, "byteLength": 12},
        ])
        self.gltf["accessors"][accessor_index]["sparse"] = {
            "count": 1,
            "indices": {"bufferView": 2, "componentType": 5123},
            "values": {"bufferView": 3},
        }

    def test_sparse_normal_override_rejected(self):
        self.add_valid_sparse_override(1)
        self.assert_rejected()

    def test_sparse_position_override_rejected(self):
        self.add_valid_sparse_override(0)
        self.assert_rejected()

    def test_unreferenced_sparse_accessor_rejected(self):
        self.gltf["accessors"].append({"sparse": {"count": 1}})
        self.assert_rejected()

    def test_weighted_morph_position_rejected(self):
        # A glTF morph target adds its POSITION deltas to the base accessor.
        # The renderer changes geometry, but Trimesh 4.11.1 ignores targets.
        self.gltf["meshes"][0]["primitives"][0]["targets"] = [{"POSITION": 0}]
        self.gltf["meshes"][0]["weights"] = [1.0]
        self.assert_rejected()

    def test_unweighted_morph_target_rejected(self):
        self.gltf["meshes"][0]["primitives"][0]["targets"] = [{"POSITION": 0}]
        self.assert_rejected()

    def test_node_morph_weights_rejected(self):
        self.gltf["nodes"] = [{"mesh": 0, "weights": [1.0]}]
        self.assert_rejected()

    def test_skin_reference_rejected(self):
        self.gltf["nodes"] = [{"mesh": 0, "skin": 0}]
        self.assert_rejected()

    def test_animation_and_skin_containers_rejected(self):
        for field in ("animations", "skins"):
            with self.subTest(field=field):
                self.gltf[field] = []
                self.assert_rejected()
                del self.gltf[field]


if __name__ == "__main__":
    unittest.main()
