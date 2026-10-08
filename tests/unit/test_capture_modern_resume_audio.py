import struct
import tempfile
import unittest
from pathlib import Path

from tools.capture_modern_resume_audio import (
    read_stereo_window, verify_resume_audio, verify_resume_log,
)


class ModernResumeAudioTests(unittest.TestCase):
    LOG = ("script f=1044 dump race-entered ok\n"
           "UR_PAUSE_STATE paused=1 surface=1\n"
           "UR_PAUSE_ACCEPTANCE OPENED\n"
           "UR_PAUSE_STATE paused=0 surface=1\n")

    def fixture(self):
        paused = {"frames": 44100, "channel_rms": [0.0, 0.0],
                  "combined_rms": 0.0, "channel_nonzero_fraction": [0.0, 0.0]}
        resumed = {"frames": 44100, "channel_rms": [1400.0, 1100.0],
                   "combined_rms": 1257.0, "channel_nonzero_fraction": [0.9, 0.8]}
        return paused, resumed

    def test_real_race_then_frozen_host_then_resume_and_stereo_output(self):
        paused, resumed = self.fixture()
        report = verify_resume_audio(self.LOG, paused, resumed)
        self.assertEqual(report["resume_count"], 1)
        self.assertEqual(report["paused_one_second"]["combined_rms"], 0)
        self.assertEqual(report["device_origin"], "sdl3-disk-playback")

    def test_pause_and_resume_order_or_identity_cannot_be_spoofed(self):
        bad = [
            self.LOG.replace("UR_PAUSE_ACCEPTANCE OPENED\n", ""),
            self.LOG.replace("paused=0", "paused=1"),
            self.LOG.replace("paused=0 surface=1", "paused=0 surface=2"),
            self.LOG + "UR_PAUSE_STATE paused=0 surface=1\n",
            self.LOG + "UR_PAUSE_STATE paused=1 surface=1\n",
            self.LOG + "UR_PAUSE_QUIT REQUESTED\n",
            self.LOG + "UR_PAUSE_ACCEPTANCE OPENED\n",
        ]
        for log in bad:
            with self.subTest(log=log), self.assertRaises(ValueError):
                verify_resume_log(log)

    def test_no_frozen_silence_or_single_channel_resume_fails(self):
        paused, resumed = self.fixture()
        for mutation in (
            dict(paused, combined_rms=1),
            dict(paused, channel_nonzero_fraction=[0, 0.01]),
        ):
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "silent"):
                verify_resume_audio(self.LOG, mutation, resumed)
        for mutation in (
            dict(resumed, channel_rms=[1400, 0]),
            dict(resumed, channel_nonzero_fraction=[0.5, 0.0]),
            dict(resumed, combined_rms=float("nan")),
        ):
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "audible"):
                verify_resume_audio(self.LOG, paused, mutation)

    def test_stereo_window_samples_exact_boundary_not_full_capture(self):
        with tempfile.TemporaryDirectory() as temp:
            pcm = Path(temp) / "device.raw"
            pcm.write_bytes(struct.pack("<hh", 1500, -1200) * 44100 +
                            struct.pack("<hh", 0, 0) * 44100)
            audible = read_stereo_window(pcm, 44100 * 4)
            silence = read_stereo_window(pcm, 44100 * 8)
            self.assertEqual(audible["channel_rms"], [1500.0, 1200.0])
            self.assertEqual(silence["channel_rms"], [0.0, 0.0])
            with self.assertRaises(ValueError):
                read_stereo_window(pcm, 44100 * 8 + 1)

    def test_probe_leaves_guest_and_audio_runtime_untouched(self):
        tool = (Path(__file__).resolve().parents[2] / "tools" /
                "capture_modern_resume_audio.py").read_text(encoding="utf-8")
        self.assertIn("PostMessageW", tool)
        self.assertIn("PAUSE_OPEN", tool)
        self.assertIn("sdl3-disk-playback", tool)
        self.assertNotIn("poke 0", tool)
        self.assertNotIn("RtlSet", tool)


if __name__ == "__main__":
    unittest.main()
