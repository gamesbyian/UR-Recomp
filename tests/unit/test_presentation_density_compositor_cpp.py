import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class PresentationDensityCompositorCppTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = pathlib.Path(tmp) / "presentation-density-compositor-test"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(ROOT / "native" / "product"),
                    str(ROOT / "native" / "product" / "presentation_density_compositor.cpp"),
                    str(ROOT / "tests" / "native" / "presentation_density_compositor_test.cpp"),
                    "-o", str(exe),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(exe)], cwd=ROOT, check=True)
            # A plain x64 binary can appear pixel-exact while executing
            # undefined unaligned uint32_t loads/stores. Compile the same
            # real-source/full-field contract with GCC's alignment and
            # integer sanitizer to prevent that regression from returning.
            sanitized = pathlib.Path(tmp) / "presentation-density-alignment-ubsan"
            subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                    "-pedantic", "-fsanitize=alignment,undefined",
                    "-fno-sanitize-recover=all",
                    "-I", str(ROOT / "native" / "product"),
                    str(ROOT / "native" / "product" /
                        "presentation_density_compositor.cpp"),
                    str(ROOT / "tests" / "native" /
                        "presentation_density_compositor_test.cpp"),
                    "-o", str(sanitized),
                ],
                cwd=ROOT,
                check=True,
            )
            subprocess.run([str(sanitized)], cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()
