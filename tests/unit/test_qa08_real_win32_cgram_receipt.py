"""ROM-free negative-gate guard for the real October 20 Windows source receipt.

The historical source artifact itself stays off Git. This test conserves
the compact source-authenticated receipt and explicitly prevents accidental
original/native admission from a same-current-epoch CRC equality.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "analysis/data/qa08-current-epoch-effective-ppu-unadmitted-20261020.json"


class QAA08ActualWin32UnadmittedSource(unittest.TestCase):
    def test_two_actual_pe_cohorts_and_guest_crc_provenance(self):
        d = json.loads(RECEIPT.read_text(encoding="utf-8"))
        self.assertEqual(d["workflow_run_id"], 39350709648)
        self.assertEqual(d["artifact_id"], 12233560894)
        self.assertEqual(d["artifact_zip_sha256"],
                         "b4dd0417d1e9f158ac6abf798251a895ac256488f2218805231b2b21f4e0430c")
        self.assertEqual(d["on_source_log_sha256"],
                         "9c4183debe10aa01dce25b87e7a5c9c9aed7747f3e411e06d8a5d4fc036cf080")
        self.assertNotEqual(d["real_windows_off_PE_sha256"],
                            d["real_windows_on_PE_sha256"])
        self.assertTrue(d["on_off_complete_guest_CRC_equality"])
        self.assertEqual(d["actual_full_guest_frames_ON"], 5484)
        self.assertEqual(d["actual_full_guest_frames_OFF"], 5484)
        self.assertEqual(d["actual_guest_CRC_SHA256_ON_OFF"],
                         "61826faa8a7c09c91a6013b5aabc5c3f1bd794d960396c76ce62fa34f7968bf8")
        self.assertEqual(d["archived_RF017_guest_CRC_sha256"],
                         "b735b0183b296ce32db009b282fab18bc9f9cf26668c02231373e9740184c568")
        self.assertFalse(d["historical_RF017_guest_equality"])
        self.assertFalse(d["same_original_native_guest_epoch_proven"])
        self.assertFalse(d["original_Snes9x_PPU_beam_equivalence_proven"])
        self.assertFalse(d["ON_OFF_full_P7_noninterference_proven"])
        self.assertFalse(d["QA08_QA10_release_accepted"])
        self.assertEqual(d["corrected_raster_pixels"],0)

    def test_actual_eight_CGRAM_consumers_not_guessed_indices(self):
        d = json.loads(RECEIPT.read_text(encoding="utf-8"))
        rows = d["genuine_observed_guest_5184_pixel_samples"]
        expected = {
            (70,58):("6c","56b5","4a52",20,17),
            (202,182):("6c","56b5","4a52",20,17),
            (84,77):("6f","4210","56b5",15,20),
            (175,145):("6f","4210","56b5",15,20),
            (53,41):("6e","4631","4210",16,15),
            (187,160):("6e","4631","4210",16,15),
            (65,52):("6d","4a52","4631",17,16),
            (190,161):("6d","4a52","4631",17,16),
        }
        self.assertEqual(len(rows),8)
        self.assertEqual(d["actual_renderer"],"legacy")
        for row in rows:
            xy=tuple(row["xy"])
            self.assertIn(xy,expected)
            idx,prev,current,old5,new5=expected[xy]
            self.assertEqual(row["cgram_index"],idx)
            self.assertEqual(row["original_2014_CGRAM_word"],prev)
            self.assertEqual(row["actual_native_PPU_CGRAM_word"],current)
            self.assertEqual(row["source_original_RGB5"],[old5]*3)
            self.assertEqual(row["actual_native_RGB5"],[new5]*3)
            self.assertEqual(row["ppu_layer"],0)
            self.assertEqual(row["ppu_inidisp"],"0e")
            self.assertFalse(row["ppu_directcolor"])
            self.assertFalse(row["host_OBJ_override"])
            self.assertTrue(row["consistent_with_prior_genuine_gray_error_class"])

    def test_actual_temporal_palette_transition_is_sampled_not_global_fix(self):
        d=json.loads(RECEIPT.read_text(encoding="utf-8"))
        states=d["per_guest_palette_6c_to_6f"]
        self.assertEqual([x["guest"] for x in states],list(range(5176,5187)))
        old=["56b5","4a52","4631","4210"]
        rotated=["4a52","4631","4210","56b5"]
        self.assertEqual(states[0]["values"],["4210","56b5","4a52","4631"])
        for row in states[1:8]:
            self.assertEqual(row["values"],old)
        for row in states[8:]:
            self.assertEqual(row["values"],rotated)
        self.assertEqual((d["source_records"],d["final_records"]),(176,88))
        self.assertFalse(d["guest_CPU_timing_root_cause_proven"])
        self.assertFalse(d["source_recolour_or_global_shift_authorized"])


if __name__ == "__main__":
    unittest.main()
