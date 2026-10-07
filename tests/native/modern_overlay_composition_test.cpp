#include "modern_overlay_composition.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    assert(resolve_modern_overlay_surface_scale(1, 256, 224) == 1);
    assert(resolve_modern_overlay_surface_scale(2, 512, 448) == 2);
    assert(resolve_modern_overlay_surface_scale(3, 1026, 672) == 3);
    assert(resolve_modern_overlay_surface_scale(4, 1024, 896) == 4);
    assert(resolve_modern_overlay_surface_scale(2, 511, 448) == 1);
    assert(resolve_modern_overlay_surface_scale(2, 512, 447) == 1);
    assert(resolve_modern_overlay_surface_scale(0, 256, 224) == 1);
    assert(resolve_modern_overlay_surface_scale(5, 1280, 1120) == 1);

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

    timing.presentation_scale = 3;
    const auto at_3x = resolve_modern_overlay_composition(timing);
    assert(at_3x.visible);
    assert(at_3x.logical_rect == at_1x.logical_rect);
    assert((at_3x.presentation_rect == HostOverlayRect{210, 24, 534, 156}));
    assert(at_3x.output_rect == at_1x.output_rect);

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

    HostOverlayCompositionRequest resized = timing;
    resized.presentation_scale = 2;
    resized.output_viewport = HostOutputViewport{160, 152, 960, 720};
    const auto resized_plan = resolve_modern_overlay_composition(resized);
    assert(resized_plan.visible);
    assert(resized_plan.logical_rect == at_1x.logical_rect);
    assert((resized_plan.output_rect == HostOverlayRect{423, 178, 667, 167}));

    HostOverlayCompositionRequest routing{};
    routing.logical_surface_width = 256;
    routing.logical_surface_height = 224;
    routing.presentation_scale = 2;
    routing.output_viewport = HostOutputViewport{0, 0, 512, 448};
    routing.anchor = HostOverlayAnchor::TopCenter;
    routing.preferred_width = 304;
    routing.preferred_height = 22;
    routing.minimum_width = 220;
    routing.minimum_height = 22;
    routing.edge_margin = 8;
    const auto routing_plan = resolve_modern_overlay_composition(routing);
    assert(routing_plan.visible);
    assert(routing_plan.compact);
    assert((routing_plan.logical_rect == HostOverlayRect{8, 8, 240, 22}));
    assert((routing_plan.presentation_rect == HostOverlayRect{16, 16, 480, 44}));

    HostOverlayCompositionRequest recent{};
    recent.logical_surface_width = 256;
    recent.logical_surface_height = 224;
    recent.presentation_scale = 2;
    recent.output_viewport = HostOutputViewport{0, 0, 512, 448};
    recent.reserved.left = 8;
    recent.anchor = HostOverlayAnchor::BottomLeft;
    recent.preferred_width = 240;
    recent.preferred_height = 13;
    recent.minimum_width = 160;
    recent.minimum_height = 13;
    const auto recent_plan = resolve_modern_overlay_composition(recent);
    assert(recent_plan.visible);
    assert((recent_plan.logical_rect == HostOverlayRect{8, 211, 240, 13}));
    assert((recent_plan.presentation_rect == HostOverlayRect{16, 422, 480, 26}));

    HostOverlayCompositionRequest tour_banner{};
    tour_banner.logical_surface_width = 256;
    tour_banner.logical_surface_height = 224;
    tour_banner.presentation_scale = 2;
    tour_banner.output_viewport = HostOutputViewport{0, 0, 512, 448};
    tour_banner.reserved.left = 8;
    tour_banner.reserved.right = 8;
    tour_banner.reserved.bottom = 12;
    tour_banner.anchor = HostOverlayAnchor::BottomCenter;
    tour_banner.preferred_width = 274;
    tour_banner.preferred_height = 22;
    tour_banner.minimum_width = 200;
    tour_banner.minimum_height = 22;
    const auto tour_banner_plan =
        resolve_modern_overlay_composition(tour_banner);
    assert(tour_banner_plan.visible);
    assert(tour_banner_plan.compact);
    assert((tour_banner_plan.logical_rect == HostOverlayRect{8, 190, 240, 22}));
    assert((tour_banner_plan.presentation_rect == HostOverlayRect{16, 380, 480, 44}));

    // A full-height pause subview keeps its logical footprint across density.
    // The Controls panel is the tightest shipping modal: 220 logical lines
    // plus the shared 2-pixel top/bottom safe margin exactly fills 224.
    HostOverlayCompositionRequest modal{};
    modal.logical_surface_width = 256;
    modal.logical_surface_height = 224;
    modal.output_viewport = HostOutputViewport{0, 0, 1024, 896};
    modal.anchor = HostOverlayAnchor::Center;
    modal.preferred_width = 212;
    modal.preferred_height = 220;
    modal.minimum_width = 212;
    modal.minimum_height = 220;
    modal.edge_margin = 2;
    const auto modal_1x = resolve_modern_overlay_composition(modal);
    assert(modal_1x.visible);
    assert((modal_1x.logical_rect == HostOverlayRect{22, 2, 212, 220}));

    modal.presentation_scale = 4;
    const auto modal_4x = resolve_modern_overlay_composition(modal);
    assert(modal_4x.visible);
    assert(modal_4x.logical_rect == modal_1x.logical_rect);
    assert((modal_4x.presentation_rect == HostOverlayRect{88, 8, 848, 880}));
    assert(modal_4x.output_rect == modal_1x.output_rect);

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
