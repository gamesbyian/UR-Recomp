"""Compile and run the real Modern codec/CAS native SRAM checkpoint contract.

This deliberately exercises the production typed product/profile/catalog
stores, rather than an imitation codec or fake optimistic-lock interface.
A bounded unit surface, NOT a real Baldosa event/acknowledged guest shutdown.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class BaldosaNativeTypedSramCheckpointTest(unittest.TestCase):
    def test_real_modern_codec_and_cas_checkpoint_semantics(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if compiler is None:
            self.skipTest("C++17 compiler unavailable")
        sources = [
            ROOT / "tests/native/baldosa_native_profile_sram_checkpoint_test.cpp",
            *(
                ROOT / "native/product" / name
                for name in (
                    "output_resolution_policy.cpp",
                    "host_product_state.cpp",
                    "host_product_store.cpp",
                    "host_profile_runtime.cpp",
                    "host_profile_state.cpp",
                    "host_profile_store.cpp",
                    "host_profile_catalog.cpp",
                    "modern_racer_identity.cpp",
                )
            ),
        ]
        with tempfile.TemporaryDirectory() as folder:
            exe = Path(folder) / "native-profile-checkpoint"
            command = [
                compiler, "-std=c++17", "-O0", "-Wall", "-Wextra",
                "-Werror", "-pedantic", "-pthread",
                "-I", str(ROOT / "native/product"),
                *(str(p) for p in sources),
                "-o", str(exe),
            ]
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            execution = subprocess.run(
                [str(exe)], capture_output=True, text=True,
                timeout=35, cwd=folder,
            )
            self.assertEqual(
                execution.returncode, 0, execution.stdout + execution.stderr)
            self.assertIn("PASS: exact native SRAM post-write", execution.stdout)


if __name__ == "__main__":
    unittest.main()
