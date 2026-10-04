#include "completed_run_ghost_projection.hpp"

namespace ur::product {
namespace {

constexpr std::size_t kScale = 0x03ED;
constexpr std::size_t kCameraX = 0x0419;
constexpr std::size_t kCameraY = 0x041D;
constexpr std::size_t kLowerBound = 0x0421;
constexpr std::size_t kUpperBound = 0x0423;
constexpr std::size_t kWrapMask = 0x0D49;
constexpr std::size_t kAlternateProjectionMode = 0x0DDB;
constexpr std::size_t kMinimumWramSize = kAlternateProjectionMode + 1;

std::uint16_t read_le16(const std::uint8_t* wram, std::size_t offset) {
    return static_cast<std::uint16_t>(
        static_cast<std::uint16_t>(wram[offset]) |
        (static_cast<std::uint16_t>(wram[offset + 1]) << 8));
}

/* 65816 BMI/BPL after CMP depend on bit 15 of the wrapped subtraction.
 * Deliberately emulate that flag rather than replacing it with a C++ signed
 * comparison, whose overflow behavior would not be the same operation. */
bool negative_after_cmp(std::uint16_t lhs, std::uint16_t rhs) {
    return (static_cast<std::uint16_t>(lhs - rhs) & 0x8000u) != 0;
}

int signed_word(std::uint16_t value) {
    return (value & 0x8000u)
        ? static_cast<int>(value) - 0x10000
        : static_cast<int>(value);
}

}  // namespace

std::optional<CompletedRunGhostProjectionContext>
read_completed_run_ghost_projection_context(
    const std::uint8_t* wram,
    std::size_t wram_size) {
    if (!wram || wram_size < kMinimumWramSize) return std::nullopt;

    // $0DDB takes a separate composition path with different Y bounds.
    if (wram[kAlternateProjectionMode] != 0) return std::nullopt;

    const std::uint16_t shifts = read_le16(wram, kScale);
    // Real ordinary-race captures use a tiny viewport scaling count. Refuse
    // implausible/corrupt context instead of burning an unbounded host loop.
    if (shifts > 15u) return std::nullopt;

    return CompletedRunGhostProjectionContext{
        read_le16(wram, kCameraX),
        read_le16(wram, kCameraY),
        shifts,
        read_le16(wram, kLowerBound),
        read_le16(wram, kUpperBound),
        read_le16(wram, kWrapMask),
    };
}

std::optional<CompletedRunGhostScreenProjection>
project_completed_run_ghost_sample(
    const CompletedRunGhostWorldSample& sample,
    const CompletedRunGhostProjectionContext& live) {
    // $82:ACF5..AD06: Y = worldY - cameraY, visible in [-41, 225).
    const std::uint16_t y_delta =
        static_cast<std::uint16_t>(sample.world_y - live.camera_y);
    if (negative_after_cmp(y_delta, 0xFFD7u) ||
        !negative_after_cmp(y_delta, 0x00E1u)) {
        return std::nullopt;
    }

    // $82:AD08..AD23: preserve raw X delta in X, scale A for viewport
    // culling, then retain the scaled value for the high-OAM sign bit.
    const std::uint16_t raw_x =
        static_cast<std::uint16_t>(sample.world_x - live.camera_x);
    std::uint16_t scaled_x = raw_x;
    for (std::uint16_t i = 0; i < live.horizontal_scale_shifts; ++i) {
        scaled_x = static_cast<std::uint16_t>(scaled_x << 1);
    }

    if (negative_after_cmp(scaled_x, live.horizontal_lower_bound) ||
        !negative_after_cmp(scaled_x, live.horizontal_upper_bound)) {
        return std::nullopt;
    }

    // $82:AD25..AD5D: screen X uses the UNSCALED delta masked by $0D49;
    // negative scaled X sets the high OAM bit.
    const std::uint8_t x_low = static_cast<std::uint8_t>(
        raw_x & live.horizontal_wrap_mask);
    const bool x_high = (scaled_x & 0x8000u) != 0;
    const int x = x_high
        ? static_cast<int>(x_low) - 0x100
        : static_cast<int>(x_low);

    return CompletedRunGhostScreenProjection{
        x,
        signed_word(y_delta),
        x_high,
    };
}

}  // namespace ur::product
