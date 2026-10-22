"""Source-derived H25 QA04 POSIX anchored evidence-reader regressions.

These tests do not certify physical Windows QA or native CreateFileW behavior.
"""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import qa04_anchored_posix as guard


@unittest.skipUnless(os.name == "posix" and hasattr(os, "O_NOFOLLOW"),
                     "POSIX descriptor pilot only; Win32 native handles outstanding")
class AnchoredEvidenceTests(unittest.TestCase):
    def test_nested_regular_file_and_exact_size(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "packet"
            nested = root / "nested"
            nested.mkdir(parents=True)
            sample = b"verified first-party bytes"
            (nested / "proof.bin").write_bytes(sample)
            self.assertEqual(guard.sha256_anchored(root, "nested/proof.bin", len(sample)),
                             hashlib.sha256(sample).hexdigest())
            with self.assertRaises(ValueError):
                guard.sha256_anchored(root, "nested/proof.bin", len(sample) - 1)

    def test_symlink_leaf_ancestor_and_hardlink_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "packet"
            root.mkdir()
            (root / "x").write_bytes(b"x")
            alias = Path(d) / "alias"
            alias.symlink_to(root, target_is_directory=True)
            with self.assertRaises(OSError):
                guard.sha256_anchored(alias, "x", 1)
            leaf = root / "redirect"
            leaf.symlink_to(root / "x")
            with self.assertRaises(OSError):
                guard.sha256_anchored(root, "redirect", 1)
            os.link(root / "x", root / "hardlink")
            with self.assertRaisesRegex(ValueError, "hardlinked"):
                guard.sha256_anchored(root, "x", 1)

    def test_path_alias_nonregular_and_size_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "packet"
            root.mkdir()
            (root / "x").write_bytes(b"x")
            for bad in ("../x", "./x", "x/../x", "/x", "x//x", ""):
                with self.subTest(relative=bad):
                    with self.assertRaises(ValueError):
                        guard.sha256_anchored(root, bad, 1)
            for size in (0, -1, True, 32 * 1024 * 1024 + 1):
                with self.subTest(size=size):
                    with self.assertRaises(ValueError):
                        guard.sha256_anchored(root, "x", size)
            if hasattr(os, "mkfifo"):
                os.mkfifo(root / "fifo")
                with self.assertRaises(ValueError):
                    guard.sha256_anchored(root, "fifo", 1)

    def test_post_open_rename_hashes_original_open_inode(self):
        # A pathname swap after the descriptor opens cannot substitute the
        # bytes being hashed; this is still not an immutable identity claim.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "packet"
            root.mkdir()
            original = root / "x"
            original.write_bytes(b"original")
            (root / "replacement").write_bytes(b"attacker")
            real_read = os.read
            switched = False

            def swap_then_read(fd, count):
                nonlocal switched
                if not switched:
                    switched = True
                    original.rename(root / "original-backup")
                    original.symlink_to(root / "replacement")
                return real_read(fd, count)

            with patch.object(guard.os, "read", side_effect=swap_then_read):
                result = guard.sha256_anchored(root, "x", len(b"original"))
            self.assertTrue(switched)
            self.assertEqual(result, hashlib.sha256(b"original").hexdigest())
            self.assertEqual(original.read_bytes(), b"attacker")


if __name__ == "__main__":
    unittest.main()
