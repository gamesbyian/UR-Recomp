"""ROM-free safeguards for authentic 40-frame original 2D source review choices."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.art.select_original_mesen_live_pose_exemplars import (
    SCHEMA, TICKS, visible_mask, visible_rgba, mask_iou, select_one_component,
)


def mask(*indices: int) -> bytes:
    values = bytearray(4096)
    for index in indices:
        values[index] = 1
    return bytes(values)


class SourceReviewExemplarTests(unittest.TestCase):
    def test_actual_red_screen_mirror_is_declared_not_optimized(self):
        source = mask(2, 8, 64+20)
        actual = visible_mask(source, "red")
        self.assertEqual(
            [i for i,v in enumerate(actual) if v],
            [55, 61, 64+43])
        self.assertEqual(visible_mask(source, "blue"), source)
        self.assertEqual(visible_mask(actual, "red"), source)
        self.assertNotEqual(actual, source)
        for value in (b"", bytes(4095), bytes([2])*4096):
            with self.assertRaisesRegex(ValueError, "binary source"):
                visible_mask(value, "blue")
        with self.assertRaisesRegex(ValueError, "identity"):
            visible_mask(source, "unknown")

    def test_actual_source_rgb_pixels_reflect_without_recolouring(self):
        rgba=bytearray(64*64*4)
        rgba[4*(1*64+2):4*(1*64+2)+4]=bytes([74,181,0,255])
        rgba[4*(2*64+8):4*(2*64+8)+4]=bytes([255,0,0,255])
        blue=visible_rgba(bytes(rgba),"blue")
        red=visible_rgba(bytes(rgba),"red")
        self.assertEqual(blue,bytes(rgba))
        self.assertEqual(red[4*(1*64+61):4*(1*64+61)+4],
                         bytes([74,181,0,255]))
        self.assertEqual(red[4*(2*64+55):4*(2*64+55)+4],
                         bytes([255,0,0,255]))
        self.assertEqual(visible_rgba(red,"red"),blue)
        self.assertEqual(
            bytes(1 if red[p+3] else 0 for p in range(0,len(red),4)),
            visible_mask(mask(1*64+2,2*64+8),"red"))
        for bad in (b"",bytes(4095*4),bytes([255,0,0,254])*(64*64)):
            with self.subTest(bad=bad[:4]),self.assertRaisesRegex(
                    ValueError,"original opaque/transparent"):
                visible_rgba(bad,"red")
        with self.assertRaisesRegex(ValueError,"original opaque/transparent"):
            visible_rgba(blue,"yellow")

    def test_iou_uses_original_binary_source_only_and_rejects_empty(self):
        a = mask(0,1,2)
        b = mask(0,1,3)
        self.assertEqual(mask_iou(a,b), 0.5)
        self.assertEqual(mask_iou(a,a), 1)
        with self.assertRaisesRegex(ValueError, "zero-area"):
            mask_iou(bytes(4096),bytes(4096))
        with self.assertRaisesRegex(ValueError, "binary"):
            mask_iou(b"x", a)
        with self.assertRaisesRegex(ValueError, "binary"):
            mask_iou(bytes([3])*4096, a)

    def test_medoid_and_max_distance_contrast_deterministic_under_ties(self):
        keys = [(1601,"blue"),(1607,"blue"),(1618,"blue"),(1631,"blue")]
        pixels = {
            keys[0]:mask(0,1,2,3),
            keys[1]:mask(0,1,2,4),
            keys[2]:mask(0,1,2,5),
            keys[3]:mask(20,21,22,23),
        }
        result = select_one_component(list(reversed(keys)),pixels)
        self.assertEqual(result["size"], 4)
        self.assertEqual(result["medoid"], [1601,"blue"])
        self.assertEqual(result["contrast"], [1631,"blue"])
        self.assertEqual(result["members"], [list(x) for x in keys])
        self.assertLess(result["min_pairwise_visible_alpha_iou"], 0.01)
        self.assertLess(result["mean_pairwise_visible_alpha_iou"], 0.5)
        small = select_one_component(keys[:2], pixels)
        self.assertIsNone(small["contrast"])
        singleton = select_one_component(keys[:1], pixels)
        self.assertIsNone(singleton["mean_pairwise_visible_alpha_iou"])
        self.assertEqual(singleton["medoid_average_visible_alpha_iou"], 1.0)

    def test_duplicate_invalid_source_or_role_cannot_enter_selection(self):
        one=(1601,"blue")
        good=mask(0)
        for keys, data in (
                ([], {}),
                ([one,one],{one:good}),
                ([(1600,"blue")], {(1600,"blue"):good}),
                ([(1601,"p3")], {(1601,"p3"):good}),
                ([one], {one:bytes(4096)}),
                ([one], {one:bytes([2])*4096}),
                ([one], {})):
            with self.subTest(keys=keys),self.assertRaises(ValueError):
                select_one_component(keys,data)

    def test_frozen_source_review_groups_and_no_3d_claims(self):
        path=Path(__file__).resolve().parents[2]/(
            "analysis/data/racer-original-live40-screen-review-exemplars-20261103.json")
        receipt=json.loads(path.read_text())
        self.assertEqual(receipt["schema"], SCHEMA)
        self.assertEqual(receipt["actual_original_USA_ROM_source_zip_sha256"],
                         "709fbc2a1cd94b888d8ae0d43894c42c5d455bd968f6bc11f26e710f44e2788f")
        self.assertEqual(receipt["summary"]["actual_original_sprite_observations"],40)
        self.assertEqual(receipt["summary"]["unclassified_new_source_observations"],38)
        self.assertEqual(receipt["summary"]["screen_oriented_review_exemplars"],15)
        self.assertEqual(receipt["summary"]["exact_tile_connected_components"],11)
        self.assertEqual(receipt["summary"]["content_independent_reference_only_groups"],3)
        groups=receipt["historical_source_content_components"]
        self.assertEqual(len(groups),11)
        self.assertEqual(sorted(g["size"] for g in groups),[1,1,1,2,2,3,3,4,4,8,9])
        self.assertEqual(sum(g["size"] for g in groups),38)
        clean=[g for g in groups if
               g["source_content_connection"]=="historical_tile_disjoint_review_only"]
        self.assertEqual(sorted(g["size"] for g in clean),[1,4,4])
        self.assertEqual(
            sorted(tuple(x) for group in clean for x in group["members"]),
            sorted([(1648,"blue"),(1671,"blue"),(1700,"blue"),(2011,"blue"),
                    (1671,"red"),(1700,"red"),(1731,"red"),(2283,"blue"),
                    (2445,"blue")]))
        union=[tuple(x) for group in groups for x in group["members"]]
        self.assertEqual(len(set(union)),38)
        self.assertNotIn((1601,"red"), union)  # frozen historical withheld
        self.assertNotIn((1952,"blue"), union) # frozen historical fit
        self.assertEqual(len(receipt["screen_oriented_review_exemplars"]),15)
        self.assertEqual(
            receipt["screen_oriented_review_exemplars"],
            sorted(receipt["screen_oriented_review_exemplars"],
                   key=lambda x:(x[0],0 if x[1]=="blue" else 1)))
        for g in groups:
            self.assertEqual(g["size"],len(g["members"]))
            self.assertIn(g["medoid"],g["members"])
            self.assertEqual(g["contrast"] is not None, g["size"]>=4)
        for field in ("new_live_source_fit_or_holdout_roles_assigned",
                      "exemplars_prospectively_blind_to_2026_GLB_scores",
                      "original_1994_pose_labels_verified",
                      "original_source_3D_geometry_camera_bones_verified",
                      "source_to_experimental_3D_GLb_pose_mapping_verified",
                      "owner_likeness_approved"):
            self.assertFalse(receipt[field])


if __name__=="__main__":
    unittest.main()
