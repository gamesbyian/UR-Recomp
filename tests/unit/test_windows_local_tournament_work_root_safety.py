"""Regression: manual Windows QA must never recursively erase an existing user root."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
ROUTE = ROOT / "tests/native/run_windows_local_tournament_package_acceptance.sh"


class PackagedTournamentWorkRootSafetyTests(unittest.TestCase):
    def test_existing_work_root_is_refused_before_any_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "fake-extracted-package"
            package.mkdir()
            (package / "run-uniracers.cmd").write_text("exit /b 0\r\n")
            existing = root / "existing-work"
            existing.mkdir()
            sentinel = existing / "user data" / "untouchable.srm"
            sentinel.parent.mkdir()
            sentinel.write_bytes(b"original saved fixture, must survive")
            proc = subprocess.run(
                ["bash", str(ROUTE), str(package), str(existing)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("non-existing work directory", proc.stderr)
            self.assertEqual(sentinel.read_bytes(), b"original saved fixture, must survive")

    def test_empty_work_path_and_broken_symlink_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            package.mkdir()
            for work in ("", str(root / "dangling")):
                if work:
                    try:
                        (root / "dangling").symlink_to(root / "not-created", target_is_directory=True)
                    except (OSError, NotImplementedError):
                        continue
                proc = subprocess.run(
                    ["bash", str(ROUTE), str(package), work],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn("non-existing work directory", proc.stderr)

    def test_work_root_inside_immutable_package_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "Extracted Package"
            package.mkdir()
            nested = package / "QA Output"
            proc = subprocess.run(
                ["bash", str(ROUTE), str(package), str(nested)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("cannot be inside the package", proc.stderr)
            self.assertFalse(nested.exists())

    def test_nonexistent_parent_fails_without_creating_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            package.mkdir()
            nested = root / "missing-parent" / "qa"
            proc = subprocess.run(
                ["bash", str(ROUTE), str(package), str(nested)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertFalse(nested.parent.exists())

    def test_no_recursive_delete_in_package_route(self):
        text = ROUTE.read_text(encoding="utf-8")
        self.assertNotIn("rm -rf", text)
        self.assertIn('[[ -z "$WORK" || -e "$WORK" || -L "$WORK" ]]', text)


if __name__ == "__main__":
    unittest.main()
