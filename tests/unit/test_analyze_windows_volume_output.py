import copy
import unittest

from tools.analyze_windows_volume_output import volume_output_report


class WindowsVolumeOutputTests(unittest.TestCase):
    def fixtures(self):
        before = "UR_VOLUME_ACCEPTANCE START percent=100\n"
        adjust = (
            "UR_VOLUME_ACCEPTANCE START percent=100\n"
            "UR_PAUSE_OPTIONS OPENED\n"
            "UR_VOLUME SELECTED percent=95\n"
            "UR_VOLUME SELECTED percent=90\n"
            "UR_VOLUME SELECTED percent=95\n"
        )
        after = "UR_VOLUME_ACCEPTANCE START percent=95\n"
        pcm = {
            "schema_version": 1,
            "audio_origin": "sdl3-disk-playback",
            "device_format": "S16LE",
            "channels": 2, "sample_rate": 44100,
            "rms": 4000, "tail_rms": 6000,
            "tail_channel_rms": [5000, 7000],
            "duration_seconds": 16.5, "tail_duration_seconds": 1.0,
        }
        after_pcm = dict(pcm, rms=3800, tail_rms=5700,
                         tail_channel_rms=[4750, 6650])
        return before, adjust, after, pcm, after_pcm

    def test_persisted_framework_option_and_device_output_are_distinct(self):
        report = volume_output_report(*self.fixtures())
        self.assertEqual(report["framework_volume_percent"]["before"], 100)
        self.assertEqual(report["framework_volume_percent"]["fresh_process_loaded"], 95)
        self.assertEqual(report["framework_volume_percent"]["step_observations"],
                         [95, 90, 95])
        self.assertAlmostEqual(report["device_output"]["tail_rms_ratio"], 0.95)
        self.assertEqual(report["device_output"]["channel_tail_ratios"], [0.95, 0.95])
        self.assertIn("no assumed exact gain", report["limits"])

    def test_detects_failed_persistent_settings_and_unsupported_option_route(self):
        cases = list(self.fixtures())
        cases[2] = "UR_VOLUME_ACCEPTANCE START percent=100\n"
        with self.assertRaisesRegex(ValueError, "did not load"):
            volume_output_report(*cases)
        cases = list(self.fixtures())
        cases[1] = cases[1].replace("UR_PAUSE_OPTIONS OPENED", "UR_PAUSE_OPTIONS MISSING")
        with self.assertRaisesRegex(ValueError, "was not exercised"):
            volume_output_report(*cases)
        cases = list(self.fixtures())
        cases[1] += "UR_VOLUME_ACCEPTANCE ROW_NOT_REACHED\n"
        with self.assertRaisesRegex(ValueError, "was not reached"):
            volume_output_report(*cases)

    def test_rejects_invalid_pcm_metadata_and_nonfinite_levels(self):
        cases = list(self.fixtures())
        cases[3] = dict(cases[3], audio_origin="synthetic")
        with self.assertRaisesRegex(ValueError, "invalid native Windows SDL3"):
            volume_output_report(*cases)
        cases = list(self.fixtures())
        cases[4] = dict(cases[4], tail_rms=float("nan"))
        with self.assertRaisesRegex(ValueError, "invalid audible PCM"):
            volume_output_report(*cases)
        cases = list(self.fixtures())
        cases[4] = dict(cases[4], tail_channel_rms=[1234, 0])
        with self.assertRaisesRegex(ValueError, "missing audible left/right"):
            volume_output_report(*cases)
        cases = list(self.fixtures())
        cases[4] = dict(cases[4], sample_rate=32000)
        with self.assertRaisesRegex(ValueError, "invalid native Windows SDL3"):
            volume_output_report(*cases)

    def test_duplicate_logs_or_unexpected_adjustments_fail_closed(self):
        cases = list(self.fixtures())
        cases[0] += "UR_VOLUME_ACCEPTANCE START percent=100\n"
        with self.assertRaisesRegex(ValueError, "expected exactly 1"):
            volume_output_report(*cases)
        cases = list(self.fixtures())
        cases[1] = cases[1].replace(
            "UR_VOLUME SELECTED percent=95\n", "", 1
        )
        with self.assertRaisesRegex(ValueError, "exactly 3"):
            volume_output_report(*cases)
        cases = list(self.fixtures())
        cases[0] += "UR_VOLUME SELECTED percent=95\n"
        with self.assertRaisesRegex(ValueError, "expected exactly 0"):
            volume_output_report(*cases)


if __name__ == "__main__":
    unittest.main()
