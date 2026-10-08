import copy
import math
import unittest
from pathlib import Path

from tools.check_native_audio_device_rate import check_rate

ROOT = Path(__file__).resolve().parents[2]


class NativeWindowsDeviceRateTests(unittest.TestCase):
    @staticmethod
    def fixture():
        output = {
            "schema_version": 1, "audio_origin": "sdl3-disk-playback",
            "device_format": "S16LE", "channels": 2, "sample_rate": 48000,
            "tail_pcm_frames": 48000, "tail_duration_seconds": 1.0,
            "tail_channel_rms": [4500.0, 5200.0],
            "duration_seconds": 18.5,
        }
        queue = {
            "schema_version": 1, "audio_origin": "snesrecomp-production-audio-stats",
            "snapshots": 12,
            "post_startup_deltas": {
                "dropped_audible": 0, "underflows": 0, "missing_frames": 0,
            },
        }
        return output, queue

    def test_real_48k_stereo_with_release_queue_passes(self):
        output, queue = self.fixture()
        report = check_rate(output, queue)
        self.assertEqual(report["device_rate_hz"], 48000)
        self.assertEqual(report["last_one_second_channel_rms"], [4500, 5200])
        self.assertEqual(report["release_audio_queue_post_startup_loss"], 0)

    def test_fake_negotiation_or_silent_output_fails(self):
        output, queue = self.fixture()
        for key, value in [
            ("sample_rate", 44100),
            ("tail_pcm_frames", 44100),
            ("channels", 1),
            ("audio_origin", "injected-pcm"),
            ("tail_channel_rms", [0.0, 5200.0]),
            ("tail_channel_rms", [4500.0, math.nan]),
            ("duration_seconds", 0.2),
        ]:
            bad = copy.deepcopy(output)
            bad[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                check_rate(bad, queue)

    def test_production_starvation_cannot_be_hidden_by_loud_tail(self):
        output, queue = self.fixture()
        for key in ("dropped_audible", "underflows", "missing_frames"):
            bad = copy.deepcopy(queue)
            bad["post_startup_deltas"][key] = 1
            with self.subTest(counter=key), self.assertRaisesRegex(ValueError, "loss"):
                check_rate(output, bad)
        bad = copy.deepcopy(queue)
        bad["snapshots"] = 2
        with self.assertRaisesRegex(ValueError, "snapshots"):
            check_rate(output, bad)

    def test_44k_control_is_explicit_not_accidental_rate_fallback(self):
        output, queue = self.fixture()
        output["sample_rate"] = 44100
        output["tail_pcm_frames"] = 44100
        self.assertEqual(check_rate(output, queue, requested_rate=44100)["device_rate_hz"], 44100)
        with self.assertRaisesRegex(ValueError, "unsupported"):
            check_rate(output, queue, requested_rate=32040)

    def test_real_workflow_proves_canonical_guest_and_deletes_raw_samples(self):
        workflow = (
            ROOT / ".github/workflows/windows-native-audio-output.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("check_native_audio_device_rate.py", workflow)
        self.assertIn("SDL_AUDIO_FREQUENCY=48000", workflow)
        # SDL disk's environment variable does not override SNESRecomp's
        # own audio open specification. A real Windows run exposed this:
        # the device remained at 44100 until the framework config changed.
        self.assertIn("AudioFreq = 48000", workflow)
        self.assertIn('>"$ROOT/config.ini"', workflow)
        self.assertIn("audio-rate-48000-proof.json", workflow)
        self.assertIn('rm -f "$PCM"', workflow)
        self.assertIn("tests/input/reach-first-race.script", workflow)


if __name__ == "__main__":
    unittest.main()
