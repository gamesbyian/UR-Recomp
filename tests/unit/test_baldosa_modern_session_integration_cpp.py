"""Check acknowledged Baldosa lifecycle through the existing Modern session ABI."""
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class BaldosaModernSessionIntegrationTests(unittest.TestCase):
    def test_native_lifecycle_contract(self):
        sources = (
            "output_resolution_policy.cpp",
            "host_product_state.cpp",
            "session_control.cpp",
            "session_runtime_adapter.cpp",
            "race_restart_anchor.cpp",
            "race_restart_lifecycle.cpp",
            "modern_session_runtime.cpp",
            "modern_session_c_api.cpp",
        )
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "baldosa-modern-session-test"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", "-I", str(ROOT / "native/product"),
                    *(str(ROOT / "native/product" / source) for source in sources),
                    str(ROOT / "tests/native/baldosa_modern_session_integration_test.cpp"),
                    "-o", str(exe),
                ],
                cwd=ROOT, check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
