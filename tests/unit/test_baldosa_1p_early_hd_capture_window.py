"""Compile and exercise the exact real opt-in first-party P1 screenshot window."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class EarlyOnePlayerCapturedArtTests(unittest.TestCase):
    def test_native_capture_selector_preserves_existing_two_player_window(self):
        compiler = shutil.which("c++") or shutil.which("g++")
        if not compiler:
            self.skipTest("C++ compiler unavailable")
        source = (ROOT / "tools/baldosa_native_racer_presentation.cpp").read_text()
        start = source.index("bool authored_capture_window(unsigned frame) noexcept {")
        stop = source.index("int density() noexcept {", start)
        body = source[start:stop]
        self.assertEqual(source.count("bool authored_capture_window(unsigned frame) noexcept {"), 1)
        self.assertIn('std::getenv("UR_BALDOSA_HD_EARLY_1P_CAPTURE")', body)
        self.assertIn("authored_capture_window(g_frame)", source)
        snippet = r"""
#include <cassert>
#include <cstdlib>
#include <cstring>
""" + body + r"""
int main() {
    assert(!authored_capture_window(1699));
    assert(!authored_capture_window(1728));
    assert(!authored_capture_window(1744));
    assert(authored_capture_window(1800));
    assert(authored_capture_window(1856));
    assert(authored_capture_window(2450));
    assert(!authored_capture_window(2451));
    setenv("UR_BALDOSA_HD_EARLY_1P_CAPTURE", "1", 1);
    assert(!authored_capture_window(1699));
    assert(authored_capture_window(1700));
    assert(authored_capture_window(1728));
    assert(authored_capture_window(1744));
    assert(authored_capture_window(1799));
    assert(authored_capture_window(1808));
    assert(!authored_capture_window(2451));
    setenv("UR_BALDOSA_HD_EARLY_1P_CAPTURE", "yes", 1);
    assert(!authored_capture_window(1728));
}
"""
        with tempfile.TemporaryDirectory() as td:
            cpp, exe = Path(td) / "window.cpp", Path(td) / "window"
            cpp.write_text(snippet)
            subprocess.run([compiler, "-std=c++17", str(cpp), "-o", str(exe)],
                           check=True, capture_output=True, text=True)
            subprocess.run([str(exe)], check=True, capture_output=True, text=True)

    def test_native_1p_route_opt_in_does_not_enable_unsafe_fixture(self):
        workflow = (ROOT / ".github/workflows/baldosa-core-spike.yml").read_text()
        self.assertIn("UR_BALDOSA_HD_EARLY_1P_CAPTURE=1", workflow)
        self.assertIn("env -u UR_RACER_HD_UNSAFE_OVERLAP_FIXTURE", workflow)
        self.assertIn("-u UR_BALDOSA_HD_SOURCE_ART_FIXTURE", workflow)
        self.assertIn("race_1p_ur_guarded_hd", workflow)


if __name__ == "__main__":
    unittest.main()
