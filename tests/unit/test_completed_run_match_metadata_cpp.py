import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class CompletedRunMatchMetadataCppTests(unittest.TestCase):
    def test_match_metadata_round_trip_and_run_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "completed-run-match-metadata-test"
            subprocess.run(
                [
                    "g++",
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-I",
                    str(ROOT / "native/product"),
                    "-I",
                    str(ROOT / "native/title"),
                    str(ROOT / "tests/native/completed_run_match_metadata_test.cpp"),
                    str(ROOT / "native/product/completed_run_match_metadata.cpp"),
                    str(ROOT / "native/product/completed_run_record.cpp"),
                    str(ROOT / "native/product/local_multiplayer_match_binding.cpp"),
                    str(ROOT / "native/product/modern_racer_identity.cpp"),
                    str(ROOT / "native/product/host_product_state.cpp"),
                    str(ROOT / "native/product/output_resolution_policy.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
