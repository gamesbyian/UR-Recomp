import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class MultiplayerMatchRecordCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "multiplayer-match-record-test"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(ROOT / "native" / "product"),
                    "-I", str(ROOT / "native" / "title"),
                    str(ROOT / "native" / "product" / "modern_racer_identity.cpp"),
                    str(ROOT / "native" / "product" / "host_profile_runtime.cpp"),
                    str(ROOT / "native" / "product" / "host_product_state.cpp"),
                    str(ROOT / "native" / "product" / "output_resolution_policy.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_record.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_store.cpp"),
                    str(ROOT / "native" / "product" / "local_multiplayer_match_binding.cpp"),
                    str(ROOT / "native" / "product" / "multiplayer_match_record.cpp"),
                    str(ROOT / "tests" / "native" / "multiplayer_match_record_test.cpp"),
                    "-o", str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)
            # Separate operating-system processes compete for the same
            # millisecond .urrun/.urmatch basename. A successful publication
            # must never replace another writer's run or sidecar.
            pair_root = pathlib.Path(tmp) / "concurrent-pairs"
            pair_root.mkdir()
            writers = [
                subprocess.Popen(
                    [str(exe), "append", str(pair_root), str(i)],
                    cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                for i in range(8)
            ]
            outputs = [worker.communicate() for worker in writers]
            for writer, (_, err) in zip(writers, outputs):
                self.assertEqual(writer.returncode, 0, err.decode())
            paths = [out.decode().strip() for out, _ in outputs]
            self.assertEqual(len(set(paths)), 8, paths)
            subprocess.run(
                [str(exe), "inspect", str(pair_root)],
                cwd=ROOT, check=True,
            )

            # Kill the process at the exact sidecar-first boundary.
            # Restarts must see no public run and must not infer a result
            # from the abandoned .urmatch or staging directories.
            crash_root = pathlib.Path(tmp) / "crash-pair"
            crash_root.mkdir()
            crashed = subprocess.run(
                [str(exe), "crash", str(crash_root)],
                cwd=ROOT, capture_output=True,
            )
            self.assertEqual(crashed.returncode, 77, crashed.stderr.decode())
            self.assertEqual(list(crash_root.glob("*.urrun")), [])
            self.assertEqual(len(list(crash_root.glob("*.urmatch"))), 1)
            restarted = subprocess.run(
                [str(exe), "append", str(crash_root), "3"],
                cwd=ROOT, capture_output=True,
            )
            self.assertEqual(restarted.returncode, 0, restarted.stderr.decode())
            self.assertEqual(len(list(crash_root.glob("*.urrun"))), 1)
            self.assertEqual(len(list(crash_root.glob("*.urmatch"))), 2)


if __name__ == "__main__":
    unittest.main()
