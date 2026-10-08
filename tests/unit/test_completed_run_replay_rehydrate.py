import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "native" / "product"
NATIVE = ROOT / "tests" / "native"


class CompletedRunReplayRehydrateTests(unittest.TestCase):
    def test_saved_record_rehydrates_in_another_process(self):
        with tempfile.TemporaryDirectory() as work:
            work = pathlib.Path(work)
            writer = work / "writer"
            rehydrate = work / "rehydrate"
            record = work / "record.urrun"
            stream = work / "replayed.input"
            common = [
                "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                "-pedantic", "-I", str(PRODUCT),
                str(PRODUCT / "completed_run_record.cpp"),
            ]
            subprocess.run(
                common + [
                    str(NATIVE / "completed_run_record_process_tool.cpp"),
                    "-o", str(writer),
                ],
                check=True, cwd=ROOT,
            )
            subprocess.run(
                common + [
                    str(PRODUCT / "completed_run_replay.cpp"),
                    str(NATIVE / "completed_run_replay_rehydrate.cpp"),
                    "-o", str(rehydrate),
                ],
                check=True, cwd=ROOT,
            )
            subprocess.run([str(writer), "write", str(record)], check=True)
            result = subprocess.run(
                [str(rehydrate), str(record), str(stream)],
                check=True, capture_output=True, text=True,
            )
            self.assertIn("UR_RUN_REPLAY_REHYDRATE PASS", result.stdout)
            self.assertEqual(
                stream.read_text(),
                "0:120:80:0\n120:24:81:0\n144:24:80:0\n",
            )

            # A corrupted persisted artifact cannot replace an existing
            # staged input stream. The caller must never replay damaged data.
            record.write_bytes(
                record.read_bytes().replace(
                    b"elapsed_ticks60 1713", b"elapsed_ticks60 1714"
                )
            )
            rejected = subprocess.run(
                [str(rehydrate), str(record), str(stream)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("checksum mismatch", rejected.stderr)
            self.assertEqual(
                stream.read_text(),
                "0:120:80:0\n120:24:81:0\n144:24:80:0\n",
            )


if __name__ == "__main__":
    unittest.main()
