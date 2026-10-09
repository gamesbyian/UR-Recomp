"""Physical keyboard and P1 Start -> real Modern native session authority."""
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class BaldosaPhysicalPauseInputTest(unittest.TestCase):
    def test_native_modern_input_edges(self):
        sources = (
            "output_resolution_policy.cpp", "host_product_state.cpp",
            "session_control.cpp", "session_runtime_adapter.cpp",
            "race_restart_anchor.cpp", "race_restart_lifecycle.cpp",
            "modern_session_runtime.cpp", "modern_session_c_api.cpp",
        )
        with tempfile.TemporaryDirectory() as temp:
            exe = pathlib.Path(temp) / "physical-pause-edges"
            subprocess.run([
                "g++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
                "-pedantic", "-I", str(ROOT / "native/product"),
                *(str(ROOT / "native/product" / x) for x in sources),
                str(ROOT / "tests/native/baldosa_physical_pause_input_test.cpp"),
                "-o", str(exe),
            ], check=True, cwd=ROOT)
            subprocess.run([str(exe)], check=True, cwd=ROOT)

if __name__ == "__main__":
    unittest.main()
