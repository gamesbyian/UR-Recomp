"""ROM-free production host-state Unicode path regression.

The source is UTF-8 as returned by SDL_GetPrefPath. This test is not a
Windows physical, power-loss or release acceptance test.
"""
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class HostProductUnicodePathCppTests(unittest.TestCase):
    def test_production_utf8_path_roundtrip(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "host-product-unicode-path-test"
            cmd = [
                compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                "-pedantic", "-I", str(ROOT / "native" / "product"),
                str(ROOT / "native" / "product" / "output_resolution_policy.cpp"),
                str(ROOT / "native" / "product" / "host_product_state.cpp"),
                str(ROOT / "native" / "product" / "host_product_store.cpp"),
                str(ROOT / "tests" / "native" / "host_product_unicode_path_regression.cpp"),
                "-o", str(exe),
            ]
            subprocess.run(cmd, cwd=ROOT, check=True, timeout=90)
            subprocess.run([str(exe)], cwd=ROOT, check=True, timeout=30)


if __name__ == "__main__":
    unittest.main()
