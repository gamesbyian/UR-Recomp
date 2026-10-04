import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class HostProfileStoreCppTests(unittest.TestCase):
    def test_process_restart_legacy_default_recovery_and_authentic_inertness(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "host-profile-store-acceptance"
            state = pathlib.Path(tmp) / "profile.state"
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
                    str(ROOT / "native" / "product" / "host_profile_state.cpp"),
                    str(ROOT / "native" / "product" / "host_profile_store.cpp"),
                    str(ROOT / "tests" / "native" / "host_profile_store_acceptance.cpp"),
                    "-o",
                    str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            for mode in (
                "save",
                "load",
                "legacy-host-default",
                "malformed",
                "authentic",
            ):
                subprocess.run([str(exe), mode, str(state)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
