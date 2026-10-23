"""ROM-free tests for direct public-Drive intake and staged-source guards."""
import hashlib
from io import BytesIO
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from zipfile import ZipFile

from tools import vault_gdown_intake as intake


def archive(files):
    stream = BytesIO()
    with ZipFile(stream, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return stream.getvalue()


def git_tree(name, data):
    digest = hashlib.sha1(
        b"blob " + str(len(data)).encode() + b"\0" + data
    ).hexdigest()
    return ("100644 blob " + digest + "\t" + name + "\0").encode()


class VaultGdownIntakeTests(unittest.TestCase):
    def test_drive_ids_only_from_google(self):
        self.assertEqual(
            intake.drive_id("https://drive.google.com/uc?id=1Abcdefghij12345"),
            "1Abcdefghij12345",
        )
        self.assertEqual(
            intake.drive_id("https://drive.google.com/file/d/1Abcdefghij12345/view"),
            "1Abcdefghij12345",
        )
        with self.assertRaises(ValueError):
            intake.drive_id("https://not-google.example/uc?id=1Abcdefghij12345")

    def test_windows_portable_paths(self):
        for name in ("../escape.py", "CON.py", "bad\\name.py", "case:ads.py",
                     "dir/../bad.py", "/absolute.py", "trailing./x.py"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                intake.safe_path(name)
        self.assertEqual(intake.safe_path("payload/tests/unit/foo.py"),
                         Path("payload/tests/unit/foo.py"))

    def test_source_filter_never_stages_binary_or_private_dirs(self):
        self.assertTrue(intake.safe_source_member("payload/tests/foo.py", 100))
        for name in ("payload/roms/test.py", "capture/sample.py",
                     "payload/game.sfc", ".github/workflows/build.yml",
                     "payload/secret_key.py"):
            with self.subTest(name=name):
                self.assertFalse(intake.safe_source_member(name, 100))
        self.assertFalse(intake.safe_source_member("test.py",
                                                   intake.MAX_SOURCE_BYTES + 1))

    def test_folder_json_duplicates_are_rejected(self):
        def fake_runner(*args, **kwargs):
            self.assertEqual(args[0][0], "gdown")
            return SimpleNamespace(stdout=json.dumps([
                {"url": "https://drive.google.com/uc?id=1Abcdefghij12345",
                 "path": "archive.zip"},
                {"url": "https://drive.google.com/uc?id=1Bbcdefghij12345",
                 "path": "ARCHIVE.ZIP"},
            ]))
        with self.assertRaisesRegex(ValueError, "collision"):
            intake.list_public_folder(intake.DEFAULT_FOLDER, runner=fake_runner)

    def test_source_staging_excludes_exact_main_blobs(self):
        exact = b"print('on main')\n"
        unique = b"print('new candidate')\n"
        blob = archive({
            "payload/tools/exact.py": exact,
            "payload/tools/new.py": unique,
            "payload/game.sfc": b"restricted binary",
            "MANIFEST.json": b"{}",
        })
        with tempfile.TemporaryDirectory() as tmp:
            scan = intake.scan_zip(
                blob, git_tree("tools/exact.py", exact),
                stage_root=Path(tmp)
            )
            self.assertEqual(scan["staged_sources"], 1)
            self.assertTrue(
                (Path(tmp) / "payload/tools/new.py").is_file()
            )
            self.assertFalse(
                (Path(tmp) / "payload/tools/exact.py").exists()
            )
            self.assertFalse(
                (Path(tmp) / "payload/game.sfc").exists()
            )
            self.assertTrue(scan["rights_and_publication_review_required"])

    def test_invalid_zip_member_rejected_without_extraction(self):
        blob = archive({"../outside.py": b"unsafe"})
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                intake.scan_zip(blob, b"", stage_root=Path(tmp))
            self.assertEqual(list(Path(tmp).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
