import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class CompletedRunGhostTraceLimitsTests(unittest.TestCase):
    def test_bounded_optional_sidecar_does_not_poison_run(self):
        with tempfile.TemporaryDirectory() as work:
            root = pathlib.Path(work)
            exe = root / "ghost-trace-limits"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", "-I", str(ROOT / "native/product"),
                    str(ROOT / "native/product/completed_run_record.cpp"),
                    str(ROOT / "native/product/completed_run_ghost.cpp"),
                    str(ROOT / "native/product/completed_run_ghost_trace.cpp"),
                    str(ROOT / "tests/native/completed_run_ghost_trace_limits_test.cpp"),
                    "-o", str(exe),
                ],
                cwd=ROOT, check=True,
            )
            subprocess.run([str(exe), str(root / "run.urrun")], check=True)


if __name__ == "__main__":
    unittest.main()
