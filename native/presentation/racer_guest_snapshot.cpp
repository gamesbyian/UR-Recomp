#include "racer_guest_snapshot.hpp"

namespace ur::presentation {
namespace {

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
    if (wram == nullptr || size < RacerGuestAddresses::wram_size) {
        return std::nullopt;
    }

    RacerGuestSnapshot snapshot{};
    snapshot.composition = {
        read_le16(wram + RacerGuestAddresses::p1_primary),
        read_le16(wram + RacerGuestAddresses::p2_primary),
        read_le16(wram + RacerGuestAddresses::p1_companion),
        read_le16(wram + RacerGuestAddresses::p2_companion),
        read_le16(wram + RacerGuestAddresses::p1_selector),
        read_le16(wram + RacerGuestAddresses::p2_selector),
        read_le16(wram + RacerGuestAddresses::p1_companion_gate),
        read_le16(wram + RacerGuestAddresses::p2_companion_gate),
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
        snapshot->composition,
        player
    );
}

}  // namespace ur::presentation
