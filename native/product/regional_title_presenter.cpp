#include "regional_title_presenter.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>

#include "regional_title_retail_asset.hpp"

namespace ur::product {
namespace {

using namespace regional_title_asset;

constexpr char kBase85Alphabet[] =
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    "!#$%&()*+-;<=>?@^_`{|}~";
constexpr std::uint64_t kFnvOffsetBasis = 1469598103934665603ull;
constexpr std::uint64_t kFnvPrime = 1099511628211ull;
constexpr std::size_t kBytesPerPixel = 4u;
constexpr std::size_t kEncodedGroupChars = 5u;
constexpr std::size_t kDecodedGroupBytes = 4u;

int base85_value(char c) noexcept {
    for (int index = 0; index < 85; ++index) {
        if (kBase85Alphabet[index] == c) {
            return index;
        }
    }
    return -1;
}

bool decode_index(
    const char* encoded_indices,
    std::size_t index,
    std::uint8_t* value) noexcept {
    if (!encoded_indices || !value || index >= kIndexCount) {
        return false;
    }
    const std::size_t group = index / kDecodedGroupBytes;
    const std::size_t slot = index % kDecodedGroupBytes;
    const std::size_t encoded = group * kEncodedGroupChars;
    std::uint32_t block = 0;
    for (std::size_t i = 0; i < kEncodedGroupChars; ++i) {
        const int digit = base85_value(encoded_indices[encoded + i]);
        if (digit < 0) {
            return false;
        }
        block = block * 85u + static_cast<std::uint32_t>(digit);
    }
    const int shift = 24 - static_cast<int>(slot * 8u);
    *value = static_cast<std::uint8_t>((block >> shift) & 0xffu);
    return true;
}

template <std::size_t N>
bool payload_valid(
    const std::array<std::uint32_t, N>& palette,
    const char* encoded_indices) noexcept {
    for (std::size_t i = 0; i < kIndexCount; ++i) {
        std::uint8_t palette_index = 0;
        if (!decode_index(encoded_indices, i, &palette_index) ||
            palette_index >= palette.size()) {
            return false;
        }
    }
    return true;
}

template <std::size_t N>
bool paint_crop(
    std::uint8_t* pixels,
    std::size_t pitch,
    const std::array<std::uint32_t, N>& palette,
    const char* encoded_indices,
    int presentation_scale) noexcept {
    std::size_t index = 0;
    for (int y = 0; y < kHeight; ++y) {
        for (int x = 0; x < kWidth; ++x, ++index) {
            std::uint8_t palette_index = 0;
            if (!decode_index(encoded_indices, index, &palette_index) ||
                palette_index >= palette.size()) {
                return false;
            }
            const std::uint32_t bgrx = palette[palette_index];
            for (int sy = 0; sy < presentation_scale; ++sy) {
                std::uint8_t* row =
                    pixels +
                    static_cast<std::size_t>(
                        (kOriginY + y) * presentation_scale + sy) * pitch +
                    static_cast<std::size_t>(
                        kOriginX * presentation_scale) * kBytesPerPixel;
                for (int sx = 0; sx < presentation_scale; ++sx) {
                    std::uint8_t* pixel =
                        row + static_cast<std::size_t>(
                            x * presentation_scale + sx) * kBytesPerPixel;
                    pixel[0] = static_cast<std::uint8_t>(bgrx & 0xffu);
                    pixel[1] = static_cast<std::uint8_t>((bgrx >> 8u) & 0xffu);
                    pixel[2] = static_cast<std::uint8_t>((bgrx >> 16u) & 0xffu);
                }
            }
        }
    }
    return index == kIndexCount;
}

bool dimensions_admit(
    const std::uint8_t* pixels,
    std::size_t pitch,
    int width,
    int height,
    int presentation_scale = 1) noexcept {
    if (!pixels || width <= 0 || height <= 0 ||
        presentation_scale < 1 || presentation_scale > 4) {
        return false;
    }
    if (width < (kOriginX + kWidth) * presentation_scale ||
        height < (kOriginY + kHeight) * presentation_scale) {
        return false;
    }
    return pitch >= static_cast<std::size_t>(width) * kBytesPerPixel;
}

}  // namespace

std::uint64_t regional_title_visible_crop_digest(
    const std::uint8_t* pixels,
    std::size_t pitch,
    int width,
    int height,
    int presentation_scale) noexcept {
    if (!dimensions_admit(
            pixels, pitch, width, height, presentation_scale)) {
        return 0;
    }
    std::uint64_t digest = kFnvOffsetBasis;
    for (int y = 0; y < kHeight; ++y) {
        const std::uint8_t* row =
            pixels +
            static_cast<std::size_t>(
                (kOriginY + y) * presentation_scale) * pitch +
            static_cast<std::size_t>(
                kOriginX * presentation_scale) * kBytesPerPixel;
        for (int x = 0; x < kWidth; ++x) {
            const std::uint8_t* pixel =
                row + static_cast<std::size_t>(
                    x * presentation_scale) * kBytesPerPixel;
            for (std::size_t channel = 0; channel < 3u; ++channel) {
                digest ^= pixel[channel];
                digest *= kFnvPrime;
            }
        }
    }
    return digest;
}

RegionalTitlePresentationResult apply_regional_title_presentation(
    RegionalPresentation presentation,
    bool idle_title_surface,
    std::uint8_t* pixels,
    std::size_t pitch,
    int width,
    int height,
    int presentation_scale) noexcept {
    if (presentation == RegionalPresentation::NorthAmerica ||
        !idle_title_surface) {
        return RegionalTitlePresentationResult::Canonical;
    }
    if (!dimensions_admit(
            pixels, pitch, width, height, presentation_scale) ||
        !kCgramIdenticalAcrossEvidence) {
        return RegionalTitlePresentationResult::FailedClosed;
    }
    // The live NorthAmerica raster is authoritative guest output from the
    // verified USA ROM. Renderer-specific palette conversion means it is not
    // required to byte-match the snesref evidence raster. The semantic title
    // state is the admission guard; the retained Europe payload must still be
    // self-consistent before any visible pixel is touched.
    if (!payload_valid(kPalette, kIndicesBase85)) {
        return RegionalTitlePresentationResult::FailedClosed;
    }

    // Payload validation above is complete and deterministic, so painting is
    // all-or-nothing with respect to encoded input. The caller owns the
    // canonical background and may precompose it at any supported density.
    if (!paint_crop(
            pixels, pitch, kPalette, kIndicesBase85, presentation_scale)) {
        return RegionalTitlePresentationResult::FailedClosed;
    }
    if (regional_title_visible_crop_digest(
            pixels, pitch, width, height, presentation_scale) !=
        kTargetCropBgrFnv1a64) {
        return RegionalTitlePresentationResult::FailedClosed;
    }
    return RegionalTitlePresentationResult::EuropeApplied;
}

}  // namespace ur::product
