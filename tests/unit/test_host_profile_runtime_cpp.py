import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class HostProfileRuntimeCppTests(unittest.TestCase):
    def test_save_root_policy_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "host-profile-runtime-test"
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
                    str(ROOT / "native" / "product" / "output_resolution_policy.cpp"),
                    str(ROOT / "native" / "product" / "host_product_state.cpp"),
                    str(ROOT / "native" / "product" / "host_profile_runtime.cpp"),
                    str(ROOT / "tests" / "native" / "host_profile_runtime_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
