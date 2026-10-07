#pragma once

#include <array>
#include <string>

namespace ur::product {

// Physical pad glyphs in SNESRecomp's kGamepadBtn order (config.h):
// A, B, X, Y, Back, Guide, Start, L3, R3, L1, R1, DpadUp, DpadDown,
// DpadLeft, DpadRight, L2, R2. A/B/X/Y are positional (A = south), matching
// the names [GamepadMap] uses, so a glyph is what is printed on the button
// the player presses, never the SNES control it produces.
inline constexpr std::array<const char*, 17> kModernPadButtonGlyphs = {
    "A", "B", "X", "Y", "BACK", "GUIDE", "START", "L3", "R3",
    "LB", "RB", "UP", "DOWN", "LEFT", "RIGHT", "LT", "RT",
};

// Reverse-map one P1 SNES control (0..11, Up..R) to the first physical
// button whose unmodified binding produces it. `command_for_button(button)`
// is the framework's live GamepadMap lookup; `controls_base` is its first
// SNES-control command id. A control nothing is bound to reads "NONE".
template <typename CommandForButton>
std::string modern_pad_glyph_for_control(
    int control,
    int controls_base,
    CommandForButton command_for_button) {
    if (control < 0 || control > 11) return "NONE";
    for (std::size_t button = 0; button < kModernPadButtonGlyphs.size();
         ++button) {
        if (command_for_button(static_cast<int>(button)) ==
            controls_base + control) {
            return kModernPadButtonGlyphs[button];
        }
    }
    return "NONE";
}

}  // namespace ur::product
