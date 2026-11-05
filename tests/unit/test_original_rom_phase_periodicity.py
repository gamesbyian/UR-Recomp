"""Real original 24x64 ROM graphics vs artist-recalled 16 pedal variants."""
import json
from pathlib import Path
import unittest

from tools.art.audit_original_rom_phase_periodicity import (
    audit,score_one_original_orientation,phase_support_positions,
    PHASES,LAGS,SCHEMA,ROM_SHA
)

ROOT=Path(__file__).resolve().parents[2]


def one_phase_frame(p):
    result=bytearray(4096)
    result[23*64+8+p%16]=5
    return bytes(result)


class OriginalSixteenVersusTwentyFourPhaseTests(unittest.TestCase):
    def test_synthetic_sixteen_repeat_wins_without_fitting(self):
        frames=tuple(one_phase_frame(p) for p in range(PHASES))
        support=phase_support_positions(frames)
        self.assertEqual(len(support),16)
        scores=score_one_original_orientation(frames)
        self.assertEqual(set(scores["lag_results"]),{str(i) for i in LAGS})
        sixteen=scores["lag_results"]["16"]
        self.assertEqual(sixteen["source_exact_4bpp_index_match_fraction"],1.)
        self.assertEqual(sixteen["phase_support_alpha_iou"],1.)
        self.assertTrue(all(sixteen["source_exact_4bpp_index_matches"]>
                            scores["lag_results"][str(lag)][
                                "source_exact_4bpp_index_matches"]
                            for lag in range(1,16)))

    def test_original_index_plane_validation_rejects_fake_source(self):
        frames=tuple(one_phase_frame(i) for i in range(24))
        for invalid in (frames[:23],
                        tuple([bytes(4096)]*24),
                        frames[:1]+(bytes([16])+bytes(4095),)+frames[2:],
                        frames[:2]+(b"not a 64 image",)+frames[3:]):
            with self.subTest(invalid=invalid[:1]),self.assertRaises(ValueError):
                phase_support_positions(invalid)
        with self.assertRaisesRegex(ValueError,"original USA ROM"):
            audit(bytes(2097152))

    def test_authenticated_original_rom_all_64_angles_and_sixteen_hypothesis(self):
        path=ROOT/"reference/roms/retail/Uniracers_USA.sfc"
        self.assertTrue(path.is_file(),"source original ROM must be present for genuine test")
        result=audit(path.read_bytes())
        self.assertEqual(result["schema"],SCHEMA)
        self.assertEqual(result["original_USA_ROM_sha256"],ROM_SHA)
        self.assertEqual(result["original_ROM_presentation_grid"],[24,64])
        self.assertEqual(set(result["all_original_64_orientation_diagnostics"]),
                         {str(i) for i in range(64)})
        self.assertEqual(set(result["all_lag_summary"]),{str(i) for i in range(1,17)})
        self.assertEqual(result["historical_interview_pedal_variant_count_recollected"],16)
        self.assertTrue(result["historical_16_pedal_variants_NOT_identified_as_ROM_phase_period"])
        self.assertFalse(result["original_1994_3D_pedal_angle_or_mesh_recovered"])
        first=result["all_lag_summary"]["1"]
        last=result["all_lag_summary"]["16"]
        self.assertEqual(first["equal_base_pair_count"],512)
        self.assertEqual(first["phase_support_pixel_instances"],
                         last["phase_support_pixel_instances"])
        for lag,row in result["all_lag_summary"].items():
            with self.subTest(lag=lag):
                self.assertTrue(0<=row["source_exact_index_fraction"]<=1)
                self.assertTrue(0<=row["source_phase_sensitive_alpha_iou"]<=1)
                self.assertEqual(row["alpha_tp_fp_fn"]["tp"]+
                                 row["alpha_tp_fp_fn"]["fp"]+
                                 row["alpha_tp_fp_fn"]["fn"]>0,True)
        print("ART4K_AUTHENTIC_ROM_16_VS_24_GRAPHICS_SUMMARY",
              json.dumps({
                  "source_original_ROM_sha256":result["original_USA_ROM_sha256"],
                  "lag16":last,
                  "best_other_lag":result["best_other_lag_by_exact_source_index_fraction"],
                  "best_other_score":result["all_lag_summary"][str(
                      result["best_other_lag_by_exact_source_index_fraction"])],
                  "lag16_exceeds_every_other":
                      result["lag16_exceeds_every_other_tested_lag_in_exact_source_index_fraction"]
              },sort_keys=True))


if __name__=="__main__":
    unittest.main()
