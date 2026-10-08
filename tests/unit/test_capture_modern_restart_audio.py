import unittest
from pathlib import Path

from tools.capture_modern_restart_audio import verify_restart_log

ROOT = Path(__file__).resolve().parents[2]


class ModernRestartAudioTests(unittest.TestCase):
    LOG = (
        "script f=1044 dump race-entered ok\n"
        "UR_PAUSE_STATE paused=1 surface=0\n"
        "UR_PAUSE_ACCEPTANCE OPENED\n"
        "UR_PAUSE_SELECTION selected=1 restart=1\n"
        "UR_PAUSE_STATE paused=0 surface=0\n"
        "script f=220 dump audio-restart-guest ok\n"
    )

    def test_real_restart_requires_available_selection_unpause_and_guest_advance(self):
        evidence = verify_restart_log(self.LOG)
        self.assertEqual(evidence["source_race_guest_frame"], 1044)
        self.assertEqual(evidence["restart_guest_resume_frame"], 220)
        self.assertEqual(evidence["pause_surface"], 0)
        self.assertEqual(evidence["restart_selected"], 1)
        self.assertEqual(evidence["guest_resumed_after_restart"], 1)

    def test_unpause_without_actual_restart_selection_fails(self):
        for bad in (
            self.LOG.replace("selected=1", "selected=0"),
            self.LOG.replace("restart=1", "restart=0"),
            self.LOG.replace("UR_PAUSE_SELECTION selected=1 restart=1\n", ""),
            self.LOG.replace("UR_PAUSE_STATE paused=0", "UR_PAUSE_STATE paused=1"),
            self.LOG.replace("paused=0 surface=0", "paused=0 surface=2"),
            self.LOG.replace("dump audio-restart-guest ok", "dump replay-only ok"),
            self.LOG.replace("script f=220", "script f=0"),
            self.LOG + "UR_PAUSE_SELECTION selected=1 restart=1\n",
            self.LOG + "UR_PAUSE_QUIT REQUESTED\n",
        ):
            with self.subTest(log=bad), self.assertRaises(ValueError):
                verify_restart_log(bad)

    def test_guest_cannot_resume_before_win32_restart_activation(self):
        bad = self.LOG.replace(
            "UR_PAUSE_SELECTION selected=1 restart=1\n"
            "UR_PAUSE_STATE paused=0 surface=0\n",
            "UR_PAUSE_STATE paused=0 surface=0\n"
            "UR_PAUSE_SELECTION selected=1 restart=1\n")
        with self.assertRaisesRegex(ValueError, "out of order"):
            verify_restart_log(bad)

    def test_audio_script_follows_existing_first_race_without_guest_pokes(self):
        canonical = (ROOT / "tests/input/modern-focus-pause.script").read_text()
        source = (ROOT / "tests/input/audio-modern-restart.script").read_text()
        self.assertTrue(canonical.endswith("wait 3600\n"))
        self.assertTrue(source.startswith(canonical[:-len("wait 3600\n")]))
        self.assertIn("dump audio-restart-guest", source)
        self.assertTrue(source.endswith("wait 3600\n"))
        self.assertNotIn("poke ", source)

    def test_real_native_keyboard_and_postclose_device_path_are_used(self):
        source = (ROOT / "tools/capture_modern_restart_audio.py").read_text()
        for expected in ("_find_game_window", "PostMessageW",
                         "SELECTED_RESTART", "read_stereo_window",
                         "_stop_entire_tree", "verify_resume_audio"):
            self.assertIn(expected, source)
        self.assertNotIn("RtlReset(", source)


if __name__ == "__main__":
    unittest.main()
