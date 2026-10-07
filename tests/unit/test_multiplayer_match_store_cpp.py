import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class MultiplayerMatchStoreCppTests(unittest.TestCase):
    def test_paired_run_and_match_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "multiplayer-match-store-test"
            store = pathlib.Path(tmp) / "runs"
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
                    "-I",
                    str(ROOT / "native" / "title"),
                    str(ROOT / "native" / "product" / "completed_run_record.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_store.cpp"),
                    str(ROOT / "native" / "product" / "multiplayer_match_record.cpp"),
                    str(ROOT / "native" / "product" / "multiplayer_match_store.cpp"),
                    str(ROOT / "native" / "product" / "local_multiplayer_match_binding.cpp"),
                    str(ROOT / "native" / "product" / "modern_racer_identity.cpp"),
                    str(ROOT / "native" / "product" / "host_profile_runtime.cpp"),
                    str(ROOT / "native" / "product" / "host_product_state.cpp"),
                    str(ROOT / "native" / "product" / "output_resolution_policy.cpp"),
                    str(ROOT / "tests" / "native" / "multiplayer_match_store_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe), str(store)], cwd=ROOT, check=True)
            self.assertEqual(len(list(store.glob("*.urrun"))), 1)
            self.assertEqual(len(list(store.glob("*.urrun.urmatch"))), 1)


if __name__ == "__main__":
    unittest.main()
