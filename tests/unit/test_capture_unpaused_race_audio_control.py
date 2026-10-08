import unittest
from pathlib import Path

from tools.capture_unpaused_race_audio_control import (
    verify_unpaused_control_log,
)

ROOT = Path(__file__).resolve().parents[2]


class UnpausedRaceAudioControlTests(unittest.TestCase):
    LOG = (
        "script f=1044 dump race-entered ok\n"
        "script f=1244 dump audio-restart-guest ok\n"
    )

    def test_original_race_continues_without_any_host_pause(self):
        result = verify_unpaused_control_log(self.LOG)
        self.assertEqual(result["race_entered_frame"], 1044)
        self.assertEqual(result["later_unpaused_frame"], 1244)

    def test_control_does_not_accept_fake_or_stalled_progress(self):
        for bad in (
            self.LOG + "UR_PAUSE_STATE paused=1 surface=1\n",
            self.LOG + "UR_PAUSE_ACCEPTANCE OPENED\n",
            self.LOG.replace("script f=1244", "script f=1045"),
            self.LOG.replace("script f=1244", "script f=0"),
            self.LOG.replace("race-entered", "unknown"),
            self.LOG.replace("audio-restart-guest", "another"),
            self.LOG + "script f=1244 dump audio-restart-guest ok\n",
        ):
            with self.subTest(log=bad), self.assertRaises(ValueError):
                verify_unpaused_control_log(bad)

    def test_same_unmodified_guest_route_used_for_restart_and_control(self):
        script = ROOT / "tests/input/audio-modern-restart.script"
        self.assertTrue(script.read_text().endswith("wait 3600\n"))
        tool = (ROOT / "tools/capture_unpaused_race_audio_control.py").read_text()
        flow = (ROOT / ".github/workflows/windows-modern-restart-audio-probe.yml").read_text()
        self.assertIn("tools.capture_unpaused_race_audio_control", flow)
        self.assertIn("if: always()", flow)
        self.assertIn("min_tail_rms=0", tool)
        self.assertNotIn("poke ", tool)
        self.assertNotIn("RtlReset(", tool)


if __name__ == "__main__":
    unittest.main()
