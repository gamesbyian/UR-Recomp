import copy
import unittest

from tools.analyze_audio_phase_matrix import CHECKPOINTS, phase_levels


class NativeAudioPhaseMatrixTests(unittest.TestCase):
    def fixtures(self):
        native = {
            key: {
                "schema_version": 1,
                "audio_origin": "sdl3-disk-playback",
                "device_format": "S16LE",
                "channels": 2,
                "tail_duration_seconds": 1.0,
                "tail_rms": rms,
                "tail_peak": peak,
            }
            for key, rms, peak in zip(
                CHECKPOINTS,
                (2100, 3900, 6800),
                (11000, 18500, 30000),
            )
        }
        reference = {
            "schema_version": 1,
            "engines": [
                {"engine": "snes9x", "checkpoints": {
                    key: {"rms": rms} for key, rms in zip(CHECKPOINTS, (2409, 4007, 6919))
                }},
                {"engine": "beetle", "checkpoints": {
                    key: {"rms": rms} for key, rms in zip(CHECKPOINTS, (2193, 3753, 6381))
                }},
            ],
        }
        return native, reference

    def test_relative_levels_and_reference_consensus(self):
        native, reference = self.fixtures()
        report = phase_levels(native, reference)
        self.assertTrue(report["reference_phase_order_consensus"])
        self.assertTrue(report["native_matches_reference_phase_order"])
        self.assertEqual(report["profiles"]["native-sdl-disk"]["relative_to_main_menu"]["main-menu-ready"], 1)
        self.assertAlmostEqual(report["profiles"]["native-sdl-disk"]["race_to_menu_rms_ratio"], 6800 / 2100, delta=1e-6)
        self.assertEqual(report["profiles"]["snes9x"]["rms_phase_order"], list(CHECKPOINTS))
        self.assertEqual(report["native_tail_peak"]["race-entered"], 30000)

    def test_native_order_difference_is_evidence_not_an_unjustified_failure(self):
        native, reference = self.fixtures()
        native["race-entered"]["tail_rms"] = 1000
        report = phase_levels(native, reference)
        self.assertTrue(report["reference_phase_order_consensus"])
        self.assertFalse(report["native_matches_reference_phase_order"])

    def test_native_evidence_must_be_complete_and_positive(self):
        native, reference = self.fixtures()
        del native["race-entered"]
        with self.assertRaisesRegex(ValueError, "exactly the three"):
            phase_levels(native, reference)
        native, reference = self.fixtures()
        native["now-playing-ready"]["tail_rms"] = float("nan")
        with self.assertRaisesRegex(ValueError, "positive and finite"):
            phase_levels(native, reference)
        native, reference = self.fixtures()
        native["main-menu-ready"]["tail_duration_seconds"] = 0.5
        with self.assertRaisesRegex(ValueError, "1-second"):
            phase_levels(native, reference)
        native, reference = self.fixtures()
        native["main-menu-ready"]["audio_origin"] = "synthetic"
        with self.assertRaisesRegex(ValueError, "invalid native"):
            phase_levels(native, reference)

    def test_reference_provenance_and_schema_must_be_consistent(self):
        native, reference = self.fixtures()
        reference["engines"] = reference["engines"][:1]
        with self.assertRaisesRegex(ValueError, "at least two"):
            phase_levels(native, reference)
        native, reference = self.fixtures()
        reference["engines"][1]["engine"] = "snes9x"
        with self.assertRaisesRegex(ValueError, "unique"):
            phase_levels(native, reference)
        native, reference = self.fixtures()
        del reference["engines"][1]["checkpoints"]["race-entered"]
        with self.assertRaisesRegex(ValueError, "canonical reference"):
            phase_levels(native, reference)


if __name__ == "__main__":
    unittest.main()
