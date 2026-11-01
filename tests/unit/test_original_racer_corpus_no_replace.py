"""Foreign-directory-safe original raster output: no clobber and receipt-last."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.art.export_registered_original_racer_corpus import publish_private_corpus_stage


class SourceCorpusNoReplaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root / "staged-complete"
        (self.stage/"stock").mkdir(parents=True)
        self.image = self.stage/"stock"/("source-"+"a"*64+".png")
        self.image.write_bytes(b"synthetic unlicensed bytes")
        self.manifest = self.stage/"source-corpus.json"
        self.manifest.write_bytes(b'{"schema":"synthetic-test"}\n')
        self.dest = self.root / "private-published"

    def test_exact_existing_bytes_are_published_and_receipt_last(self):
        publish_private_corpus_stage(self.stage, self.dest)
        self.assertEqual((self.dest/"stock"/self.image.name).read_bytes(), self.image.read_bytes())
        self.assertEqual((self.dest/"source-corpus.json").read_bytes(), self.manifest.read_bytes())
        with self.assertRaises(FileExistsError):
            publish_private_corpus_stage(self.stage, self.dest)
        self.assertEqual((self.dest/"source-corpus.json").read_bytes(), self.manifest.read_bytes())

    def test_preexisting_truly_empty_directory_is_never_replaced(self):
        # On POSIX, the old os.rename(stage, out) WOULD replace this.
        self.dest.mkdir()
        with self.assertRaises(FileExistsError):
            publish_private_corpus_stage(self.stage, self.dest)
        self.assertEqual(list(self.dest.iterdir()), [])

    def test_preexisting_nonempty_foreign_directory_is_never_replaced(self):
        self.dest.mkdir()
        marker = self.dest/"foreign"
        marker.write_bytes(b"untouched")
        with self.assertRaises(FileExistsError):
            publish_private_corpus_stage(self.stage, self.dest)
        self.assertEqual(marker.read_bytes(), b"untouched")
        self.assertFalse((self.dest/"source-corpus.json").exists())

    def test_preexisting_symlink_never_clobbered(self):
        foreign = self.root/"foreign"
        foreign.mkdir()
        try:
            self.dest.symlink_to(foreign, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("this local platform disallows symlink creation")
        with self.assertRaises(FileExistsError):
            publish_private_corpus_stage(self.stage, self.dest)
        self.assertTrue(self.dest.is_symlink())
        self.assertFalse((foreign/"source-corpus.json").exists())

    def test_failure_during_source_links_never_publishes_receipt(self):
        with patch("tools.art.export_registered_original_racer_corpus.os.link",
                   side_effect=OSError("hard links unsupported")):
            with self.assertRaisesRegex(OSError, "unsupported"):
                publish_private_corpus_stage(self.stage, self.dest)
        self.assertTrue(self.dest.is_dir())
        self.assertFalse((self.dest/"source-corpus.json").exists())
        self.assertEqual(self.manifest.read_bytes(), b'{"schema":"synthetic-test"}\n')

    def test_failure_during_final_receipt_link_cannot_claim_success(self):
        original = os.link
        def fail_final(source, dest, **kwargs):
            if Path(dest).name == "source-corpus.json":
                raise OSError("receipt link failure")
            return original(source, dest, **kwargs)
        with patch("tools.art.export_registered_original_racer_corpus.os.link",
                   side_effect=fail_final):
            with self.assertRaisesRegex(OSError, "receipt link"):
                publish_private_corpus_stage(self.stage, self.dest)
        self.assertTrue((self.dest/"stock"/self.image.name).is_file())
        self.assertFalse((self.dest/"source-corpus.json").exists())

    def test_invalid_staged_image_name_does_not_publish_receipt(self):
        other = self.stage/"stock"/"untrusted.png"
        other.write_bytes(b"not-source")
        with self.assertRaisesRegex(ValueError, "identity"):
            publish_private_corpus_stage(self.stage, self.dest)
        self.assertFalse((self.dest/"source-corpus.json").exists())

    def test_duplicate_filename_owned_by_concurrent_writer_is_not_replaced(self):
        original = os.link
        def compete(source, dest, **kwargs):
            if Path(dest).suffix == ".png":
                Path(dest).write_bytes(b"foreign file")
            return original(source, dest, **kwargs)
        with patch("tools.art.export_registered_original_racer_corpus.os.link",
                   side_effect=compete):
            with self.assertRaises(FileExistsError):
                publish_private_corpus_stage(self.stage, self.dest)
        target = self.dest/"stock"/self.image.name
        self.assertEqual(target.read_bytes(), b"foreign file")
        self.assertFalse((self.dest/"source-corpus.json").exists())


if __name__ == "__main__":
    unittest.main()
