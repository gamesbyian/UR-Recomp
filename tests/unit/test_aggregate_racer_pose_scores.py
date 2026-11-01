"""Adversarial multipose source-weighting and real-retained-raster tests."""
from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import zlib
import unittest
from pathlib import Path

from tools.art.aggregate_racer_pose_scores import (
    SCHEMA, PACKET_SCHEMA, _safe_file, summarize_verified_rows, evaluate,
)
from tools.art.build_racer_source_pixel_corpus import build as original_corpus, STRIP
from tools.art.score_racer_candidate import score_retained_original
from tools.art.racer_source_pixels import decode_rgba_png


def fake_row(i, role="fit", source="a", candidate="b", iou=0.5):
    return {
        "guest_frame": i, "player": "p1", "role": role,
        "source_binary_mask_sha256": source*64,
        "candidate_binary_mask_sha256": candidate*64,
        "mask_iou": iou, "boundary_chamfer_mean_physical_px": 1.0-iou,
    }


class GroupingTests(unittest.TestCase):
    def test_repeated_holds_have_one_pose_weight(self):
        observations = (
            [fake_row(i, source="a", iou=0.1) for i in range(1205, 1215)] +
            [fake_row(1215, source="c", iou=0.9)]
        )
        result = summarize_verified_rows(observations)
        self.assertEqual(result["observation_count"], 11)
        self.assertEqual(result["unique_source_binary_silhouette_count"], 2)
        # Source observation weighted score would be 0.1727; correct equal
        # source-shape weight is 0.5. A held pose cannot outvote a new pose.
        self.assertEqual(result["split_metrics"]["fit"]["equal_pose_weighted_mask_iou"], .5)
        self.assertEqual(result["split_metrics"]["fit"]["source_observation_count"], 11)
        self.assertEqual(result["split_metrics"]["fit"]["unique_original_silhouette_count"], 2)
        self.assertFalse(result["diagnostic_split_is_independent_3d_camera_or_source_family"])
        self.assertFalse(result["owner_likeness_approved"])

    def test_same_binary_shape_cannot_cross_fit_and_diagnostic(self):
        with self.assertRaisesRegex(ValueError, "crosses"):
            summarize_verified_rows([fake_row(1205), fake_row(1206, role="diagnostic")])

    def test_palette_same_shape_is_one_group_but_3d_candidate_inconsistency_visible(self):
        a = fake_row(1205, source="a", candidate="b", iou=.5)
        b = fake_row(1206, source="a", candidate="c", iou=.7)
        result = summarize_verified_rows([a, b])
        self.assertEqual(result["unique_source_binary_silhouette_count"], 1)
        g = result["source_pose_groups"][0]
        self.assertEqual(g["mean_mask_iou_for_same_source_shape"], .6)
        self.assertEqual(g["distinct_candidate_binary_masks"], 2)

    def test_bad_weights_and_empty_fail(self):
        for rows in ([], [fake_row(1, iou=-1)], [fake_row(1, iou=1.1)],
                     [fake_row(1, role="independent-camera")],
                     [fake_row(1, source="not-a-hash")]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                summarize_verified_rows(rows)

    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as base:
            root=Path(base)
            (root/"inside.png").write_bytes(b"synthetic")
            self.assertEqual(_safe_file(root, "inside.png", ".png"), root/"inside.png")
            for name in ("../escape.png", "/etc/passwd", "a\\b.png", "inside.txt"):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    _safe_file(root, name, ".png")


class RetainedOriginalControlTests(unittest.TestCase):
    """Use the real retained sprite only as a trivially perfect unit control."""
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        self.source = STRIP/"stock/p1-00.png"
        self.local = self.root/"candidate-4x.png"
        w, h, pixels, _ = decode_rgba_png(self.source)
        self.assertEqual((w, h), (64, 64))
        def chunk(tag, payload):
            return (struct.pack(">I", len(payload)) + tag + payload +
                    struct.pack(">I", zlib.crc32(tag+payload)&0xffffffff))
        lines = []
        for y in range(64):
            row = b"".join(pixels[(y*64+x)*4:(y*64+x+1)*4]*4 for x in range(64))
            lines.extend([bytes([0]) + row]*4)
        raw = (bytes([137,80,78,71,13,10,26,10]) +
               chunk(b"IHDR", struct.pack(">IIBBBBB",256,256,8,6,0,0,0)) +
               chunk(b"IDAT", zlib.compress(b"".join(lines))) +
               chunk(b"IEND", b""))
        self.local.write_bytes(raw)
        self.source_img_sha = hashlib.sha256(self.local.read_bytes()).hexdigest()
        corpus = original_corpus()
        self.source_row = next(x for x in corpus["observations"]
                               if x["player"]=="p1" and x["guest_frame"]==1205)

    def packet_entry(self, frame, role="fit"):
        score = score_retained_original("p1", frame, self.local, self.source_img_sha, 4)
        packet = {
            "schema": PACKET_SCHEMA,
            "source_scad_sha256": "a"*64,
            "source_glb_sha256": "b"*64,
            "source_camera_manifest_sha256": "c"*64,
            "source_original_representation_id": (
                self.source_row["representation_id"]),
            "source_1994_3d_camera_verified": False,
            "shipping_art_approved": False,
            "owner_likeness_approved": False,
            "candidate_png_sha256": self.source_img_sha,
            "silhouette_score": score,
            "projected_alpha": {"candidate_png_sha256": self.source_img_sha},
        }
        path = self.root/("packet-"+str(frame)+".json")
        path.write_text(json.dumps(packet), encoding="utf-8")
        return {
            "role": role, "packet_path": path.name,
            "packet_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "candidate_path": self.local.name, "candidate_png_sha256": self.source_img_sha,
        }

    def manifest(self, entries):
        path=self.root/"suite.json"
        path.write_text(json.dumps({"schema": SCHEMA, "packets": entries}), encoding="utf-8")
        return path

    def test_actual_source_pixel_packet_is_trivial_control(self):
        result = evaluate(self.manifest([self.packet_entry(1205)]))
        self.assertEqual(result["split_metrics"]["fit"]["equal_pose_weighted_mask_iou"], 1)
        self.assertEqual(result["unique_source_binary_silhouette_count"], 1)
        self.assertFalse(result["no_source_1994_camera_or_3d_pose_certified"] is False)
        self.assertFalse(result["shipping_art_approved"])

    def test_packet_sha_tamper_rejected_before_scoring(self):
        record=self.packet_entry(1205)
        record["packet_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError, "packet SHA256 mismatch"):
            evaluate(self.manifest([record]))

    def test_same_original_silhouette_cannot_falsify_diagnostic_partition(self):
        fit=self.packet_entry(1205)
        diagnostic=self.packet_entry(1206, role="diagnostic")
        with self.assertRaisesRegex(ValueError, "crosses"):
            evaluate(self.manifest([fit, diagnostic]))


if __name__ == "__main__":
    unittest.main()
