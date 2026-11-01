"""Synthetic five-part GLB projection with exact fixed-camera constraints."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.art import render_racer_glb_projection as render

HAS_OPTIONAL = all(
    value is not None for value in (render.np, render.trimesh, render.Image)
)


@unittest.skipUnless(HAS_OPTIONAL, "optional numpy/trimesh/Pillow projection tools")
class FixedCameraGlbProjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "candidate.glb"
        scene = render.trimesh.Scene()
        for i, name in enumerate(render.PARTS):
            mesh = render.trimesh.creation.box(extents=[0.3, 0.2, 0.4])
            transform = render.trimesh.transformations.translation_matrix(
                [i * 0.15, 0, i * 0.4]
            )
            scene.add_geometry(
                mesh, node_name=name, geom_name=name + "__material_0",
                transform=transform,
            )
        self.path.write_bytes(scene.export(file_type="glb"))
        self.sha = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.camera = {
            "schema": render.CAMERA_SCHEMA,
            "source_pixel_aspect": "7:6",
            "right_world": [1, 0, 0],
            "up_world": [0, 0, 1],
            "origin_world": [0, 0, 0],
            "logical_pixels_per_model_unit_vertical": 9.5,
            "source_anchor_x2_y2": [67, 76],
            "camera_calibration_status": "provisional",
        }

    def test_real_glb_roundtrip_and_repeatable_alpha(self):
        vertices, faces, sha, count = render.model_mesh(self.path, self.sha)
        self.assertEqual(sha, self.sha)
        self.assertGreater(count, 4)
        img = render.render_mask(vertices, faces, self.camera)
        self.assertEqual(img.shape, (256, 256))
        self.assertGreater(int(img.sum()), 100)
        p1, p2 = self.root / "a.png", self.root / "b.png"
        self.assertEqual(
            render.render_to_png(img, p1), render.render_to_png(img, p2)
        )
        self.assertEqual(p1.read_bytes(), p2.read_bytes())

    def test_camera_shift_changes_projection_without_auto_fit(self):
        v, f, _, _ = render.model_mesh(self.path, self.sha)
        original = render.render_mask(v, f, self.camera)
        shifted = dict(self.camera, source_anchor_x2_y2=[79, 76])
        moved = render.render_mask(v, f, shifted)
        self.assertFalse((original == moved).all())
        self.assertEqual(original.shape, moved.shape)

    def test_tampered_glb_hash_rejected(self):
        with self.assertRaisesRegex(ValueError, "SHA256"):
            render.model_mesh(self.path, "0" * 64)

    def test_wrong_camera_basis_and_aspect_rejected(self):
        for change in (
            {"right_world": [0, 0, 1]},
            {"up_world": [1, 0, 0]},
            {"source_pixel_aspect": "1:1"},
            {"logical_pixels_per_model_unit_vertical": 0},
            {"source_anchor_x2_y2": [67, 76.0]},
            {"camera_calibration_status": "source-calibrated"},
        ):
            camera = dict(self.camera, **change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                render.camera_config(camera)

    def test_receipt_matches_exact_file_bytes_and_rejects_replaced_camera(self):
        camera = self.root / "camera.json"
        camera.write_text(json.dumps(self.camera), encoding="utf-8")
        output = self.root / "projected.png"
        result = render.project(self.path, self.sha, camera, output)
        self.assertEqual(
            result["candidate_png_sha256"],
            hashlib.sha256(output.read_bytes()).hexdigest(),
        )
        self.assertEqual(result["source_model_glb_sha256"], self.sha)
        self.assertFalse(result["source_camera_auto_fit"])
        self.assertFalse(result["owner_likeness_approved"])
        self.assertFalse(result["shipping_art_approved"])
        camera.write_text("{}", encoding="utf-8")
        with self.assertRaises(ValueError):
            render.project(self.path, self.sha, camera, output)

    def test_missing_part_parent_rejected(self):
        scene = render.trimesh.Scene()
        scene.add_geometry(render.trimesh.creation.box(), node_name="tire")
        self.path.write_bytes(scene.export(file_type="glb"))
        sha = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "five required"):
            render.model_mesh(self.path, sha)


if __name__ == "__main__":
    unittest.main()
