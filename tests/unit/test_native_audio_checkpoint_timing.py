import unittest
import subprocess
import sys
import tempfile
from pathlib import Path

from tools.check_native_audio_checkpoint_timing import validate_log


class NativeAudioCaptureWindowTests(unittest.TestCase):
    def test_proves_thirty_guest_frames_on_either_side_of_boundary(self):
        text = (
            "script f=506 dump main-menu-ready ok\n"
            "script f=536 dump main-menu-ready-audio-post ok\n"
        )
        result = validate_log(text, "main-menu-ready")
        self.assertEqual(result["guest_frame_at_checkpoint"], 506)
        self.assertEqual(result["guest_frame_at_post_capture"], 536)
        self.assertEqual(result["guest_frames_after_checkpoint"], 30)

    def test_mismatched_frame_distance_rejected(self):
        text = (
            "script f=1044 dump race-entered ok\n"
            "script f=1069 dump race-entered-audio-post ok\n"
        )
        with self.assertRaisesRegex(ValueError, "waited 25 frames"):
            validate_log(text, "race-entered")

    def test_wrong_or_missing_marker_cannot_silently_pass(self):
        log = "script f=829 dump now-playing-ready ok\n"
        with self.assertRaisesRegex(ValueError, "found 0"):
            validate_log(log, "now-playing-ready")
        with self.assertRaisesRegex(ValueError, "unrecognized"):
            validate_log(log, "not-a-checkpoint")

    def test_duplicated_marker_rejected(self):
        line = "script f=506 dump main-menu-ready ok\n"
        log = line + line + "script f=536 dump main-menu-ready-audio-post ok\n"
        with self.assertRaisesRegex(ValueError, "found 2"):
            validate_log(log, "main-menu-ready")

    def test_shipping_python_module_entrypoint_resolves_repo_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "audio-native.log"
            log.write_text(
                "script f=506 dump main-menu-ready ok\n"
                "script f=536 dump main-menu-ready-audio-post ok\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable, "-m", "tools.check_native_audio_checkpoint_timing",
                    str(log), "main-menu-ready",
                ],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True, text=True, check=False, timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("NATIVE_AUDIO_WINDOW PASS", result.stdout)

    def test_substring_or_incomplete_marker_rejected(self):
        log = (
            "script f=506 dump main-menu-ready ok but not finished\n"
            "script f=536 dump main-menu-ready-audio-post ok\n"
        )
        with self.assertRaisesRegex(ValueError, "found 0"):
            validate_log(log, "main-menu-ready")


if __name__ == "__main__":
    unittest.main()
