"""Original source temporal-motion evidence: synthetic controls plus retained PNGs."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.art.build_original_racer_temporal_witness import (
    SCHEMA, build_witness, contiguous_holds, source_mask_geometry, transition,
)
from tools.art.build_racer_source_pixel_corpus import build as source_corpus, REGISTRY


def alpha(*positions, value=255):
    out=bytearray(4096)
    for x,y in positions:
        out[y*64+x]=value
    return bytes(out)


class OriginalTemporalMotionGeometryTests(unittest.TestCase):
    def test_two_pixel_shape_measures_anisotropic_original_pixel_aspect(self):
        shape=source_mask_geometry(alpha((9,20),(15,20)))
        self.assertEqual(shape["opaque_pixels"],2)
        self.assertEqual(shape["bbox_source_logical_xyxy"],[9,20,15,20])
        self.assertEqual(shape["alpha_centroid_logical_xy"],[12,20])
        self.assertEqual(shape["alpha_centroid_physical_x_y"],[14,20])
        self.assertEqual(shape["alpha_second_moment_physical_xx_xy_yy"],[12.25,0,0])
        self.assertEqual(shape["lowest_alpha_midpoint_x2_y2"],[24,40])

    def test_original_frame_delta_has_no_hidden_image_registration(self):
        first=alpha((10,20),(11,20))
        second=alpha((11,20),(12,20))
        res=transition(first,second,source_mask_geometry(first),source_mask_geometry(second))
        self.assertEqual(res["binary_mask_xor_pixels"],2)
        self.assertAlmostEqual(res["original_binary_mask_overlap_iou"],1/3,places=8)
        self.assertEqual(res["centroid_delta_source_logical_xy"],[1,0])
        self.assertEqual(res["lowest_alpha_midpoint_delta_x2_y2"],[2,0])

    def test_alpha_intensity_change_is_not_new_binary_shape(self):
        first=alpha((10,20),value=128)
        second=alpha((10,20),value=255)
        res=transition(first,second,source_mask_geometry(first),source_mask_geometry(second))
        self.assertEqual(res["binary_mask_xor_pixels"],0)
        self.assertEqual(res["original_binary_mask_overlap_iou"],1)

    def test_real_frame_hold_run_length_does_not_invent_new_poses(self):
        rows=[
            {"frame":1205,"sha":"a"}, {"frame":1206,"sha":"a"},
            {"frame":1207,"sha":"b"}, {"frame":1208,"sha":"b"},
            {"frame":1210,"sha":"b"},
        ]
        runs=contiguous_holds(rows,"sha")
        self.assertEqual([x["frame_count"] for x in runs],[2,2,1])
        self.assertEqual(runs[2]["first_frame"],1210)

    def test_empty_or_malformed_original_raster_rejected(self):
        with self.assertRaisesRegex(ValueError,"4096"):
            source_mask_geometry(b"")
        with self.assertRaisesRegex(ValueError,"empty"):
            source_mask_geometry(bytes(4096))
        with self.assertRaisesRegex(ValueError,"4096"):
            transition(bytes(10),alpha((10,20)),{},{})


class RealFirstFamilyTemporalWitnessTests(unittest.TestCase):
    def test_first_family_reports_exact_original_sha_and_temporal_counts(self):
        witness=build_witness()
        corpus=source_corpus()
        self.assertEqual(witness["schema"],SCHEMA)
        self.assertEqual(witness["source_rom_sha256"],corpus["historical_manifest_declared_rom_sha256"])
        self.assertEqual(witness["source_frame_observations"],32)
        self.assertEqual(witness["temporal_transition_observations"],30)
        self.assertEqual(witness["unique_original_binary_silhouettes"],10)
        self.assertEqual(witness["source_binary_mask_changed_transition_count"],9)
        self.assertEqual(witness["source_binary_mask_held_transition_count"],21)
        self.assertEqual(witness["players"]["p1"]["changed_binary_transitions"],6)
        self.assertEqual(witness["players"]["p2"]["changed_binary_transitions"],3)
        self.assertEqual(witness["players"]["p1"]["distinct_original_binary_masks"],6)
        self.assertEqual(witness["players"]["p2"]["distinct_original_binary_masks"],4)
        self.assertFalse(witness["original_1994_3d_pose_mapping_recovered"])
        self.assertFalse(witness["true_physical_wheel_ground_contact_verified"])
        self.assertFalse(witness["shipping_art_approved"])
        for player in ("p1","p2"):
            frames=witness["players"][player]["frames"]
            self.assertEqual([r["frame"] for r in frames],list(range(1205,1221)))
            self.assertEqual(len(witness["players"][player]["frame_transitions"]),15)
            self.assertEqual(
                witness["players"][player]["unchanged_binary_transitions"]+
                witness["players"][player]["changed_binary_transitions"],15)
            for row in frames:
                self.assertEqual(len(row["source_binary_mask_sha256"]),64)

    def test_unchanged_p1_1205_1206_original_is_a_hold(self):
        result=build_witness()
        p1=result["players"]["p1"]
        self.assertTrue(p1["frame_transitions"][0]["original_full_rgba_unchanged"])
        self.assertTrue(p1["frame_transitions"][0]["original_alpha_silhouette_unchanged"])
        self.assertEqual(p1["frame_transitions"][0]["binary_mask_xor_pixels"],0)
        self.assertGreater(
            sum(x["binary_mask_xor_pixels"]>0 for x in p1["frame_transitions"]),0)
        self.assertGreaterEqual(p1["source_rgba_hold_runs"][0]["frame_count"],2)

    def test_original_registry_sha_is_independent_input(self):
        with patch("tools.art.build_original_racer_temporal_witness.build") as mocked:
            mocked.return_value=copy.deepcopy(source_corpus())
            mocked.return_value["source_registry_current_sha256"]="0"*64
            with self.assertRaisesRegex(ValueError,"registry changed"):
                build_witness()

    def test_tampered_source_contact_anchor_rejected_even_if_sha_updated(self):
        original=json.loads(REGISTRY.read_text(encoding="utf-8"))
        identity=original["motion_review_sequence"]["frames"][0]["p1_representation_id"]
        target=next(row for row in original["entries"] if row["representation_id"]==identity)
        target["registration"]["semantic_anchors"]["wheel_contact_x2_y2"]=[11,76]
        with tempfile.TemporaryDirectory() as base:
            path=Path(base)/"altered-registry.json"
            path.write_text(json.dumps(original),encoding="utf-8")
            corpus=copy.deepcopy(source_corpus())
            corpus["source_registry_current_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
            with patch("tools.art.build_original_racer_temporal_witness.REGISTRY",path),patch(
                "tools.art.build_original_racer_temporal_witness.build",return_value=corpus
            ):
                with self.assertRaisesRegex(ValueError,"contact register"):
                    build_witness()


if __name__=="__main__":
    unittest.main()
