"""Windows native audio_wav wire-path and JSON response regression controls."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path, PureWindowsPath

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_native_pcm_at_kon as pcm


class NativeWavWirePathTests(unittest.TestCase):
    def test_windows_drive_and_unc_paths_round_trip_native_json(self):
        for original, expected in (
            (r"C:\qa01\native\voice7.wav", "C:/qa01/native/voice7.wav"),
            (r"\\server\share\voice7.wav", "//server/share/voice7.wav"),
        ):
            with self.subTest(path=original):
                wire = pcm.wav_command_path(PureWindowsPath(original))
                self.assertEqual(wire, expected)
                # Pinned debug_server.c uses send_fmt with an unescaped %s.
                reply = '{"ok":true,"path":"' + wire + '","start":39500,"count":2500}'
                self.assertEqual(json.loads(reply)["path"], wire)

    def test_posix_path_remains_unchanged(self):
        self.assertEqual(pcm.wav_command_path(Path("/tmp/voice7.wav")),
                         "/tmp/voice7.wav")

    def test_unsafe_posix_paths_fail_before_wav_request(self):
        for name in ("/tmp/has\\backslash.wav", '/tmp/has"quote.wav',
                     "/tmp/has\x00nul.wav"):
            with self.subTest(path=repr(name)):
                with self.assertRaisesRegex(ValueError, "safely"):
                    pcm.wav_command_path(Path(name))


if __name__ == "__main__":
    unittest.main()
