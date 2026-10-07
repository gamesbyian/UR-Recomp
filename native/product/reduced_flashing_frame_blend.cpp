#include "reduced_flashing_frame_blend.hpp"

#include <limits>

namespace ur::product {
namespace {

constexpr std::uint8_t byte_mean_floor(
    std::uint8_t a,
    std::uint8_t b) noexcept {
    return static_cast<std::uint8_t>(
        (a & b) + (((a ^ b) >> 1) & 0x7Fu));
}

}  // namespace

void ReducedFlashingFrameBlend::reset() noexcept {
    valid_ = false;
}

bool ReducedFlashingFrameBlend::ensure_geometry(
    int width,
    int height) noexcept {
    if (width <= 0 || height <= 0) return false;

    const auto w = static_cast<std::size_t>(width);
    const auto h = static_cast<std::size_t>(height);
    if (w > std::numeric_limits<std::size_t>::max() / h) return false;
    const auto pixels = w * h;
    if (pixels > std::numeric_limits<std::size_t>::max() / 4u) return false;
    const auto bytes = pixels * 4u;

    if (width_ == width &&
        height_ == height &&
        previous_.size() == bytes) {
        return true;
    }

    try {
        previous_.resize(bytes);
    } catch (...) {
        return false;
    }
    width_ = width;
    height_ = height;
    valid_ = false;
    return true;
}

bool ReducedFlashingFrameBlend::apply(
    std::uint8_t* frame,
    int width,
    int height,
    std::size_t pitch_bytes,
    bool advance_reference) noexcept {
    if (!frame || width <= 0 || height <= 0) return false;

    const auto row_bytes = static_cast<std::size_t>(width) * 4u;
    if (row_bytes / 4u != static_cast<std::size_t>(width) ||
        pitch_bytes < row_bytes) {
        return false;
    }
    if (!ensure_geometry(width, height)) return false;

    if (!advance_reference && !valid_) {
        return false;
    }

    const bool blended = valid_;
    for (int y = 0; y < height; ++y) {
        auto* row = frame + static_cast<std::size_t>(y) * pitch_bytes;
        auto* previous =
            previous_.data() + static_cast<std::size_t>(y) * row_bytes;
        for (std::size_t i = 0; i < row_bytes; ++i) {
            const std::uint8_t current = row[i];
            if (blended) {
                row[i] = byte_mean_floor(current, previous[i]);
            }
            if (advance_reference) {
                previous[i] = current;
            }
        }
    }

    if (advance_reference) valid_ = true;
    return blended;
}

}  // namespace ur::product
