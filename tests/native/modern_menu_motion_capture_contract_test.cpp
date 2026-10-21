// Synthetic TEST-ONLY source-paced C++ motion/pixel oracle consumed by an
// independent Python verifier. These rows are NOT true native host captures
// or SDL-presented frames. No guest, controller or game runtime is emulated.
#include "modern_menu_motion.hpp"

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

namespace {

struct PaintPixels {
    bool valid() const noexcept { return true; }

    void fill_rect(std::uint32_t* pixels, int stride, int height,
                   int x, int y, int width, int rect_height,
                   std::uint32_t colour) const noexcept {
        if (!pixels || stride <= 0 || height <= 0 || width <= 0 ||
            rect_height <= 0 || x < 0 || y < 0 || x > stride ||
            y > height || width > stride - x ||
            rect_height > height - y) return;
        for (int py = y; py < y + rect_height; ++py)
            for (int px = x; px < x + width; ++px)
                pixels[static_cast<std::size_t>(py) * stride + px] = colour;
    }
};

bool inspect_actual_marker_pixels(const std::vector<std::uint32_t>& buffer,
                                  int stride, const ur::product::ModernMenuMotionPose& pose,
                                  int root_x) noexcept {
    using namespace ur::product;
    int count = 0, x_min = stride, x_max = -1, y_min = 224, y_max = -1;
    for (int y = 0; y < 224; ++y) {
        for (int x = 0; x < stride; ++x) {
            const auto value = buffer[static_cast<std::size_t>(y) * stride + x];
            if (value == 0u) continue;
            if (value != kModernStockMenuPalette.cursor_blue) return false;
            ++count;
            x_min = std::min(x_min, x);
            x_max = std::max(x_max, x);
            y_min = std::min(y_min, y);
            y_max = std::max(y_max, y);
        }
    }
    const bool inset = !pose.reduced_motion &&
        pose.cursor_spin_phase >= 4 && pose.cursor_spin_phase < 12;
    const int height = inset ? 10 : 12;
    const int expected_y = 10 + 57 + 21 * pose.selection +
        pose.cursor_remainder_px + (inset ? 1 : 0);
    return count == 2 * height && x_min == root_x + 5 &&
           x_max == root_x + 6 && y_min == expected_y &&
           y_max == expected_y + height - 1;
}

} // namespace

int main(int argc, char** argv) {
    const bool wide = argc == 2 &&
        std::strcmp(argv[1], "--wide") == 0;
    if (argc > 2 || (argc == 2 && !wide)) return 2;
    const int width = wide ? 342 : 256;
    const int root_x = wide ? 11 : 8;
    const int root_w = wide ? 320 : 240;
    const ur::product::HostOverlayRect root_rect{root_x, 10, root_w, 204};

    std::vector<std::uint32_t> pixels(
        static_cast<std::size_t>(width) * 224u, 0);
    const PaintPixels painter{};
    ur::product::ModernMenuMotionState state{};
    unsigned selection = 0;
    for (unsigned i = 0; i < 48; ++i) {
        // Real UI semantics would be driven by controller navigation;
        // here they are deterministic synthetic edges testing the model.
        switch (i) {
        case 1: selection = 1; break;
        case 4: selection = 0; break;
        case 6: selection = 1; break;
        case 8: selection = 3; break; // discontinuous skip snaps
        case 10: selection = 2; break;
        case 12: selection = 1; break;
        case 33: selection = 2; break;
        case 37: selection = 1; break;
        default: break;
        }
        const bool reduced = i >= 25 && i < 29;
        const std::uint64_t tick = 14u + i;
        const auto pose = ur::product::advance_modern_menu_motion(
            state,
            {tick, static_cast<std::uint8_t>(selection), true, reduced});
        if (!pose.visible || pose.selection != selection) return 3;

        std::fill(pixels.begin(), pixels.end(), 0u);
        const bool painted = ur::product::paint_modern_menu_selection_motion(
            painter, pixels.data(), width, 224, 1, root_rect, pose);
        if (!painted ||
            !inspect_actual_marker_pixels(pixels, width, pose, root_x))
            return 4;

        std::printf(
            "UR_MODERN_MENU_MOTION_CAPTURE ordinal=%u tick60=%llu "
            "selection=%u spin=%d offset=%d entrance=%d reduced=%u "
            "root_x=%d root_w=%d surface_w=%d surface_h=224 painted=%u\n",
            i, static_cast<unsigned long long>(tick), selection,
            pose.cursor_spin_phase, pose.cursor_remainder_px,
            pose.entrance_distance_px, reduced ? 1u : 0u,
            root_x, root_w, width, painted ? 1u : 0u);
    }
    return 0;
}
