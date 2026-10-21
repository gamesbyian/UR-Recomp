#pragma once

// Source-verification gate for a large Modern frontend stock-racer hero.
// This is presentation-only. The caller must supply 64x64 ORIGINAL ROM-
// reconstructed ARGB poses with provenance, never a procedural 4x replacement.
// See docs/MODERN-MENU-ANIMATION.md for admission rules and current HOLD.
//
// No ROM fetching, guest memory, SDL, untrusted synthesized art, or gameplay
// animation state is reachable from this renderer. If no validated sprite
// family is supplied the caller draws nothing. Intentional fail closed.

#include "modern_menu_motion.hpp"

#include <cstddef>
#include <cstdint>

namespace ur::product {

inline constexpr int kModernMenuStockHeroCanvas = 64;
inline constexpr std::size_t kModernMenuStockHeroPixels = 64u * 64u;
inline constexpr std::size_t kModernMenuStockHeroMaxFrames = 8u;

struct ModernMenuStockHeroFrame {
    const std::uint32_t* argb_pixels = nullptr;
    std::size_t pixel_count = 0;
    std::uint16_t semantic_frame_id = 0;
    std::uint64_t source_argb_digest = 0;
    bool original_raster_source_verified = false;
};

struct ModernMenuStockHeroSequence {
    const ModernMenuStockHeroFrame* frames = nullptr;
    std::size_t frame_count = 0;
    bool original_pose_order_verified = false;
};

struct ModernMenuStockHeroPlacement {
    // Coordinates are in presentation framebuffer pixels.
    int left = 0;
    int top = 0;
    int scale = 1; // 1..4 only; nearest-neighbour stock art
};

enum class ModernMenuStockHeroDraw : std::uint8_t {
    Missing = 0,
    Unverified = 1,
    OutOfBounds = 2,
    Drawn = 3,
};

// FNV is a reproducible presentation integrity fingerprint, not provenance.
// Original source/evidence registration is separately required for admission.
// Decode ARGB as four explicit bytes, stable across host machine endianness.
inline std::uint64_t modern_menu_stock_hero_digest(
    const std::uint32_t* pixels, std::size_t count) noexcept {
    if (!pixels || count != kModernMenuStockHeroPixels) return 0;
    std::uint64_t digest = 1469598103934665603ull;
    for (std::size_t i = 0; i < count; ++i) {
        const auto p = pixels[i];
        for (int shift = 24; shift >= 0; shift -= 8) {
            digest ^= (p >> shift) & 0xffu;
            digest *= 1099511628211ull;
        }
    }
    return digest;
}

inline bool modern_menu_stock_hero_frame_eligible(
    const ModernMenuStockHeroFrame& frame) noexcept {
    return frame.original_raster_source_verified &&
           frame.argb_pixels &&
           frame.pixel_count == kModernMenuStockHeroPixels &&
           frame.semantic_frame_id != 0 &&
           frame.source_argb_digest != 0 &&
           modern_menu_stock_hero_digest(
               frame.argb_pixels, frame.pixel_count) ==
               frame.source_argb_digest;
}

// All frames validated before a single pixel is painted. Source animation
// order is not inferred by sorting semantic IDs, and unknown IDs never get
// auto-mapped to a nearest Remastered asset.
inline bool modern_menu_stock_hero_sequence_eligible(
    const ModernMenuStockHeroSequence& sequence) noexcept {
    if (!sequence.frames || !sequence.original_pose_order_verified ||
        sequence.frame_count == 0 ||
        sequence.frame_count > kModernMenuStockHeroMaxFrames) return false;
    for (std::size_t i = 0; i < sequence.frame_count; ++i)
        if (!modern_menu_stock_hero_frame_eligible(sequence.frames[i]))
            return false;
    return true;
}

// Draw a source-gated hero into an existing native host compositing buffer.
// The owner of the surrounding 16:9/4:3 layout supplies placement. The pose
// model contributes bob/reaction offsets, not a new wheel or stunt sprite.
// Only fully transparent 64x64 padding may extend beyond the screen.
// Every opaque pixel of EVERY registered original pose must remain inside
// the supplied safe area at the requested scale, or the entire draw is
// refused before touching destination pixels. No visible clipping allowed.
inline ModernMenuStockHeroDraw paint_modern_menu_stock_hero(
    std::uint32_t* destination, int pitch_pixels, int surface_height,
    HostOverlayRect safe_area, ModernMenuStockHeroPlacement placement,
    const ModernMenuStockHeroSequence& sequence,
    const ModernMenuMotionPose& motion) noexcept {
    if (!motion.visible || !sequence.frames || !sequence.frame_count)
        return ModernMenuStockHeroDraw::Missing;
    if (!modern_menu_stock_hero_sequence_eligible(sequence))
        return ModernMenuStockHeroDraw::Unverified;
    if (!destination || pitch_pixels <= 0 || surface_height <= 0 ||
        placement.scale < 1 || placement.scale > 4 ||
        safe_area.x < 0 || safe_area.y < 0 ||
        safe_area.width <= 0 || safe_area.height <= 0 ||
        safe_area.x > pitch_pixels || safe_area.y > surface_height ||
        safe_area.width > pitch_pixels - safe_area.x ||
        safe_area.height > surface_height - safe_area.y)
        return ModernMenuStockHeroDraw::OutOfBounds;

    const std::int64_t draw_x =
        static_cast<std::int64_t>(placement.left) +
        static_cast<std::int64_t>(
            motion.reduced_motion ? 0 : motion.hero_lean_px) * placement.scale;
    const std::int64_t draw_y =
        static_cast<std::int64_t>(placement.top) +
        static_cast<std::int64_t>(
            motion.reduced_motion ? 0 : motion.hero_bob_px) * placement.scale;
    const std::int64_t safe_right =
        static_cast<std::int64_t>(safe_area.x) + safe_area.width;
    const std::int64_t safe_bottom =
        static_cast<std::int64_t>(safe_area.y) + safe_area.height;

    // Source motion (modern_menu_motion.hpp) can move any admitted pose
    // one logical pixel LEFT/RIGHT and two pixels UP. Validating only
    // today's motion offset allows a later, equally authentic source pose
    // to vanish near a screen edge, or to be cropped frame-by-frame.
    // Fail closed for the ENTIRE future animated placement envelope,
    // including when reduced motion is currently selected and may be
    // disabled later. Original sprite pixels remain untouched.
    if (motion.hero_lean_px < -1 || motion.hero_lean_px > 1 ||
        motion.hero_bob_px < -2 || motion.hero_bob_px > 0)
        return ModernMenuStockHeroDraw::OutOfBounds;
    int min_x = kModernMenuStockHeroCanvas;
    int min_y = kModernMenuStockHeroCanvas;
    int max_x = -1;
    int max_y = -1;
    for (std::size_t n = 0; n < sequence.frame_count; ++n) {
        const auto* frame = sequence.frames[n].argb_pixels;
        bool occupied = false;
        for (int y = 0; y < kModernMenuStockHeroCanvas; ++y) {
            for (int x = 0; x < kModernMenuStockHeroCanvas; ++x) {
                if ((frame[static_cast<std::size_t>(y) *
                           kModernMenuStockHeroCanvas + x] >> 24) == 0u)
                    continue;
                occupied = true;
                if (x < min_x) min_x = x;
                if (x > max_x) max_x = x;
                if (y < min_y) min_y = y;
                if (y > max_y) max_y = y;
            }
        }
        if (!occupied) return ModernMenuStockHeroDraw::Unverified;
    }
    const std::int64_t envelope_left =
        static_cast<std::int64_t>(placement.left) +
        static_cast<std::int64_t>(min_x - 1) * placement.scale;
    const std::int64_t envelope_right =
        static_cast<std::int64_t>(placement.left) +
        static_cast<std::int64_t>(max_x + 2) * placement.scale;
    const std::int64_t envelope_top =
        static_cast<std::int64_t>(placement.top) +
        static_cast<std::int64_t>(min_y - 2) * placement.scale;
    const std::int64_t envelope_bottom =
        static_cast<std::int64_t>(placement.top) +
        static_cast<std::int64_t>(max_y + 1) * placement.scale;
    if (envelope_left < safe_area.x || envelope_top < safe_area.y ||
        envelope_right > safe_right || envelope_bottom > safe_bottom)
        return ModernMenuStockHeroDraw::OutOfBounds;

    // The verified original guest clip is a SINGLE event, not a cyclic
    // idle. Modulo here would silently invent the unobserved final->first
    // seam if any caller supplied a later UI tick/pose ordinal. Hold the
    // last observed original pose instead, even for very large ordinals.
    // A negative ordinal is malformed host input, never a source frame.
    if (motion.hero_frame_ordinal < 0)
        return ModernMenuStockHeroDraw::Unverified;
    const std::size_t ordinal =
        static_cast<std::size_t>(motion.hero_frame_ordinal);
    const std::size_t phase = motion.reduced_motion ? 0u :
        (ordinal >= sequence.frame_count ? sequence.frame_count - 1u
                                         : ordinal);
    const auto* src = sequence.frames[phase].argb_pixels;
    for (int y = 0; y < kModernMenuStockHeroCanvas; ++y) {
        for (int x = 0; x < kModernMenuStockHeroCanvas; ++x) {
            const std::uint32_t pixel =
                src[static_cast<std::size_t>(y) *
                    kModernMenuStockHeroCanvas + x];
            const std::uint32_t alpha = (pixel >> 24) & 255u;
            if (alpha == 0) continue;
            const auto x_origin = static_cast<int>(
                draw_x + static_cast<std::int64_t>(x) * placement.scale);
            const auto y_origin = static_cast<int>(
                draw_y + static_cast<std::int64_t>(y) * placement.scale);
            for (int sy = 0; sy < placement.scale; ++sy) {
                auto* line = destination +
                    static_cast<std::size_t>(y_origin + sy) *
                        static_cast<std::size_t>(pitch_pixels);
                for (int sx = 0; sx < placement.scale; ++sx) {
                    auto& dst = line[x_origin + sx];
                    if (alpha == 255u) {
                        dst = pixel;
                    } else {
                        const std::uint32_t inverse = 255u - alpha;
                        const auto blend = [alpha, inverse](
                            std::uint32_t a, std::uint32_t b) {
                            return (a * alpha + b * inverse + 127u) / 255u;
                        };
                        const auto red = blend(
                            (pixel >> 16u) & 255u, (dst >> 16u) & 255u);
                        const auto green = blend(
                            (pixel >> 8u) & 255u, (dst >> 8u) & 255u);
                        const auto blue = blend(
                            pixel & 255u, dst & 255u);
                        dst = 0xff000000u | (red << 16u) |
                            (green << 8u) | blue;
                    }
                }
            }
        }
    }
    return ModernMenuStockHeroDraw::Drawn;
}

}  // namespace ur::product
