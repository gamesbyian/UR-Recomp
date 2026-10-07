#pragma once

namespace ur::product {

// Internal Render Scale is presentation density only. The logical field may
// be stock-width or an evidence-backed widened world surface; the generic
// nearest-density compositor preserves every logical source pixel and margin
// after title-specific replacement presenters decline a frame. A host-owned
// logical overlay may still force 1x until that overlay owns an explicit
// density transform.
constexpr int resolve_internal_render_scale(
    bool modern_mode,
    bool world_expanded,
    bool logical_overlay_active,
    int configured_scale) noexcept {
    (void)world_expanded;
    if (!modern_mode || logical_overlay_active ||
        configured_scale < 1 || configured_scale > 4) {
        return 1;
    }
    return configured_scale;
}

}  // namespace ur::product
