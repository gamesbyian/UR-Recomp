"""ROM-free future chromatic-probe model diagnostics, not raster parity."""
import hashlib
from io import BytesIO
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import qa08_probe_robustness as qa08
from qa08_probe_robustness import expand,predict,choose_probe,genuine_scale_compatibility

class ChromaticProbeModelTest(unittest.TestCase):
    def test_stable_model_has_twelve_distinct_exact_predictions(self):
        p=predict((5,13,22))
        self.assertEqual(len(p),12)
        self.assertEqual(len(set(p.values())),12)

    def test_grayscale_model_is_not_chromatic_evidence(self):
        self.assertLess(len(set(predict((5,5,5)).values())),12)

    def test_selects_future_probe_without_claiming_observation(self):
        p=choose_probe()
        self.assertEqual(p['distinct_exact_predictions'],12)
        self.assertGreaterEqual(p['minimum_pairwise_L1'],3)
        self.assertTrue(p['plus_minus_one_measurement_cannot_uniquely_identify_scaling'])
        self.assertFalse(p['same_epoch_ppu_proven'])
        self.assertEqual(p['release_gate_credit'],0)

    def test_rejects_invalid_rgb5_inputs(self):
        for invalid in (-1,32,True,3.5):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                expand(invalid)
        for invalid in ((0,0,32),(3,3),[3,4,5]):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                predict(invalid)

    def test_unpinned_archive_never_enters_genuine_evidence(self):
        with self.assertRaisesRegex(ValueError,'unauthenticated'):
            genuine_scale_compatibility(Path(__file__))

class SourceTripletAdmissionRegression(unittest.TestCase):
    """Fresh synthetic controls for archived H27 QA08 parser review evidence.

    These source-stage admission checks are not renderer, hardware, chromatic
    pixel, or release-acceptance evidence.
    """

    @staticmethod
    def _rows():
        rows = []
        for x in range(88):
            ident = f"frame=5176 x={x} logical_y=41 ppu_line=42"
            rows.extend((
                f"UR_QA08_LATE_PPU_SOURCE {ident} sub=0 selected_rgb555=4a52",
                f"UR_QA08_LATE_PPU_SOURCE {ident} sub=1 selected_rgb555=39ce",
                f"UR_QA08_LATE_PPU_FINAL {ident} RGB8=138,138,138",
            ))
        return rows

    @staticmethod
    def _admit(rows):
        target = BytesIO()
        with ZipFile(target, "w") as archive:
            archive.writestr("on-source.log", "\n".join(rows) + "\n")
        original_bytes = target.getvalue()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "synthetic-qa08-source.zip"
            path.write_bytes(original_bytes)
            with patch.object(qa08, "AUTHENTIC_SHA256",
                              hashlib.sha256(original_bytes).hexdigest()):
                return qa08.genuine_scale_compatibility(path)

    def test_complete_88_consecutive_triplets_admit_without_gate_credit(self):
        result = self._admit(self._rows())
        self.assertEqual(result["source_triplets"], 88)
        self.assertFalse(result["chromatic_source_observed"])

    def test_second_source_colour_is_required_and_range_checked(self):
        for replacement in ("", " selected_rgb555=ffff"):
            with self.subTest(replacement=replacement):
                rows = self._rows()
                rows[1] = rows[1].replace(" selected_rgb555=39ce",
                                          replacement)
                with self.assertRaisesRegex(
                        ValueError, "missing QA08|malformed QA08 source RGB555"):
                    self._admit(rows)

    def test_missing_ppu_line_on_every_stage_is_not_valid_provenance(self):
        rows = [row.replace(" ppu_line=42", "") for row in self._rows()]
        with self.assertRaisesRegex(ValueError, "missing QA08"):
            self._admit(rows)

    def test_nonnumeric_frames_are_rejected_before_correspondence(self):
        rows = [row.replace("frame=5176", "frame=bogus")
                for row in self._rows()]
        with self.assertRaisesRegex(ValueError, "invalid QA08 source stage coordinate"):
            self._admit(rows)


if __name__=='__main__':unittest.main()
