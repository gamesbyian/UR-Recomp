#include "racer_guest_snapshot.hpp"

namespace ur::presentation {
namespace {

constexpr std::size_t kWramSize = 0x20000;

constexpr std::size_t kP1Primary = 0x0FE9;
constexpr std::size_t kP2Primary = 0x0FEB;
constexpr std::size_t kP1Companion = 0x0D3F;
constexpr std::size_t kP2Companion = 0x0D41;
constexpr std::size_t kP1Selector = 0x0C83;
constexpr std::size_t kP2Selector = 0x0C85;
constexpr std::size_t kP1CompanionGate = 0x0D1B;
constexpr std::size_t kP2CompanionGate = 0x0D1D;

constexpr std::uint16_t read_le16(const std::uint8_t* p) noexcept {
    return static_cast<std::uint16_t>(
        static_cast<std::uint16_t>(p[0]) |
        (static_cast<std::uint16_t>(p[1]) << 8)
    );
}

}  // namespace

std::optional<RacerGuestSnapshot> read_racer_guest_snapshot(
    const std::uint8_t* wram,
    std::size_t size
) noexcept {
    if (wram == nullptr || size < kWramSize) {
        return std::nullopt;
    }

    RacerGuestSnapshot snapshot{};
    snapshot.composition = {
        read_le16(wram + kP1Primary),
        read_le16(wram + kP2Primary),
        read_le16(wram + kP1Companion),
        read_le16(wram + kP2Companion),
        read_le16(wram + kP1Selector),
        read_le16(wram + kP2Selector),
        read_le16(wram + kP1CompanionGate),
        read_le16(wram + kP2CompanionGate),
    };
    snapshot.p1_semantic_frame_id = snapshot.composition.p1_primary;
    snapshot.p2_semantic_frame_id = snapshot.composition.p2_primary;
    return snapshot;
}

SelectionResult select_racer_presentation_from_wram(
    GraphicsPack requested_pack,
    const std::uint8_t* wram,
    std::size_t size,
    std::uint8_t player
) noexcept {
    const auto snapshot = read_racer_guest_snapshot(wram, size);
    if (!snapshot.has_value()) {
        return {
            requested_pack,
            GraphicsPack::Original,
            FallbackReason::UnregisteredSemanticFrame,
            nullptr,
        };
    }

    const std::uint16_t semantic_frame_id =
        player == 1 ? snapshot->p1_semantic_frame_id :
        player == 2 ? snapshot->p2_semantic_frame_id :
                      static_cast<std::uint16_t>(0xFFFF);

    return select_racer_presentation(
        requested_pack,
        semantic_frame_id,
        snapshot->composition
    );
}

}  // namespace ur::presentation
