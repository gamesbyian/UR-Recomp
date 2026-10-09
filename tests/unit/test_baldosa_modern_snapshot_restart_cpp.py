"""Native Modern acknowledged pause plus existing SRAM-preserving Retry."""
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class BaldosaModernSnapshotRestartTests(unittest.TestCase):
    def test_snapshot_reuses_modern_anchor(self):
        parts = (
            "output_resolution_policy.cpp", "host_product_state.cpp",
            "session_control.cpp", "session_runtime_adapter.cpp",
            "race_restart_anchor.cpp", "race_restart_lifecycle.cpp",
            "modern_session_runtime.cpp", "modern_session_c_api.cpp",
        )
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "baldosa-modern-snapshot"
            subprocess.run([
                "g++", "-std=c++17", "-O2", "-Wall", "-Wextra",
                "-Werror", "-pedantic", "-I", str(ROOT / "native/product"),
                *(str(ROOT / "native/product" / p) for p in parts),
                str(ROOT / "tests/native/baldosa_modern_snapshot_restart_test.cpp"),
                "-o", str(exe),
            ], cwd=ROOT, check=True)
            subprocess.run([str(exe)], cwd=ROOT, check=True)

if __name__ == "__main__":
    unittest.main()
