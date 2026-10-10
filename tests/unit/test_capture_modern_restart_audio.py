import unittest
from pathlib import Path
from unittest.mock import patch

from tools.capture_modern_restart_audio import (
    verify_restart_log, validate_restart_audio, read_stereo_after_native_exit,
)

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
        self.assertFalse(any(line.lstrip().startswith("poke ") for line in source.splitlines()))


    def test_failed_recovery_retains_raw_free_bounded_capture_evidence(self):
        paused = {"frames": 44100, "channel_rms": [0, 0],
                  "combined_rms": 0, "channel_nonzero_fraction": [0, 0]}
        resumed = {"frames": 44100, "channel_rms": [0, 0],
                   "combined_rms": 0, "channel_nonzero_fraction": [0, 0]}
        report = {"paused_one_second": paused,
                  "restarted_final_one_second": resumed,
                  "last_eight_seconds_envelope": {"windows": []}}
        # A real restarted guest is insufficient to accept absent audio.
        with self.assertRaisesRegex(ValueError, "audible stereo"):
            validate_restart_audio(report, self.LOG)
        self.assertIn("last_eight_seconds_envelope", report)
        self.assertNotIn("recovery_confirmed", report)
        resumed = {"frames": 44100, "channel_rms": [1000, 1100],
                   "combined_rms": 1050, "channel_nonzero_fraction": [0.9, 0.8]}
        report["restarted_final_one_second"] = resumed
        verified = validate_restart_audio(report, self.LOG)
        self.assertTrue(verified["recovery_confirmed"])
        self.assertEqual(verified["restarted_final_one_second"], resumed)

    def test_bounded_postexit_file_unlock_recovers_but_no_audio_failures_hide(self):
        window = {"frames": 44100, "combined_rms": 320}
        # The OS may release the playback file only after the process tree
        # wrapper has terminated. This is a lock release, NOT a substituted
        # audio sample or a retry of any failed guest/audio invariant.
        with patch("tools.capture_modern_restart_audio.read_stereo_window",
                   side_effect=[PermissionError("SDL file open"),
                                PermissionError("SDL file open"), window]) as read:
            with patch("tools.capture_modern_restart_audio.time.sleep") as sleep:
                self.assertEqual(read_stereo_after_native_exit(
                    Path("capture.raw"), 176400), window)
                self.assertEqual(read.call_count, 3)
                self.assertEqual(sleep.call_count, 2)

        for failure in (FileNotFoundError("device file missing"),
                        ValueError("PCM truncated"),
                        RuntimeError("bad channel window")):
            with self.subTest(failure=str(failure)):
                with patch("tools.capture_modern_restart_audio.read_stereo_window",
                           side_effect=failure) as read:
                    with patch("tools.capture_modern_restart_audio.time.sleep") as sleep:
                        with self.assertRaises(type(failure)):
                            read_stereo_after_native_exit(Path("capture.raw"), 176400)
                        self.assertEqual(read.call_count, 1)
                        sleep.assert_not_called()

        with patch("tools.capture_modern_restart_audio.read_stereo_window",
                   side_effect=PermissionError("persistent device denial")) as read:
            with patch("tools.capture_modern_restart_audio.time.sleep") as sleep:
                with self.assertRaises(PermissionError):
                    read_stereo_after_native_exit(
                        Path("capture.raw"), 176400, unlock_timeout_seconds=0)
                self.assertEqual(read.call_count, 1)
                sleep.assert_not_called()
        with self.assertRaises(ValueError):
            read_stereo_after_native_exit(Path("capture.raw"), 176400,
                                          unlock_timeout_seconds=6)

    def test_real_native_keyboard_and_postclose_device_path_are_used(self):
        source = (ROOT / "tools/capture_modern_restart_audio.py").read_text()
        for expected in ("_find_game_window", "PostMessageW",
                         "SELECTED_RESTART", "read_stereo_window",
                         "_stop_entire_tree", "verify_resume_audio"):
            self.assertIn(expected, source)
        self.assertNotIn("RtlReset(", source)


if __name__ == "__main__":
    unittest.main()
