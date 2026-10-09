"""Compile and execute the real Baldosa wide bridge with isolated PPU stubs."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class BaldosaWideDensityBridgeTest(unittest.TestCase):
    def test_wide_host_1x_through_4x(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "baldosa-wide-density-bridge"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
                    "-I", str(ROOT / "native/title"),
                    "-I", str(ROOT / "native/product"),
                    str(ROOT / "tests/native/baldosa_wide_density_bridge_test.cpp"),
                    str(ROOT / "tools/baldosa_native_ws24_presentation.cpp"),
                    str(ROOT / "native/product/presentation_density_compositor.cpp"),
                    "-o", str(target),
                ],
                check=True,
                cwd=ROOT,
            )
            subprocess.run([str(target)], check=True, cwd=ROOT)


if __name__ == "__main__":
    unittest.main()
