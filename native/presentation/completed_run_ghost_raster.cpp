#include "completed_run_ghost_raster.hpp"

namespace ur::presentation {
namespace {

std::uint8_t blend_channel(
    std::uint8_t dst,
    std::uint8_t src,
    std::uint8_t alpha
) noexcept {
    const unsigned inv = 255u - alpha;
    return static_cast<std::uint8_t>(
        (static_cast<unsigned>(src) * alpha +
         static_cast<unsigned>(dst) * inv + 127u) / 255u
    );
}

std::uint32_t blend_pixel(
    std::uint32_t dst,
    std::uint32_t src,
    std::uint8_t opacity
) noexcept {
    const std::uint8_t src_a =
        static_cast<std::uint8_t>((src >> 24) & 0xffu);
    const std::uint8_t effective_a = static_cast<std::uint8_t>(
        (static_cast<unsigned>(src_a) * opacity + 127u) / 255u
    );
    if (effective_a == 0) return dst;

    const std::uint8_t sr = static_cast<std::uint8_t>(src & 0xffu);
    const std::uint8_t sg = static_cast<std::uint8_t>((src >> 8) & 0xffu);
    const std::uint8_t sb = static_cast<std::uint8_t>((src >> 16) & 0xffu);
    const std::uint8_t dr = static_cast<std::uint8_t>(dst & 0xffu);
    const std::uint8_t dg = static_cast<std::uint8_t>((dst >> 8) & 0xffu);
    const std::uint8_t db = static_cast<std::uint8_t>((dst >> 16) & 0xffu);
    const std::uint8_t da = static_cast<std::uint8_t>((dst >> 24) & 0xffu);

    const unsigned out_a =
        effective_a +
        (static_cast<unsigned>(da) * (255u - effective_a) + 127u) / 255u;

    return static_cast<std::uint32_t>(
        blend_channel(dr, sr, effective_a) |
        (static_cast<std::uint32_t>(blend_channel(dg, sg, effective_a)) << 8) |
        (static_cast<std::uint32_t>(blend_channel(db, sb, effective_a)) << 16) |
        (static_cast<std::uint32_t>(out_a) << 24)
    );
}

}  // namespace

bool draw_completed_run_ghost_racer(
    std::uint8_t* dst,
    std::size_t pitch,
    int frame_w,
    int frame_h,
    int scale,
    const ur::product::CompletedRunGhostPresentationFrame& frame,
    const RacerRegistration& registration,
    CompletedRunGhostRenderStyle style
) noexcept {
    if (dst == nullptr ||
        frame_w <= 0 ||
        frame_h <= 0 ||
        style.opacity == 0 ||
        !valid_racer_hd_internal_render_scale(scale) ||
        pitch < static_cast<std::size_t>(frame_w * scale) * 4u ||
        registration.semantic_frame_id != frame.semantic_frame_id) {
        return false;
    }

    const int output_w = frame_w * scale;
    const int output_h = frame_h * scale;
    const int origin_x = frame.screen_x * scale;
    const int origin_y = frame.screen_y * scale;
    const int asset_size = kRacerHdLogicalSize * scale;
    bool drew = false;

    for (int oy = 0; oy < asset_size; ++oy) {
        const int dy = origin_y + oy;
        if (dy < 0 || dy >= output_h) continue;
        auto* row = reinterpret_cast<std::uint32_t*>(
            dst + static_cast<std::size_t>(dy) * pitch
        );
        for (int ox = 0; ox < asset_size; ++ox) {
            const int dx = origin_x + ox;
            if (dx < 0 || dx >= output_w) continue;

            const std::uint32_t src = sample_racer_hd_scaled_asset(
                registration,
                ox,
                oy,
                scale,
                frame.hflip,
                frame.vflip
            );
            if ((src >> 24) == 0) continue;
            row[dx] = blend_pixel(row[dx], src, style.opacity);
            drew = true;
        }
    }

    return drew;
}

}  // namespace ur::presentation
