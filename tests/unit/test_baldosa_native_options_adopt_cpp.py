#!/usr/bin/env python3
"""Window-key display changes are adopted into the existing typed store."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "native/product"
LIFECYCLE = ROOT / "tools/baldosa_native_pause_lifecycle.cpp"


class NativeOptionsAdoptTests(unittest.TestCase):
    def test_cpp_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            exe = Path(directory) / "adopt"
            subprocess.run(
                ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-I", str(PRODUCT),
                 str(ROOT / "tests/native/baldosa_native_options_adopt_test.cpp"),
                 *(str(PRODUCT / name) for name in (
                     "output_resolution_policy.cpp", "host_product_state.cpp",
                     "host_product_store.cpp")),
                 "-o", str(exe)],
                check=True)
            run = subprocess.run([str(exe)], capture_output=True, text=True,
                                 cwd=directory, check=True)
            self.assertIn("PASS: live display adopted", run.stdout)

    def test_adoption_is_change_driven_and_shares_the_boot_gate(self):
        source = LIFECYCLE.read_text(encoding="utf-8")
        start = source.index("void adopt_live_display_change() {")
        glue = source[start:source.index("\n}\n", start)]
        # File I/O only when the live display actually changed; the first
        # observation is the boot-restored value, not a change.
        self.assertLess(glue.index("live == g_adopt_live_display"),
                        glue.index("baldosa_options_adopt_live_display("))
        # Same gate as baldosa_options_boot in the Modern root.
        self.assertIn('std::getenv("UR_BALDOSA_MODERN_ROOT")', glue)
        self.assertIn('std::strcmp(mode, "authentic") == 0', glue)
        self.assertIn("baldosa_native_options_user_path_utf8()", glue)
        self.assertIn("options_path.empty()", glue)
        self.assertIn("options_path, fullscreen, vsync", glue)
        self.assertNotIn('std::getenv("SNESRECOMP_USER_DATA_DIR")', glue)
        frame = source[source.index('extern "C" void ur_baldosa_product_after_run_frame('):]
        self.assertIn("adopt_live_display_change();", frame[:frame.index("\n}\n")])


if __name__ == "__main__":
    unittest.main()
