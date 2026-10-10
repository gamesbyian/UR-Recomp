#pragma once

#include <array>
#include <cstddef>

namespace ur::product {

// Edge coalescing for physical *frontend navigation* only. The existing
// Baldosa human-input filter remains the sole guest controller authority.
// Each physical key/button has an independent latch; auto-repeat and repeated
// SDL KEYDOWN events cannot activate an already-held Modern action.
class ModernRootPhysicalEdges {
public:
    static constexpr std::size_t kKeyboardActions = 4;  // up/down/enter/escape
    static constexpr std::size_t kP1Buttons = 5;        // up/down/A/Start/B

    bool keyboard(std::size_t index, bool pressed) noexcept {
        return transition(keys_, index, pressed);
    }
    bool p1_gamepad(std::size_t index, bool pressed) noexcept {
        return transition(pad_, index, pressed);
    }
    void reset() noexcept {
        keys_.fill(false);
        pad_.fill(false);
    }

private:
    template <std::size_t N>
    static bool transition(std::array<bool, N>& latches,
                           std::size_t index, bool pressed) noexcept {
        if (index >= N) return false;
        const bool was_pressed = latches[index];
        latches[index] = pressed;
        return pressed && !was_pressed;
    }

    std::array<bool, kKeyboardActions> keys_{};
    std::array<bool, kP1Buttons> pad_{};
};

}  // namespace ur::product
