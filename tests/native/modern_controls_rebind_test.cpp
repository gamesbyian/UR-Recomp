#include "modern_controls_rebind.hpp"

#include <cassert>
#include <cstring>

using namespace ur::product;

int main() {
    static_assert(
        static_cast<int>(ModernControlBinding::Count) == 12,
        "SNES P1 controls must remain the framework's 12-button set");

    ModernControlsRebindState state;
    assert(state.selected == ModernControlBinding::A);
    assert(!state.capturing);
    assert(modern_control_binding_count() == 12);
    assert(std::strcmp(
               modern_control_binding_name(ModernControlBinding::Start),
               "START") == 0);

    assert(modern_controls_move(&state, -1));
    assert(state.selected == ModernControlBinding::Right);
    assert(modern_controls_move(&state, 1));
    assert(state.selected == ModernControlBinding::A);

    auto command = modern_controls_handle_action(
        &state, ModernControlsAction::Confirm);
    assert(command.kind == ModernControlsCommandKind::BeginCapture);
    assert(command.binding == ModernControlBinding::A);
    assert(state.capturing);

    // Navigation and clear/reset commands are modal while waiting for a key.
    assert(!modern_controls_move(&state, 1));
    command = modern_controls_handle_action(
        &state, ModernControlsAction::Clear);
    assert(!command.actionable());
    assert(state.capturing);

    // Invalid/unbound scancodes are not accepted as captured keyboard input.
    command = modern_controls_capture_key(&state, 0);
    assert(!command.actionable());
    assert(state.capturing);

    command = modern_controls_capture_key(&state, 42);
    assert(command.kind == ModernControlsCommandKind::ApplyCapturedKey);
    assert(command.binding == ModernControlBinding::A);
    assert(command.key_scancode == 42);
    assert(!state.capturing);

    // Duplicate physical keys are intentionally legal. The model emits the
    // same scancode for another logical SNES control without deduplication.
    (void)modern_controls_handle_action(&state, ModernControlsAction::Next);
    command = modern_controls_handle_action(&state, ModernControlsAction::Confirm);
    assert(state.capturing);
    command = modern_controls_capture_key(&state, 42);
    assert(command.kind == ModernControlsCommandKind::ApplyCapturedKey);
    assert(command.binding == ModernControlBinding::B);
    assert(command.key_scancode == 42);
    assert(!state.capturing);

    // Return to A so the existing navigation assertions retain their intent.
    (void)modern_controls_handle_action(&state, ModernControlsAction::Previous);

    (void)modern_controls_handle_action(
        &state, ModernControlsAction::Next);
    assert(state.selected == ModernControlBinding::B);

    command = modern_controls_handle_action(
        &state, ModernControlsAction::Clear);
    assert(command.kind == ModernControlsCommandKind::ClearBinding);
    assert(command.binding == ModernControlBinding::B);

    command = modern_controls_handle_action(
        &state, ModernControlsAction::Reset);
    assert(command.kind == ModernControlsCommandKind::ResetPlayer);

    command = modern_controls_handle_action(
        &state, ModernControlsAction::Confirm);
    assert(state.capturing);
    command = modern_controls_handle_action(
        &state, ModernControlsAction::Back);
    assert(!command.actionable());
    assert(!state.capturing);

    command = modern_controls_handle_action(
        &state, ModernControlsAction::Back);
    assert(command.kind == ModernControlsCommandKind::Close);

    return 0;
}
