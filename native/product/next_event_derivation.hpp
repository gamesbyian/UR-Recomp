#pragma once

#include <array>
#include <cstdint>
#include <optional>

namespace ur::product {

// Return the only unfinished slot in a five-event tour, but only when the
// qualification state is well-formed and exactly four events are qualified.
// Ambiguous, complete, empty, or malformed rows fail closed.
constexpr std::optional<std::uint8_t> unique_remaining_tour_slot(
    const std::array<std::uint8_t, 5>& qualified
) noexcept {
    std::optional<std::uint8_t> remaining;
    unsigned qualified_count = 0;
    for (std::uint8_t slot = 0; slot < qualified.size(); ++slot) {
        if (qualified[slot] > 1) return std::nullopt;
        if (qualified[slot] == 1) {
            ++qualified_count;
            continue;
        }
        if (remaining) return std::nullopt;
        remaining = slot;
    }
    return qualified_count == 4 ? remaining : std::nullopt;
}

// Convert the unique remaining tour slot into the canonical zero-based global
// 45-course id used by the stock menu/course catalog. No route is implied.
constexpr std::optional<std::uint8_t> unique_next_track_id(
    std::uint8_t tour_row,
    const std::array<std::uint8_t, 5>& qualified
) noexcept {
    if (tour_row >= 9) return std::nullopt;
    const auto slot = unique_remaining_tour_slot(qualified);
    if (!slot) return std::nullopt;
    return static_cast<std::uint8_t>(tour_row * 5u + *slot);
}

}  // namespace ur::product
