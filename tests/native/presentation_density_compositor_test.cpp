#include "presentation_density_compositor.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <vector>

using ur::product::compose_nearest_density_frame;

namespace {

constexpr std::uint32_t A = 0xFF112233u;
constexpr std::uint32_t B = 0xFF445566u;
constexpr std::uint32_t C = 0xFF778899u;
constexpr std::uint32_t D = 0xFFAABBCCu;

void assert_2x() {
    const std::array<std::uint32_t, 4> src{A, B, C, D};
    std::array<std::uint32_t, 16> dst{};
    assert(compose_nearest_density_frame(
        reinterpret_cast<std::uint8_t*>(dst.data()),
        4u * 4u,
        reinterpret_cast<const std::uint8_t*>(src.data()),
        2,
        2,
        2));

    const std::array<std::uint32_t, 16> expected{
        A, A, B, B,
        A, A, B, B,
        C, C, D, D,
        C, C, D, D,
    };
    assert(dst == expected);
}

void assert_3x_with_padded_pitch() {
    const std::array<std::uint32_t, 2> src{A, B};
    constexpr int stride = 8;
    std::array<std::uint32_t, stride * 3> dst{};
    dst.fill(0xDEADBEEFu);

    assert(compose_nearest_density_frame(
        reinterpret_cast<std::uint8_t*>(dst.data()),
        stride * sizeof(std::uint32_t),
        reinterpret_cast<const std::uint8_t*>(src.data()),
        2,
        1,
        3));

    for (int y = 0; y < 3; ++y) {
        const auto offset = static_cast<std::size_t>(y * stride);
        assert(dst[offset + 0] == A);
        assert(dst[offset + 1] == A);
        assert(dst[offset + 2] == A);
        assert(dst[offset + 3] == B);
        assert(dst[offset + 4] == B);
        assert(dst[offset + 5] == B);
        assert(dst[offset + 6] == 0xDEADBEEFu);
        assert(dst[offset + 7] == 0xDEADBEEFu);
    }
}


void assert_unaligned_original_source_and_odd_host_pitch() {
    // A source buffer and each destination row are deliberately unaligned.
    // A 17-byte pitch rotates destination row alignment every scanline.
    constexpr std::array<std::uint32_t, 4> source_pixels{A, B, C, D};
    constexpr std::size_t logical_width = 2;
    constexpr std::size_t scale = 2;
    constexpr std::size_t destination_pitch = 17;
    std::array<std::uint8_t, 18> source{};
    source.fill(0xBAu);
    for (std::size_t i = 0; i < source_pixels.size(); ++i) {
        std::memcpy(source.data() + 1 + i * 4, &source_pixels[i], 4);
    }
    std::array<std::uint8_t, 1 + 4 * destination_pitch + 1> result{};
    result.fill(0xCDu);
    assert(compose_nearest_density_frame(
        result.data() + 1, destination_pitch, source.data() + 1,
        static_cast<int>(logical_width), 2, static_cast<int>(scale)));
    assert(result.front() == 0xCDu && result.back() == 0xCDu);
    const std::array<std::uint32_t, 16> expected{
        A, A, B, B,
        A, A, B, B,
        C, C, D, D,
        C, C, D, D,
    };
    for (std::size_t y = 0; y < 4; ++y) {
        const std::uint8_t* row = result.data() + 1 + y * destination_pitch;
        for (std::size_t x = 0; x < 4; ++x) {
            std::uint32_t observed = 0;
            std::memcpy(&observed, row + x * 4, 4);
            assert(observed == expected[y * 4 + x]);
        }
        // The byte following each 16-byte output line belongs to pitch,
        // not to the source raster and may not be overwritten.
        assert(row[16] == 0xCDu);
    }
    // Source data and both external sentinels are never modified.
    assert(source.front() == 0xBAu && source.back() == 0xBAu);
    for (std::size_t i = 0; i < source_pixels.size(); ++i) {
        std::uint32_t value = 0;
        std::memcpy(&value, source.data() + 1 + i * 4, 4);
        assert(value == source_pixels[i]);
    }
}

void assert_invalid_stride_arithmetic_rejected_without_writes() {
    const std::array<std::uint32_t, 1> source{A};
    std::array<std::uint8_t, 16> result{};
    result.fill(0xEAu);
    // A pathological pitch times output height must be checked before
    // pointer arithmetic, including on 32-bit size_t hosts.
    assert(!compose_nearest_density_frame(
        result.data(), std::numeric_limits<std::size_t>::max(),
        reinterpret_cast<const std::uint8_t*>(source.data()), 1, 2, 4));
    assert(!compose_nearest_density_frame(
        result.data(), 4, reinterpret_cast<const std::uint8_t*>(source.data()),
        std::numeric_limits<int>::max(), 1, 4));
    for (auto byte : result) assert(byte == 0xEAu);
}

}  // namespace

