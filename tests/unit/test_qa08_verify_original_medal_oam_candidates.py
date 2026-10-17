"""Reject invented medal ownership while protecting exact source OAM candidates."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location(
    "qa08_oam_candidates",ROOT/"tools/qa08_verify_original_medal_oam_candidates.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OAMCandidateTest(unittest.TestCase):
    def test_two_byte_oam_high_table_and_palette_priority_decode(self):
        blob=bytearray(544)
        # Source-bound medal slot 112: x=200, y=91, tile $A2,
        # palette 5, priority 1, small OBJ size select 3.
        blob[4*112:4*112+4]=bytes([200,91,162,0x1b])
        s=module.decode(bytes(blob),112)
        self.assertEqual((s["x_signed9"],s["y_mod256"],s["tile"]),
                         (200,91,162))
        self.assertEqual((s["OBJ_palette"],s["OBJ_priority"],s["large_sprite_bit"]),
                         (5,1,0))
        self.assertTrue(module.candidate_contains(s,202,100))
        self.assertFalse(module.candidate_contains(s,224,100))
        self.assertFalse(module.candidate_contains(s,202,107))
        # High X9 bit must be decoded as signed negative x, never x+256.
        blob[4*113:4*113+4]=bytes([250,115,164,0x1d])
        blob[512+113//4]|=1<<((113%4)*2)
        self.assertEqual(module.decode(bytes(blob),113)["x_signed9"],-6)

    def test_bad_OAM_bytes_or_unverified_archive_refused(self):
        with self.assertRaises(ValueError):
            module.decode(bytes(543),112)
        with self.assertRaises(ValueError):
            module.decode(bytes(544),128)
        with tempfile.TemporaryDirectory() as tmp:
            fake=Path(tmp)/"fake.zip"
            with zipfile.ZipFile(fake,"w") as z:
                z.writestr("registers/qa08_results_cgram.info.json",'{"frame":5184}')
            with self.assertRaisesRegex(ValueError,"original OAM"):
                module.inspect(fake,fake,fake)

    def test_machine_receipt_is_static_rectangle_candidate_not_render_truth(self):
        report=json.loads(
            (ROOT/"analysis/data/qa08-original-medal-static-OAM-candidates-20261016.json").read_text())
        self.assertEqual(report["original_OAM_fields"],[5183,5184])
        self.assertEqual(report["pixel_geometry"],[256,224])
        self.assertEqual(report["distinct_source_result_raster_frames_verified"],21)
        counts=report["each_frame_pixels_by_nominal_OAM_rectangles"]
        self.assertEqual(counts,{"source_medal_slots_112_114":278,
                                 "adjacent_slots_96_99":18,"total_bad_pixels":296})
        slots=report["actual_original_snapshot_slot_candidates"]
        self.assertEqual([x["slot"] for x in slots],[96,97,98,99,112,113,114])
        self.assertEqual([x["OBJ_palette"] for x in slots[-3:]],[5,6,7])
        self.assertEqual([x["y_mod256"] for x in slots[-3:]],[91,115,139])
        self.assertEqual([x["x_signed9"] for x in slots[-3:]],[200,200,200])
        self.assertEqual(len(report["per_frame_source_qualified_counts"]),21)
        for s in slots:
            self.assertEqual(s["large_sprite_bit"],0)
            self.assertEqual(s["OBJ_priority"],1)
        for key in ("original_5184_and_native_4032_same_CPU_or_PPU_frame_phase_proven",
                    "snapshot_rectangle_implies_effective_scanline_OBJ_owner",
                    "source_palette_priority_arithmetic_corrected_or_admitted",
                    "original_vs_native_sampled_raster_release_accepted"):
            self.assertFalse(report[key])
        self.assertEqual(report["result_medal_mismatch_mask_SHA256"],module.EXPECTED_MASK)
        self.assertEqual(len(module.OAM_ZIP),64)

if __name__=="__main__":
    unittest.main()
