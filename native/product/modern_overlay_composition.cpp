#include "modern_overlay_composition.hpp"

#include <algorithm>
#include <cstdint>

namespace ur::product {
namespace {

bool valid_request(const HostOverlayCompositionRequest& request) noexcept {
    return request.logical_surface_width > 0 &&
           request.logical_surface_height > 0 &&
           request.presentation_scale >= 1 &&
           request.presentation_scale <= 4 &&
           request.output_viewport.width > 0 &&
           request.output_viewport.height > 0 &&
           request.reserved.left >= 0 && request.reserved.top >= 0 &&
           request.reserved.right >= 0 && request.reserved.bottom >= 0 &&
           request.preferred_width > 0 && request.preferred_height > 0 &&
           request.minimum_width > 0 && request.minimum_height > 0 &&
           request.minimum_width <= request.preferred_width &&
           request.minimum_height <= request.preferred_height &&
           request.edge_margin >= 0;
}

int project_edge(
    int logical_edge,
    int logical_extent,
    int output_origin,
    int output_extent) noexcept {
    const std::int64_t scaled =
        static_cast<std::int64_t>(logical_edge) * output_extent;
    return output_origin + static_cast<int>(
        (scaled + logical_extent / 2) / logical_extent);
}

}  // namespace

HostOverlayCompositionPlan resolve_modern_overlay_composition(
    const HostOverlayCompositionRequest& request) noexcept {
    HostOverlayCompositionPlan plan{};
    if (!valid_request(request)) return plan;

    const int safe_x = request.reserved.left + request.edge_margin;
    const int safe_y = request.reserved.top + request.edge_margin;
    const int safe_right = request.logical_surface_width -
        request.reserved.right - request.edge_margin;
    const int safe_bottom = request.logical_surface_height -
        request.reserved.bottom - request.edge_margin;
    const int safe_width = safe_right - safe_x;
    const int safe_height = safe_bottom - safe_y;
    if (safe_width < request.minimum_width ||
        safe_height < request.minimum_height) {
        return plan;
    }

    const int width = std::min(request.preferred_width, safe_width);
    const int height = std::min(request.preferred_height, safe_height);
    int x = safe_x;
    int y = safe_y;

    switch (request.anchor) {
    case HostOverlayAnchor::TopCenter:
    case HostOverlayAnchor::Center:
    case HostOverlayAnchor::BottomCenter:
        x = safe_x + (safe_width - width) / 2;
        break;
    case HostOverlayAnchor::TopRight:
    case HostOverlayAnchor::BottomRight:
        x = safe_right - width;
        break;
    case HostOverlayAnchor::TopLeft:
    case HostOverlayAnchor::BottomLeft:
        break;
    }

    switch (request.anchor) {
    case HostOverlayAnchor::Center:
        y = safe_y + (safe_height - height) / 2;
        break;
    case HostOverlayAnchor::BottomLeft:
    case HostOverlayAnchor::BottomCenter:
    case HostOverlayAnchor::BottomRight:
        y = safe_bottom - height;
        break;
    case HostOverlayAnchor::TopLeft:
    case HostOverlayAnchor::TopCenter:
    case HostOverlayAnchor::TopRight:
        break;
    }

    plan.logical_rect = {x, y, width, height};
    plan.presentation_scale = request.presentation_scale;
    plan.presentation_rect = {
        x * request.presentation_scale,
        y * request.presentation_scale,
        width * request.presentation_scale,
        height * request.presentation_scale,
    };

    const int output_x0 = project_edge(
        x, request.logical_surface_width,
        request.output_viewport.x, request.output_viewport.width);
    const int output_y0 = project_edge(
        y, request.logical_surface_height,
        request.output_viewport.y, request.output_viewport.height);
    const int output_x1 = project_edge(
        x + width, request.logical_surface_width,
        request.output_viewport.x, request.output_viewport.width);
    const int output_y1 = project_edge(
        y + height, request.logical_surface_height,
        request.output_viewport.y, request.output_viewport.height);
    plan.output_rect = {
        output_x0,
        output_y0,
        std::max(1, output_x1 - output_x0),
        std::max(1, output_y1 - output_y0),
    };
    plan.visible = true;
    plan.compact = width != request.preferred_width ||
                   height != request.preferred_height;
    return plan;
}

}  // namespace ur::product
