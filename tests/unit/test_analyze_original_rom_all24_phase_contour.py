"""One exact original 24x64 ROM contour run plus fast source-only fixtures."""
import hashlib
import json
from pathlib import Path
import unittest

from tools.art.recover_original_rom_derotated_consensus import (
    consensus,ROM_SHA,SOURCE_SHA,N,
)
from tools.art.analyze_original_rom_all24_phase_contour import (
    SCHEMA,PHASES,summarize,analyze,
)

ROOT=Path(__file__).resolve().parents[2]


def fixture():
    records={}
    for phase in PHASES:
        im=bytearray(N)
        im[2*64+2]=1             # always original upper silhouette
        im[3*64+3]=7+phase%2     # same alpha, varying original index4 paint
        im[40*64+30]=4           # always original lower silhouette
        im[40*64+(31+phase%2)]=5 # two changing original lower positions
        if phase%4==0:
            im[20*64+10]=6       # changing source middle position
        records[phase]=consensus([bytes(im)]*64,[bytes([1])*N]*64)
    return records


class OriginalAll24PhaseContourTests(unittest.TestCase):
    def test_fixed_source_synthetic_alpha_and_paint_independent(self):
        r=summarize(fixture(),enforce_original_four_golden=False)
        self.assertEqual(r["source_original_common_valid_2D_positions"],4096)
        self.assertEqual(r["source_all24_always_consensus_alpha_positions"],3)
        self.assertEqual(r["source_all24_ever_consensus_alpha_positions"],6)
        self.assertEqual(r["source_all24_phase_variable_2D_alpha_positions"],3)
        self.assertEqual(r["source_all24_always_near_invariant_opaque_core_positions"],3)
        self.assertEqual([r["per_fixed_source_image_y_band"][band][
            "source_all24_phase_variable_2D_alpha_positions"]
            for band in ("upper_y0_14","middle_y15_26","lower_y27_63")],
            [0,1,2])
        self.assertEqual(len(r["all_original_24_ROM_phase_index_neighbor_pairs"]),24)
        first=r["all_original_24_ROM_phase_index_neighbor_pairs"]["0->1"]
        self.assertEqual(first["source_alpha_tp_fp_fn"],{"tp":3,"fp":1,"fn":2})
        self.assertAlmostEqual(first["source_original_2D_consensus_alpha_iou"],.5)
        self.assertTrue(first["original_ROM_index_neighbors_not_actual_Mesen_PPU_time"])
        self.assertLess(first["source_4bpp_exact_index_recall_on_shared_opaque"],1.)
        self.assertEqual(r["source_original_four_phase_golden_preserved"],[4,5,4,1])

    def test_fail_closed_missing_and_corrupted_24_phase_source(self):
        good=fixture()
        for broken in ({}, {k:v for k,v in good.items() if k!=23}):
            with self.assertRaisesRegex(ValueError,"24 original"):
                summarize(broken,enforce_original_four_golden=False)
        import copy
        wrong=copy.deepcopy(good)
        wrong[2]["source_consensus_binary_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"inconsistent"):
            summarize(wrong,enforce_original_four_golden=False)
        self.assertRaises(ValueError,analyze,b"",b"{}")

    def test_exact_authenticated_original_USA_ROM_full_1536_source_contours(self):
        # This is the one-time source qualification; the ROM was already
        # inspected during 1994 source archaeology. Once real counts are
        # preserved, keep a focused synthetic fast regression to avoid
        # paying for 1536 original sprite extractions on every PR.
        rom=(ROOT/"reference/roms/retail/Uniracers_USA.sfc").read_bytes()
        axis=(ROOT/"analysis/data/racer-original-ROM-24phase-64angle-source-axis-20261103.json").read_bytes()
        self.assertEqual(hashlib.sha256(rom).hexdigest(),ROM_SHA)
        self.assertEqual(hashlib.sha256(axis).hexdigest(),SOURCE_SHA)
        result=analyze(rom,axis)
        self.assertEqual(result["schema"],SCHEMA)
        self.assertEqual(result["source_exact_original_sprite_states_analyzed"],1536)
        self.assertEqual(result["source_original_four_phase_golden_preserved"],[291,304,164,13])
        self.assertEqual(len(result["all_original_24_ROM_phase_index_neighbor_pairs"]),24)
        self.assertFalse(result["original_1994_3D_mesh_camera_joint_physical_angles_recovered"])
        self.assertFalse(result["owner_art_likeness_approved"])
        print("OK ART4K_REAL_ORIGINAL_24PHASE_64ORIENTATION_SHAPE_REPORT",
              json.dumps({
                  "common":result["source_original_common_valid_2D_positions"],
                  "always":result["source_all24_always_consensus_alpha_positions"],
                  "ever":result["source_all24_ever_consensus_alpha_positions"],
                  "varying":result["source_all24_phase_variable_2D_alpha_positions"],
                  "core":result["source_all24_always_near_invariant_opaque_core_positions"],
                  "bands":{k:v["source_all24_phase_variable_2D_alpha_positions"]
                           for k,v in result["per_fixed_source_image_y_band"].items()},
                  "neighbors":{k:v["source_original_2D_consensus_alpha_iou"]
                               for k,v in result["all_original_24_ROM_phase_index_neighbor_pairs"].items()},
              },sort_keys=True))


if __name__=="__main__":
    unittest.main()
