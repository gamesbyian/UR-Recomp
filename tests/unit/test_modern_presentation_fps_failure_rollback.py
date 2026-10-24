"""Executable host-function regression for refused presentation FPS/VSync changes.

Compiles the exact apply_presentation_fps_setting function from the current
native host against bounded fake desktop hooks. This proves live cadence
rollback, not an SDL device or physical Windows acceptance.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
HOST = ROOT / "native/product/uniracers_modern_host.cpp"
START = "bool apply_presentation_fps_setting("
END = "bool apply_display_mode_setting("

MOCKS = r"""
#include <cstdio>
#include <cstdlib>

namespace ur::product {
enum class HostPresentationFpsMode { Game, Fps90 };
enum class HostVSyncMode { Off, On };
struct HostSettings {
    HostPresentationFpsMode presentation_fps_mode =
        HostPresentationFpsMode::Game;
    HostVSyncMode vsync_mode = HostVSyncMode::On;
};
struct HostProductState { HostSettings settings; };
}
ur::product::HostProductState g_product_state{};
auto g_live_presentation_fps_mode =
    ur::product::HostPresentationFpsMode::Game;
bool g_modern = true;
int g_resets = 0;
int g_vsync_calls = 0;
int g_fail_calls = 0;
int g_last_vsync = -1;
bool modern_mode() { return g_modern; }
int vsync_mode_value(ur::product::HostVSyncMode mode) {
    return mode == ur::product::HostVSyncMode::On ? 1 : 0;
}
void snesrecomp_desktop_request_clock_reset() { ++g_resets; }
int snesrecomp_desktop_set_vsync(int mode) {
    ++g_vsync_calls;
    if (g_vsync_calls <= g_fail_calls) return 0;
    g_last_vsync = mode;
    return 1;
}
void product_diagnostic(const char*) {}
const char* presentation_fps_mode_name(
    ur::product::HostPresentationFpsMode) { return "mode"; }
double presentation_fps_target(
    ur::product::HostPresentationFpsMode, double) { return 90.; }
"""

CHECKS = r"""
int main() {
    using namespace ur::product;
    HostSettings candidate{};
    candidate.presentation_fps_mode = HostPresentationFpsMode::Fps90;

    // Failure after a live mode change must restore both cadence and VSync.
    g_fail_calls = 1;
    if (apply_presentation_fps_setting(candidate)) return 1;
    if (g_live_presentation_fps_mode != HostPresentationFpsMode::Game)
        return 2;
    if (g_resets != 2 || g_vsync_calls != 2 || g_last_vsync != 1)
        return 3;

    // Even two driver refusals must never commit the failed cadence.
    g_fail_calls = 2;
    g_vsync_calls = g_resets = 0;
    g_last_vsync = -1;
    if (apply_presentation_fps_setting(candidate)) return 4;
    if (g_live_presentation_fps_mode != HostPresentationFpsMode::Game)
        return 5;
    if (g_resets != 2 || g_vsync_calls != 2) return 6;

    // Successful apply retains the requested cadence without rollback.
    g_fail_calls = 0;
    g_vsync_calls = g_resets = 0;
    if (!apply_presentation_fps_setting(candidate)) return 7;
    if (g_live_presentation_fps_mode != HostPresentationFpsMode::Fps90)
        return 8;
    if (g_resets != 1 || g_vsync_calls != 1) return 9;

    // Authentic mode must not mutate the active host state.
    g_modern = false;
    g_vsync_calls = g_resets = 0;
    if (apply_presentation_fps_setting(candidate)) return 10;
    if (g_resets || g_vsync_calls) return 11;
    return 0;
}
"""


class PresentationFpsApplyRollbackTests(unittest.TestCase):
    def test_real_host_function_rolls_back_on_vsync_refusal(self):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if not compiler:
            self.skipTest("No C++ compiler available")
        source = HOST.read_text(encoding="utf-8")
        start = source.index(START)
        end = source.index(END, start)
        function = source[start:end]
        self.assertIn("g_live_presentation_fps_mode = previous_mode;", function)
        self.assertIn("g_product_state.settings.vsync_mode", function)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            cpp = path / "fps_apply.cpp"
            exe = path / "fps_apply"
            cpp.write_text(MOCKS + function + CHECKS, encoding="utf-8")
            subprocess.run(
                [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                 "-pedantic", str(cpp), "-o", str(exe)],
                check=True, capture_output=True, text=True,
            )
            subprocess.run([str(exe)], check=True, capture_output=True,
                           text=True)


if __name__ == "__main__":
    unittest.main()
