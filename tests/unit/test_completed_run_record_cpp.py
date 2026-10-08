import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class CompletedRunRecordCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "completed-run-record-test"
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
                    str(ROOT / "tests" / "native" / "completed_run_record_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=tmp, check=True)


    def test_fresh_process_replay_frame_window_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            fixture = tmp / "completed-run-fixture"
            compare = tmp / "compare-completed-runs"
            compile_base = [
                "g++", "-std=c++17", "-Wall", "-Wextra",
                "-Werror", "-pedantic",
                "-I", str(ROOT / "native" / "product"),
                str(ROOT / "native" / "product" / "completed_run_record.cpp"),
            ]
            subprocess.run(
                compile_base + [
                    str(ROOT / "tests" / "native" /
                        "completed_run_record_process_tool.cpp"),
                    "-o", str(fixture),
                ],
                cwd=ROOT, check=True,
            )
            subprocess.run(
                compile_base + [
                    str(ROOT / "tests" / "native" /
                        "completed_run_replay_compare.cpp"),
                    "-o", str(compare),
                ],
                cwd=ROOT, check=True,
            )

            artifacts = {}
            for label, frames in (
                ("original", 300),
                ("same", 300),
                ("plus-one", 301),
                ("minus-one", 299),
                ("plus-two", 302),
                ("minus-two", 298),
            ):
                path = tmp / f"{label}.urrun"
                subprocess.run(
                    [str(fixture), "write", str(path), str(frames)],
                    check=True,
                )
                artifacts[label] = path

            for label in ("same", "plus-one", "minus-one"):
                result = subprocess.run(
                    [str(compare), str(artifacts["original"]),
                     str(artifacts[label])],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("UR_RUN_REPLAY_COMPARE PASS", result.stdout)

            for label in ("plus-two", "minus-two"):
                result = subprocess.run(
                    [str(compare), str(artifacts["original"]),
                     str(artifacts[label])],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 4, result.stderr)
                self.assertIn(
                    "DIFF frame_count exceeds one terminal lifecycle frame",
                    result.stderr,
                )


if __name__ == "__main__":
    unittest.main()
