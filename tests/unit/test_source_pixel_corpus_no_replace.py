"""The retained ROM-composed pixel auditor must never replace foreign outputs."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.art import build_racer_source_pixel_corpus as corpus


class PixelCorpusPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "original-source-receipt.json"

    def run_tool(self):
        with patch.object(sys, "argv", ["build_racer_source_pixel_corpus",
                                         "--out", str(self.output)]):
            # No need to hold/use original ROM or source PNGs in these
            # output atomicity tests: build() remains separately tested.
            with patch.object(corpus, "build", return_value={"schema": corpus.SCHEMA,
                                                               "source_rom_reextracted_in_this_run": False}):
                with redirect_stdout(io.StringIO()):
                    corpus.main()

    def test_new_source_report_is_complete_and_cannot_be_replaced(self):
        self.run_tool()
        self.assertEqual(self.output.read_text(), (
            '{\n'
            '  "schema": "UR-RACER-SOURCE-PIXEL-CORPUS/1",\n'
            '  "source_rom_reextracted_in_this_run": false\n'
            '}\n'
        ))
        with self.assertRaises(FileExistsError):
            self.run_tool()
        self.assertFalse(list(self.root.glob(".ur-report-stage-*")))

    def test_existing_original_source_filename_is_not_replaced(self):
        self.output.write_bytes(b"FOREIGN ORIGINAL IMAGE BYTES")
        with self.assertRaises(FileExistsError):
            self.run_tool()
        self.assertEqual(self.output.read_bytes(), b"FOREIGN ORIGINAL IMAGE BYTES")

    def test_foreign_symlink_is_not_followed(self):
        original = self.root / "unrelated-original-source.png"
        original.write_bytes(b"preserve")
        try:
            self.output.symlink_to(original)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unsupported")
        with self.assertRaises(FileExistsError):
            self.run_tool()
        self.assertTrue(self.output.is_symlink())
        self.assertEqual(original.read_bytes(), b"preserve")

    def test_preexisting_empty_directory_cannot_be_replaced(self):
        self.output.mkdir()
        with self.assertRaises(FileExistsError):
            self.run_tool()
        self.assertEqual(list(self.output.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
