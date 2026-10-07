#include "presentation_density_compositor.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
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

}  // namespace

int main() {
    assert_2x();
    assert_3x_with_padded_pitch();

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
