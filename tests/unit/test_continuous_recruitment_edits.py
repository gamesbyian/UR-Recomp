"""Media editors must refuse unverified videos before invoking FFmpeg."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "continuous_editor", ROOT / "tools/showcase/build_continuous_recruitment_edits.py")
assert SPEC and SPEC.loader
editor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(editor)


class SourceContractTests(unittest.TestCase):
    def setup_sample(self, base: Path):
        clip = base / "ur-native-2p-clean-600f.mp4"
        clip.write_bytes(b"not-an-actual-video: fixture")
        manifest = base / "manifest.json"
        data = {
            "status": "verified_consecutive_host_presentations",
            "guest_frame_start": 2100,
            "guest_frame_end": 2699,
            "consecutive_host_presentations": 600,
            "dropped_or_skipped_host_frame_ids": 0,
            "control_guest_crc_sha256": "a" * 64,
            "recorded_guest_crc_sha256": "a" * 64,
            "published_sha256": {clip.name: hashlib.sha256(clip.read_bytes()).hexdigest()}
        }
        manifest.write_text(json.dumps(data))
        return clip, manifest, data

    def accept(self, clip, manifest):
        with patch.object(editor, "probe", return_value={
            "width": 1920, "height": 1080,
            "r_frame_rate": "60/1", "nb_read_frames": "600"
        }):
            return editor.source_contract(clip, manifest)

    def test_accepts_complete_indexed_video(self):
        with tempfile.TemporaryDirectory() as td:
            clip, path, data = self.setup_sample(Path(td))
            self.assertEqual(self.accept(clip, path), data)

    def test_rejects_untrusted_provenance(self):
        for key, change in (
            ("status", "sampled_frames"),
            ("guest_frame_end", 2698),
            ("consecutive_host_presentations", 599),
            ("dropped_or_skipped_host_frame_ids", 1),
            ("recorded_guest_crc_sha256", "b" * 64),
        ):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as td:
                clip, path, data = self.setup_sample(Path(td))
                data[key] = change
                path.write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, "accepted"):
                    self.accept(clip, path)

    def test_rejects_substituted_video(self):
        with tempfile.TemporaryDirectory() as td:
            clip, path, _ = self.setup_sample(Path(td))
            clip.write_bytes(b"different")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                self.accept(clip, path)

    def test_rejects_decimated_30hz_video(self):
        with tempfile.TemporaryDirectory() as td:
            clip, path, _ = self.setup_sample(Path(td))
            with patch.object(editor, "probe", return_value={
                "width": 1920, "height": 1080,
                "r_frame_rate": "30/1", "nb_read_frames": "300"
            }):
                with self.assertRaisesRegex(ValueError, "600 genuine"):
                    editor.source_contract(clip, path)


if __name__ == "__main__":
    unittest.main()
