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

    def test_exact_selected_outer_member_stages_no_unapproved_siblings(self):
        chosen = b"print('approved source')\n"
        other = b"print('not approved')\n"
        blob = archive({
            "source/approved.py": chosen, "source/unreviewed.py": other,
            "payload/roms/restricted.py": b"not a candidate",
        })
        with tempfile.TemporaryDirectory() as tmp:
            result = intake.scan_zip(
                blob, b"", stage_root=Path(tmp),
                stage_member="source/approved.py",
                stage_sha256=hashlib.sha256(chosen).hexdigest())
            self.assertEqual(result["staged_sources"], 1)
            self.assertEqual(result["staged_bytes"], len(chosen))
            self.assertEqual((Path(tmp) / "selected/source/approved.py").read_bytes(), chosen)
            self.assertEqual(len(list(Path(tmp).rglob("*.py"))), 1)
            self.assertFalse((Path(tmp) / "source/unreviewed.py").exists())

    def test_exact_nested_member_stages_one_byte_verified_leaf(self):
        chosen = b"def fixed():\n    return True\n"
        nested = archive({
            "src/candidate.py": chosen,
            "src/another.py": b"print('unreviewed')",
        })
        blob = archive({
            "bundles/recovery.zip": nested,
            "source/unreviewed.py": b"print('unreviewed sibling')",
        })
        with tempfile.TemporaryDirectory() as tmp:
            result = intake.scan_zip(
                blob, b"", stage_root=Path(tmp),
                stage_member="bundles/recovery.zip!/src/candidate.py",
                stage_sha256=hashlib.sha256(chosen).hexdigest())
            self.assertEqual(result["staged_sources"], 1)
            self.assertEqual(len([m for m in result["members"] if m["staged"]]), 1)
            self.assertIn("bundles/recovery.zip!/src/candidate.py",
                          {m["member"] for m in result["members"] if m["staged"]})
            self.assertEqual((Path(tmp) / "selected/src/candidate.py").read_bytes(), chosen)
            self.assertEqual(len(list(Path(tmp).rglob("*.py"))), 1)

    def test_exact_selection_fails_without_writing_source_on_bad_hash(self):
        chosen = b"print('proposed')\n"
        blob = archive({"source/candidate.py": chosen})
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "not eligible"):
                intake.scan_zip(
                    blob, b"", stage_root=Path(tmp),
                    stage_member="source/candidate.py", stage_sha256="0" * 64)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_exact_selected_source_must_be_unmatched_and_unrestricted(self):
        source = b"print('already on main')\n"
        blob = archive({"src/existing.py": source})
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "not eligible"):
                intake.scan_zip(
                    blob, git_tree("tools/existing.py", source),
                    stage_root=Path(tmp), stage_member="src/existing.py",
                    stage_sha256=hashlib.sha256(source).hexdigest())
            self.assertEqual(list(Path(tmp).iterdir()), [])
        hidden = b"print('held')\n"
        blob = archive({"private/cache.zip": archive({"src/held.py": hidden})})
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "not eligible"):
                intake.scan_zip(
                    blob, b"", stage_root=Path(tmp),
                    stage_member="private/cache.zip!/src/held.py",
                    stage_sha256=hashlib.sha256(hidden).hexdigest())
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_invalid_member_selection_needs_matching_path_and_digest(self):
        blob = archive({"src/test.py": b"print('source')\n"})
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "requires both"):
                intake.scan_zip(
                    blob, b"", stage_root=Path(tmp), stage_member="src/test.py")
            with self.assertRaisesRegex(ValueError, "invalid exact"):
                intake.scan_zip(
                    blob, b"", stage_root=Path(tmp),
                    stage_member="src/test.py", stage_sha256="not-a-sha")

    def test_selected_staging_rejects_archive_replacement_before_writing_source(self):
        original = b"print('approved')\n"
        raw = archive({"src/candidate.py": original})
        member_digest = hashlib.sha256(original).hexdigest()
        def downloader(command, **kwargs):
            Path(command[command.index("-O") + 1]).write_bytes(raw)
            return SimpleNamespace(stdout="", stderr="")
        entry = {
            "id": "1Abcdefghij12345", "path": "candidate.zip",
            "url": "https://drive.google.com/uc?id=1Abcdefghij12345",
        }
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "requires original archive SHA-256 pin"):
                intake.pull(
                    entry, Path(tmp), b"", stage=True,
                    stage_member="src/candidate.py",
                    stage_sha256=member_digest,
                    runner=downloader,
                )
            self.assertEqual(list(Path(tmp).iterdir()), [])
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "archive SHA-256 differs"):
                intake.pull(
                    entry, Path(tmp), b"", stage=True,
                    stage_member="src/candidate.py",
                    stage_sha256=member_digest,
                    expected_archive_sha256="f" * 64,
                    runner=downloader,
                )
            self.assertFalse((Path(tmp) / "staged").exists())
        with tempfile.TemporaryDirectory() as tmp:
            result = intake.pull(
                entry, Path(tmp), b"", stage=True,
                stage_member="src/candidate.py",
                stage_sha256=member_digest,
                expected_archive_sha256=hashlib.sha256(raw).hexdigest(),
                runner=downloader,
            )
            self.assertEqual(result["zip"]["staged_sources"], 1)
            self.assertEqual(
                (Path(tmp) / "staged/1Abcdefghij12345/selected/src/candidate.py").read_bytes(),
                original,
            )

    def test_review_leads_preserve_nested_source_hashes_without_private_names(self):
        identical = b"print('on main')\n"
        fresh = b"print('new')\n"
        nested = archive({
            "src/nested.py": b"print('nested')\n",
            "private/secret.py": b"not for metadata",
        })
        blob = archive({
            "payload/h26.zip": nested,
            "payload/tools/new.py": fresh,
            "payload/tools/identical.py": identical,
        })
        scan = intake.scan_zip(blob, git_tree("tools/current.py", identical))
        leads = {lead["member"]: lead for lead in scan["review_leads"]}
        self.assertEqual(set(leads), {
            "payload/tools/new.py", "payload/h26.zip!/src/nested.py",
        })
        self.assertEqual(leads["payload/tools/new.py"]["sha256"],
                         hashlib.sha256(fresh).hexdigest())
        self.assertEqual(scan["review_leads_filtered_or_truncated"], 1)
        self.assertTrue(all(lead["status"] == "unmatched_needs_review"
                            for lead in leads.values()))

    def test_review_leads_are_bounded_independently_of_archive_members(self):
        blob = archive({f"payload/tools/lead_{i:03}.py": b"print(42)\n"
                        for i in range(intake.MAX_REVIEW_LEADS + 4)})
        scan = intake.scan_zip(blob, b"")
        self.assertEqual(len(scan["review_leads"]), intake.MAX_REVIEW_LEADS)
        self.assertEqual(scan["review_leads_filtered_or_truncated"], 4)
        self.assertEqual(scan["staged_sources"], 0)

    def test_invalid_zip_member_rejected_without_extraction(self):
        blob = archive({"../outside.py": b"unsafe"})
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                intake.scan_zip(blob, b"", stage_root=Path(tmp))
            self.assertEqual(list(Path(tmp).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
