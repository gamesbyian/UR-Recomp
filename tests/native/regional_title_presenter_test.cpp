#include "regional_title_presenter.hpp"
#include "regional_title_retail_asset.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace {

using namespace ur::product;
using namespace ur::product::regional_title_asset;

constexpr int kFrameWidth = 256;
constexpr int kFrameHeight = 224;
constexpr std::size_t kPitch = static_cast<std::size_t>(kFrameWidth) * 4u;

constexpr char kBase85Alphabet[] =
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    "!#$%&()*+-;<=>?@^_`{|}~";

int base85_value(char c) {
    for (int i = 0; i < 85; ++i) {
        if (kBase85Alphabet[i] == c) return i;
    }
    return -1;
}

std::uint8_t decode_source_index(std::size_t index) {
    const std::size_t group = index / 4u;
    const std::size_t slot = index % 4u;
    const std::size_t encoded = group * 5u;
    std::uint32_t block = 0;
    for (std::size_t i = 0; i < 5u; ++i) {
        const int digit = base85_value(kSourceIndicesBase85[encoded + i]);
        assert(digit >= 0);
        block = block * 85u + static_cast<std::uint32_t>(digit);
    }
    return static_cast<std::uint8_t>((block >> (24 - static_cast<int>(slot * 8u))) & 0xffu);
}

std::vector<std::uint8_t> canonical_title_frame() {
    std::vector<std::uint8_t> frame(
        static_cast<std::size_t>(kFrameWidth) * kFrameHeight * 4u,
        0u);
    std::size_t index = 0;
    for (int y = 0; y < kHeight; ++y) {
        auto* row = frame.data() +
            static_cast<std::size_t>(kOriginY + y) * kPitch +
            static_cast<std::size_t>(kOriginX) * 4u;
        for (int x = 0; x < kWidth; ++x, ++index) {
            const std::uint8_t palette_index = decode_source_index(index);
            assert(palette_index < kSourcePalette.size());
            const std::uint32_t bgrx = kSourcePalette[palette_index];
            auto* pixel = row + static_cast<std::size_t>(x) * 4u;
            pixel[0] = static_cast<std::uint8_t>(bgrx & 0xffu);
            pixel[1] = static_cast<std::uint8_t>((bgrx >> 8u) & 0xffu);
            pixel[2] = static_cast<std::uint8_t>((bgrx >> 16u) & 0xffu);
            pixel[3] = 0u;
        }
    }
    assert(index == kIndexCount);
    return frame;
}

}  // namespace

int main() {
    auto canonical = canonical_title_frame();
    assert(regional_title_visible_crop_digest(
               canonical.data(), kPitch, kFrameWidth, kFrameHeight) ==
           kSourceCropBgrFnv1a64);

    {
        auto frame = canonical;
        const auto result = apply_regional_title_presentation(
            RegionalPresentation::NorthAmerica,
            true,
            frame.data(),
            kPitch,
            kFrameWidth,
            kFrameHeight);
        assert(result == RegionalTitlePresentationResult::Canonical);
        assert(frame == canonical);
        assert(regional_title_visible_crop_digest(
                   frame.data(), kPitch, kFrameWidth, kFrameHeight) ==
               kSourceCropBgrFnv1a64);
    }

    {
        auto frame = canonical;
        const auto result = apply_regional_title_presentation(
            RegionalPresentation::Europe,
            false,
            frame.data(),
            kPitch,
            kFrameWidth,
            kFrameHeight);
        assert(result == RegionalTitlePresentationResult::Canonical);
        assert(frame == canonical);
    }

    {
        auto frame = canonical;
        std::array<std::uint8_t, 64> guest_state{};
        for (std::size_t i = 0; i < guest_state.size(); ++i) {
            guest_state[i] = static_cast<std::uint8_t>(i * 3u + 1u);
        }
        const auto guest_before = guest_state;
        const auto result = apply_regional_title_presentation(
            RegionalPresentation::Europe,
            true,
            frame.data(),
            kPitch,
            kFrameWidth,
            kFrameHeight);
        assert(result == RegionalTitlePresentationResult::EuropeApplied);
        assert(regional_title_visible_crop_digest(
                   frame.data(), kPitch, kFrameWidth, kFrameHeight) ==
               kTargetCropBgrFnv1a64);
        assert(guest_state == guest_before);
    }

    {
        auto logical = canonical;
        constexpr int scale = 3;
        constexpr int scaled_width = kFrameWidth * scale;
        constexpr int scaled_height = kFrameHeight * scale;
        constexpr std::size_t scaled_pitch =
            static_cast<std::size_t>(scaled_width) * 4u;
        std::vector<std::uint8_t> frame(
            static_cast<std::size_t>(scaled_width) * scaled_height * 4u,
            0u);
        for (int y = 0; y < kFrameHeight; ++y) {
            const auto* src = reinterpret_cast<const std::uint32_t*>(
                logical.data() + static_cast<std::size_t>(y) * kPitch);
            for (int sy = 0; sy < scale; ++sy) {
                auto* dst = reinterpret_cast<std::uint32_t*>(
                    frame.data() +
                    static_cast<std::size_t>(y * scale + sy) * scaled_pitch);
                for (int x = 0; x < kFrameWidth; ++x) {
                    for (int sx = 0; sx < scale; ++sx) {
                        dst[x * scale + sx] = src[x];
                    }
                }
            }
        }

        const auto result = apply_regional_title_presentation(
            RegionalPresentation::Europe,
            true,
            frame.data(),
            scaled_pitch,
            scaled_width,
            scaled_height,
            scale);
        assert(result == RegionalTitlePresentationResult::EuropeApplied);
        assert(regional_title_visible_crop_digest(
                   frame.data(),
                   scaled_pitch,
                   scaled_width,
                   scaled_height,
                   scale) == kTargetCropBgrFnv1a64);

        std::size_t index = 0;
        for (int y = 0; y < kHeight; ++y) {
            for (int x = 0; x < kWidth; ++x, ++index) {
                const auto* first =
                    frame.data() +
                    static_cast<std::size_t>(
                        (kOriginY + y) * scale) * scaled_pitch +
                    static_cast<std::size_t>(
                        (kOriginX + x) * scale) * 4u;
                for (int sy = 0; sy < scale; ++sy) {
                    for (int sx = 0; sx < scale; ++sx) {
                        const auto* pixel =
                            first +
                            static_cast<std::size_t>(sy) * scaled_pitch +
                            static_cast<std::size_t>(sx) * 4u;
                        assert(pixel[0] == first[0]);
                        assert(pixel[1] == first[1]);
                        assert(pixel[2] == first[2]);
                    }
                }
            }
        }
        assert(index == kIndexCount);
    }

    {
        auto frame = canonical;
        const auto before = frame;
        const auto result = apply_regional_title_presentation(
            RegionalPresentation::Europe,
            true,
            frame.data(),
            kPitch,
            kFrameWidth,
            kFrameHeight,
            5);
        assert(result == RegionalTitlePresentationResult::FailedClosed);
        assert(frame == before);
    }

    {
        auto frame = canonical;
        const auto before = frame;
        const auto result = apply_regional_title_presentation(
            RegionalPresentation::Europe,
            true,
            frame.data(),
            kPitch,
            kWidth - 1,
            kFrameHeight);
        assert(result == RegionalTitlePresentationResult::FailedClosed);
        assert(frame == before);
    }

    return 0;
}
