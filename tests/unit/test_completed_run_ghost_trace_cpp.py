import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class CompletedRunGhostTraceCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "completed-run-ghost-trace-test"
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-I",
                    str(ROOT / "native" / "product"),
                    str(ROOT / "native" / "product" / "completed_run_record.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_ghost.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_ghost_trace.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_store.cpp"),
                    str(ROOT / "tests" / "native" / "completed_run_ghost_trace_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            run = pathlib.Path(tmp) / "run.urrun"
            trace = pathlib.Path(str(run) + ".urghost")
            subprocess.run([str(exe), str(run)], cwd=ROOT, check=True)
            self.assertTrue(trace.is_file())
            # Fresh executable invocation, no shared process state from writer.
            subprocess.run(
                [str(exe), str(run), "--verify-persisted-targets"],
                cwd=ROOT,
                check=True,
            )


if __name__ == "__main__":
    unittest.main()
