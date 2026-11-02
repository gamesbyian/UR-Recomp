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



class AtomicReceiptPublicationTests(unittest.TestCase):
    def test_complete_receipt_visible_only_after_staging_fsync(self):
        import qa01_native_pcm_at_kon as offline
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            destination = root / "receipt.json"
            payload = json.dumps({"wav_sha256": "a" * 64}, sort_keys=True) + "\n"
            original_link = offline.os.link
            def verify_before_link(staged, target, **kwargs):
                self.assertEqual(target, destination.name)
                self.assertEqual(kwargs.get("src_dir_fd"), kwargs.get("dst_dir_fd"))
                self.assertFalse(destination.exists())
                fd = offline.os.open(staged, offline.os.O_RDONLY,
                                     dir_fd=kwargs["src_dir_fd"])
                with offline.os.fdopen(fd, "r", encoding="utf-8") as snapshot:
                    self.assertEqual(snapshot.read(), payload)
                return original_link(staged, target, **kwargs)
            with patch.object(offline.os, "link", side_effect=verify_before_link):
                offline.publish_receipt_no_replace(destination, payload)
            self.assertEqual(destination.read_text(encoding="utf-8"), payload)
            self.assertFalse(list(root.glob(".qa01-receipt-stage-*")))

    def test_existing_and_dangling_symlink_receipts_are_preserved(self):
        import qa01_native_pcm_at_kon as offline
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            destination = root / "receipt.json"
            destination.write_bytes(b"FOREIGN")
            with self.assertRaises(FileExistsError):
                offline.publish_receipt_no_replace(destination, "{}\n")
            self.assertEqual(destination.read_bytes(), b"FOREIGN")
            destination.unlink()
            foreign = root / "not-yet-created.json"
            destination.symlink_to(foreign)
            with self.assertRaises(FileExistsError):
                offline.publish_receipt_no_replace(destination, "{}\n")
            self.assertTrue(destination.is_symlink())
            self.assertFalse(foreign.exists())
            self.assertFalse(list(root.glob(".qa01-receipt-stage-*")))

    def test_interrupted_staging_never_exposes_partial_receipt(self):
        import qa01_native_pcm_at_kon as offline
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            destination = root / "receipt.json"
            with patch.object(offline.os, "fsync", side_effect=OSError("incomplete staged write")):
                with self.assertRaises(OSError):
                    offline.publish_receipt_no_replace(destination, "{}\n")
            self.assertFalse(destination.exists())
            self.assertFalse(list(root.glob(".qa01-receipt-stage-*")))


if __name__ == "__main__":
    unittest.main()
