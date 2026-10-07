#pragma once

#include <cstdint>

namespace ur::product {

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
