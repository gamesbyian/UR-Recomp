import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class HostProfileGhostTargetCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "host-profile-ghost-target-test"
            profile = pathlib.Path(tmp) / "host-profile.txt"
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
                    str(ROOT / "native" / "product" / "host_profile_state.cpp"),
                    str(ROOT / "native" / "product" / "host_profile_store.cpp"),
                    str(ROOT / "native" / "product" / "host_profile_ghost_target.cpp"),
                    str(ROOT / "tests" / "native" / "host_profile_ghost_target_test.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe), str(profile)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
