"""Cheap source/GLB five-pose 2D axis coverage and claim-boundary tests."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location(
    "source_to_model_axis",
    ROOT/"tools/art/compare_original_chroma_axes_to_glb_poses.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def originals():
    return [
        {"original_binary_mask_sha256":f"{i:064x}",
         "equal_colour_variant_mean_projected_angle_deg":float(a)}
        for i,a in enumerate((-29,-16,-3,6,20,43))
    ]


class UnpairedAxisCoverageTests(unittest.TestCase):
    def test_frozen_directions_reveal_sparse_pose_coverage(self):
        poses={p:{"signed_axis_angle_from_image_vertical_deg":a}
               for p,a in (
                  ("upright",7.0),("pedal",7.0),("wheelie",34.0),
                  ("stunt",-42.0),("bank",8.0))}
        result=module.summarize_unpaired_source_coverage(originals(),poses)
        self.assertEqual(result["original_binary_mask_count"],6)
        self.assertEqual(result["experimental_2026_pose_count"],5)
        self.assertEqual(result["original_source_axis_range_deg"],[-29.0,43.0])
        self.assertEqual(result["experimental_glb_axis_range_deg"],[-42.0,34.0])
        self.assertGreater(result["original_masks_with_axis_gap_gt_10_deg"],0)
        self.assertFalse(result["pose_identity_inferred_from_smallest_angle"])
        self.assertEqual(len(result["per_original_binary_mask_unpaired_axis_gap"]),6)

    def test_duplicate_mask_and_invalid_pose_rejected(self):
        poses={p:{"signed_axis_angle_from_image_vertical_deg":float(i)}
               for i,p in enumerate(module.POSE_GLB_SHA)}
        duplicate=originals()
        duplicate[1]["original_binary_mask_sha256"]=duplicate[0]["original_binary_mask_sha256"]
        with self.assertRaisesRegex(ValueError,"repeated"):
            module.summarize_unpaired_source_coverage(duplicate,poses)
        bad=dict(poses)
        bad["bank"]={"signed_axis_angle_from_image_vertical_deg":float("nan")}
        with self.assertRaises(ValueError):
            module.summarize_unpaired_source_coverage(originals(),bad)
        del bad["bank"]
        with self.assertRaises(ValueError):
            module.summarize_unpaired_source_coverage(originals(),bad)

    def test_rejects_tampered_original_source_angle_and_mask_identity(self):
        # A valid-looking self-declared corpus SHA and mask count must NOT
        # make arbitrary angle or mask identities source-authenticated.
        from copy import deepcopy
        trusted={
            "schema":module.SOURCE_SCHEMA,
            "source_rom_sha256":module.CANONICAL_ROM_SHA,
            "source_corpus_sha256":"a"*64,
            "source_variants":{
                "independent_exact_source_binary_masks":2,
                "source_masks":[
                    {"original_binary_mask_sha256":"1"*64,
                     "equal_colour_variant_mean_projected_angle_deg":4.5},
                    {"original_binary_mask_sha256":"2"*64,
                     "equal_colour_variant_mean_projected_angle_deg":-13.2}
                ]
            }
        }
        previous=module.recompute_original_source_angles
        module.recompute_original_source_angles=lambda corpus:deepcopy(trusted)
        try:
            module.verify_source_axis_report(Path("/source.json"),deepcopy(trusted))
            forged=deepcopy(trusted)
            forged["source_variants"]["source_masks"][0][
                "equal_colour_variant_mean_projected_angle_deg"]=89.0
            with self.assertRaisesRegex(ValueError,"differs"):
                module.verify_source_axis_report(Path("/source.json"),forged)
            forged=deepcopy(trusted)
            forged["source_variants"]["source_masks"][0][
                "original_binary_mask_sha256"]="9"*64
            with self.assertRaisesRegex(ValueError,"differs"):
                module.verify_source_axis_report(Path("/source.json"),forged)
        finally:
            module.recompute_original_source_angles=previous

    def test_historical_exact_five_glb_source_names_are_distinct_and_sha_valid(self):
        self.assertEqual(set(module.POSE_GLB_SHA),
                         {"upright","pedal","wheelie","stunt","bank"})
        self.assertEqual(len(set(module.POSE_GLB_SHA.values())),5)
        self.assertTrue(all(len(s)==64 for s in module.POSE_GLB_SHA.values()))
        self.assertEqual(len(module.COMMIT),40)

if __name__=="__main__":
    unittest.main()
