"""Full original 64x64 4bpp sprite rotations test viewpoint identifiability."""
import hashlib
import json
from pathlib import Path
import unittest

from tools.art.audit_original_rom_fullsprite_rotation_null import (
    SCHEMA, PHASES, ODD_ANGLES, rigid_rotation_indices, score, audit,
    ROM_SHA, SOURCE_SHA,
)

ROOT=Path(__file__).resolve().parents[2]


class OriginalWholeSpriteRotationTests(unittest.TestCase):
    def test_rigid_rotation_retains_index_value_and_alpha_semantics(self):
        original=bytearray(4096)
        original[29*64+31]=7
        quarter=rigid_rotation_indices(bytes(original),16,31.5,19.5)
        self.assertEqual(quarter[19*64+22],7)
        self.assertEqual(sum(x!=0 for x in quarter),1)
        self.assertEqual(rigid_rotation_indices(bytes(original),0,31.5,19.5),
                         bytes(original))
        own=score(quarter,quarter)
        self.assertEqual(own["alpha_iou"],1.0)
        self.assertEqual(own["opaque_exact_index_recall"],1.0)
        changed=bytearray(quarter)
        changed[19*64+22]=8
        separate=score(quarter,bytes(changed))
        self.assertEqual(separate["alpha_iou"],1.0)
        self.assertEqual(separate["opaque_exact_index_recall"],0.0)
        self.assertEqual(separate["different_original_4bpp_indices_in_overlap"],1)
        with self.assertRaisesRegex(ValueError,"4bpp"):
            rigid_rotation_indices(b"bad",16,31.5,19.5)
        with self.assertRaises(ValueError):
            rigid_rotation_indices(bytes(original),64,31.5,19.5)

    def test_actual_original_all_1536_source_frames_full_index_variation(self):
        rom=(ROOT/"reference/roms/retail/Uniracers_USA.sfc").read_bytes()
        source=(ROOT/"analysis/data/racer-original-ROM-24phase-64angle-source-axis-20261103.json").read_bytes()
        self.assertEqual(hashlib.sha256(rom).hexdigest(),ROM_SHA)
        self.assertEqual(hashlib.sha256(source).hexdigest(),SOURCE_SHA)
        result=audit(rom,source)
        self.assertEqual(result["schema"],SCHEMA)
        self.assertEqual(result["source_original_phase_indices_tested"],list(PHASES))
        self.assertEqual(result["source_original_orientation_indices_tested"],list(ODD_ANGLES))
        self.assertEqual(len(result["per_original_source_sprite"]),4*32)
        self.assertTrue(result["full_original_4bpp_colour_indices_not_just_alpha_tested"])
        self.assertTrue(result["already_inspected_ROM_frame_manifold_NOT_prospective_blind"])
        self.assertFalse(result["independent_1994_3D_camera_or_viewpoint_recovered"])
        for name,row in result["aggregate"].items():
            self.assertEqual(row["source_sprite_observations"],128)
            self.assertTrue(0<=row["pooled_alpha_iou"]<=1)
            self.assertTrue(0<=row["pooled_source_opaque_index_exact_recall"]<=1)
            self.assertGreater(row["source_opaque_alpha_intersection"]+
                               row["source_opaque_alpha_false_negative"],0)
        # Exact executed original ROM receipt at 093d31998bee, Actions run
        # 41787502835, job 126433276743. Freeze 128 original full sprite
        # comparisons: higher phase-region support IoU does not imply
        # whole-source geometry/paint recovery.
        expected={
            "static_2D_sprite": {
                "source_opaque_alpha_intersection":14788,
                "source_opaque_alpha_false_positive":26300,
                "source_opaque_alpha_false_negative":26353,
                "original_4bpp_exact_matching_opaque_pixels":2660,
                "original_4bpp_differing_opaque_intersection":12128,
                "pooled_alpha_iou":0.21927314,
                "pooled_source_opaque_index_exact_recall":0.0646557,
            },
            "one_pivot_2D_rigid_rotation": {
                "source_opaque_alpha_intersection":32793,
                "source_opaque_alpha_false_positive":8183,
                "source_opaque_alpha_false_negative":8348,
                "original_4bpp_exact_matching_opaque_pixels":9806,
                "original_4bpp_differing_opaque_intersection":22987,
                "pooled_alpha_iou":0.66484876,
                "pooled_source_opaque_index_exact_recall":0.23835104,
            }
        }
        for arm,items in expected.items():
            for key,value in items.items():
                self.assertEqual(result["aggregate"][arm][key],value,
                                 (arm,key))
        self.assertLess(result["aggregate"]["one_pivot_2D_rigid_rotation"]
                        ["pooled_source_opaque_index_exact_recall"],0.25)
        # Print a compact exact-head evidence record in the existing unit
        # shard's accepted OK-line channel without adding CI jobs.
        print("OK ART4K_ORIGINAL_FULLSPRITE_ROTATION_NULL",
              json.dumps(result["aggregate"],sort_keys=True))

    def test_wrong_original_axis_evidence_rejected(self):
        with self.assertRaisesRegex(ValueError,"SHA"):
            audit(b"",b"{}")


if __name__=="__main__":
    unittest.main()
