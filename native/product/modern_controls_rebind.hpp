#pragma once

#include <cstdint>
#include <optional>

namespace ur::product {

enum class ModernControlBinding : std::uint8_t {
    A = 0,
    B,
    X,
    Y,
    L,
    R,
    Start,
    Select,
    Up,
    Down,
    Left,
    Right,
    Count,
};

enum class ModernControlsCommandKind : std::uint8_t {
    None = 0,
    BeginCapture,
    ApplyCapturedKey,
    ClearBinding,
    ResetPlayer,
    Close,
};

struct ModernControlsCommand {
    ModernControlsCommandKind kind = ModernControlsCommandKind::None;
    ModernControlBinding binding = ModernControlBinding::A;
    int key_scancode = 0;

    bool actionable() const noexcept {
        return kind != ModernControlsCommandKind::None;
    }
};

enum class ModernControlsAction : std::uint8_t {
    Previous = 0,
    Next,
    Confirm,
    Back,
    Clear,
    Reset,
};

struct ModernControlsRebindState {
    ModernControlBinding selected = ModernControlBinding::A;
    bool capturing = false;
};

int modern_control_binding_count() noexcept;
const char* modern_control_binding_name(ModernControlBinding binding) noexcept;

bool modern_controls_move(
    ModernControlsRebindState* state,
    int delta) noexcept;

ModernControlsCommand modern_controls_handle_action(
    ModernControlsRebindState* state,
    ModernControlsAction action) noexcept;

ModernControlsCommand modern_controls_capture_key(
    ModernControlsRebindState* state,
    int key_scancode) noexcept;

}  // namespace ur::product
