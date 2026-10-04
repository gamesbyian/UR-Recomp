#include "completed_run_ghost_raster.hpp"

#include <algorithm>
#include <cassert>
#include <cstdint>
#include <vector>

using namespace ur::presentation;

namespace {

ur::product::CompletedRunGhostPresentationFrame baseline_frame() {
    ur::product::CompletedRunGhostPresentationFrame frame;
    frame.semantic_frame_id = 0x0541;
    frame.composition = {
        0x0541, 0x0540, 0x0D0D, 0x0000, 0, 0, 0x0001, 0x0000};
    frame.screen_x = 80;
    frame.screen_y = 40;
    frame.hflip = false;
    frame.vflip = false;
    return frame;
}

}  // namespace

int main() {
    const auto frame = baseline_frame();
    const auto selected =
        select_completed_run_ghost_racer_presentation(
            GraphicsPack::Remastered, frame);
    assert(selected.uses_replacement());
    assert(selected.registration);

    constexpr int width = 256;
    constexpr int height = 224;
    std::vector<std::uint32_t> pixels(
        static_cast<std::size_t>(width) * height,
        0xff203040u);
    const auto before = pixels;

    assert(draw_completed_run_ghost_racer(
        reinterpret_cast<std::uint8_t*>(pixels.data()),
        static_cast<std::size_t>(width) * 4,
        width,
        height,
        1,
        frame,
        *selected.registration,
        128));

    std::size_t changed = 0;
    for (std::size_t i = 0; i < pixels.size(); ++i) {
        if (pixels[i] != before[i]) ++changed;
    }
    assert(changed > 0);

    // Zero opacity is deliberately inert.
    const auto after_draw = pixels;
    assert(!draw_completed_run_ghost_racer(
        reinterpret_cast<std::uint8_t*>(pixels.data()),
        static_cast<std::size_t>(width) * 4,
        width,
        height,
        1,
        frame,
        *selected.registration,
        0));
    assert(pixels == after_draw);

    // Semantic mismatch fails closed instead of drawing the wrong asset.
    auto wrong = frame;
    wrong.semantic_frame_id = 0x057D;
    assert(!draw_completed_run_ghost_racer(
        reinterpret_cast<std::uint8_t*>(pixels.data()),
        static_cast<std::size_t>(width) * 4,
        width,
        height,
        1,
        wrong,
        *selected.registration,
        128));

    // Offscreen clipping remains safe and can still draw the visible slice.
    auto clipped = frame;
    clipped.screen_x = -30;
    clipped.screen_y = -20;
    std::fill(pixels.begin(), pixels.end(), 0xff203040u);
    assert(draw_completed_run_ghost_racer(
        reinterpret_cast<std::uint8_t*>(pixels.data()),
        static_cast<std::size_t>(width) * 4,
        width,
        height,
        1,
        clipped,
        *selected.registration,
        128));

    assert(!draw_completed_run_ghost_racer(
        nullptr,
        static_cast<std::size_t>(width) * 4,
        width,
        height,
        1,
        frame,
        *selected.registration,
        128));

    return 0;
}
