"""Synthetic ROM-free tests for intentionally scoped nested ZIP inspection."""
from io import BytesIO
import hashlib
from unittest.mock import patch
import unittest
from zipfile import ZipFile

from tools import recovery_scoped_zip_audit as audit


def archive(files):
    stream = BytesIO()
    with ZipFile(stream, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return stream.getvalue()


class ScopedZipAuditTests(unittest.TestCase):
    def test_only_selected_archive_is_read_and_crc_checked(self):
        inner = archive({"test.py": b"pass\n"})
        outer = archive({"evidence/inner.zip": inner, "unrelated.py": b"not validated\n"})
        report = audit.inspect(outer, ["evidence/inner.zip"])
        self.assertEqual([x["members_declared"] for x in report["layers"]], [2, 1])
        self.assertEqual(report["selected_members"][0]["sha256"],
                         hashlib.sha256(inner).hexdigest())
        self.assertTrue(report["selected_members"][0]["crc_verified"])
        self.assertFalse(report["all_unselected_member_contents_verified"])
        self.assertFalse(report["full_archive_crosswalk_qualified"])
        self.assertFalse(report["source_publication_authorized"])
        self.assertEqual(report["release_gate_credit"], 0)

    def test_explicit_leaf_git_blob_is_verified_without_extraction(self):
        source = b"print('preserved')\n"
        child = archive({"tools/source.py": source})
        outer = archive({"evidence/child.zip": child})
        report = audit.inspect(outer, ["evidence/child.zip"], leaf="tools/source.py")
        leaf = report["leaf_member"]
        self.assertEqual(leaf["bytes"], len(source))
        self.assertTrue(leaf["crc_verified"])
        self.assertEqual(leaf["sha256"], hashlib.sha256(source).hexdigest())
        expected_git_sha = hashlib.sha1(
            b"blob " + str(len(source)).encode() + b"\0" + source
        ).hexdigest()
        self.assertEqual(leaf["git_blob_sha"], expected_git_sha)
        with self.assertRaisesRegex(ValueError, "missing"):
            audit.inspect(outer, ["evidence/child.zip"], leaf="absent.py")

    def test_paths_and_aliasing_are_rejected(self):
        for files in (
            {"../escape.py": b"x"},
            {"foo.py": b"x", "FOO.py": b"x"},
            {"package.py": b"x", "package.py/child.zip": b"y"},
        ):
            with self.subTest(files=tuple(files)), self.assertRaisesRegex(
                    ValueError, "unsafe|duplicate|collision"):
                audit.inspect(archive(files), [])

    def test_missing_nested_member_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            audit.inspect(archive({"file.txt": b"hi"}), ["nonexistent.zip"])

    def test_depth_size_and_read_budgets(self):
        src = archive({"file.py": b"ok"})
        with self.assertRaisesRegex(ValueError, "depth"):
            audit.inspect(src, ["file.zip"] * (audit.MAX_DEPTH + 1))
        with patch.object(audit, "MAX_ARCHIVE_BYTES", len(src) - 1):
            with self.assertRaisesRegex(ValueError, "input budget"):
                audit.inspect(src, [])
        nested = archive({"deep.py": b"test"})
        outer = archive({"nested.zip": nested})
        with patch.object(audit, "MAX_SELECTED_MEMBER_BYTES", len(nested) - 1):
            with self.assertRaisesRegex(ValueError, "read budget"):
                audit.inspect(outer, ["nested.zip"])

    def test_corrupt_outer_zip_fails(self):
        with self.assertRaisesRegex(ValueError, "corrupt"):
            audit.inspect(b"not-a-ZIP", [])


if __name__ == "__main__":
    unittest.main()
