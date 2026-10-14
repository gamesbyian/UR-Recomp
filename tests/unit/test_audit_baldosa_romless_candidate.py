#!/usr/bin/env python3
"""Negative-path consumer tests for the independent ROM-free ZIP inspector."""
import hashlib
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import assemble_baldosa_windows_candidate as candidate
from audit_baldosa_romless_candidate import inspect


def fake_pe(path):
    # Structural test only, not an executable or a Windows acceptance witness.
    image = bytearray(65537)
    image[:2] = b"MZ"
    struct.pack_into("<I", image, 0x3c, 128)
    image[128:132] = b"PE\x00\x00"
    struct.pack_into("<H", image, 132, 0x8664)
    struct.pack_into("<H", image, 152, 0x20b)
    path.write_bytes(image)


def repack(original, target, *, modified=None, extra=None, reverse=False,
           symlink=None):
    with zipfile.ZipFile(original) as source:
        source_infos = source.infolist()
        if reverse:
            source_infos.reverse()
        with zipfile.ZipFile(target, "w") as destination:
            for info in source_infos:
                data = source.read(info.filename)
                if modified and info.filename in modified:
                    data = modified[info.filename]
                # Preserve the original member identity and metadata, except
                # for the explicitly requested adversarial reparse type.
                if symlink == info.filename:
                    info.external_attr = 0o120777 << 16
                destination.writestr(info, data)
            if extra is not None:
                destination.writestr(candidate.PREFIX + "save.srm", b"not a save")


class CandidateArchiveAuditTest(unittest.TestCase):
    def test_valid_producer_archive_is_independently_source_bound(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            exe = root / candidate.EXE
            fake_pe(exe)
            archive = root / "romless.zip"
            revision = "0123456789abcdef" * 2 + "01234567"
            created_sha = candidate.create_candidate(exe, archive, revision)
            result = inspect(
                archive, expected_revision=revision,
                expected_zip_sha256=created_sha)
            self.assertEqual(result["source_revision"], revision)
            self.assertEqual(result["zip_sha256"], created_sha)
            self.assertEqual(result["exe_sha256"],
                             hashlib.sha256(exe.read_bytes()).hexdigest())
            self.assertTrue(result["all_immutable_members_verified"])
            self.assertFalse(result["rom_bundled"])
            with self.assertRaisesRegex(ValueError, "source"):
                inspect(archive, expected_revision="deadbeef")
            with self.assertRaisesRegex(ValueError, "pinned"):
                inspect(archive, expected_zip_sha256="0" * 64)

    def test_tampered_readme_manifest_rehashed_member_and_extra_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            exe = root / candidate.EXE
            fake_pe(exe)
            archive = root / "canonical.zip"
            candidate.create_candidate(exe, archive, "abc123")
            with zipfile.ZipFile(archive) as z:
                readme = z.read(candidate.PREFIX + candidate.README)
                manifest = json.loads(z.read(candidate.PREFIX + candidate.MANIFEST))
            changed = readme.replace(b"NOT a completed remaster",
                                     b"an approved final release")
            self.assertNotEqual(changed, readme)
            member = candidate.PREFIX + candidate.README
            modified = root / "modified.zip"
            repack(archive, modified, modified={member: changed})
            with self.assertRaisesRegex(ValueError, "member bytes"):
                inspect(modified)

            # Self-consistent new manifest is not an authenticity proof.
            # The independently pinned outer digest must still reject it.
            readme_row = next(row for row in manifest["immutable_files"]
                              if row["path"] == candidate.README)
            readme_row["sha256"] = hashlib.sha256(changed).hexdigest()
            readme_row["bytes"] = len(changed)
            rewritten = (json.dumps(manifest, sort_keys=True, indent=2) +
                         "\n").encode("utf-8")
            self_rehashed = root / "self-rehashed.zip"
            repack(archive, self_rehashed, modified={
                member: changed,
                candidate.PREFIX + candidate.MANIFEST: rewritten,
            })
            with self.assertRaisesRegex(ValueError, "pinned"):
                inspect(self_rehashed,
                        expected_zip_sha256=hashlib.sha256(
                            archive.read_bytes()).hexdigest())

            extra = root / "extra.zip"
            repack(archive, extra, extra=True)
            with self.assertRaisesRegex(ValueError, "members"):
                inspect(extra)
            reordering = root / "wrong-order.zip"
            repack(archive, reordering, reverse=True)
            with self.assertRaisesRegex(ValueError, "members"):
                inspect(reordering)

    def test_redirected_member_and_bad_manifest_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            exe = root / candidate.EXE
            fake_pe(exe)
            archive = root / "canonical.zip"
            candidate.create_candidate(exe, archive, "abc123")
            bad_link = root / "symlink.zip"
            repack(archive, bad_link, symlink=candidate.PREFIX + candidate.EXE)
            with self.assertRaisesRegex(ValueError, "non-regular"):
                inspect(bad_link)
            with zipfile.ZipFile(archive) as z:
                manifest = json.loads(z.read(candidate.PREFIX + candidate.MANIFEST))
            manifest["rom_bundled"] = True
            bad_manifest = root / "rom-present.zip"
            repack(archive, bad_manifest, modified={
                candidate.PREFIX + candidate.MANIFEST: (
                    json.dumps(manifest, sort_keys=True, indent=2) +
                    "\n").encode(),
            })
            with self.assertRaisesRegex(ValueError, "ROM-free"):
                inspect(bad_manifest)


if __name__ == "__main__":
    unittest.main()
