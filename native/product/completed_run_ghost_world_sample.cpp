#include "completed_run_ghost_world_sample.hpp"

namespace ur::product {
namespace {

constexpr std::size_t kWorldX = 0x0411;
constexpr std::size_t kWorldY = 0x0415;
constexpr std::size_t kPitch = 0x04C7;
constexpr std::size_t kFacing = 0x0BA1;
constexpr std::size_t kSemanticFrame = 0x0FE9;
constexpr std::size_t kP1Primary = 0x0FE9;
constexpr std::size_t kP2Primary = 0x0FEB;
constexpr std::size_t kP1Companion = 0x0D3F;
constexpr std::size_t kP2Companion = 0x0D41;
constexpr std::size_t kP1Selector = 0x0C83;
constexpr std::size_t kP2Selector = 0x0C85;
constexpr std::size_t kP1CompanionGate = 0x0D1B;
constexpr std::size_t kP2CompanionGate = 0x0D1D;
constexpr std::size_t kSpriteAttr = 0x150C;
constexpr std::size_t kMinimumWramSize = kSpriteAttr + 1;

std::uint16_t read_le16(const std::uint8_t* wram, std::size_t offset) {
    return static_cast<std::uint16_t>(
        static_cast<std::uint16_t>(wram[offset]) |
        (static_cast<std::uint16_t>(wram[offset + 1]) << 8));
}

}  // namespace

std::optional<CompletedRunGhostWorldSample> read_completed_run_ghost_world_sample(
    const std::uint8_t* wram,
    std::size_t wram_size,
    std::uint64_t race_frame) {
    if (!wram || wram_size < kMinimumWramSize) return std::nullopt;

    CompletedRunGhostWorldSample sample;
    sample.race_frame = race_frame;
    sample.world_x = read_le16(wram, kWorldX);
    sample.world_y = read_le16(wram, kWorldY);
    sample.pitch_angle = read_le16(wram, kPitch);
    sample.semantic_frame_id = read_le16(wram, kSemanticFrame);
    sample.facing = wram[kFacing];
    sample.sprite_attr = wram[kSpriteAttr];
    sample.composition = {
        read_le16(wram, kP1Primary),
        read_le16(wram, kP2Primary),
        read_le16(wram, kP1Companion),
        read_le16(wram, kP2Companion),
        read_le16(wram, kP1Selector),
        read_le16(wram, kP2Selector),
        read_le16(wram, kP1CompanionGate),
        read_le16(wram, kP2CompanionGate),
    };
    return sample;
}

}  // namespace ur::product
