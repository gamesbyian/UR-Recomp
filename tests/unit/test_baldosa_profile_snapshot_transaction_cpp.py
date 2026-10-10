"""Bounded candidate: acknowledge native guest before typed Modern SRAM CAS.

Compiles and runs the *real* host product/profile stores and real staged
write/rollback APIs, with one mock SRAM-flush callback only. This is not a
native Baldosa event, crash-recovery proof, or full shipping frontend.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "native/product"
SOURCES = [
    "host_product_state.cpp", "host_product_store.cpp",
    "host_profile_runtime.cpp", "host_profile_store.cpp",
    "host_profile_state.cpp", "host_profile_catalog.cpp",
    "modern_racer_identity.cpp", "output_resolution_policy.cpp",
]


class BaldosaProfileSnapshotTransactionTests(unittest.TestCase):
    def test_real_modern_cas_and_failure_rollbacks(self):
        cxx = shutil.which("g++")
        if cxx is None:
            self.skipTest("native C++ compiler unavailable")
        with tempfile.TemporaryDirectory() as directory:
            exe = Path(directory) / "native-profile-snapshot-test"
            subprocess.run(
                [
                    cxx, "-std=c++17", "-O2", "-Wall", "-Wextra",
                    "-Werror", "-pedantic", "-I", str(PRODUCT),
                    str(ROOT / "tests/native/baldosa_profile_snapshot_transaction_test.cpp"),
                    *(str(PRODUCT / name) for name in SOURCES),
                    "-o", str(exe),
                ],
                cwd=ROOT, check=True, timeout=90,
            )
            result = subprocess.run(
                [str(exe)], cwd=ROOT, text=True, capture_output=True,
                timeout=20, check=True,
            )
            self.assertIn(
                "PASS: acknowledged native guest SRAM CAS", result.stdout)


if __name__ == "__main__":
    unittest.main()
