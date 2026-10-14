"""ROM-free adversarial check of the existing Windows launcher ZIP witness."""
import inspect
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import verify_baldosa_windows_extracted_launcher as verifier


class WindowsArchiveContinuityTests(unittest.TestCase):
    def test_unchanged_archive_is_accepted_and_tampered_archive_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "candidate.zip"
            archive.write_bytes(b"unit-only candidate bytes")
            original_hash = verifier.digest(archive)
            self.assertIsNone(verifier.require_archive_unchanged(archive, original_hash))
            archive.write_bytes(b"unit-only candidate altered")
            with self.assertRaisesRegex(ValueError, "ZIP changed during Windows"):
                verifier.require_archive_unchanged(archive, original_hash)
            archive.unlink()
            with self.assertRaises(FileNotFoundError):
                verifier.require_archive_unchanged(archive, original_hash)

    def test_real_windows_runner_must_check_before_claiming_zip_unchanged(self):
        source = inspect.getsource(verifier.run)
        self.assertIn("approved_archive_sha256 = digest(archive)", source)
        self.assertIn("require_archive_unchanged(archive, approved_archive_sha256)", source)
        self.assertIn('"archive_sha256": approved_archive_sha256', source)
        self.assertIn('"published_zip_unchanged": True', source)


if __name__ == "__main__":
    unittest.main()
