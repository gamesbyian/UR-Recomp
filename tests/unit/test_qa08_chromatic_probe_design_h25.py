"""ROM-free recovery regressions for the original H25 chromatic proposal."""
from hashlib import sha256
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa08_chromatic_discriminator as admission
from qa08_chromatic_probe_design import design, model_predictions, expand5


def fixture(chromatic=False, duplicate=False):
    lines = []
    for i in range(88):
        x = 1 if duplicate else i
        rgb5 = "59a5" if chromatic else "4a52"
        rgb8 = "138,139,140" if chromatic else "138,138,138"
        for sub in (0, 1):
            lines.append(f"UR_QA08_LATE_PPU_SOURCE frame=5176 x={x} logical_y=41 sub={sub} selected_rgb555={rgb5}")
        lines.append(f"UR_QA08_LATE_PPU_FINAL frame=5176 x={x} logical_y=41 RGB8={rgb8}")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("on-source.log", "\r\n".join(lines) + "\r\n")
    return buf.getvalue()


class H25ChromaticRecovery(unittest.TestCase):
    def test_twelve_future_predictions_are_distinct(self):
        p = model_predictions()
        self.assertEqual(len(p), 12)
        self.assertEqual(len(set(p.values())), 12)
        self.assertLess(len(set(model_predictions((5, 5, 5)).values())), 12)
        self.assertEqual(5 | (13 << 5) | (22 << 10), 0x59a5)

    def test_invalid_channel_shapes_rejected(self):
        for x in (-1, 32, True, False, 2.0, "5"):
            with self.subTest(x=x), self.assertRaises(ValueError):
                expand5(x)
        for x in ((5, 13), (True, 13, 22), (32, 13, 22), [5, 13, 22]):
            with self.subTest(x=x), self.assertRaises(ValueError):
                model_predictions(x)

    def classify(self, raw, *, error=None):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "source.zip"
            p.write_bytes(raw)
            with patch.object(admission, "ARCHIVE_SHA", sha256(raw).hexdigest()):
                if error:
                    with self.assertRaisesRegex(ValueError, error):
                        design(p)
                else:
                    return design(p)

    def test_authenticated_grayscale_proposes_only_unobserved_chromatic_witness(self):
        outcome = self.classify(fixture())
        self.assertEqual(outcome["candidate_rgb555_hex"], "59a5")
        self.assertEqual(outcome["observed_source_triplets"], 88)
        self.assertEqual(outcome["hypotheses_distinguished"], 12)
        self.assertFalse(outcome["chromatic_pixel_observed"])
        self.assertFalse(outcome["same_epoch_native_effective_ppu_proven"])
        self.assertEqual(outcome["release_gate_credit"], 0)

    def test_existing_chromatic_observation_demands_new_design(self):
        self.classify(fixture(chromatic=True), error="already exists")

    def test_duplicate_stage_coordinate_rejected(self):
        self.classify(fixture(duplicate=True), error="malformed")

    def test_unauthenticated_zip_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "wrong.zip"
            p.write_bytes(fixture())
            with self.assertRaisesRegex(ValueError, "SHA mismatch"):
                design(p)

    def test_incomplete_triplets_refused(self):
        self.classify(b"invalid", error="expected 264")


if __name__ == "__main__":
    unittest.main()
