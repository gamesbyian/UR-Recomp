"""Restorability means a successful *independent* clone of all main ancestors."""
import os
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from backup_main_history import BACKUP_REF, create, digest

def run(*args):
    return subprocess.run(args, check=True, capture_output=True,
                          text=True, timeout=25).stdout.strip()

class MainHistoryBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        run("git", "init", "-q", "-b", "main", str(self.repo))
        run("git", "-C", str(self.repo), "config", "user.email", "test@example.invalid")
        run("git", "-C", str(self.repo), "config", "user.name", "Fixture")
        (self.repo / "README.md").write_text("one\n")
        run("git", "-C", str(self.repo), "add", "README.md")
        run("git", "-C", str(self.repo), "commit", "-qm", "one")
        (self.repo / "README.md").write_text("two\n")
        run("git", "-C", str(self.repo), "commit", "-qam", "two")

    def test_complete_main_ancestry_is_independently_restored(self):
        out = self.root / "bundle-out"
        manifest = create(self.repo, out, max_mib=5)
        self.assertEqual(manifest["history_commit_count"], 2)
        self.assertEqual(manifest["recovered_main_sha"], manifest["source_main_sha"])
        self.assertTrue(manifest["self_restore_verified"])
        self.assertFalse(manifest["independent_drive_copy_verified"])
        self.assertEqual(manifest["bundle_sha256"],
                         digest(out / manifest["bundle_file"]))
        self.assertEqual(run("git", "-C", str(self.repo), "rev-parse", BACKUP_REF),
                         manifest["source_main_sha"])

    def test_shallow_clone_must_not_claim_full_history(self):
        clone = self.root / "shallow"
        run("git", "clone", "-q", "--depth", "1",
            self.repo.as_uri(), str(clone))
        self.assertEqual(run("git", "-C", str(clone),
                             "rev-parse", "--is-shallow-repository"), "true")
        with self.assertRaisesRegex(ValueError, "shallow history"):
            create(clone, self.root / "must-not-exist", max_mib=5)

    def test_output_byte_cap_fails_closed(self):
        (self.repo / "opaque.bin").write_bytes(os.urandom(2 * 1024 * 1024))
        run("git", "-C", str(self.repo), "add", "opaque.bin")
        run("git", "-C", str(self.repo), "commit", "-qm", "opaque")
        output = self.root / "capped"
        with self.assertRaisesRegex(ValueError, "exceeds explicit 1 MiB budget"):
            create(self.repo, output, max_mib=1)
        self.assertFalse((output / "UR-Recomp-main-history.bundle").exists())
        self.assertFalse((output / "manifest.json").exists())


    def test_transfer_parts_reassemble_to_identical_git_bundle(self):
        (self.repo / "opaque.bin").write_bytes(os.urandom(2 * 1024 * 1024))
        run("git", "-C", str(self.repo), "add", "opaque.bin")
        run("git", "-C", str(self.repo), "commit", "-qm", "opaque")
        output = self.root / "split"
        manifest = create(self.repo, output, max_mib=5, part_mib=1)
        parts = manifest["transfer_parts"]
        self.assertGreaterEqual(len(parts), 3)
        self.assertTrue(all(0 < x["bytes"] <= 1024 * 1024 for x in parts))
        assembled = b"".join((output / "transfer" / x["file"]).read_bytes() for x in parts)
        self.assertEqual(assembled, (output / manifest["bundle_file"]).read_bytes())
        stored = json.loads((output / "manifest.json").read_text())
        self.assertEqual(stored["transfer_parts"], parts)
        self.assertEqual(stored["bundle_sha256"], digest(output / manifest["bundle_file"]))

    def test_transfer_limit_rejects_oversized_parts(self):
        with self.assertRaisesRegex(ValueError, "1..80 MiB"):
            create(self.repo, self.root / "invalid-parts", max_mib=5, part_mib=81)

    def test_invalid_budget_rejected(self):
        for max_mib in (-1, 0, 1025, 1.25, "100"):
            with self.subTest(max_mib=max_mib), self.assertRaisesRegex(ValueError, "budget"):
                create(self.repo, self.root / "not-written", max_mib=max_mib)

if __name__ == "__main__":
    unittest.main()
