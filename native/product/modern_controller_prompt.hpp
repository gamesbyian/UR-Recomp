#pragma once

#include <cstdint>

namespace ur::product {

/*
 * SNESRecomp's configured GamepadMap resolves physical input to these stable
 * semantic controls before title-owned product handling:
 *
 * Up, Down, Left, Right, Select, Start, A, B, X, Y, L, R.
 *
 * Product prompts may name these semantic controls. They must not infer a
 * physical Xbox/PlayStation/Nintendo glyph from device brand or SDL button
 * index because the user may have remapped GamepadMap.
 */
enum class ModernControllerSemanticControl : std::uint8_t {
    Up = 0,
    Down = 1,
    Left = 2,
    Right = 3,
    Select = 4,
    Start = 5,
    A = 6,
    B = 7,
    X = 8,
    Y = 9,
    L = 10,
    R = 11,
};

constexpr bool modern_controller_semantic_control_from_index(
    int control,
    ModernControllerSemanticControl* out) noexcept {
    if (!out || control < 0 || control > 11) return false;
    *out = static_cast<ModernControllerSemanticControl>(control);
    return true;
}

constexpr const char* modern_controller_semantic_name(
    ModernControllerSemanticControl control) noexcept {
    switch (control) {
    case ModernControllerSemanticControl::Up: return "UP";
    case ModernControllerSemanticControl::Down: return "DOWN";
    case ModernControllerSemanticControl::Left: return "LEFT";
    case ModernControllerSemanticControl::Right: return "RIGHT";
    case ModernControllerSemanticControl::Select: return "SELECT";
    case ModernControllerSemanticControl::Start: return "START";
    case ModernControllerSemanticControl::A: return "A";
    case ModernControllerSemanticControl::B: return "B";
    case ModernControllerSemanticControl::X: return "X";
    case ModernControllerSemanticControl::Y: return "Y";
    case ModernControllerSemanticControl::L: return "L";
    case ModernControllerSemanticControl::R: return "R";
    }
    return "UNKNOWN";
}

constexpr const char* modern_controller_semantic_prompt(
    ModernControllerSemanticControl control) noexcept {
    switch (control) {
    case ModernControllerSemanticControl::Up: return "[UP]";
    case ModernControllerSemanticControl::Down: return "[DOWN]";
    case ModernControllerSemanticControl::Left: return "[LEFT]";
    case ModernControllerSemanticControl::Right: return "[RIGHT]";
    case ModernControllerSemanticControl::Select: return "[SELECT]";
    case ModernControllerSemanticControl::Start: return "[START]";
    case ModernControllerSemanticControl::A: return "[A]";
    case ModernControllerSemanticControl::B: return "[B]";
    case ModernControllerSemanticControl::X: return "[X]";
    case ModernControllerSemanticControl::Y: return "[Y]";
    case ModernControllerSemanticControl::L: return "[L]";
    case ModernControllerSemanticControl::R: return "[R]";
    }
    return "[?]";
}

constexpr const char* modern_controller_prompt_from_index(
    int control) noexcept {
    ModernControllerSemanticControl semantic{};
    return modern_controller_semantic_control_from_index(control, &semantic)
        ? modern_controller_semantic_prompt(semantic)
        : "[?]";
}

}  // namespace ur::product
