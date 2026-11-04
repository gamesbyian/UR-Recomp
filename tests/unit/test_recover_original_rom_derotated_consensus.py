"""Original ROM 2D de-rotation consensus is a source contour, never a 3D mesh."""
import hashlib
import json
from pathlib import Path
import unittest

from tools.art.recover_original_rom_derotated_consensus import (
    SCHEMA, ROM_SHA, SOURCE_SHA, N, PHASES,
    FROZEN_EVEN_ORIENTATION_PIVOT,
    consensus, even_source_pivot, analyze,
)

ROOT=Path(__file__).resolve().parents[2]


class OriginalROMDerotatedConsensus(unittest.TestCase):
    def test_source_pixel_coverage_is_distinct_from_blank_and_part_colour(self):
        images=[bytearray(N) for _ in range(64)]
        valid=[bytearray([1]*N) for _ in range(64)]
        for n in range(64):
            images[n][10*64+10]=7
            if n<20:images[n][12*64+12]=4
            if n<48:images[n][14*64+14]=5
            if n<16:valid[n][17*64+17]=0
            else:images[n][17*64+17]=9
            if n<40:valid[n][19*64+19]=0
            else:images[n][19*64+19]=11
        report=consensus([bytes(i) for i in images],
                         [bytes(v) for v in valid])
        self.assertEqual(report["orientation_samples"],64)
        self.assertEqual(report["source_near_invariant_opaque_core_pixels"],2)
        self.assertEqual(report["source_consensus_opaque_pixels"],3)
        self.assertEqual(report["source_mid_frequency_view_dependent_pixels"],2)
        self.assertEqual(report["source_valid_orientation_observation_count_64"][17*64+17],48)
        self.assertEqual(report["source_valid_orientation_observation_count_64"][19*64+19],24)
        self.assertEqual(report["source_opaque_observation_count_64"][19*64+19],24)
        self.assertEqual(report["source_consensus_index4_64rows"][10][10],"7")
        self.assertEqual(report["source_consensus_index4_64rows"][12][12],"0")
        self.assertEqual(report["source_consensus_index4_64rows"][14][14],"5")
        self.assertEqual(report["source_consensus_index4_64rows"][17][17],"9")
        self.assertEqual(report["source_consensus_index4_64rows"][19][19],"0")
        self.assertEqual(report["per_fixed_source_image_y_band"]
                         ["upper_y0_14"]["source_near_invariant_opaque_core_pixels"],1)
        with self.assertRaisesRegex(ValueError,"indexed planes"):
            consensus([b"bad"],[bytes(N)])
        with self.assertRaisesRegex(ValueError,"indexed planes"):
            consensus([bytes(N)],[bytes([2])*N])

    def test_even_index_source_pivot_does_not_use_odd_orientation(self):
        boxes={str(i):[31,19,32,20] for i in range(64)}
        boxes["2"]=[32,20,32,20]
        for i in (4,6,8,10):boxes[str(i)]=[31,20,32,20]
        source={"source_phase_variation_bbox_by_ROM_angle_index":boxes}
        self.assertEqual(even_source_pivot(source),FROZEN_EVEN_ORIENTATION_PIVOT)
        boxes["3"]=[0,0,63,63]
        self.assertEqual(even_source_pivot(source),FROZEN_EVEN_ORIENTATION_PIVOT)
        boxes["2"]=[-1,0,63,63]
        with self.assertRaisesRegex(ValueError,"bounding box"):
            even_source_pivot(source)

    def test_actual_1994_ROM_4_phase_by_64_source_sprite_contours(self):
        rom=(ROOT/"reference/roms/retail/Uniracers_USA.sfc").read_bytes()
        axis=(ROOT/"analysis/data/racer-original-ROM-24phase-64angle-source-axis-20261103.json").read_bytes()
        self.assertEqual(hashlib.sha256(rom).hexdigest(),ROM_SHA)
        self.assertEqual(hashlib.sha256(axis).hexdigest(),SOURCE_SHA)
        result=analyze(rom,axis)
        self.assertEqual(result["schema"],SCHEMA)
        self.assertEqual(result["original_grid_dimensions"],[24,64])
        self.assertEqual(result["source_even_index_only_frozen_2D_rotation_pivot_xy"],
                         list(FROZEN_EVEN_ORIENTATION_PIVOT))
        self.assertEqual(set(result["per_original_ROM_phase"]),
                         {str(x) for x in PHASES})
        self.assertFalse(result["original_1994_3D_geometry_camera_joint_or_materials_recovered"])
        self.assertFalse(result["owner_art_likeness_approved"])
        self.assertTrue(result["source_64x64_rotation_canvas_cropping_not_counted_as_background"])
        # Authentic USA ROM execution, head 5a862badb692, Actions
        # 41890911468; freeze the original 4x64 orientation normalized
        # source pixel counts to detect decoder/rotation/crop regressions.
        frozen={
            "0":(297,173,329),
            "6":(300,165,337),
            "12":(295,176,326),
            "18":(297,171,331),
        }
        for phase,(expected_consensus,expected_core,expected_fringe) in frozen.items():
            frame=result["per_original_ROM_phase"][phase]
            self.assertEqual(frame["source_consensus_opaque_pixels"],expected_consensus)
            self.assertEqual(frame["source_near_invariant_opaque_core_pixels"],expected_core)
            self.assertEqual(frame["source_mid_frequency_view_dependent_pixels"],expected_fringe)
        for phase,record in result["per_original_ROM_phase"].items():
            with self.subTest(phase=phase):
                self.assertEqual(record["orientation_samples"],64)
                self.assertEqual(len(record["source_consensus_index4_64rows"]),64)
                self.assertTrue(all(len(row)==64 for row in
                                    record["source_consensus_index4_64rows"]))
                self.assertEqual(len(record["source_valid_orientation_observation_count_64"]),N)
                self.assertEqual(len(record["source_opaque_observation_count_64"]),N)
                self.assertGreater(record["source_valid_coverage_pixels"],N//2)
                self.assertGreater(record["source_near_invariant_opaque_core_pixels"],0)
                self.assertGreater(record["source_mid_frequency_view_dependent_pixels"],0)
                self.assertGreaterEqual(record["source_consensus_opaque_pixels"],
                                        record["source_near_invariant_opaque_core_pixels"])
        print("OK ART4K_ORIGINAL_ROM_DEROTATED_CONSENSUS_UNIT",
              json.dumps({p:{
                  "core":r["source_near_invariant_opaque_core_pixels"],
                  "consensus":r["source_consensus_opaque_pixels"],
                  "fringe":r["source_mid_frequency_view_dependent_pixels"]}
                  for p,r in result["per_original_ROM_phase"].items()},sort_keys=True))

    def test_corrupted_original_provenance_fails(self):
        with self.assertRaisesRegex(ValueError,"SHA"):
            analyze(b"",b"{}")


if __name__=="__main__":
    unittest.main()
