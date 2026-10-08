#pragma once

#include <cstdint>

namespace ur::product {

// The stock 2P guest continues to receive two independent pad sources.
// A Modern tournament panel freezes guest frames and owns the human P1 word,
// but its own event handler does not own P2. Consume new P2 presses/releases
// at the source boundary while that panel is visible; remember consumed
// presses so their release is also swallowed AFTER the panel closes.
//
// A P2 button already held BEFORE the panel opens is not necessarily present
// in this source-edge mask. That pre-existing-held case still requires a
// guest-word or framework-state witness before claiming full input isolation.
// This pure policy therefore covers a narrower, demonstrable boundary.
struct TournamentP2ModalInputDecision {
    std::uint32_t consumed_buttons = 0u;
    bool consume_event = false;
};

constexpr TournamentP2ModalInputDecision tournament_p2_modal_input(
    std::uint32_t consumed_buttons,
    bool panel_visible,
    std::uint32_t button_bit,
    bool pressed) noexcept {
    if (panel_visible) {
        if (button_bit) {
            if (pressed) {
                consumed_buttons |= button_bit;
            } else {
                consumed_buttons &= ~button_bit;
            }
        }
        return {consumed_buttons, true};
    }
    if (!pressed && button_bit && (consumed_buttons & button_bit)) {
        return {consumed_buttons & ~button_bit, true};
    }
    return {consumed_buttons, false};
}

}  // namespace ur::product
