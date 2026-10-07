#include "presentation_density_compositor.hpp"

#include <cstddef>
#include <cstdint>

namespace ur::product {

bool compose_nearest_density_frame(
    std::uint8_t* dst,
    std::size_t pitch,
    const std::uint8_t* field,
    int frame_width,
    int frame_height,
    int scale) noexcept {
    if (!dst || !field ||
        frame_width <= 0 || frame_height <= 0 ||
        scale < 1 || scale > 4) {
        return false;
    }

    const std::size_t out_width =
        static_cast<std::size_t>(frame_width) * static_cast<std::size_t>(scale);
    if (pitch < out_width * 4u) return false;

    for (int y = 0; y < frame_height; ++y) {
        const auto* src = reinterpret_cast<const std::uint32_t*>(
            field + static_cast<std::size_t>(y) *
                        static_cast<std::size_t>(frame_width) * 4u);
        for (int sy = 0; sy < scale; ++sy) {
            auto* row = reinterpret_cast<std::uint32_t*>(
                dst + static_cast<std::size_t>(y * scale + sy) * pitch);
            for (int x = 0; x < frame_width; ++x) {
                const std::uint32_t pixel = src[x];
                for (int sx = 0; sx < scale; ++sx) {
                    row[x * scale + sx] = pixel;
                }
            }
        }
    }
    return true;
}

}  // namespace ur::product
