#include "modern_overlay_composition.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    const HostOutputViewport out_1080{0, 0, 1920, 1080};

    HostOverlayCompositionRequest timing{};
    timing.logical_surface_width = 256;
    timing.logical_surface_height = 224;
    timing.output_viewport = out_1080;
    timing.anchor = HostOverlayAnchor::TopRight;
    timing.preferred_width = 178;
    timing.preferred_height = 52;
    timing.minimum_width = 120;
    timing.minimum_height = 52;
    timing.edge_margin = 8;

    const auto at_1x = resolve_modern_overlay_composition(timing);
    assert(at_1x.visible);
    assert(!at_1x.compact);
    assert((at_1x.logical_rect == HostOverlayRect{70, 8, 178, 52}));
    assert((at_1x.presentation_rect == HostOverlayRect{70, 8, 178, 52}));
    assert((at_1x.output_rect == HostOverlayRect{525, 39, 1335, 250}));

    timing.presentation_scale = 2;
    const auto at_2x = resolve_modern_overlay_composition(timing);
    assert(at_2x.visible);
    assert(at_2x.logical_rect == at_1x.logical_rect);
    assert((at_2x.presentation_rect == HostOverlayRect{140, 16, 356, 104}));
    assert(at_2x.output_rect == at_1x.output_rect);

    timing.presentation_scale = 4;
    const auto at_4x = resolve_modern_overlay_composition(timing);
    assert(at_4x.visible);
    assert(at_4x.logical_rect == at_1x.logical_rect);
    assert((at_4x.presentation_rect == HostOverlayRect{280, 32, 712, 208}));
    assert(at_4x.output_rect == at_1x.output_rect);

    HostOverlayCompositionRequest wide = timing;
    wide.logical_surface_width = 342;
    wide.presentation_scale = 2;
    const auto wide_plan = resolve_modern_overlay_composition(wide);
    assert(wide_plan.visible);
    assert((wide_plan.logical_rect == HostOverlayRect{156, 8, 178, 52}));
    assert((wide_plan.presentation_rect == HostOverlayRect{312, 16, 356, 104}));

    HostOverlayCompositionRequest hud_safe = timing;
    hud_safe.presentation_scale = 1;
    hud_safe.reserved.top = 36;
    hud_safe.reserved.right = 24;
    const auto hud_plan = resolve_modern_overlay_composition(hud_safe);
    assert(hud_plan.visible);
    assert((hud_plan.logical_rect == HostOverlayRect{46, 44, 178, 52}));

    HostOverlayCompositionRequest narrow = timing;
    narrow.logical_surface_width = 148;
    const auto compact = resolve_modern_overlay_composition(narrow);
    assert(compact.visible);
    assert(compact.compact);
    assert((compact.logical_rect == HostOverlayRect{8, 8, 132, 52}));

    HostOverlayCompositionRequest too_small = timing;
    too_small.logical_surface_width = 130;
    too_small.reserved.left = 8;
    too_small.reserved.right = 8;
    assert(!resolve_modern_overlay_composition(too_small).visible);

    HostOverlayCompositionRequest invalid = timing;
    invalid.presentation_scale = 5;
    assert(!resolve_modern_overlay_composition(invalid).visible);

    HostOverlayCompositionRequest bottom{};
    bottom.logical_surface_width = 256;
    bottom.logical_surface_height = 224;
    bottom.presentation_scale = 2;
    bottom.output_viewport = HostOutputViewport{160, 152, 960, 720};
    bottom.reserved.bottom = 32;
    bottom.anchor = HostOverlayAnchor::BottomCenter;
    bottom.preferred_width = 200;
    bottom.preferred_height = 22;
    bottom.minimum_width = 120;
    bottom.minimum_height = 22;
    bottom.edge_margin = 8;
    const auto bottom_plan = resolve_modern_overlay_composition(bottom);
    assert(bottom_plan.visible);
    assert((bottom_plan.logical_rect == HostOverlayRect{28, 162, 200, 22}));
    assert((bottom_plan.presentation_rect == HostOverlayRect{56, 324, 400, 44}));

    return 0;
}
