#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>

#include "racer_replacement_selector.hpp"

namespace ur::presentation {

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
