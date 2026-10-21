"""Compile ROM-free negative coverage for all future original-hero motion offsets."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tests/native/modern_menu_stock_hero_envelope_test.cpp"


class OriginalHeroEnvelopeTest(unittest.TestCase):
    def test_real_cpp_compositor_rejects_future_frame_clipping(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("C++17 compiler unavailable")
        with tempfile.TemporaryDirectory() as temp:
            exe = Path(temp) / "hero-envelope-test"
            build = subprocess.run(
                [compiler, "-std=c++17", "-O1", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", "-I", str(ROOT), str(TEST),
                 "-o", str(exe)],
                text=True, capture_output=True, check=False)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run(
                [str(exe)], text=True, capture_output=True, check=False)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_strictly_optional_source_racer(self):
        header = (ROOT / "native/product/modern_menu_stock_hero.hpp").read_text(
            encoding="utf-8")
        self.assertIn("source_argb_digest", header)
        self.assertIn("original_pose_order_verified", header)
        self.assertIn("original_raster_source_verified", header)
        self.assertNotIn("SDL_", header)
        self.assertNotIn("guest_wram", header)
        self.assertIn("envelope_left", header)
        self.assertIn("envelope_right", header)
        self.assertIn("envelope_top", header)
        self.assertIn("envelope_bottom", header)


if __name__ == "__main__":
    unittest.main()
