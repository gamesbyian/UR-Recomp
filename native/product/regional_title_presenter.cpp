#include "regional_title_presenter.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

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
    const char* encoded_indices) noexcept {
    std::size_t index = 0;
    for (int y = 0; y < kHeight; ++y) {
        std::uint8_t* row =
            pixels + static_cast<std::size_t>(kOriginY + y) * pitch +
            static_cast<std::size_t>(kOriginX) * kBytesPerPixel;
        for (int x = 0; x < kWidth; ++x, ++index) {
            std::uint8_t palette_index = 0;
            if (!decode_index(encoded_indices, index, &palette_index) ||
                palette_index >= palette.size()) {
                return false;
            }
            const std::uint32_t bgrx = palette[palette_index];
            std::uint8_t* pixel =
                row + static_cast<std::size_t>(x) * kBytesPerPixel;
            pixel[0] = static_cast<std::uint8_t>(bgrx & 0xffu);
            pixel[1] = static_cast<std::uint8_t>((bgrx >> 8u) & 0xffu);
            pixel[2] = static_cast<std::uint8_t>((bgrx >> 16u) & 0xffu);
        }
    }
    return index == kIndexCount;
}

bool dimensions_admit(
    const std::uint8_t* pixels,
    std::size_t pitch,
    int width,
    int height) noexcept {
    if (!pixels || width <= 0 || height <= 0) {
        return false;
    }
    if (width < kOriginX + kWidth || height < kOriginY + kHeight) {
        return false;
    }
    return pitch >= static_cast<std::size_t>(width) * kBytesPerPixel;
}

}  // namespace

std::uint64_t regional_title_visible_crop_digest(
    const std::uint8_t* pixels,
    std::size_t pitch,
    int width,
    int height) noexcept {
    if (!dimensions_admit(pixels, pitch, width, height)) {
        return 0;
    }
    std::uint64_t digest = kFnvOffsetBasis;
    for (int y = 0; y < kHeight; ++y) {
        const std::uint8_t* row =
            pixels + static_cast<std::size_t>(kOriginY + y) * pitch +
            static_cast<std::size_t>(kOriginX) * kBytesPerPixel;
        for (int x = 0; x < kWidth; ++x) {
            for (std::size_t channel = 0; channel < 3u; ++channel) {
                digest ^= row[static_cast<std::size_t>(x) * kBytesPerPixel + channel];
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
    int height) noexcept {
    if (presentation == RegionalPresentation::NorthAmerica ||
        !idle_title_surface) {
        return RegionalTitlePresentationResult::Canonical;
    }
    if (!dimensions_admit(pixels, pitch, width, height) ||
        !kCgramIdenticalAcrossEvidence) {
        return RegionalTitlePresentationResult::FailedClosed;
    }
    if (regional_title_visible_crop_digest(pixels, pitch, width, height) !=
        kSourceCropBgrFnv1a64) {
        return RegionalTitlePresentationResult::FailedClosed;
    }

    // Validate both retained payloads before touching a visible pixel so the
    // Europe write and the emergency canonical repaint are both trustworthy.
    if (!payload_valid(kPalette, kIndicesBase85) ||
        !payload_valid(kSourcePalette, kSourceIndicesBase85)) {
        return RegionalTitlePresentationResult::FailedClosed;
    }

    if (!paint_crop(pixels, pitch, kPalette, kIndicesBase85) ||
        regional_title_visible_crop_digest(pixels, pitch, width, height) !=
            kTargetCropBgrFnv1a64) {
        // A post-write mismatch is treated as corrupt/inconsistent evidence.
        // Repaint the exact retained canonical crop before returning failure.
        (void)paint_crop(
            pixels, pitch, kSourcePalette, kSourceIndicesBase85);
        return RegionalTitlePresentationResult::FailedClosed;
    }
    return RegionalTitlePresentationResult::EuropeApplied;
}

}  // namespace ur::product
