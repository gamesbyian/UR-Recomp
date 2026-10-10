// The real Baldosa wide-host wrapper under a stubbed guest/PPU boundary.
// Test the production compositor delegate and all four source-world edges,
// not a second stand-in implementation of the wrapper.
#include "presentation_density_compositor.hpp"
#include "uniracers_ws_margins.h"
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <initializer_list>
#include <vector>

extern "C" {
// Production scene classification reads original guest WRAM, never edits it.
std::uint8_t g_ram[0x20000] = {};
}

namespace {
int g_scale = 1;
int g_last_margin = -1;
int g_calls = 0;
bool g_calibrated = false;
bool g_force_uncalibrated = false;
}

extern "C" void ur_ws_margins_prepare_frame(int enabled, int extra) {
    g_last_margin = enabled ? extra : 0;
    g_calibrated = enabled != 0;
}
extern "C" int ur_ws_margins_calibrated(void) {
    return g_calibrated && !g_force_uncalibrated ? 1 : 0;
}
extern "C" void ur_baldosa_hd_begin_sim_frame(unsigned) {}
extern "C" int ur_baldosa_hd_presentation_scale(void) { return g_scale; }
extern "C" int ur_baldosa_hd_draw_frame(
    std::uint8_t* dst, std::size_t pitch, const std::uint8_t* field,
    int width, int height, double) {
    ++g_calls;
    // At 342px the authored presenter refuses source-OBJ capture. Its
    // production 1x path returns unhandled so the wide wrapper owns stock
    // memcpy; 2x-4x use the exact nearest-density fallback.
    if (g_scale == 1) return 0;
    return ur::product::compose_nearest_density_frame(
        dst, pitch, field, width, height, g_scale) ? 1 : 0;
}

extern "C" void ur_baldosa_ws24_prepare_frame(int, int, int*, int*);
extern "C" void ur_baldosa_ws24_begin_sim_frame(unsigned);
extern "C" int ur_baldosa_ws24_draw_frame(
    std::uint8_t*, std::size_t, const std::uint8_t*, int, int, double);

static void check_frame(int scale, int logical_width) {
    constexpr int h = 224;
    const int row_pixels = logical_width * scale + 3;
    const auto pitch = static_cast<std::size_t>(row_pixels) * 4;
    const std::uint32_t sentinel = 0xDEADBEEFu;
    std::vector<std::uint32_t> field(
        static_cast<std::size_t>(logical_width) * h);
    std::vector<std::uint32_t> output(
        static_cast<std::size_t>(row_pixels) * h * scale, sentinel);
    // The top/bottom and left/centre/right pixels have independent colour.
    // This catches partial-width writes, wrong offsets and split seam bleed.
    for (int y = 0; y < h; ++y)
        for (int x = 0; x < logical_width; ++x)
            field[static_cast<std::size_t>(y) * logical_width + x] =
                0xFF000000u | (static_cast<std::uint32_t>(y) << 16) |
                static_cast<std::uint32_t>(x);
    const int before = g_calls;
    assert(ur_baldosa_ws24_draw_frame(
        reinterpret_cast<std::uint8_t*>(output.data()), pitch,
        reinterpret_cast<const std::uint8_t*>(field.data()),
        logical_width, h, 0.0) == 1);
    assert(g_calls == before + 1); // one compositor, not two renderers
    for (int y : {0, 111, 112, 223}) {
        for (int x : {0, 42, 43, 170, 298, 299, 341}) {
            if (x >= logical_width) continue;
            const auto expected =
                field[static_cast<std::size_t>(y) * logical_width + x];
            for (int sy = 0; sy < scale; ++sy)
                for (int sx = 0; sx < scale; ++sx)
                    assert(output[
                        static_cast<std::size_t>(y * scale + sy) * row_pixels +
                        x * scale + sx] == expected);
        }
    }
    for (int y = 0; y < h * scale; ++y)
        for (int x = logical_width * scale; x < row_pixels; ++x)
            assert(output[static_cast<std::size_t>(y) * row_pixels + x] ==
                   sentinel);
}

int main() {
    assert(setenv("UR_BALDOSA_WS342", "1", 1) == 0);
    ur_baldosa_ws24_begin_sim_frame(1800);
    int width = 0, height = 0;
    ur_baldosa_ws24_prepare_frame(0, 0, &width, &height);
    assert(width == 342 && height == 224 && g_last_margin == 48);
    for (int scale : {1, 2, 3, 4}) {
        g_scale = scale;
        check_frame(scale, width);
    }
    // Calibration failure must restore source width, never fabricate margins.
    g_force_uncalibrated = true;
    ur_baldosa_ws24_prepare_frame(0, 0, &width, &height);
    assert(width == 256 && height == 224);
    g_force_uncalibrated = false;
    ur_baldosa_ws24_begin_sim_frame(1799);
    ur_baldosa_ws24_prepare_frame(0, 0, &width, &height);
    assert(width == 256 && height == 224 && g_last_margin == 0);
    g_scale = 4;
    check_frame(g_scale, width);

    // Separate real-game lifecycle gating: no magic frame range and no
    // width expansion during setup/results, even after the first race.
    assert(setenv("UR_BALDOSA_WS342_LIVE", "1", 1) == 0);
    g_ram[0x0313] = 0x01; // Active, but no pre-race mode recognized.
    g_ram[0x009F] = 0x00;
    ur_baldosa_ws24_begin_sim_frame(3000);
    ur_baldosa_ws24_prepare_frame(0, 0, &width, &height);
    assert(width == 256 && height == 224 && g_last_margin == 0);

    g_ram[0x0313] = 0x00;
    g_ram[0x009F] = 0x3C; // Title-owned 1P pre-race latch.
    ur_baldosa_ws24_begin_sim_frame(3001);
    ur_baldosa_ws24_prepare_frame(0, 0, &width, &height);
    assert(width == 256 && g_last_margin == 0);
    g_ram[0x0313] = 0x01;
    g_ram[0x009F] = 0x00; // Incidental active-race frontend scratch.
    ur_baldosa_ws24_begin_sim_frame(3002);
    ur_baldosa_ws24_prepare_frame(0, 0, &width, &height);
    assert(width == 342 && height == 224 && g_last_margin == 48);
    for (int scale : {1, 2, 3, 4}) {
        g_scale = scale;
        check_frame(scale, width);
    }

    g_ram[0x0313] = 0x00;
    g_ram[0x009F] = 0xF9; // Terminal/results view stays centered.
    ur_baldosa_ws24_begin_sim_frame(3003);
    ur_baldosa_ws24_prepare_frame(0, 0, &width, &height);
    assert(width == 256 && height == 224 && g_last_margin == 0);

    g_ram[0x009F] = 0x3E; // VS pre-race.
    ur_baldosa_ws24_begin_sim_frame(3004);
    ur_baldosa_ws24_prepare_frame(0, 0, &width, &height);
    assert(width == 256);
    g_ram[0x0313] = 0x01;
    g_ram[0x009F] = 0x00;
    g_force_uncalibrated = true; // No guessed course pixels on failure.
    ur_baldosa_ws24_begin_sim_frame(3005);
    ur_baldosa_ws24_prepare_frame(0, 0, &width, &height);
    assert(width == 256 && height == 224);
    g_force_uncalibrated = false;
    ur_baldosa_ws24_begin_sim_frame(3006);
    ur_baldosa_ws24_prepare_frame(0, 0, &width, &height);
    assert(width == 342 && height == 224);
    g_scale = 4;
    check_frame(g_scale, width);
    return 0;
}
