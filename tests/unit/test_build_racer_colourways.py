"""ROM-free ART-4K P1/P2 GLB geometry-invariance and provenance tests."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "tools/art/build_racer_colourways.py"
spec = importlib.util.spec_from_file_location("art4k_colourways", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    """A valid, minimal 16-material, five-parent glTF binary, no NumPy needed."""
    groups = [("tire", 2), ("rim_and_hub", 5), ("fork_and_frame", 4),
              ("pedals", 3), ("saddle", 2)]
    doc = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": 0}],
           "bufferViews": [], "accessors": [], "meshes": [], "nodes": []}
    binary = bytearray()
    receipt = {"components": []}
    for part, count in groups:
        materials = []
        for i in range(count):
            name = f"{part}__material_{i}"
            rgba = module.P2_BLUE if name == module.SLOT else (12+i, 44+i, 79+i, 255)
            positions = struct.pack("<9f", float(i+1), 0, 0,
                                    float(i+2), 0, 0, float(i+1), 1, 0)
            pos_view = len(doc["bufferViews"])
            doc["bufferViews"].append(
                {"buffer": 0, "byteOffset": len(binary), "byteLength": len(positions)})
            binary.extend(positions)
            pos_access = len(doc["accessors"])
            doc["accessors"].append(
                {"componentType": 5126, "type": "VEC3",
                 "bufferView": pos_view, "count": 3})
            colours = bytes(rgba) * 3
            col_view = len(doc["bufferViews"])
            doc["bufferViews"].append(
                {"buffer": 0, "byteOffset": len(binary), "byteLength": len(colours)})
            binary.extend(colours)
            col_access = len(doc["accessors"])
            doc["accessors"].append(
                {"componentType": 5121, "type": "VEC4", "normalized": True,
                 "count": 3, "bufferView": col_view,
                 "min": list(rgba), "max": list(rgba)})
            doc["meshes"].append({
                "name": name,
                "primitives": [{"attributes": {"POSITION": pos_access, "COLOR_0": col_access},
                                "mode": 4}]})
            doc["nodes"].append({"name": name, "mesh": len(doc["meshes"])-1})
            materials.append({"node": name, "rgba": list(rgba)})
        receipt["components"].append({"name": part, "materials": materials})
    doc["buffers"][0]["byteLength"] = len(binary)
    return module.encode_glb(doc, binary), receipt


class ColourwayTests(unittest.TestCase):
    def setUp(self):
        self.raw, self.receipt = fixture()

    def test_changes_only_target_colour_and_accessor_bounds(self):
        outputs, fingerprint = module.variants(self.raw, self.receipt)
        self.assertEqual(outputs["p2"], self.raw)
        self.assertNotEqual(outputs["p1"], self.raw)
        original, orig_binary = module.read_glb(self.raw)
        changed, new_binary = module.read_glb(outputs["p1"])
        layout = module.colour_layout(original, orig_binary, self.receipt)
        self.assertEqual(module.neutral_fingerprint(original, orig_binary, layout),
                         fingerprint)
        self.assertEqual(module.neutral_fingerprint(changed, new_binary, layout),
                         fingerprint)
        index, offset, size, count, _ = layout
        self.assertEqual(new_binary[offset:offset+size],
                         bytes(module.P1_RED) * count)
        self.assertEqual(orig_binary[offset:offset+size],
                         bytes(module.P2_BLUE) * count)
        for key in ("min", "max"):
            self.assertEqual(changed["accessors"][index][key], list(module.P1_RED))

    def test_refuses_corrupt_source_and_unregistered_material(self):
        for bad in (b"", self.raw[:20], b"bad!" + self.raw[4:], self.raw[:-4]):
            with self.subTest(length=len(bad)), self.assertRaises(ValueError):
                module.variants(bad, self.receipt)
        forged = copy.deepcopy(self.receipt)
        forged["components"][2]["materials"][0]["rgba"] = list(module.P1_RED)
        with self.assertRaises(ValueError):
            module.variants(self.raw, forged)

    def test_refuses_fork_accessor_alias_and_position_storage(self):
        doc, binary = module.read_glb(self.raw)
        target = module.colour_layout(doc, binary, self.receipt)[0]
        doc["meshes"][0]["primitives"][0]["attributes"]["COLOR_0"] = target
        with self.assertRaises(ValueError):
            module.variants(module.encode_glb(doc, binary), self.receipt)
        doc, binary = module.read_glb(self.raw)
        doc["accessors"][target]["bufferView"] = doc["accessors"][0]["bufferView"]
        with self.assertRaises(ValueError):
            module.variants(module.encode_glb(doc, binary), self.receipt)

    def test_refuses_distinct_bufferview_alias_of_fork_colour(self):
        doc, binary = module.read_glb(self.raw)
        layout = module.colour_layout(doc, binary, self.receipt)
        # Repoint a POSITION accessor to an overlapping but separately
        # indexed bufferView. Distinct view IDs are not proof of isolation.
        original_index = doc["meshes"][0]["primitives"][0]["attributes"]["POSITION"]
        view = {"buffer": 0, "byteOffset": layout[1], "byteLength": layout[2]}
        doc["bufferViews"].append(view)
        doc["accessors"][original_index]["bufferView"] = len(doc["bufferViews"]) - 1
        with self.assertRaisesRegex(ValueError, "overlap"):
            module.variants(module.encode_glb(doc, binary), self.receipt)

    def test_refuses_altered_opaque_colour_bytes(self):
        doc, binary = module.read_glb(self.raw)
        layout = module.colour_layout(doc, binary, self.receipt)
        binary[layout[1]] ^= 1
        with self.assertRaisesRegex(ValueError, "differs"):
            module.variants(module.encode_glb(doc, binary), self.receipt)

    def test_five_pose_immutable_batch_and_explicit_false_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "sample.glb"
            sample.write_bytes(self.raw)
            receipt = root / "sample.json"
            receipt.write_text(json.dumps(self.receipt))
            previous = module.validate
            module.validate = lambda base, pose: (
                {"source_sha256": "a"*64,
                 "glb_sha256": module.digest(sample.read_bytes()),
                 "receipt_sha256": module.digest(receipt.read_bytes())},
                {"glb": sample, "receipt": receipt})
            try:
                result = module.build(root, root / "output", "b"*40)
                second = module.build(root, root / "output", "b"*40)
            finally:
                module.validate = previous
            self.assertNotEqual(result["directory"], second["directory"])
            body = json.loads(Path(result["receipt"]).read_text())
            self.assertEqual(set(body["poses"]), set(module.POSES))
            self.assertFalse(body["original_character_likeness_approved"])
            self.assertFalse(body["original_sprite_to_blockout_pose_mapped"])
            self.assertFalse(body["source_raster_colour_to_3d_material_proven"])
            for pose in module.POSES:
                for player in ("p1", "p2"):
                    record = body["poses"][pose]["outputs"][player]
                    output = Path(result["directory"]) / record["filename"]
                    self.assertEqual(module.digest(output.read_bytes()),
                                     record["sha256"])


    def test_rejects_source_changed_after_pointer_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "sample.glb"
            sample.write_bytes(self.raw)
            receipt = root / "sample.json"
            receipt.write_text(json.dumps(self.receipt))
            original_digest = module.digest(sample.read_bytes())
            sample.write_bytes(self.raw + b"spoof")
            previous = module.validate
            module.validate = lambda base, pose: (
                {"source_sha256": "a"*64, "glb_sha256": original_digest,
                 "receipt_sha256": module.digest(receipt.read_bytes())},
                {"glb": sample, "receipt": receipt})
            try:
                with self.assertRaisesRegex(ValueError, "changed since SHA preflight"):
                    module.build(root, root / "out", "b"*40)
            finally:
                module.validate = previous

    def test_mixed_source_shas_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = module.validate
            module.validate = lambda base, pose: (
                {"source_sha256": ("a" if pose == "upright" else "b")*64}, {})
            try:
                with self.assertRaisesRegex(ValueError, "mixed"):
                    module.build(Path(directory), Path(directory)/"out", "c"*40)
            finally:
                module.validate = previous


if __name__ == "__main__":
    unittest.main()
