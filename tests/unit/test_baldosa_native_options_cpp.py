#!/usr/bin/env python3
"""Compile and run the real native Options model against the real store."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "native/product"


class NativeOptionsModelTests(unittest.TestCase):
    def _build_and_run(self, extra_flags):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        files = [
            ROOT / "tests/native/baldosa_native_options_test.cpp",
            *[PRODUCT / name for name in (
                "output_resolution_policy.cpp",
                "host_product_state.cpp",
                "host_product_store.cpp",
            )],
        ]
        with tempfile.TemporaryDirectory() as directory:
            exe = Path(directory) / "options"
            built = subprocess.run(
                [compiler, "-std=c++17", "-O0", "-g", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-pthread", *extra_flags,
                 "-I", str(PRODUCT), *map(str, files), "-o", str(exe)],
                capture_output=True, text=True, timeout=180)
            self.assertEqual(built.returncode, 0, built.stderr + built.stdout)
            run = subprocess.run(
                [str(exe)], capture_output=True, text=True,
                cwd=directory, timeout=60)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            self.assertIn("PASS: native Options apply, persist, roll back",
                          run.stdout)

    def test_options_model_strict(self):
        self._build_and_run([])

    def _sanitizers_available(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            return False
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "probe.cpp"
            source.write_text("int main() { return 0; }\n")
            built = subprocess.run(
                [compiler, "-fsanitize=address,undefined", str(source),
                 "-o", str(Path(directory) / "probe")],
                capture_output=True, text=True, timeout=120)
            return built.returncode == 0

    def test_options_model_under_sanitizers(self):
        # Capability probe only: the Windows MinGW toolchain ships no
        # libasan/libubsan; the strict build above still runs everywhere.
        if not self._sanitizers_available():
            self.skipTest("sanitizer runtime unavailable on this toolchain")
        self._build_and_run(["-fsanitize=address,undefined",
                             "-fno-sanitize-recover=all"])


if __name__ == "__main__":
    unittest.main()
