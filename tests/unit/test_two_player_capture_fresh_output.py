"""QA guard against stale ordinary-2P run/match files being read as a new capture."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "tests/native/run_modern_two_player_join_record_acceptance.sh"


def rejected(work: Path) -> subprocess.CompletedProcess[str]:
    # Failing executable ensures no real game or ROM is required. A correctly
    # rejected dirty tree exits 2 BEFORE attempting any executable or save.
    return subprocess.run(
        ["bash", str(CAPTURE), "/does-not-exist-game",
         "/does-not-exist-rom", str(work), "/does-not-exist-checker"],
        capture_output=True, text=True, check=False, timeout=5,
    )


class TwoPlayerFreshOutputTests(unittest.TestCase):
    def test_existing_capture_outputs_are_rejected_before_running_guest(self):
        with tempfile.TemporaryDirectory() as tmp:
            for dirty in ("prefs", "multiplayer-runs", "real-joined-capture.log"):
                with self.subTest(dirty=dirty):
                    work = Path(tmp) / dirty
                    work.mkdir()
                    path = work / dirty
                    if dirty == "real-joined-capture.log":
                        path.write_text("previous capture\n", encoding="utf-8")
                    else:
                        path.mkdir()
                    result = rejected(work)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn("requires unused output paths", result.stderr)
                    self.assertFalse((work / "prefs/gamesbyian/UR-Recomp").exists())

    def test_symlinked_output_roots_are_rejected_even_when_dangling(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("prefs", "multiplayer-runs", "real-joined-capture.log"):
                with self.subTest(name=name):
                    work = root / name
                    work.mkdir()
                    (work / name).symlink_to(root / "nonexistent-target")
                    result = rejected(work)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn("requires unused output paths", result.stderr)

    def test_work_directory_symlink_cannot_redirect_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "real-root").mkdir()
            alias = root / "work-alias"
            alias.symlink_to(root / "real-root", target_is_directory=True)
            result = rejected(alias)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("requires unused output paths", result.stderr)


if __name__ == "__main__":
    unittest.main()
