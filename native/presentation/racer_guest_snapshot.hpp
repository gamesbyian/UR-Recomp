#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>

#include "racer_replacement_selector.hpp"

namespace ur::presentation {

struct RacerGuestAddresses {
    static constexpr std::size_t wram_size = 0x20000;
    static constexpr std::size_t p1_primary = 0x0FE9;
    static constexpr std::size_t p2_primary = 0x0FEB;
    static constexpr std::size_t p1_companion = 0x0D3F;
    static constexpr std::size_t p2_companion = 0x0D41;
    static constexpr std::size_t p1_selector = 0x0C83;
    static constexpr std::size_t p2_selector = 0x0C85;
    static constexpr std::size_t p1_companion_gate = 0x0D1B;
    static constexpr std::size_t p2_companion_gate = 0x0D1D;
};

struct RacerGuestSnapshot {
    RacerCompositionState composition;
    std::uint16_t p1_semantic_frame_id;
    std::uint16_t p2_semantic_frame_id;
};

std::optional<RacerGuestSnapshot> read_racer_guest_snapshot(
    const std::uint8_t* wram,
    std::size_t size
) noexcept;

SelectionResult select_racer_presentation_from_wram(
    GraphicsPack requested_pack,
    const std::uint8_t* wram,
    std::size_t size,
    std::uint8_t player
) noexcept;

}  // namespace ur::presentation
