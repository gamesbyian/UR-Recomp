#include "presentation_density_compositor.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

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

    const std::size_t width = static_cast<std::size_t>(frame_width);
    const std::size_t height = static_cast<std::size_t>(frame_height);
    const std::size_t density = static_cast<std::size_t>(scale);
    constexpr std::size_t pixel_bytes = sizeof(std::uint32_t);
    constexpr std::size_t max = std::numeric_limits<std::size_t>::max();

    // The interface accepts byte buffers and an arbitrary destination pitch.
    // Check address arithmetic before touching memory. Allocation extents and
    // non-overlapping source/destination remain obligations of the caller.
    if (width > max / pixel_bytes ||
        height > max / (width * pixel_bytes) ||
        width > max / density ||
        width * density > max / pixel_bytes ||
        height > max / density) {
        return false;
    }
    const std::size_t source_pitch = width * pixel_bytes;
    const std::size_t output_row_bytes = width * density * pixel_bytes;
    const std::size_t output_height = height * density;
    if (pitch < output_row_bytes || pitch > max / output_height) {
        return false;
    }

    for (std::size_t y = 0; y < height; ++y) {
        const std::uint8_t* source = field + y * source_pitch;
        for (std::size_t sy = 0; sy < density; ++sy) {
            std::uint8_t* row = dst + (y * density + sy) * pitch;
            for (std::size_t x = 0; x < width; ++x) {
                std::uint32_t pixel = 0;
                // Real SDL/host buffers need not be uint32_t-aligned. The
                // previous reinterpret_cast dereferences had undefined
                // behaviour on odd row pitches and non-aligned source data.
                std::memcpy(&pixel, source + x * pixel_bytes, pixel_bytes);
                for (std::size_t sx = 0; sx < density; ++sx) {
                    std::memcpy(row + (x * density + sx) * pixel_bytes,
                                &pixel, pixel_bytes);
                }
            }
        }
    }
    return true;
}

}  // namespace ur::product
