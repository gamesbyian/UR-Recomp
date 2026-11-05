"""ROM-free collision controls for ART-4K immutable report publication."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.art.no_replace_report import publish_text_once


class ReportNoReplaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.destination = self.root / "score.json"

    def assert_no_staging(self):
        self.assertEqual(list(self.root.glob(".ur-report-stage-*")), [])

    def test_new_report_is_complete_and_has_no_staging_leftovers(self):
        publish_text_once(self.destination, '{"score": 1}\n')
        self.assertEqual(self.destination.read_bytes(), b'{"score": 1}\n')
        self.assert_no_staging()

    def test_existing_report_cannot_be_overwritten(self):
        self.destination.write_text("original", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            publish_text_once(self.destination, "replacement")
        self.assertEqual(self.destination.read_text(encoding="utf-8"), "original")
        self.assert_no_staging()

    def test_existing_symlink_cannot_redirect_report_to_foreign_file(self):
        foreign = self.root / "foreign.txt"
        foreign.write_text("foreign", encoding="utf-8")
        try:
            self.destination.symlink_to(foreign)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        with self.assertRaises(FileExistsError):
            publish_text_once(self.destination, "replacement")
        self.assertTrue(self.destination.is_symlink())
        self.assertEqual(foreign.read_text(encoding="utf-8"), "foreign")
        self.assert_no_staging()

    def test_competing_empty_directory_created_at_publication_is_preserved(self):
        real_link = os.link
        def competitor(source, destination, *args, **kwargs):
            Path(destination).mkdir()
            return real_link(source, destination, *args, **kwargs)
        with patch("tools.art.no_replace_report.os.link", side_effect=competitor):
            with self.assertRaises(FileExistsError):
                publish_text_once(self.destination, "replacement")
        self.assertTrue(self.destination.is_dir())
        self.assertEqual(list(self.destination.iterdir()), [])
        self.assert_no_staging()

    def test_unsupported_hardlinks_fail_closed_and_clean_stage(self):
        with patch("tools.art.no_replace_report.os.link", side_effect=OSError("unsupported")):
            with self.assertRaisesRegex(OSError, "unsupported"):
                publish_text_once(self.destination, "replacement")
        self.assertFalse(self.destination.exists())
        self.assert_no_staging()


if __name__ == "__main__":
    unittest.main()
