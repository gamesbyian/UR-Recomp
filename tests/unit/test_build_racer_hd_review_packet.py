import json
import tempfile
import unittest
from pathlib import Path

from tools.build_racer_hd_review_packet import (
    build_review_manifest,
    build_review_packet,
)


class RacerHdReviewPacketTest(unittest.TestCase):
    def dossier(self):
        return {
            "family": "ordinary-racer",
            "temporal_window": {"start": 1, "end": 2, "frame_count": 2},
            "representations": [
                {
                    "representation_id": "a",
                    "stock_evidence": {
                        "png": "stock/a.png",
                        "nearest_4x_png": "nearest-4x/a.png",
                    },
                    "art_review": {
                        "authored_candidate": {
                            "png": "authored-candidate/a.png",
                            "approval_status": "motion-reviewed",
                            "gameplay_scale_review": {
                                "alpha_iou": 0.75,
                                "stock_only_pixel_count": 1,
                                "candidate_only_pixel_count": 1,
                                "stock_only_pixels": [[2, 3]],
                                "candidate_only_pixels": [[4, 5]],
                            },
                        },
                    },
                },
                {
                    "representation_id": "b",
                    "stock_evidence": {
                        "png": "stock/b.png",
                        "nearest_4x_png": "nearest-4x/b.png",
                    },
                    "art_review": {
                        "authored_candidate": {
                            "png": "authored-candidate/b.png",
                            "approval_status": "motion-reviewed reuse",
                            "gameplay_scale_review": {"alpha_iou": 0.75},
                        },
                    },
                },
            ],
        }

    def equivalence(self):
        return {
            "semantic_representation_count": 2,
            "unique_stock_pose_count": 1,
            "pose_groups": [
                {
                    "pose_id": "p1-pose-001",
                    "player": "p1",
                    "stock_rgba_sha256": "stock",
                    "representation_ids": ["a", "b"],
                    "semantic_frame_ids": ["0x1"],
                    "observed_frames": [1, 2],
                    "authored_source_representation_id": "a",
                    "authored_asset_rgba_sha256": "art",
                    "needs_authored_asset": False,
                    "authored_asset_conflict": False,
                },
            ],
            "worklist": {
                "authored_pose_count": 1,
                "unauthored_pose_count": 0,
                "conflicting_authored_pose_count": 0,
            },
        }

    def test_review_manifest_uses_unique_pose_not_semantic_guard_count(self):
        manifest = build_review_manifest(self.dossier(), self.equivalence())
        self.assertEqual(manifest["semantic_representation_count"], 2)
        self.assertEqual(manifest["unique_pose_count"], 1)
        self.assertEqual(manifest["authored_pose_count"], 1)
        self.assertEqual(manifest["unauthored_pose_count"], 0)
        self.assertEqual(len(manifest["poses"]), 1)
        pose = manifest["poses"][0]
        self.assertEqual(pose["representation_ids"], ["a", "b"])
        self.assertEqual(pose["authored_png"], "authored-candidate/a.png")
        self.assertEqual(pose["gameplay_scale_review"]["alpha_iou"], 0.75)

    def test_packet_shipping_status_comes_from_hash_bound_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dossier = root / "manifest.json"
            equivalence = root / "equivalence.json"
            readiness = root / "readiness.json"
            dossier.write_text(json.dumps(self.dossier()))
            equivalence.write_text(json.dumps(self.equivalence()))
            readiness.write_text(json.dumps({
                "schema_version": 1,
                "family": "ordinary-racer",
                "source_temporal_window": {"start": 1, "end": 2},
                "shipping_ready": True,
                "unique_pose_count": 1,
                "review_basis": {
                    "workflow_run": 123,
                    "artifact_id": 456,
                    "temporal_window": [1205, 1220],
                    "review_surface": "review/index.html",
                },
                "family_blockers": [],
                "counts": {
                    "approved": 1,
                    "needs_refinement": 0,
                    "rejected": 0,
                    "unreviewed": 0,
                    "changed_since_review": 0,
                    "unauthored": 0,
                    "authored_conflicts": 0,
                },
                "poses": [{
                    "pose_id": "p1-pose-001",
                    "player": "p1",
                    "authored_asset_rgba_sha256": "art",
                    "review_status": "approved",
                    "shipping_art_approved": True,
                    "blocker_codes": [],
                    "reviewed_authored_rgba_sha256": "art",
                }],
            }))

            out = root / "review"
            manifest = build_review_packet(
                dossier,
                equivalence,
                out,
                readiness_path=readiness,
            )
            pose = manifest["poses"][0]
            self.assertEqual(pose["shipping_review_status"], "approved")
            self.assertTrue(pose["shipping_art_approved"])
            self.assertEqual(pose["shipping_blocker_codes"], [])
            self.assertEqual(pose["reviewed_authored_rgba_sha256"], "art")
            self.assertTrue(manifest["shipping_readiness"]["shipping_ready"])
            self.assertEqual(
                manifest["shipping_readiness"]["review_basis"]["workflow_run"],
                123,
            )
            self.assertEqual(
                manifest["shipping_readiness"]["family_blockers"],
                [],
            )
            html = (out / "index.html").read_text()
            self.assertIn("workflow run 123", html)
            self.assertIn("artifact 456", html)
            self.assertIn("window 1205–1220", html)
            self.assertIn("review/index.html", html)

    def test_packet_rejects_readiness_from_wrong_family_or_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dossier = root / "manifest.json"
            equivalence = root / "equivalence.json"
            readiness = root / "readiness.json"
            dossier.write_text(json.dumps(self.dossier()))
            equivalence.write_text(json.dumps(self.equivalence()))

            base = {
                "family": "ordinary-racer",
                "source_temporal_window": {"start": 1, "end": 2},
                "shipping_ready": True,
                "unique_pose_count": 1,
                "counts": {},
                "review_basis": {},
                "family_blockers": [],
                "poses": [{
                    "pose_id": "p1-pose-001",
                    "player": "p1",
                    "authored_asset_rgba_sha256": "art",
                    "review_status": "approved",
                    "shipping_art_approved": True,
                    "blocker_codes": [],
                }],
            }

            wrong_family = dict(base)
            wrong_family["family"] = "other"
            readiness.write_text(json.dumps(wrong_family))
            with self.assertRaisesRegex(ValueError, "family does not match"):
                build_review_packet(
                    dossier, equivalence, root / "wrong-family",
                    readiness_path=readiness,
                )

            wrong_window = dict(base)
            wrong_window["source_temporal_window"] = {"start": 1, "end": 3}
            readiness.write_text(json.dumps(wrong_window))
            with self.assertRaisesRegex(ValueError, "temporal window does not match"):
                build_review_packet(
                    dossier, equivalence, root / "wrong-window",
                    readiness_path=readiness,
                )

    def test_packet_rejects_readiness_pose_set_or_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dossier = root / "manifest.json"
            equivalence = root / "equivalence.json"
            readiness = root / "readiness.json"
            dossier.write_text(json.dumps(self.dossier()))
            equivalence.write_text(json.dumps(self.equivalence()))

            base = {
                "family": "ordinary-racer",
                "source_temporal_window": {"start": 1, "end": 2},
                "shipping_ready": True,
                "unique_pose_count": 1,
                "counts": {},
                "review_basis": {},
                "family_blockers": [],
                "poses": [{
                    "pose_id": "p1-pose-001",
                    "player": "p1",
                    "authored_asset_rgba_sha256": "art",
                    "review_status": "approved",
                    "shipping_art_approved": True,
                    "blocker_codes": [],
                }],
            }

            wrong_id = json.loads(json.dumps(base))
            wrong_id["poses"][0]["pose_id"] = "stale-pose"
            readiness.write_text(json.dumps(wrong_id))
            with self.assertRaisesRegex(ValueError, "pose IDs do not match"):
                build_review_packet(
                    dossier, equivalence, root / "wrong-id",
                    readiness_path=readiness,
                )

            wrong_hash = json.loads(json.dumps(base))
            wrong_hash["poses"][0]["authored_asset_rgba_sha256"] = "stale"
            readiness.write_text(json.dumps(wrong_hash))
            with self.assertRaisesRegex(ValueError, "authored hash does not match"):
                build_review_packet(
                    dossier, equivalence, root / "wrong-hash",
                    readiness_path=readiness,
                )

    def test_packet_copies_baseline_assets_for_before_after_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current_root = root / "current"
            baseline_root = root / "baseline-source"
            current_root.mkdir()
            baseline_root.mkdir()

            dossier = current_root / "manifest.json"
            equivalence = current_root / "equivalence.json"
            baseline_dossier = baseline_root / "manifest.json"
            baseline_equivalence = baseline_root / "equivalence.json"

            current = self.dossier()
            before = self.dossier()
            current["representations"][0]["art_review"]["authored_candidate"]["png"] = (
                "authored-candidate/a.png"
            )
            before["representations"][0]["art_review"]["authored_candidate"]["png"] = (
                "authored-candidate/a.png"
            )
            current["representations"][0]["art_review"]["authored_candidate"][
                "rgba_sha256"
            ] = "current"
            before["representations"][0]["art_review"]["authored_candidate"][
                "rgba_sha256"
            ] = "before"

            current_eq = self.equivalence()
            baseline_eq = self.equivalence()
            current_eq["pose_groups"][0]["authored_asset_rgba_sha256"] = "current"
            baseline_eq["pose_groups"][0]["authored_asset_rgba_sha256"] = "before"

            dossier.write_text(json.dumps(current))
            equivalence.write_text(json.dumps(current_eq))
            baseline_dossier.write_text(json.dumps(before))
            baseline_equivalence.write_text(json.dumps(baseline_eq))
            source_png = baseline_root / "authored-candidate" / "a.png"
            source_png.parent.mkdir()
            source_png.write_bytes(b"baseline-png")

            out = root / "review"
            manifest = build_review_packet(
                dossier,
                equivalence,
                out,
                baseline_dossier_path=baseline_dossier,
                baseline_equivalence_path=baseline_equivalence,
            )

            self.assertEqual(
                manifest["baseline_comparison"]["changed_authored_pose_count"], 1
            )
            self.assertEqual(
                manifest["baseline_comparison"]["copied_authored_png_count"], 1
            )
            self.assertTrue(
                (out / "baseline" / "p1-pose-001.png").is_file()
            )
            html = (out / "index.html").read_text()
            self.assertIn("Before · authored 4× inspection", html)
            self.assertIn("After · gameplay footprint", html)

    def test_packet_renders_live_frames_at_known_native_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dossier = root / "manifest.json"
            equivalence = root / "equivalence.json"
            dossier.write_text(json.dumps(self.dossier()))
            equivalence.write_text(json.dumps(self.equivalence()))

            original = root / "original.ppm"
            hd = root / "hd.ppm"
            original.write_bytes(
                b"P6\n256 224\n255\n" + bytes([1, 2, 3]) * (256 * 224)
            )
            hd.write_bytes(
                b"P6\n1024 896\n255\n" + bytes([4, 5, 6]) * (1024 * 896)
            )

            out = root / "review"
            manifest = build_review_packet(
                dossier, equivalence, out, original, hd
            )

            self.assertEqual(
                manifest["live_reference"]["original_dimensions"], [256, 224]
            )
            self.assertEqual(
                manifest["live_reference"]["hd_dimensions"], [1024, 896]
            )
            self.assertTrue((out / "live-original.png").is_file())
            self.assertTrue((out / "live-hd.png").is_file())
            html = (out / "index.html").read_text()
            self.assertIn("2 exact guards → 1 unique poses", html)
            self.assertIn("After · gameplay footprint", html)
            self.assertIn("Live split-screen reference", html)
            self.assertIn("Alpha mismatch", html)
            self.assertIn('x="2" y="3"', html)
            self.assertIn('x="4" y="5"', html)


if __name__ == "__main__":
    unittest.main()
