"""CLI publication boundary: failed live post-WAV verification cannot leave a final WAV."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa01_live_kon_pcm as live


class LivePublicationTests(unittest.TestCase):
    def exercise(self, mode: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executable = root / "native.exe"
            executable.write_bytes(b"source-bound-executable-placeholder")
            final = root / "final.wav"
            receipt = root / "receipt.json"
            payload = b"captured-stereo-pcm-placeholder"

            def watcher(_command_fn, *, wav_path, **_kwargs):
                self.assertNotEqual(wav_path, final)
                self.assertFalse(final.exists())
                wav_path.write_bytes(payload)
                if mode == "post_wav_failure":
                    raise ValueError("multiple voice-7 KON events inside PCM window")
                if mode == "destination_race":
                    final.write_bytes(b"FOREIGN")
                return {"kon_sample_index": 45000, "sample_frames": 2500,
                        "wav_sha256": hashlib.sha256(payload).hexdigest()}

            argv = ["qa01_live_kon_pcm.py", "--wav-out", str(final),
                    "--json-out", str(receipt), "--source-sha", "a" * 40,
                    "--native-executable", str(executable)]
            with patch.object(live, "connect", return_value=(Mock(), Mock())), \
                    patch.object(live, "watch_first_kon", side_effect=watcher), \
                    patch.object(sys, "argv", argv):
                if mode == "success":
                    self.assertEqual(live.main(), 0)
                else:
                    with self.assertRaisesRegex(ValueError,
                                                "multiple voice-7 KON|refusing to replace WAV"):
                        live.main()

            self.assertFalse(list(root.glob(".qa01-live-*")),
                             "attempt staging must be cleaned on success and failure")
            if mode == "success":
                self.assertEqual(final.read_bytes(), payload)
                report = json.loads(receipt.read_text(encoding="utf-8"))
                self.assertEqual(report["wav_sha256"], hashlib.sha256(payload).hexdigest())
                self.assertEqual(report["native_executable_sha256"],
                                 hashlib.sha256(executable.read_bytes()).hexdigest())
            elif mode == "destination_race":
                self.assertEqual(final.read_bytes(), b"FOREIGN")
                self.assertFalse(receipt.exists())
            else:
                self.assertFalse(final.exists())
                self.assertFalse(receipt.exists())

    def test_post_wav_rejection_leaves_no_final_wav(self):
        self.exercise("post_wav_failure")

    def test_final_publication_preserves_foreign_race_winner(self):
        self.exercise("destination_race")

    def test_success_publishes_wav_and_receipt(self):
        self.exercise("success")


class ReceiptParentBeforeCaptureTests(unittest.TestCase):
    def test_unwritable_receipt_parent_refused_before_debug_connection(self):
        import qa01_native_pcm_at_kon as offline

        for module in (offline, live):
            with self.subTest(module=module.__name__), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                executable = root / "native.exe"
                executable.write_bytes(b"synthetic")
                blocked = root / "foreign-file"
                blocked.write_bytes(b"FOREIGN")
                wav = root / "candidate.wav"
                argv = [module.__name__ + ".py", "--wav-out", str(wav),
                        "--json-out", str(blocked / "receipt.json"),
                        "--source-sha", "a" * 40,
                        "--native-executable", str(executable)]
                if module is offline:
                    argv += ["--kon-sample-index", "40000"]
                with patch.object(sys, "argv", argv), patch.object(module, "connect") as connect:
                    with self.assertRaises(SystemExit) as cm:
                        module.main()
                    self.assertEqual(cm.exception.code, 2)
                    connect.assert_not_called()
                self.assertFalse(wav.exists())
                self.assertEqual(blocked.read_bytes(), b"FOREIGN")



class NativeExecutableSnapshotTests(unittest.TestCase):
    def test_unreadable_binary_refused_before_connect_for_both_routes(self):
        import qa01_native_pcm_at_kon as offline

        for module in (offline, live):
            with self.subTest(route=module.__name__), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                executable = root / "native.exe"
                executable.write_bytes(b"binary-that-will-be-unreadable")
                wav = root / "candidate.wav"
                receipt = root / "receipt.json"
                argv = [module.__name__ + ".py", "--wav-out", str(wav),
                        "--json-out", str(receipt), "--source-sha", "a" * 40,
                        "--native-executable", str(executable)]
                if module is offline:
                    argv += ["--kon-sample-index", "40000"]
                with patch.object(sys, "argv", argv), \
                        patch.object(module, "connect") as connect, \
                        patch.object(Path, "read_bytes",
                                     side_effect=PermissionError("synthetic unreadable binary")):
                    with self.assertRaises(SystemExit) as caught:
                        module.main()
                    self.assertEqual(caught.exception.code, 2)
                    connect.assert_not_called()
                self.assertFalse(wav.exists())
                self.assertFalse(receipt.exists())

    def test_live_binary_disappearance_after_snapshot_preserves_pre_capture_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executable = root / "native.exe"
            executable.write_bytes(b"pre-capture-binary")
            expected = hashlib.sha256(executable.read_bytes()).hexdigest()
            wav = root / "candidate.wav"
            receipt = root / "receipt.json"
            payload = b"captured-stereo-pcm-placeholder"

            def watcher(_command_fn, *, wav_path, **_kwargs):
                wav_path.write_bytes(payload)
                executable.unlink()
                return {"kon_sample_index": 45000, "sample_frames": 2500,
                        "wav_sha256": hashlib.sha256(payload).hexdigest()}

            argv = ["qa01_live_kon_pcm.py", "--wav-out", str(wav),
                    "--json-out", str(receipt), "--source-sha", "a" * 40,
                    "--native-executable", str(executable)]
            with patch.object(sys, "argv", argv), \
                    patch.object(live, "connect", return_value=(Mock(), Mock())), \
                    patch.object(live, "watch_first_kon", side_effect=watcher):
                self.assertEqual(live.main(), 0)
            self.assertEqual(wav.read_bytes(), payload)
            report = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(report["native_executable_sha256"], expected)
            self.assertFalse(report["source_to_binary_identity_independently_verified"])


if __name__ == "__main__":
    unittest.main()
