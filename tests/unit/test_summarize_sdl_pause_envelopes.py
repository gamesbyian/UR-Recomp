import copy
import math
import unittest

from tools.summarize_sdl_pause_envelopes import PHASES, reduce_envelopes


def envelope(values, *, rate=8000):
    assert len(values) == 30
    windows = []
    for index, value in enumerate(values):
        windows.append({
            "start_seconds_before_end": round(3 - index * 0.1, 6),
            "end_seconds_before_end": round(2.9 - index * 0.1, 6),
            "frames": round(rate * 0.1),
            "rms": [value, value],
            "combined_rms": value,
            "peak": [0, 0] if value == 0 else [int(value), int(value)],
            "peak_adjacent_step": [0, 0] if value == 0 else [20, 30],
            "zero_fraction": [1, 1] if value == 0 else [0, 0],
        })
    return {
        "schema_version": 1,
        "audio_origin": "sdl3-disk-playback",
        "device_format": "S16LE",
        "channels": 2,
        "sample_rate": rate,
        "window_ms": 100,
        "captured_tail_seconds": 3,
        "windows": windows,
    }


class PauseEnvelopeShapeTests(unittest.TestCase):
    def fixtures(self):
        return {
            PHASES[0]: envelope([0] * 16 + [200] * 14),
            PHASES[1]: envelope([300] * 20 + [0] * 10),
            PHASES[2]: envelope([300] * 10 + [0] * 5 + [200] * 15),
        }

    def test_source_order_zero_runs_and_transient_maxima(self):
        result = reduce_envelopes(self.fixtures())
        self.assertEqual(result["schema_version"], 1)
        before, paused, resumed = (
            result["phases"][name] for name in PHASES
        )
        self.assertEqual(before["leading_silence_seconds"], 1.6)
        self.assertEqual(paused["trailing_silence_seconds"], 1.0)
        self.assertEqual(resumed["literal_silent_buckets"], [10, 11, 12, 13, 14])
        self.assertEqual(resumed["first_nonzero_bucket"], 0)
        self.assertEqual(resumed["last_nonzero_bucket"], 29)
        self.assertEqual(before["peak_adjacent_sample_step"], [20, 30])
        self.assertEqual(before["bucket_rms"][16], 200)

    def test_all_silent_is_valid_diagnostic_evidence(self):
        cases = self.fixtures()
        cases[PHASES[1]] = envelope([0] * 30)
        result = reduce_envelopes(cases)
        paused = result["phases"][PHASES[1]]
        self.assertEqual(paused["leading_silence_seconds"], 3)
        self.assertEqual(paused["trailing_silence_seconds"], 3)
        self.assertIsNone(paused["first_nonzero_bucket"])
        self.assertIsNone(paused["last_nonzero_bucket"])

    def test_missing_and_corrupted_provenance_fail_closed(self):
        cases = self.fixtures()
        del cases[PHASES[0]]
        with self.assertRaisesRegex(ValueError, "exactly three"):
            reduce_envelopes(cases)
        cases = self.fixtures()
        cases[PHASES[0]]["audio_origin"] = "synthesized"
        with self.assertRaisesRegex(ValueError, "untrusted PCM"):
            reduce_envelopes(cases)
        cases = self.fixtures()
        cases[PHASES[0]]["window_ms"] = 50
        with self.assertRaisesRegex(ValueError, "100 ms"):
            reduce_envelopes(cases)

    def test_zero_fraction_contradiction_and_nonfinite_rms_rejected(self):
        cases = self.fixtures()
        cases[PHASES[1]]["windows"][22]["zero_fraction"] = [0, 1]
        with self.assertRaisesRegex(ValueError, "contradictory"):
            reduce_envelopes(cases)
        cases = self.fixtures()
        cases[PHASES[2]]["windows"][0]["combined_rms"] = float("nan")
        with self.assertRaisesRegex(ValueError, "inconsistent combined"):
            reduce_envelopes(cases)
        cases = self.fixtures()
        cases[PHASES[1]]["windows"][0]["rms"] = [100, float("inf")]
        with self.assertRaisesRegex(ValueError, "invalid stereo"):
            reduce_envelopes(cases)

    def test_mistimed_buckets_and_missing_window_rejected(self):
        cases = self.fixtures()
        cases[PHASES[0]]["windows"][10]["start_seconds_before_end"] = 1.2
        with self.assertRaisesRegex(ValueError, "invalid device-relative"):
            reduce_envelopes(cases)
        cases = self.fixtures()
        cases[PHASES[0]]["windows"].pop()
        with self.assertRaisesRegex(ValueError, "incomplete bounded"):
            reduce_envelopes(cases)
        cases = self.fixtures()
        cases[PHASES[0]]["windows"][0]["peak_adjacent_step"] = [65536, 0]
        with self.assertRaisesRegex(ValueError, "invalid stereo"):
            reduce_envelopes(cases)


if __name__ == "__main__":
    unittest.main()