int main() {
    assert_2x();
    assert_3x_with_padded_pitch();
    assert_unaligned_original_source_and_odd_host_pitch();
    assert_invalid_stride_arithmetic_rejected_without_writes();

    {
        constexpr int logical_width = 342;
        constexpr int scale = 4;
        std::vector<std::uint32_t> src(
            static_cast<std::size_t>(logical_width), 0u);
        for (int x = 0; x < logical_width; ++x) {
            src[static_cast<std::size_t>(x)] =
                0xFF000000u | static_cast<std::uint32_t>(x);
        }
        std::vector<std::uint32_t> wide(
            static_cast<std::size_t>(logical_width * scale * scale), 0u);
        const std::size_t pitch =
            static_cast<std::size_t>(logical_width * scale) *
            sizeof(std::uint32_t);
        assert(compose_nearest_density_frame(
            reinterpret_cast<std::uint8_t*>(wide.data()),
            pitch,
            reinterpret_cast<const std::uint8_t*>(src.data()),
            logical_width,
            1,
            scale));
        for (int sy = 0; sy < scale; ++sy) {
            const auto row =
                static_cast<std::size_t>(sy * logical_width * scale);
            for (int x = 0; x < logical_width; ++x) {
                for (int sx = 0; sx < scale; ++sx) {
                    assert(wide[
                        row + static_cast<std::size_t>(x * scale + sx)] ==
                        src[static_cast<std::size_t>(x)]);
                }
            }
        }
    }

    const std::array<std::uint32_t, 1> src{A};
    std::array<std::uint32_t, 16> dst{};

    assert(compose_nearest_density_frame(
        reinterpret_cast<std::uint8_t*>(dst.data()),
        4u,
        reinterpret_cast<const std::uint8_t*>(src.data()),
        1, 1, 1));
    assert(dst[0] == A);

    assert(!compose_nearest_density_frame(
        nullptr, 4u,
        reinterpret_cast<const std::uint8_t*>(src.data()),
        1, 1, 1));
    assert(!compose_nearest_density_frame(
        reinterpret_cast<std::uint8_t*>(dst.data()), 4u,
        nullptr, 1, 1, 1));
    assert(!compose_nearest_density_frame(
        reinterpret_cast<std::uint8_t*>(dst.data()), 4u,
        reinterpret_cast<const std::uint8_t*>(src.data()),
        0, 1, 1));
    assert(!compose_nearest_density_frame(
        reinterpret_cast<std::uint8_t*>(dst.data()), 4u,
        reinterpret_cast<const std::uint8_t*>(src.data()),
        1, 0, 1));
    assert(!compose_nearest_density_frame(
        reinterpret_cast<std::uint8_t*>(dst.data()), 4u,
        reinterpret_cast<const std::uint8_t*>(src.data()),
        1, 1, 0));
    assert(!compose_nearest_density_frame(
        reinterpret_cast<std::uint8_t*>(dst.data()), 4u,
        reinterpret_cast<const std::uint8_t*>(src.data()),
        1, 1, 5));
    assert(!compose_nearest_density_frame(
        reinterpret_cast<std::uint8_t*>(dst.data()), 7u,
        reinterpret_cast<const std::uint8_t*>(src.data()),
        2, 1, 1));

    return 0;
}
