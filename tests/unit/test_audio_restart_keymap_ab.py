import copy
import math
import unittest
from pathlib import Path

from tools.summarize_audio_restart_keymap_ab import reduce_keymap_trials

ROOT = Path(__file__).resolve().parents[2]


class RestartStartKeyMapABTests(unittest.TestCase):
    def fixture(self):
        envelope = {
            "audio_origin": "sdl3-disk-playback", "sample_rate": 44100,
            "window_ms": 100, "captured_tail_seconds": 8.0,
            "windows": [{"combined_rms": 1250.0} for _ in range(80)],
        }
        item = {
            "schema_version": 1,
            "authority": "packaged Windows real pause-menu Restart Win32 Down/Enter",
            "device_origin": "sdl3-disk-playback", "sample_rate": 44100,
            "restart_selected": 1, "host_resumed": 1,
            "guest_resumed_after_restart": 1, "restart_guest_resume_frame": 1125,
            "paused_one_second": {
                "frames": 44100, "combined_rms": 0.0,
                "channel_rms": [0.0, 0.0],
                "channel_nonzero_fraction": [0.0, 0.0],
            },
            "restarted_final_one_second": {
                "frames": 44100, "combined_rms": 1050,
                "channel_rms": [1000, 1100],
                "channel_nonzero_fraction": [0.8, 0.9],
            },
            "last_eight_seconds_envelope": envelope,
        }
        return {
            "start-return": [copy.deepcopy(item) for _ in range(3)],
            "start-unbound": [copy.deepcopy(item) for _ in range(3)],
        }

    def test_recovery_count_and_exact_literal_silence_length(self):
        trials = self.fixture()
        bad = trials["start-return"][0]
        bad["restarted_final_one_second"]["channel_rms"] = [0.0, 0.0]
        bad["restarted_final_one_second"]["channel_nonzero_fraction"] = [0, 0]
        for slot in bad["last_eight_seconds_envelope"]["windows"][21:]:
            slot["combined_rms"] = 0
        report = reduce_keymap_trials(trials)
        self.assertEqual(report["cohorts"]["start-return"]["audible_stereo_count"], 2)
        self.assertEqual(report["cohorts"]["start-unbound"]["audible_stereo_count"], 3)
        self.assertEqual(report["difference_in_audible_counts"], 1)
        self.assertEqual(report["cohorts"]["start-return"]["trials"][0][
            "trailing_literal_silence_100ms_buckets"], 59)

    def test_does_not_accept_harness_fabricated_or_missing_guest(self):
        trials = self.fixture()
        for mutation in (
            {"guest_resumed_after_restart": 0},
            {"authority": "synthetic"},
            {"device_origin": "synthetic"},
        ):
            bad = copy.deepcopy(trials)
            bad["start-unbound"][1].update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                reduce_keymap_trials(bad)
        with self.assertRaisesRegex(ValueError, "exactly 3"):
            reduce_keymap_trials({"start-return": trials["start-return"][:1],
                                  "start-unbound": trials["start-unbound"]})

    def test_silent_pause_and_both_audio_channels_are_required(self):
        trials = self.fixture()
        for field, value in (
            ("channel_rms", [900, math.nan]),
            ("channel_nonzero_fraction", [0.5, -0.2]),
        ):
            bad = copy.deepcopy(trials)
            bad["start-return"][0]["restarted_final_one_second"][field] = value
            with self.assertRaises(ValueError):
                reduce_keymap_trials(bad)
        bad = self.fixture()
        bad["start-unbound"][1]["paused_one_second"]["channel_rms"] = [0, 5]
        with self.assertRaisesRegex(ValueError, "incomplete"):
            reduce_keymap_trials(bad)

    def test_workflow_uses_disposable_keymap_and_never_alters_original_script(self):
        workflow = (ROOT / ".github/workflows/windows-modern-restart-audio-probe.yml"
                   ).read_text(encoding="utf-8")
        self.assertIn("start = None", workflow)
        self.assertIn("start = Return", workflow)
        self.assertIn("summarize_audio_restart_keymap_ab", workflow)
        self.assertIn("audio-modern-restart.script", workflow)
        self.assertIn("UR_PAUSE_OPEN_ACCEPTANCE=1", workflow)
        self.assertIn('rm -f "$PCM"', workflow)
        self.assertIn("restart-keymap-comparison.json", workflow)
        source = (ROOT / "tools/summarize_audio_restart_keymap_ab.py"
                  ).read_text(encoding="utf-8")
        self.assertNotIn("RtlReset(", source)
        self.assertNotIn("poke ", source)


if __name__ == "__main__":
    unittest.main()
