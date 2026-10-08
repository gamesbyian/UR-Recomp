#pragma once

#include <cstdint>

namespace ur::product {

inline constexpr std::uint32_t kTournamentP2GuestButtonMask = 0x0fffu;

struct ModernTournamentP2GuestInputState {
    // Mark the whole P2 word as needing release when the tournament modal
    // opens. Host-owned frame hold can skip every controller sample while
    // the panel is visible, so recording only on frozen frames is unsafe.
    std::uint32_t awaiting_release = 0u;
};

struct ModernTournamentP2GuestInputResult {
    ModernTournamentP2GuestInputState state{};
    std::uint32_t inputs = 0u;
};

constexpr ModernTournamentP2GuestInputState tournament_p2_guest_arm() noexcept {
    return {kTournamentP2GuestButtonMask};
}

// Called on human P2 input only, before it is shifted into the guest word.
// Scripted/input-file/debug masks are not passed through this title callback.
// A held bit from before a modal cannot reappear after closing until the
// framework has observed that bit released. Other bits are free immediately
// after the first post-close physical sample that shows them up.
constexpr ModernTournamentP2GuestInputResult tournament_p2_guest_filter(
    ModernTournamentP2GuestInputState state,
    bool tournament_panel_visible,
    std::uint32_t raw_human_inputs) noexcept {
    if (tournament_panel_visible) {
        return {state, 0u};
    }
    const auto raw_buttons = raw_human_inputs & kTournamentP2GuestButtonMask;
    state.awaiting_release &= raw_buttons;
    return {state,
        (raw_buttons & ~state.awaiting_release) |
        (raw_human_inputs & ~kTournamentP2GuestButtonMask)};
}

} // namespace ur::product
