import copy
import unittest
from pathlib import Path

from tools.check_modern_host_pause_audio import check_host_pause_audio


class ModernHostPauseSilenceTests(unittest.TestCase):
    def fixture(self):
        log = (
            "script f=1044 dump race-entered ok\n"
            "UR_PAUSE_STATE paused=1 surface=1\n"
            "UR_PAUSE_ACCEPTANCE OPENED\n"
        )
        audio = {
            "schema_version": 1, "audio_origin": "sdl3-disk-playback",
            "device_format": "S16LE", "channels": 2, "sample_rate": 44100,
            "duration_seconds": 22.38, "rms": 3009.72,
            "nonzero_fraction": 0.6362, "tail_pcm_frames": 44100,
            "tail_duration_seconds": 1.0, "tail_rms": 0.0,
            "tail_nonzero_fraction": 0.0, "tail_channel_rms": [0.0, 0.0],
            "tail_peak": 0,
        }
        envelope = {
            "schema_version": 1, "audio_origin": "sdl3-disk-playback",
            "device_format": "S16LE", "channels": 2, "sample_rate": 44100,
            "window_ms": 100, "captured_tail_seconds": 3.0,
            "windows": [
                {
                    "frames": 4410, "combined_rms": 0.0,
                    "rms": [0.0, 0.0], "peak": [0, 0],
                    "zero_fraction": [1.0, 1.0],
                }
                for _ in range(30)
            ],
        }
        return log, audio, envelope

    def test_real_pause_after_audible_race_measures_three_seconds_silence(self):
        result = check_host_pause_audio(*self.fixture())
        self.assertEqual(result["host_paused"], 1)
        self.assertEqual(result["guest_race_entered_frame"], 1044)
        self.assertEqual(result["last_three_seconds_silent_buckets"], 30)
        self.assertEqual(result["last_second_rms"], 0)
        self.assertGreater(result["pre_pause_whole_capture_rms"], 50)

    def test_never_audible_capture_cannot_vacuously_pass(self):
        log, audio, envelope = self.fixture()
        for mutation in (
            dict(audio, rms=0),
            dict(audio, nonzero_fraction=0),
            dict(audio, duration_seconds=5),
            dict(audio, audio_origin="fake"),
        ):
            with self.subTest(mutation=mutation):
                with self.assertRaisesRegex(ValueError, "playback|audible"):
                    check_host_pause_audio(log, mutation, envelope)

    def test_weak_tail_and_single_lingering_audio_bucket_rejected(self):
        log, audio, envelope = self.fixture()
        with self.assertRaisesRegex(ValueError, "silent SDL device tail"):
            check_host_pause_audio(log, dict(audio, tail_rms=1.0), envelope)
        with self.assertRaisesRegex(ValueError, "silent SDL device tail"):
            check_host_pause_audio(log, dict(audio, tail_channel_rms=[0, 1]), envelope)
        corrupt = copy.deepcopy(envelope)
        corrupt["windows"][18]["combined_rms"] = 0.001
        with self.assertRaisesRegex(ValueError, "envelope bucket 18"):
            check_host_pause_audio(log, audio, corrupt)
        corrupt = copy.deepcopy(envelope)
        corrupt["windows"][29]["zero_fraction"] = [1.0, 0.9]
        with self.assertRaisesRegex(ValueError, "envelope bucket 29"):
            check_host_pause_audio(log, audio, corrupt)

    def test_missing_pause_provenance_or_incomplete_envelope_fails(self):
        log, audio, envelope = self.fixture()
        with self.assertRaisesRegex(ValueError, "paused=1"):
            check_host_pause_audio(log.replace("paused=1", "paused=0"), audio, envelope)
        bad = copy.deepcopy(envelope)
        bad["windows"].pop()
        with self.assertRaisesRegex(ValueError, "complete SDL device envelope"):
            check_host_pause_audio(log, audio, bad)
        bad = copy.deepcopy(envelope)
        bad["audio_origin"] = "fabricated"
        with self.assertRaisesRegex(ValueError, "complete SDL device envelope"):
            check_host_pause_audio(log, audio, bad)

    def test_shipping_audio_workflow_enforces_silence_from_real_pause(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / ".github/workflows/windows-native-audio-output.yml").read_text()
        self.assertIn("tools.check_modern_host_pause_audio", workflow)
        self.assertIn("UR_PAUSE_OPEN_ACCEPTANCE=1", workflow)
        self.assertIn("audio-modern-host-pause-silence.json", workflow)
        self.assertIn("tools/capture_modern_paused_audio.py", workflow)
        self.assertNotIn("poke ", (
            root / "tools/check_modern_host_pause_audio.py"
        ).read_text())


if __name__ == "__main__":
    unittest.main()
