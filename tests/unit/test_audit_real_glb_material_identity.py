"""ROM-free material fingerprint controls for five authentic exported GLBs."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.art.audit_real_glb_material_identity import (
    EXPECTED_PART_MATERIALS, MESH_NAMES, POSES, read_glb_materials,
    reduce_five_materials, validate_rgb_materials,
)


def fake_one():
    return {
        name: ([28, 89, 222, 255] if name == "fork_and_frame__material_0"
               else [60, 60, 60, 255])
        for name in MESH_NAMES
    }


def fake_five():
    return {pose: copy.deepcopy(fake_one()) for pose in POSES}


class ExperimentalMaterialIdentityTests(unittest.TestCase):
    def receipt(self, source=None):
        return reduce_five_materials(
            fake_five() if source is None else source,
            manifest_sha="a"*64, sprite_rail_sha="b"*64,
        )

    def test_complete_identical_five_pose_colourway_reports_no_art_approval(self):
        report = self.receipt()
        self.assertEqual(report["distinct_material_mesh_identities"], 16)
        self.assertTrue(report["five_experimental_pose_material_sets_identical"])
        self.assertEqual(report["fork_primary_material_rgb_hex"], "#1c59de")
        self.assertTrue(report["single_experimental_colourway_not_player_specific"])
        self.assertFalse(report["source_P1_P2_separate_colourways_validated_in_this_GLB"])
        self.assertFalse(report["original_1994_material_albedo_recovered"])
        self.assertFalse(report["owner_likeness_approved"])

    def test_missing_one_part_or_material_or_pose_rejected(self):
        trials = [
            lambda data: data.pop("wheelie"),
            lambda data: data["stunt"].pop("saddle__material_1"),
            lambda data: data["pedal"].update({"unknown__material_99": [1,1,1,255]}),
        ]
        for trial in trials:
            with self.subTest(trial=trial):
                data = fake_five()
                trial(data)
                with self.assertRaisesRegex(ValueError, "five|16"):
                    self.receipt(data)

    def test_pose_specific_accidental_colour_drift_rejected(self):
        data = fake_five()
        data["bank"]["fork_and_frame__material_0"] = [198, 33, 16, 255]
        with self.assertRaisesRegex(ValueError, "drift"):
            self.receipt(data)

    def test_invalid_rgba_alpha_or_noninteger_rejected(self):
        for invalid in ([256,0,0,255], [-1,2,3,255], [1,2,3,254],
                        [1.5,2,3,255], [1,2,3], "red"):
            with self.subTest(value=invalid):
                data = fake_one()
                data["fork_and_frame__material_0"] = invalid
                with self.assertRaisesRegex(ValueError, "RGBA"):
                    validate_rgb_materials(data)

    def test_missing_site_sha_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA"):
            reduce_five_materials(fake_five(), manifest_sha="invalid",
                                  sprite_rail_sha="a"*64)

    def test_exact_material_fingerprint_deterministic_independent_of_mapping_order(self):
        a = self.receipt()
        reverse = {pose: dict(reversed(list(fake_one().items()))) for pose in reversed(POSES)}
        b = self.receipt(reverse)
        self.assertEqual(a["common_pose_material_fingerprint_sha256"],
                         b["common_pose_material_fingerprint_sha256"])
        self.assertEqual(a["authored_material_rgba_by_mesh"],
                         b["authored_material_rgba_by_mesh"])


try:
    import trimesh
except ImportError:
    trimesh = None


@unittest.skipIf(trimesh is None, "real GLB examination requires optional Trimesh")
class OptionalActualGlbLoaderTests(unittest.TestCase):
    def synthetic_scene(self, root: Path):
        scene = trimesh.Scene()
        for i, name in enumerate(sorted(MESH_NAMES)):
            mesh = trimesh.creation.box(extents=[.1,.1,.1])
            colour = [28,89,222,255] if name == "fork_and_frame__material_0" else [60,60,60,255]
            mesh.visual.vertex_colors = [colour] * len(mesh.vertices)
            scene.add_geometry(mesh, geom_name=name, node_name=name)
        file = root/"sixteen-source-variant.glb"
        file.write_bytes(scene.export(file_type="glb"))
        return file

    def test_actual_glb_16_named_vertex_colour_meshes_recover_identical_values(self):
        with tempfile.TemporaryDirectory() as base:
            file=self.synthetic_scene(Path(base))
            found=read_glb_materials(file, hashlib.sha256(file.read_bytes()).hexdigest())
        self.assertEqual(found, validate_rgb_materials(fake_one()))

    def test_changed_material_binary_rejected_even_when_name_looks_valid(self):
        with tempfile.TemporaryDirectory() as base:
            file=self.synthetic_scene(Path(base))
            with self.assertRaisesRegex(ValueError, "GLB SHA"):
                read_glb_materials(file, "0"*64)


if __name__ == "__main__":
    unittest.main()
