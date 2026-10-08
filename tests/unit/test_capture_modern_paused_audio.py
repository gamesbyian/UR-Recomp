import tempfile
import unittest
from pathlib import Path

from tools.capture_modern_paused_audio import verify_modern_pause_log


class ModernHostPauseAudioTests(unittest.TestCase):
    def fixture(self):
        return (
            "script f=1043 dump race-entered ok\n"
            "UR_PAUSE_STATE paused=1 surface=1\n"
            "UR_PAUSE_ACCEPTANCE OPENED\n"
        )

    def test_host_owned_pause_after_guest_race_and_no_restart(self):
        report = verify_modern_pause_log(self.fixture())
        self.assertEqual(report["guest_race_entered_frame"], 1043)
        self.assertEqual(report["host_pause_state"], 1)
        self.assertEqual(report["event"], "UR_PAUSE_ACCEPTANCE OPENED")

    def test_guest_start_pause_cannot_masquerade_as_host_pause(self):
        for bad in (
            "script f=1043 dump race-entered ok\nUR_PAUSE_STATE paused=1 surface=1\n",
            "script f=1043 dump race-entered ok\nUR_PAUSE_ACCEPTANCE OPENED\n",
            "UR_PAUSE_STATE paused=1 surface=1\nUR_PAUSE_ACCEPTANCE OPENED\n",
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    verify_modern_pause_log(bad)

    def test_duplicate_out_of_order_and_resumed_captures_fail(self):
        cases = [
            self.fixture() + "UR_PAUSE_ACCEPTANCE OPENED\n",
            self.fixture() + "UR_PAUSE_STATE paused=1 surface=1\n",
            self.fixture().replace("UR_PAUSE_STATE paused=1 surface=1\n", "")
            + "UR_PAUSE_STATE paused=1 surface=1\n",
            self.fixture() + "UR_PAUSE_STATE paused=0 surface=1\n",
            self.fixture() + "UR_PAUSE_QUIT REQUESTED\n",
        ]
        for log in cases:
            with self.subTest(log=log):
                with self.assertRaises(ValueError):
                    verify_modern_pause_log(log)

    def test_acceptance_is_wired_to_production_host_and_disposable_pcm(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / ".github/workflows/windows-native-audio-output.yml").read_text()
        host = (root / "native/product/uniracers_modern_host.cpp").read_text()
        tool = (root / "tools/capture_modern_paused_audio.py").read_text()
        self.assertIn('std::getenv("UR_PAUSE_OPEN_ACCEPTANCE")', host)
        self.assertIn('product_diagnostic("UR_PAUSE_ACCEPTANCE OPENED")', host)
        self.assertIn("UR_PAUSE_STATE paused=%d", host)
        self.assertIn("UR_PAUSE_OPEN_ACCEPTANCE=1", workflow)
        self.assertIn("tools.capture_modern_paused_audio", workflow)
        self.assertIn("tools/analyze_sdl_audio_envelope.py", workflow)
        self.assertIn('rm -f "$PCM"', workflow)
        self.assertIn("taskkill.exe", tool)
        self.assertNotIn("poke ", tool)


if __name__ == "__main__":
    unittest.main()
