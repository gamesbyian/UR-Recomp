"""Test fail-closed ART-4K pointer intake and atomic evidence publication."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.art import run_racer_inverse_packet as packet
from tools.art import render_racer_glb_projection as render

HAS_RENDER = all(x is not None for x in (render.np, render.trimesh, render.Image))
ATTEMPT = "a" * 32


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CurrentExportEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        self.source = self.root / "source.scad"
        self.source.write_text("synthetic original-model source fixture")
        self.export = self.root / "export"
        dest = self.export / "attempts" / ATTEMPT
        dest.mkdir(parents=True)
        self.glb = dest / "unicycle_articulated_blockout.glb"
        self.glb.write_bytes(b"glTF synthetic test fixture")
        self.receipt = dest / "articulated_blockout_receipt.json"
        self.record = {
            "schema": "ur-art4k-articulated-blockout/1",
            "attempt_id": ATTEMPT,
            "source_sha256": digest(self.source),
            "glb_sha256": digest(self.glb),
            "rig_pose": "upright",
            "pose_source_registered_to_original_game": False,
            "original_character_likeness_approved": False,
            "shipping_art_approved": False,
        }
        self.pointer = {
            "schema": "ur-art4k-export-current/1", "attempt_id": ATTEMPT,
            "source_sha256": digest(self.source), "rig_pose": "upright",
            "glb_path": f"attempts/{ATTEMPT}/unicycle_articulated_blockout.glb",
            "receipt_path": f"attempts/{ATTEMPT}/articulated_blockout_receipt.json",
            "glb_sha256": digest(self.glb),
        }
        self.last = {
            "schema": "ur-art4k-export-attempt/1", "attempt_id": ATTEMPT,
            "source_sha256": digest(self.source), "glb_sha256": digest(self.glb),
            "status": "succeeded", "current_output_usable": True,
        }
        self.write_records()

    def write_records(self):
        self.receipt.write_text(json.dumps(self.record))
        self.pointer["receipt_sha256"] = digest(self.receipt)
        (self.export / "articulated_blockout_current.json").write_text(json.dumps(self.pointer))
        (self.export / "articulated_blockout_last_attempt.json").write_text(json.dumps(self.last))

    def test_exact_successful_export_is_accepted(self):
        result = packet.validate_current_export(self.export, self.source)
        self.assertEqual(result["attempt_id"], ATTEMPT)
        self.assertEqual(result["source_glb_sha256"], digest(self.glb))
        self.assertEqual(result["source_art4k_receipt_sha256"], digest(self.receipt))

    def test_failed_or_interrupted_latest_run_cannot_reuse_old_success(self):
        for status in ("failed", "running"):
            with self.subTest(status=status):
                self.last["status"] = status
                self.write_records()
                with self.assertRaisesRegex(ValueError, "last ART-4K export"):
                    packet.validate_current_export(self.export, self.source)

    def test_last_attempt_different_from_current_pointer_rejected(self):
        self.last["attempt_id"] = "b" * 32
        self.write_records()
        with self.assertRaisesRegex(ValueError, "last ART-4K export"):
            packet.validate_current_export(self.export, self.source)

    def test_source_and_glb_tampering_rejected(self):
        self.source.write_text(self.source.read_text() + " tamper")
        with self.assertRaisesRegex(ValueError, "source hash"):
            packet.validate_current_export(self.export, self.source)
        self.source.write_text("synthetic original-model source fixture")
        self.glb.write_bytes(self.glb.read_bytes() + b"x")
        with self.assertRaisesRegex(ValueError, "do not agree"):
            packet.validate_current_export(self.export, self.source)

    def test_approval_spoof_and_receipt_tamper_rejected(self):
        self.record["shipping_art_approved"] = True
        self.write_records()
        with self.assertRaisesRegex(ValueError, "unapproved blockout"):
            packet.validate_current_export(self.export, self.source)
        self.record["shipping_art_approved"] = False
        self.write_records()
        self.receipt.write_text(self.receipt.read_text() + " ")
        with self.assertRaisesRegex(ValueError, "do not agree"):
            packet.validate_current_export(self.export, self.source)

    def test_path_escape_and_swapped_artifact_rejected(self):
        self.pointer["glb_path"] = "../outside.glb"
        self.write_records()
        with self.assertRaisesRegex(ValueError, "paths"):
            packet.validate_current_export(self.export, self.source)


@unittest.skipUnless(HAS_RENDER, "optional numpy/trimesh/Pillow projection tools")
class FullSyntheticPacketTests(CurrentExportEvidenceTests):
    def setUp(self):
        super().setUp()
        scene = render.trimesh.Scene()
        for i, name in enumerate(render.PARTS):
            scene.add_geometry(
                render.trimesh.creation.box(extents=[0.3, 0.2, 0.4]),
                node_name=name, geom_name=name + "__mat",
                transform=render.trimesh.transformations.translation_matrix(
                    [i * 0.1, 0, i * 0.3]
                ),
            )
        self.glb.write_bytes(scene.export(file_type="glb"))
        self.record["glb_sha256"] = self.pointer["glb_sha256"] = self.last["glb_sha256"] = digest(self.glb)
        self.write_records()
        self.camera = self.root / "camera.json"
        self.camera.write_text(json.dumps({
            "schema": render.CAMERA_SCHEMA,
            "source_pixel_aspect": "7:6",
            "right_world": [1, 0, 0], "up_world": [0, 0, 1],
            "origin_world": [0, 0, 0],
            "source_anchor_x2_y2": [67, 76],
            "logical_pixels_per_model_unit_vertical": 9.5,
            "camera_calibration_status": "provisional",
            "source_witness": {
                "player": "p1", "guest_frame": 1205,
                "source_representation_id": "ordinary-racer-0x057E-p1-with-p2-0543-reference"
            },
        }))
        self.out = self.root / "results"

    def test_single_execution_produces_matched_receipt_and_score(self):
        result = packet.run_packet(self.export, self.source, self.camera, "p1", 1205, self.out)
        self.assertEqual(result["silhouette_score"]["player"], "p1")
        self.assertFalse(result["shipping_art_approved"])
        pointer, _ = packet._read(self.out / "racer_inverse_current.json")
        saved, sha = packet._read(self.out / pointer["packet_path"])
        self.assertEqual(saved, result)
        self.assertEqual(sha, pointer["packet_sha256"])
        self.assertEqual(
            digest(self.out / pointer["candidate_path"]),
            pointer["candidate_png_sha256"],
        )

    def test_later_failed_export_does_not_promote_previous_render(self):
        packet.run_packet(self.export, self.source, self.camera, "p1", 1205, self.out)
        before = (self.out / "racer_inverse_current.json").read_bytes()
        self.last["status"] = "failed"
        self.write_records()
        with self.assertRaisesRegex(ValueError, "last ART-4K export"):
            packet.run_packet(self.export, self.source, self.camera, "p1", 1205, self.out)
        self.assertEqual((self.out / "racer_inverse_current.json").read_bytes(), before)
        last, _ = packet._read(self.out / "racer_inverse_last_attempt.json")
        self.assertEqual(last["status"], "failed")

    def test_mismatched_original_camera_identity_and_anchor_rejected(self):
        camera = json.loads(self.camera.read_text())
        camera["source_anchor_x2_y2"] = [69, 76]
        self.camera.write_text(json.dumps(camera))
        with self.assertRaisesRegex(ValueError, "anchor conflicts"):
            packet.validate_source_camera(self.camera, "p1", 1205)


if __name__ == "__main__":
    unittest.main()
