"""Valid-view-safe original 1994 four-phase 2D contour change tests."""
import copy
import hashlib
import unittest

from tools.art.recover_original_rom_derotated_consensus import (
    consensus,SCHEMA as SOURCE_SCHEMA,ROM_SHA,SOURCE_SHA,N,PHASES,
    FROZEN_EVEN_ORIENTATION_PIVOT,
)
from tools.art.analyze_original_rom_four_phase_contour_drift import (
    analyze,SCHEMA,
)

def mock_source():
    records={}
    points=((3,3),(4,4),(5,5),(6,6))
    for i,phase in enumerate(PHASES):
        picture=bytearray(N)
        picture[2*64+2]=2
        picture[10*64+10]=7+i
        x,y=points[i]
        picture[y*64+x]=3
        result=consensus([bytes(picture)]*64,[bytes([1])*N]*64)
        records[str(phase)]=result
    return {
        "schema":SOURCE_SCHEMA,
        "original_ROM_USA_sha256":ROM_SHA,
        "original_24x64_source_report_sha256":SOURCE_SHA,
        "original_grid_dimensions":[24,64],
        "original_phase_indices_examined":list(PHASES),
        "source_even_index_only_frozen_2D_rotation_pivot_xy":
            list(FROZEN_EVEN_ORIENTATION_PIVOT),
        "source_64x64_rotation_canvas_cropping_not_counted_as_background":True,
        "original_1994_3D_geometry_camera_joint_or_materials_recovered":False,
        "owner_art_likeness_approved":False,
        "per_original_ROM_phase":records,
    }

class OriginalFourPhaseContourTests(unittest.TestCase):
    def test_all_six_pairs_preserve_validity_and_paint(self):
        report=analyze(mock_source())
        self.assertEqual(report["schema"],SCHEMA)
        self.assertEqual(report["original_four_phase_common_valid_pixels"],4096)
        self.assertEqual(report["original_four_phase_always_near_invariant_core_pixels"],2)
        self.assertEqual(report["original_four_phase_always_consensus_alpha_pixels"],2)
        self.assertEqual(report["original_four_phase_at_least_once_consensus_alpha_pixels"],6)
        self.assertEqual(report["original_four_phase_phase_varying_2D_alpha_pixels"],4)
        pairs=report["all_six_original_phase_pair_comparisons"]
        self.assertEqual(len(pairs),6)
        self.assertEqual(pairs["0->6"]["source_2D_consensus_tp_fp_fn"],
                         {"tp":2,"fp":1,"fn":1})
        self.assertEqual(pairs["0->6"]["source_2D_consensus_alpha_iou"],.5)
        self.assertEqual(pairs["0->6"][
            "source_exact_index_paint_recall_on_shared_opaque"],.5)
        bands=report["per_fixed_source_y_band"]
        self.assertEqual(bands["upper_y0_14"][
            "original_four_phase_phase_varying_2D_alpha_pixels"],4)
        self.assertEqual(bands["middle_y15_26"][
            "original_four_phase_phase_varying_2D_alpha_pixels"],0)
        self.assertFalse(report["original_2D_phase_drift_not_recovered_1994_physical_3D_geometry"] is False)

    def test_unknown_source_canvas_is_not_transparent(self):
        source=mock_source()
        phase=source["per_original_ROM_phase"]["0"]
        # Make the original (3,3) pixel unseen by at least 33
        # orientations in phase zero; recompute the actual source
        # consensus receipt rather than inventing a new digest.
        images=[bytearray(N) for _ in range(64)]
        valid=[bytearray([1])*N for _ in range(64)]
        for n in range(64):
            images[n][2*64+2]=2
            images[n][10*64+10]=7
            if n<31:
                images[n][3*64+3]=3
                valid[n][3*64+3]=1
            else:
                valid[n][3*64+3]=0
        source["per_original_ROM_phase"]["0"]=consensus(
            [bytes(x) for x in images],[bytes(x) for x in valid])
        result=analyze(source)
        self.assertEqual(result["original_four_phase_common_valid_pixels"],4095)
        self.assertEqual(result["original_four_phase_phase_varying_2D_alpha_pixels"],3)
        self.assertEqual(result["all_six_original_phase_pair_comparisons"]["0->6"][
            "source_2D_consensus_tp_fp_fn"],{"tp":2,"fp":1,"fn":0})
        self.assertEqual(result["all_six_original_phase_pair_comparisons"]["0->6"][
            "source_original_common_valid_pixel_count"] if False else
            result["all_six_original_phase_pair_comparisons"]["0->6"][
            "source_original_common_valid_pixel_count"],4095)

    def test_corrupt_source_receipts_fail_closed(self):
        valid=mock_source()
        for key in ("schema","original_ROM_USA_sha256",
                    "source_even_index_only_frozen_2D_rotation_pivot_xy",
                    "owner_art_likeness_approved"):
            data=copy.deepcopy(valid)
            data[key]=None
            with self.subTest(key=key),self.assertRaises(ValueError):
                analyze(data)
        damaged=copy.deepcopy(valid)
        damaged["per_original_ROM_phase"]["6"]["source_consensus_index4_64rows"][2]="0"*64
        with self.assertRaisesRegex(ValueError,"inconsistent"):
            analyze(damaged)

if __name__=="__main__":
    unittest.main()
