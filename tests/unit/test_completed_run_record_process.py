import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class CompletedRunRecordProcessTests(unittest.TestCase):
    def test_fresh_process_reload_and_replay_stream(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            exe = tmp / "completed-run-process-tool"
            record = tmp / "dragster.urrun"
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
                    str(ROOT / "tests" / "native" / "completed_run_record_process_tool.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )

            # Separate processes deliberately exercise the durable artifact
            # boundary rather than sharing any in-memory record state.
            subprocess.run([str(exe), "write", str(record)], check=True)
            verified = subprocess.run(
                [str(exe), "verify", str(record)],
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertEqual(
                verified.stdout,
                "0:120:80:0\n120:24:81:0\n144:24:80:0\n",
            )

            damaged = record.read_bytes()
            record.write_bytes(damaged.replace(b"elapsed_ticks60 1713", b"elapsed_ticks60 1714"))
            rejected = subprocess.run(
                [str(exe), "verify", str(record)],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("checksum mismatch", rejected.stderr)


if __name__ == "__main__":
    unittest.main()
