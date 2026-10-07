import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class CompletedRunProfileSourcesCppTests(unittest.TestCase):
    def test_profile_catalog_and_run_namespaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "completed-run-profile-sources-test"
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
                    str(ROOT / "native" / "product" / "host_product_state.cpp"),
                    str(ROOT / "native" / "product" / "output_resolution_policy.cpp"),
                    str(ROOT / "native" / "product" / "host_profile_runtime.cpp"),
                    str(ROOT / "native" / "product" / "host_profile_state.cpp"),
                    str(ROOT / "native" / "product" / "modern_racer_identity.cpp"),
                    str(ROOT / "native" / "product" / "host_profile_catalog.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_record.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_capture.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_store.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_comparison.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_presentation.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_catalog.cpp"),
                    str(ROOT / "native" / "product" / "completed_run_profile_sources.cpp"),
                    str(ROOT / "tests" / "native" / "completed_run_profile_sources_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run(
                [str(exe), str(pathlib.Path(tmp) / "user-data")],
                cwd=ROOT,
                check=True,
            )


if __name__ == "__main__":
    unittest.main()
