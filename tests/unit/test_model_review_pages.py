"""ROM-free publication tests for source-bound 3D pose review assets."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
publish = runpy.run_path(str(ROOT / "tools/art/model-review/stage_pages.py"))
stage = publish["stage"]
validate = publish["validate"]
POSES = publish["POSES"]
SHA = "0123456789abcdef" * 2 + "01234567"
SOURCE = "c" * 64


def sha(data):
    return hashlib.sha256(data).hexdigest()


def glb():
    document = json.dumps({"asset": {"version": "2.0"},
                           "scenes": [{"nodes": []}], "scene": 0}, separators=(",", ":")).encode()
    document += b" " * ((-len(document)) % 4)
    size = 12 + 8 + len(document)
    return b"glTF" + struct.pack("<II", 2, size) + struct.pack("<I4s", len(document), b"JSON") + document


def prepare(root):
    exports = root / "exports"
    for pose in POSES:
        folder = exports / pose
        attempt = pose + "-attempt-123"
        leaf = folder / "attempts" / attempt
        leaf.mkdir(parents=True)
        file = glb()
        (leaf / "unicycle_articulated_blockout.glb").write_bytes(file)
        report = {"schema": "ur-art4k-articulated-blockout/1",
                  "attempt_id": attempt, "source_sha256": SOURCE, "rig_pose": pose,
                  "glb_sha256": sha(file), "original_character_likeness_approved": False,
                  "shipping_art_approved": False}
        receipt = json.dumps(report).encode()
        (leaf / "articulated_blockout_receipt.json").write_bytes(receipt)
        pointer = {"schema": "ur-art4k-export-current/1", "attempt_id": attempt,
                   "source_sha256": SOURCE, "rig_pose": pose,
                   "glb_path": f"attempts/{attempt}/unicycle_articulated_blockout.glb",
                   "receipt_path": f"attempts/{attempt}/articulated_blockout_receipt.json",
                   "glb_sha256": sha(file), "receipt_sha256": sha(receipt)}
        last = {"schema": "ur-art4k-export-attempt/1", "attempt_id": attempt,
                "source_sha256": SOURCE, "status": "succeeded", "current_output_usable": True}
        (folder / "articulated_blockout_current.json").write_text(json.dumps(pointer))
        (folder / "articulated_blockout_last_attempt.json").write_text(json.dumps(last))
    site = root / "site"
    site.mkdir()
    (site / "atlas.json").write_text('{"entries":[]}')
    return exports, site


class ModelReviewPublicationTests(unittest.TestCase):
    def test_valid_five_pose_publication_preserves_atlas(self):
        with tempfile.TemporaryDirectory() as d:
            exports, site = prepare(Path(d))
            initial = site / "model-review"
            initial.mkdir()
            (initial / "index.html").write_text("empty landing")
            (initial / "manifest.json").write_text('{"model_url":null}')
            stage(exports, site, SHA)
            result = json.loads((site / "model-review/manifest.json").read_text())
            self.assertEqual(result["source_commit"], SHA)
            self.assertEqual(set(result["poses"]), set(POSES))
            self.assertFalse(result["likeness_approved"])
            self.assertFalse(result["source_sprite_pose_registration"])
            self.assertTrue((site / "atlas.json").is_file())
            for pose, payload in result["poses"].items():
                path = site / "model-review" / payload["url"]
                self.assertTrue(path.is_file(), pose)
                self.assertEqual(sha(path.read_bytes()), payload["sha256"])
            self.assertIn("three", (site / "model-review/index.html").read_text())
            with self.assertRaisesRegex(ValueError, "non-placeholder"):
                stage(exports, site, SHA)

    def test_invalid_digest_cannot_publish_any_pose(self):
        with tempfile.TemporaryDirectory() as d:
            exports, site = prepare(Path(d))
            p = exports / "stunt/articulated_blockout_current.json"
            pointer = json.loads(p.read_text())
            pointer["glb_sha256"] = "0" * 64
            p.write_text(json.dumps(pointer))
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                stage(exports, site, SHA)
            self.assertFalse((site / "model-review").exists())

    def test_failed_latest_attempt_never_falls_back_to_old_success(self):
        with tempfile.TemporaryDirectory() as d:
            exports, site = prepare(Path(d))
            p = exports / "wheelie/articulated_blockout_last_attempt.json"
            last = json.loads(p.read_text())
            last["status"] = "failed"
            last["current_output_usable"] = False
            p.write_text(json.dumps(last))
            with self.assertRaisesRegex(ValueError, "last attempt not successful"):
                stage(exports, site, SHA)
            self.assertFalse((site / "model-review").exists())

    def test_stale_pointer_and_path_traversal_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            exports, site = prepare(Path(d))
            p = exports / "bank/articulated_blockout_current.json"
            ptr = json.loads(p.read_text())
            ptr["attempt_id"] = "previous-attempt"
            p.write_text(json.dumps(ptr))
            with self.assertRaisesRegex(ValueError, "stale pointer"):
                validate(exports, "bank")
            ptr["attempt_id"] = "bank-attempt-123"
            ptr["glb_path"] = "../any.glb"
            p.write_text(json.dumps(ptr))
            with self.assertRaisesRegex(ValueError, "invalid output path"):
                validate(exports, "bank")

    def test_refuse_existing_model_and_mixed_source(self):
        with tempfile.TemporaryDirectory() as d:
            exports, site = prepare(Path(d))
            p = exports / "pedal/articulated_blockout_current.json"
            ptr = json.loads(p.read_text())
            ptr["source_sha256"] = "e" * 64
            p.write_text(json.dumps(ptr))
            with self.assertRaises(ValueError):
                stage(exports, site, SHA)
            # Restore pointer and ensure a pre-existing published review is protected.
            ptr["source_sha256"] = SOURCE
            p.write_text(json.dumps(ptr))
            target = site / "model-review"
            target.mkdir()
            (target / "index.html").write_text("owner content")
            (target / "manifest.json").write_text('{"model_url":"assets/live.glb"}')
            with self.assertRaisesRegex(ValueError, "non-placeholder"):
                stage(exports, site, SHA)
            self.assertEqual((target / "index.html").read_text(), "owner content")

    def test_actual_atlas_build_includes_model_free_viewer(self):
        from tools import windows_visual_atlas as atlas
        with tempfile.TemporaryDirectory() as d:
            site = Path(d) / "site"
            atlas.build(atlas.load_catalog(), site, None, None)
            self.assertTrue((site / "index.html").is_file())
            self.assertTrue((site / "model-review/index.html").is_file())
            self.assertIsNone(json.loads((site / "model-review/manifest.json").read_text())["model_url"])
            self.assertIn("model-review/", (site / "index.html").read_text())
            rows = json.loads((site / "model-review/sprites.json").read_text())
            self.assertEqual(rows["schema"], "ur-racer-original-sprite-reference/1")
            self.assertFalse(rows["sprite_3d_pose_mapping_verified"])
            self.assertEqual(len(rows["frames"]), 32)
            self.assertEqual({r["player"] for r in rows["frames"]}, {"p1", "p2"})
            self.assertEqual({r["guest_frame"] for r in rows["frames"]}, set(range(1205, 1221)))
            for row in rows["frames"]:
                source = site / "model-review" / row["image"]
                self.assertTrue(source.is_file())
                self.assertEqual(sha(source.read_bytes()), row["sha256"])
            # Publishing GLBs must not remove existing hash-verified source images.
            exports, _ = prepare(Path(d) / "fixture")
            stage(exports, site, SHA)
            self.assertTrue((site / "model-review/sprites.json").is_file())
            self.assertEqual(len(list((site / "model-review/sprites").glob("*.png"))), 14)


if __name__ == "__main__":
    unittest.main()
