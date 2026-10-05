#pragma once

namespace ur::product {

// The current Racer HD compositor owns the stock 256x224 logical surface.
// A widened world surface must stay at 1x until that compositor can preserve
// the independently composed course margins instead of falling through after
// the framework has already allocated a scaled presentation buffer.
constexpr int resolve_internal_render_scale(
    bool modern_mode,
    bool world_expanded,
    int configured_scale) noexcept {
    if (!modern_mode || world_expanded ||
        configured_scale < 1 || configured_scale > 4) {
        return 1;
    }
    return configured_scale;
}

}  // namespace ur::product
