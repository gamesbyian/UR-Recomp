import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class CompletedRunReplayTerminalDigestTests(unittest.TestCase):
    def test_fresh_process_terminal_digest_parity(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = pathlib.Path(temporary)
            writer = folder / "write-terminal-digest"
            compare = folder / "compare-completed-runs"
            command = [
                "g++", "-std=c++17", "-Wall", "-Wextra",
                "-Werror", "-pedantic",
                "-I", str(ROOT / "native" / "product"),
                str(ROOT / "native" / "product" / "completed_run_record.cpp"),
            ]
            subprocess.run(
                command + [
                    str(ROOT / "tests" / "native" /
                        "completed_run_terminal_digest_fixture.cpp"),
                    "-o", str(writer),
                ], cwd=ROOT, check=True,
            )
            subprocess.run(
                command + [
                    str(ROOT / "tests" / "native" /
                        "completed_run_replay_compare.cpp"),
                    "-o", str(compare),
                ], cwd=ROOT, check=True,
            )

            paths = {}
            for name, digest in [
                ("absent", "-"),
                ("digest-a", "a" * 64),
                ("digest-b", "b" * 64),
            ]:
                path = folder / f"{name}.urrun"
                subprocess.run(
                    [str(writer), str(path), digest],
                    cwd=ROOT, check=True,
                )
                paths[name] = path

            for left, right in [
                ("absent", "absent"),
                ("digest-a", "digest-a"),
                ("digest-b", "digest-b"),
            ]:
                result = subprocess.run(
                    [str(compare), str(paths[left]), str(paths[right])],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("UR_RUN_REPLAY_COMPARE PASS", result.stdout)

            for left, right in [
                ("digest-a", "digest-b"),
                ("digest-a", "absent"),
                ("absent", "digest-a"),
            ]:
                result = subprocess.run(
                    [str(compare), str(paths[left]), str(paths[right])],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 4, result.stderr)
                self.assertIn(
                    "DIFF terminal_simulation_digest",
                    result.stderr,
                )


if __name__ == "__main__":
    unittest.main()
