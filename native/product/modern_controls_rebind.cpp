#include "modern_controls_rebind.hpp"

namespace ur::product {

namespace {

int binding_index(ModernControlBinding binding) noexcept {
    return static_cast<int>(binding);
}

ModernControlBinding binding_from_index(int index) noexcept {
    return static_cast<ModernControlBinding>(index);
}

}  // namespace

int modern_control_binding_count() noexcept {
    return binding_index(ModernControlBinding::Count);
}

const char* modern_control_binding_name(
    ModernControlBinding binding) noexcept {
    switch (binding) {
    case ModernControlBinding::A: return "A";
    case ModernControlBinding::B: return "B";
    case ModernControlBinding::X: return "X";
    case ModernControlBinding::Y: return "Y";
    case ModernControlBinding::L: return "L";
    case ModernControlBinding::R: return "R";
    case ModernControlBinding::Start: return "START";
    case ModernControlBinding::Select: return "SELECT";
    case ModernControlBinding::Up: return "UP";
    case ModernControlBinding::Down: return "DOWN";
    case ModernControlBinding::Left: return "LEFT";
    case ModernControlBinding::Right: return "RIGHT";
    case ModernControlBinding::Count:
    default:
        return "UNKNOWN";
    }
}

bool modern_controls_move(
    ModernControlsRebindState* state,
    int delta) noexcept {
    if (!state || state->capturing || delta == 0) return false;

    const int count = modern_control_binding_count();
    int selected = binding_index(state->selected);
    selected = (selected + (delta > 0 ? 1 : -1) + count) % count;
    state->selected = binding_from_index(selected);
    return true;
}

ModernControlsCommand modern_controls_handle_action(
    ModernControlsRebindState* state,
    ModernControlsAction action) noexcept {
    if (!state) return {};

    if (state->capturing) {
        if (action == ModernControlsAction::Back) {
            state->capturing = false;
        }
        return {};
    }

    switch (action) {
    case ModernControlsAction::Previous:
        (void)modern_controls_move(state, -1);
        return {};
    case ModernControlsAction::Next:
        (void)modern_controls_move(state, 1);
        return {};
    case ModernControlsAction::Confirm:
        state->capturing = true;
        return {
            ModernControlsCommandKind::BeginCapture,
            state->selected,
            0,
        };
    case ModernControlsAction::Clear:
        return {
            ModernControlsCommandKind::ClearBinding,
            state->selected,
            0,
        };
    case ModernControlsAction::Reset:
        return {
            ModernControlsCommandKind::ResetPlayer,
            state->selected,
            0,
        };
    case ModernControlsAction::Back:
        return {
            ModernControlsCommandKind::Close,
            state->selected,
            0,
        };
    }
    return {};
}

bool modern_controls_action_for_snes_control(
    int control,
    ModernControlsAction* action) noexcept {
    if (!action) return false;

    // SNESRecomp GamepadMap semantic order:
    // Up, Down, Left, Right, Select, Start, A, B, X, Y, L, R.
    switch (control) {
    case 0:
        *action = ModernControlsAction::Previous;
        return true;
    case 1:
        *action = ModernControlsAction::Next;
        return true;
    case 5:
    case 7:
        *action = ModernControlsAction::Back;
        return true;
    case 6:
        *action = ModernControlsAction::Confirm;
        return true;
    case 8:
        *action = ModernControlsAction::Clear;
        return true;
    case 9:
        *action = ModernControlsAction::Reset;
        return true;
    default:
        return false;
    }
}

ModernControlsCommand modern_controls_capture_key(
    ModernControlsRebindState* state,
    int key_scancode) noexcept {
    if (!state || !state->capturing || key_scancode <= 0) return {};

    state->capturing = false;
    return {
        ModernControlsCommandKind::ApplyCapturedKey,
        state->selected,
        key_scancode,
    };
}

}  // namespace ur::product
