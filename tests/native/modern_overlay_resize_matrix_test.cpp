#include "modern_overlay_composition.hpp"
#include "widescreen_output_composition.hpp"

#include <array>
#include <cassert>
#include <cstdint>

using namespace ur::product;

namespace {

struct Drawable {
    int width;
    int height;
};

constexpr std::array<Drawable, 13> kDrawables{{
    {640, 480},
    {800, 600},
    {1024, 768},
    {1280, 720},
    {1366, 768},
    {1600, 900},
    {1920, 1080},
    {2560, 1440},
    {3840, 2160},
    {853, 479},
    {1277, 719},
    {1001, 733},
    {311, 197},
}};

void assert_rect_inside(
    const HostOverlayRect& rect,
    const HostOutputViewport& viewport) {
    assert(rect.width > 0);
    assert(rect.height > 0);
    assert(rect.x >= viewport.x);
    assert(rect.y >= viewport.y);
    assert(rect.x + rect.width <= viewport.x + viewport.width);
    assert(rect.y + rect.height <= viewport.y + viewport.height);
}

HostOverlayCompositionRequest timing_request(
    const HostOutputCompositionPlan& composition,
    const HostOutputViewport& viewport,
    int scale) {
    HostOverlayCompositionRequest request{};
    request.logical_surface_width = composition.logical_view_width;
    request.logical_surface_height = composition.logical_view_height;
    request.presentation_scale = scale;
    request.output_viewport = viewport;
    request.anchor = HostOverlayAnchor::TopRight;
    request.preferred_width = 178;
    request.preferred_height = 52;
    request.minimum_width = 178;
    request.minimum_height = 52;
    request.edge_margin = 8;
    return request;
}

}  // namespace

int main() {
    const auto fixed_original = resolve_16x9_output_composition(
        HostGraphicsRepresentation::Original,
        HostSceneComposition::FixedCenter);
    const auto wide_original = resolve_16x9_output_composition(
        HostGraphicsRepresentation::Original,
        HostSceneComposition::WorldExpand);
    const auto fixed_remastered = resolve_16x9_output_composition(
        HostGraphicsRepresentation::Remastered,
        HostSceneComposition::FixedCenter);

    const HostOverlayRect fixed_expected{70, 8, 178, 52};
    const HostOverlayRect wide_expected{156, 8, 178, 52};

    for (const auto drawable : kDrawables) {
        for (const auto* composition :
             {&fixed_original, &wide_original, &fixed_remastered}) {
            const auto viewport = resolve_output_viewport(
                *composition, drawable.width, drawable.height);
            assert(viewport.width > 0);
            assert(viewport.height > 0);
            assert(viewport.x >= 0);
            assert(viewport.y >= 0);
            assert(viewport.x + viewport.width <= drawable.width);
            assert(viewport.y + viewport.height <= drawable.height);

            const auto at_1x = resolve_modern_overlay_composition(
                timing_request(*composition, viewport, 1));
            assert(at_1x.visible);
            assert_rect_inside(at_1x.output_rect, viewport);

            const HostOverlayRect expected =
                composition->logical_view_width == 342
                    ? wide_expected
                    : fixed_expected;
            assert(at_1x.logical_rect == expected);

            for (int scale = 2; scale <= 4; ++scale) {
                const auto scaled = resolve_modern_overlay_composition(
                    timing_request(*composition, viewport, scale));
                assert(scaled.visible);
                assert(scaled.logical_rect == at_1x.logical_rect);
                assert(scaled.output_rect == at_1x.output_rect);
                assert(scaled.presentation_rect.x ==
                       scaled.logical_rect.x * scale);
                assert(scaled.presentation_rect.y ==
                       scaled.logical_rect.y * scale);
                assert(scaled.presentation_rect.width ==
                       scaled.logical_rect.width * scale);
                assert(scaled.presentation_rect.height ==
                       scaled.logical_rect.height * scale);
            }
        }
    }

    // Letterboxed/pillarboxed drawable changes affect only the final viewport
    // projection. Logical anchoring is invariant.
    const auto viewport_4x3 =
        resolve_output_viewport(fixed_original, 1024, 768);
    const auto viewport_ultrawide =
        resolve_output_viewport(fixed_original, 2560, 1080);
    const auto plan_4x3 = resolve_modern_overlay_composition(
        timing_request(fixed_original, viewport_4x3, 2));
    const auto plan_ultrawide = resolve_modern_overlay_composition(
        timing_request(fixed_original, viewport_ultrawide, 2));
    assert(plan_4x3.logical_rect == plan_ultrawide.logical_rect);
    assert(plan_4x3.presentation_rect == plan_ultrawide.presentation_rect);
    assert(!(plan_4x3.output_rect == plan_ultrawide.output_rect));
    assert_rect_inside(plan_4x3.output_rect, viewport_4x3);
    assert_rect_inside(plan_ultrawide.output_rect, viewport_ultrawide);

    // Constrained logical space compacts deterministically until the caller's
    // minimum is crossed, then fails closed rather than escaping the safe area.
    HostOverlayCompositionRequest compact{};
    compact.logical_surface_width = 148;
    compact.logical_surface_height = 224;
    compact.presentation_scale = 3;
    compact.output_viewport = {0, 0, 444, 672};
    compact.anchor = HostOverlayAnchor::TopRight;
    compact.preferred_width = 178;
    compact.preferred_height = 52;
    compact.minimum_width = 120;
    compact.minimum_height = 52;
    compact.edge_margin = 8;
    const auto compact_plan = resolve_modern_overlay_composition(compact);
    assert(compact_plan.visible);
    assert(compact_plan.compact);
    assert((compact_plan.logical_rect == HostOverlayRect{8, 8, 132, 52}));
    assert_rect_inside(compact_plan.output_rect, compact.output_viewport);

    compact.logical_surface_width = 130;
    compact.reserved.left = 8;
    compact.reserved.right = 8;
    assert(!resolve_modern_overlay_composition(compact).visible);

    // Invalid window/view geometry stays empty.
    auto invalid = timing_request(fixed_original, {}, 1);
    assert(!resolve_modern_overlay_composition(invalid).visible);
    assert(resolve_output_viewport(fixed_original, 0, 720).width == 0);
    assert(resolve_output_viewport(fixed_original, 1280, 0).height == 0);

    return 0;
}
