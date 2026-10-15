#!/usr/bin/env python3
"""ROM-free checks that the candidate receipt binds journey exe to the ZIP."""
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests/unit"))
import assemble_baldosa_windows_candidate as candidate
import bind_baldosa_candidate_receipt as bind
from test_assemble_baldosa_windows_candidate import fake_x64_pe

REV = "0123456789abcdef"


def build(root: Path):
    exe = root / candidate.EXE
    fake_x64_pe(exe)
    archive = root / "UR-Recomp-Baldosa-Windows-x64-ROMLESS.zip"
    digest = candidate.create_candidate(exe, archive, REV)
    sha = root / (archive.name + ".sha256")
    sha.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    return exe, archive, sha, digest


class CandidateBindingTests(unittest.TestCase):
    def test_binds_matching_exe_zip_and_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            exe, archive, sha, digest = build(Path(d))
            r = bind.bind(exe, archive, sha, REV)
            self.assertEqual(r["zip_sha256"], digest)
            self.assertEqual(r["journey_and_packaged_executable_sha256"],
                             bind.sha256_file(exe))

    def test_rejects_different_journey_binary(self):
        with tempfile.TemporaryDirectory() as d:
            exe, archive, sha, _ = build(Path(d))
            exe.write_bytes(exe.read_bytes() + b"x")
            with self.assertRaisesRegex(ValueError, "differs from packaged"):
                bind.bind(exe, archive, sha, REV)

    def test_rejects_stale_zip_hash_file_revision_and_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            exe, archive, sha, digest = build(root)
            with self.assertRaisesRegex(ValueError, "manifest revision"):
                bind.bind(exe, archive, sha, "other-revision")
            sha.write_text("0" * 64 + f"  {archive.name}\n", encoding="ascii")
            with self.assertRaisesRegex(ValueError, "published .sha256"):
                bind.bind(exe, archive, sha, REV)
            sha.write_text(f"{digest}  other.zip\n", encoding="ascii")
            with self.assertRaisesRegex(ValueError, "archive name"):
                bind.bind(exe, archive, sha, REV)
            sha.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
            link = root / "link.exe"
            link.symlink_to(exe)
            with self.assertRaisesRegex(ValueError, "redirected"):
                bind.bind(link, archive, sha, REV)


if __name__ == "__main__":
    unittest.main()
