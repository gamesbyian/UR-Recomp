#pragma once

#include <cstdint>

namespace ur::product {

// The stock 2P guest continues to receive two independent pad sources.
// A Modern tournament panel freezes guest frames and owns the human P1 word,
// but its own event handler does not own P2. Consume new P2 press edges
// at the source boundary while that panel is visible; remember consumed
// presses so their corresponding releases are swallowed even AFTER close.
// Releases of presses predating the panel are passed to the framework.
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
        if (!button_bit) return {consumed_buttons, true};
        if (pressed) {
            return {consumed_buttons | button_bit, true};
        }
        if (consumed_buttons & button_bit) {
            // Release a press the panel itself intercepted.
            return {consumed_buttons & ~button_bit, true};
        }
        // This button was already held before the panel opened. Allow its
        // release to reach framework input so the old guest-side held state
        // can clear while guest frames are frozen. Swallowing this release
        // would risk leaving P2 stuck after the panel closes.
        return {consumed_buttons, false};
    }
    if (!pressed && button_bit && (consumed_buttons & button_bit)) {
        return {consumed_buttons & ~button_bit, true};
    }
    return {consumed_buttons, false};
}

}  // namespace ur::product
