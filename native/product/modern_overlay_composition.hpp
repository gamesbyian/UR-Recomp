#pragma once

#include "widescreen_output_composition.hpp"

#include <cstdint>

namespace ur::product {

enum class HostOverlayAnchor : std::uint8_t {
    TopLeft = 0,
    TopCenter = 1,
    TopRight = 2,
    Center = 3,
    BottomLeft = 4,
    BottomCenter = 5,
    BottomRight = 6,
};

struct HostOverlayInsets {
    int left = 0;
    int top = 0;
    int right = 0;
    int bottom = 0;
};

struct HostOverlayRect {
    int x = 0;
    int y = 0;
    int width = 0;
    int height = 0;

    constexpr bool operator==(const HostOverlayRect& other) const noexcept {
        return x == other.x && y == other.y &&
               width == other.width && height == other.height;
    }
};

struct HostOverlayCompositionPlan {
    HostOverlayRect logical_rect{};
    HostOverlayRect presentation_rect{};
    HostOverlayRect output_rect{};
    int presentation_scale = 1;
    bool visible = false;
    bool compact = false;
};

struct HostOverlayCompositionRequest {
    int logical_surface_width = 256;
    int logical_surface_height = 224;
    int presentation_scale = 1;
    HostOutputViewport output_viewport{};
    HostOverlayInsets reserved{};
    HostOverlayAnchor anchor = HostOverlayAnchor::Center;
    int preferred_width = 0;
    int preferred_height = 0;
    int minimum_width = 0;
    int minimum_height = 0;
    int edge_margin = 0;
};

/* Resolve one Modern overlay against a caller-owned logical safe area.
 *
 * Guest/view geometry, presentation density and final output geometry stay
 * separate. Reserved bands describe stock HUD/frontend content owned by the
 * caller; this shared policy never learns title-specific pixels. Preferred
 * dimensions clamp to the available logical area. If the minimum usable size
 * cannot fit, the overlay fails closed instead of overlapping reserved stock
 * content. Presentation coordinates are an exact integer-density transform of
 * logical coordinates; output coordinates are deterministic projections into
 * the already-resolved final viewport.
 */
HostOverlayCompositionPlan resolve_modern_overlay_composition(
    const HostOverlayCompositionRequest& request) noexcept;

}  // namespace ur::product
