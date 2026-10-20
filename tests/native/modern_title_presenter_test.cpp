// The host Modern title must work at genuine 342x224 and in 256 fallback.
// Use the exact production presenter with a bounds-checking painter.
#include "native/product/modern_title_presenter.hpp"

#include <algorithm>
#include <cassert>
#include <cstdint>
#include <string>
#include <vector>

using namespace ur::product;
namespace {
struct Surface {
    std::vector<std::uint32_t> pixels;
    int stride;
    int height;
    explicit Surface(int w) : pixels(static_cast<std::size_t>(w) * 224, 0x12345678u),
                              stride(w), height(224) {}
};
std::vector<std::string> words;
int fill_count = 0;
void fill(std::uint32_t* pixels, int stride, int height,
          int x, int y, int w, int h, std::uint32_t color) {
    assert(x >= 0 && y >= 0 && w >= 0 && h >= 0);
    assert(x + w <= stride && y + h <= height);
    for (int row = y; row < y + h; ++row)
        std::fill_n(pixels + row * stride + x, w, color);
    ++fill_count;
}
void stroke(std::uint32_t* p, int stride, int height,
            int x, int y, int w, int h, std::uint32_t color) {
    fill(p, stride, height, x, y, w, 1, color);
    fill(p, stride, height, x, y + h - 1, w, 1, color);
}
void text(std::uint32_t*, int, int, int, int,
          const char* value, std::uint32_t, int) {
    words.emplace_back(value);
}
bool saw(const char* text) {
    return std::find(words.begin(), words.end(), text) != words.end();
}
} // namespace

int main() {
    constexpr ModernRootOverlayPainter paint{&fill, &stroke, &text};
    static_assert(!modern_title_active(modern_title_boot(false)), "Authentic/bypass");
    static_assert(modern_title_active(modern_title_boot(true)), "native intro");
    auto state = modern_title_boot(true);
    assert(state.phase == ModernTitlePhase::Intro);
    state = modern_title_confirm(state);
    assert(state.phase == ModernTitlePhase::Leaving);
    for (int i = 0; i < 13; ++i) {
        state = modern_title_advance(state);
        assert(modern_title_active(state));
        const auto repeated = modern_title_confirm(state);
        assert(repeated.phase == ModernTitlePhase::Leaving);
        assert(repeated.exit_age == state.exit_age);
    }
    state = modern_title_advance(state);
    assert(state.phase == ModernTitlePhase::Root);
    assert(!modern_title_active(state));
    state = modern_title_confirm(state);
    assert(state.phase == ModernTitlePhase::Root);
    // Match the independently owned root animation's UR_REDUCED_MOTION=1
    // policy: the title remains readable, but there is no pulse/slide.
    auto quiet = modern_title_boot(true, true);
    assert(modern_title_active(quiet));
    assert(quiet.age >= 24);
    quiet = modern_title_confirm(quiet);
    assert(!modern_title_active(quiet));

    for (int width : {256, 342}) {
        Surface surf(width);
        words.clear();
        fill_count = 0;
        auto opening = modern_title_boot(true);
        for (int i = 0; i < 50; ++i)
            opening = modern_title_advance(opening);
        assert(render_modern_title(paint, surf.pixels.data(),
                surf.stride, surf.height, width, opening));
        assert(saw("UNIRACERS"));
        assert(saw("THE ONE-WHEEL RACING CLASSIC"));
        assert(saw("PRESS A / START"));
        assert(!saw("UNIRALLY"));
        // Full original-title pixel art is read from the verified retail
        // asset, not procedurally reconstructed. Digest the exact unscaled
        // 238x81 crop through the Modern host framebuffer.
        const auto asset_digest = [&surf, width]() {
            std::uint64_t h = 1469598103934665603ull;
            const int left = (width - regional_title_asset::kWidth) / 2;
            for (int y = 27; y < 27 + regional_title_asset::kHeight; ++y) {
                for (int x = left; x < left + regional_title_asset::kWidth; ++x) {
                    const std::uint32_t p = surf.pixels[y * surf.stride + x];
                    for (int shift = 0; shift <= 16; shift += 8) {
                        h ^= (p >> shift) & 0xffu;
                        h *= 1099511628211ull;
                    }
                }
            }
            return h;
        };
        assert(asset_digest() == regional_title_asset::kSourceCropBgrFnv1a64);
        assert(fill_count > 100);  // track sections and wheel ring
        assert(surf.pixels.front() != 0x12345678u);
        assert(surf.pixels.back() != 0x12345678u);
        // Its own logo placement, not a 342-column crop on the narrow host.
        words.clear();
        assert(render_modern_title(paint, surf.pixels.data(),
                surf.stride, surf.height, width, opening, true));
        assert(saw("UNIRALLY"));
        assert(!saw("UNIRACERS"));
        assert(asset_digest() == regional_title_asset::kTargetCropBgrFnv1a64);
        words.clear();
        opening = modern_title_confirm(opening);
        assert(render_modern_title(paint, surf.pixels.data(),
                surf.stride, surf.height, width, opening));
        assert(saw("SELECTING RACER"));
        assert(!saw("PRESS A / START"));
        words.clear();
        assert(!render_modern_title(paint, surf.pixels.data(),
                surf.stride, surf.height, width, modern_title_boot(false)));
    }
    Surface wrong(342);
    assert(!render_modern_title(paint, wrong.pixels.data(),
            wrong.stride, wrong.height, 343, modern_title_boot(true)));
    assert(!render_modern_title(paint, wrong.pixels.data(),
            wrong.stride, 200, 342, modern_title_boot(true)));
    assert(wrong.pixels.front() == 0x12345678u);
    return 0;
}
