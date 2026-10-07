#pragma once

#include <cstdint>

namespace ur::product {

enum class HostFinalWindowFilter : std::uint8_t {
    Nearest = 0,
    Linear = 1,
};

/* Whole-frame filtering happens after Original pixels, native-density
 * replacement rasters and Modern primitives/glyphs have already been
 * composited. The current product therefore defaults to nearest at this final
 * stage so the renderer cannot blur deliberately crisp mixed-source content.
 * CRT/NTSC reconstruction or curated scalers belong to an explicit later
 * display-treatment policy, not an implicit linear fallback. */
constexpr HostFinalWindowFilter default_final_window_filter() noexcept {
    return HostFinalWindowFilter::Nearest;
}

enum class HostPresentationSource : std::uint8_t {
    OriginalPixelArt = 0,
    RemasteredRaster = 1,
    ReimaginedRaster = 2,
    ModernPrimitive = 3,
    ModernGlyph = 4,
};

enum class HostPresentationSampling : std::uint8_t {
    NearestInteger = 0,
    NativeDensity = 1,
    DirectAtPresentationDensity = 2,
};

constexpr HostPresentationSampling resolve_presentation_sampling(
    HostPresentationSource source) noexcept {
    switch (source) {
    case HostPresentationSource::OriginalPixelArt:
        return HostPresentationSampling::NearestInteger;
    case HostPresentationSource::RemasteredRaster:
    case HostPresentationSource::ReimaginedRaster:
        return HostPresentationSampling::NativeDensity;
    case HostPresentationSource::ModernPrimitive:
    case HostPresentationSource::ModernGlyph:
        return HostPresentationSampling::DirectAtPresentationDensity;
    }
    return HostPresentationSampling::NearestInteger;
}

}  // namespace ur::product
