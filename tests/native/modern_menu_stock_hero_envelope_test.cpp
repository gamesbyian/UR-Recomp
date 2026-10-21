// ROM-free negative test of the real source-gated Original hero compositor.
// All pixels are synthetic. No art is admitted or distributed by this test.
#include "native/product/modern_menu_stock_hero.hpp"

#include <cassert>
#include <cstdint>
#include <vector>

int main() {
    using namespace ur::product;
    std::vector<std::uint32_t> a(kModernMenuStockHeroPixels, 0u);
    std::vector<std::uint32_t> b(kModernMenuStockHeroPixels, 0u);
    a[32 * 64 + 32] = 0xffff0000u;
    b[32 * 64 + 32] = 0xff00ff00u;
    ModernMenuStockHeroFrame frames[2]{
        {a.data(), a.size(), 0x0541,
         modern_menu_stock_hero_digest(a.data(), a.size()), true},
        {b.data(), b.size(), 0x0540,
         modern_menu_stock_hero_digest(b.data(), b.size()), true},
    };
    const ModernMenuStockHeroSequence sequence{frames, 2, true};
    ModernMenuMotionPose pose{};
    pose.visible = true;
    const HostOverlayRect safe{0, 0, 256, 224};
    std::vector<std::uint32_t> pixels(256u * 224u, 0xff151515u);
    auto before = pixels;

    // At the CURRENT pose this pixel is fully inside 256x224. A later
    // selection lean (-1), or a future bob (-2), would crop the SAME real
    // source pixel. Refuse both before drawing even with reduced motion.
    for (bool reduced : {false, true}) {
        pose.reduced_motion = reduced;
        pose.hero_bob_px = 0;
        pose.hero_lean_px = 0;
        assert(paint_modern_menu_stock_hero(
            pixels.data(), 256, 224, safe, {-32, 20, 1},
            sequence, pose) == ModernMenuStockHeroDraw::OutOfBounds);
        assert(pixels == before);
        assert(paint_modern_menu_stock_hero(
            pixels.data(), 256, 224, safe, {20, -32, 1},
            sequence, pose) == ModernMenuStockHeroDraw::OutOfBounds);
        assert(pixels == before);
    }
    pose.reduced_motion = false;

    // The SECOND registered source pose near the right boundary can
    // invalidate an otherwise currently in-bounds frame zero.
    b[32 * 64 + 63] = 0xff00ff00u;
    frames[1].source_argb_digest =
        modern_menu_stock_hero_digest(b.data(), b.size());
    assert(paint_modern_menu_stock_hero(
        pixels.data(), 256, 224, safe, {192, 30, 1},
        sequence, pose) == ModernMenuStockHeroDraw::OutOfBounds);
    assert(pixels == before);
    b[32 * 64 + 63] = 0u;
    frames[1].source_argb_digest =
        modern_menu_stock_hero_digest(b.data(), b.size());

    // One extra pixel of breathing clearance admits EVERY registered
    // frame, all future motion, and both reduced/normal modes.
    assert(paint_modern_menu_stock_hero(
        pixels.data(), 256, 224, safe, {-31, 20, 1},
        sequence, pose) == ModernMenuStockHeroDraw::Drawn);
    assert(pixels[52 * 256 + 1] == 0xffff0000u);

    std::vector<std::uint32_t> large(1024u * 896u, 0xff151515u);
    const HostOverlayRect large_safe{0, 0, 1024, 896};
    auto unchanged = large;
    pose.hero_lean_px = -1;
    assert(paint_modern_menu_stock_hero(
        large.data(), 1024, 896, large_safe, {-128, 80, 4},
        sequence, pose) == ModernMenuStockHeroDraw::OutOfBounds);
    assert(large == unchanged);
    pose.hero_lean_px = 0;
    assert(paint_modern_menu_stock_hero(
        large.data(), 1024, 896, large_safe, {-124, 80, 4},
        sequence, pose) == ModernMenuStockHeroDraw::Drawn);

    // The gesture admission envelope must track the actual source-model
    // bounded bob/lean contract, not invented tween amplitudes.
    ModernMenuMotionState state{};
    for (std::uint64_t tick = 0; tick < 256; ++tick) {
        const auto selection = static_cast<std::uint8_t>((tick / 19) % 5);
        auto real_pose = advance_modern_menu_motion(
            state, {tick, selection, true, false});
        assert(real_pose.hero_bob_px >= -2 && real_pose.hero_bob_px <= 0);
        assert(real_pose.hero_lean_px >= -1 && real_pose.hero_lean_px <= 1);
    }
    pose.hero_bob_px = -3; // non-source invented motion must fail closed
    assert(paint_modern_menu_stock_hero(
        large.data(), 1024, 896, large_safe, {400, 80, 4},
        sequence, pose) == ModernMenuStockHeroDraw::OutOfBounds);
    return 0;
}
