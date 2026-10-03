#include "modern_pause_input.h"

#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace {

std::vector<std::uint8_t> machine;
int paused = 0;

std::size_t save_snapshot(void* dst, std::size_t capacity) {
    if (machine.empty() || capacity < machine.size()) return 0;
    std::copy(machine.begin(), machine.end(), static_cast<std::uint8_t*>(dst));
    return machine.size();
}

bool load_snapshot(const void* src, std::size_t size) {
    const auto* p = static_cast<const std::uint8_t*>(src);
    machine.assign(p, p + size);
    return true;
}

void set_paused(int value) { paused = value ? 1 : 0; }
int is_paused() { return paused; }

}  // namespace

int main() {
    machine = {1, 2, 3};
    UrModernSession* session = ur_modern_session_create(
        1, 64, &save_snapshot, &load_snapshot,
        &set_paused, &is_paused, nullptr, nullptr);
    assert(session);

    UrModernPauseMenu menu{};
    ur_modern_pause_menu_reset(&menu);

    // Navigation while running is inert.
    assert(ur_modern_pause_handle_action(
               session, &menu, UR_MODERN_PAUSE_NEXT) ==
           UR_MODERN_SESSION_NO_OP);

    // Toggle opens pause and resets selection to Resume.
    assert(ur_modern_pause_handle_action(
               session, &menu, UR_MODERN_PAUSE_TOGGLE) ==
           UR_MODERN_SESSION_APPLIED);
    assert(paused == 1);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_RESUME);

    // Without an anchor the host-owned settings row is still navigable.
    assert(ur_modern_pause_handle_action(
               session, &menu, UR_MODERN_PAUSE_NEXT) ==
           UR_MODERN_SESSION_APPLIED);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_FOCUS_PAUSE);

    // Generic session input deliberately does not own settings activation.
    assert(ur_modern_pause_handle_action(
               session, &menu, UR_MODERN_PAUSE_ACTIVATE) ==
           UR_MODERN_SESSION_NO_OP);
    assert(paused == 1);

    assert(ur_modern_pause_handle_action(
               session, &menu, UR_MODERN_PAUSE_PREVIOUS) ==
           UR_MODERN_SESSION_APPLIED);
    assert(ur_modern_pause_menu_selected(&menu, 0) ==
           UR_MODERN_PAUSE_RESUME);
    assert(ur_modern_pause_handle_action(
               session, &menu, UR_MODERN_PAUSE_ACTIVATE) ==
           UR_MODERN_SESSION_APPLIED);
    assert(paused == 0);

    // Arm Restart and prove the three-row model preserves Restart ordering.
    ur_modern_session_observe_race_active(session, 1);
    assert(ur_modern_session_restart_available(session));

    assert(ur_modern_pause_handle_action(
               session, &menu, UR_MODERN_PAUSE_TOGGLE) ==
           UR_MODERN_SESSION_APPLIED);
    assert(paused == 1);

    assert(ur_modern_pause_handle_action(
               session, &menu, UR_MODERN_PAUSE_NEXT) ==
           UR_MODERN_SESSION_APPLIED);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_RESTART);

    assert(ur_modern_pause_handle_action(
               session, &menu, UR_MODERN_PAUSE_NEXT) ==
           UR_MODERN_SESSION_APPLIED);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_FOCUS_PAUSE);
    assert(ur_modern_pause_handle_action(
               session, &menu, UR_MODERN_PAUSE_ACTIVATE) ==
           UR_MODERN_SESSION_NO_OP);
    assert(paused == 1);

    assert(ur_modern_pause_handle_action(
               session, &menu, UR_MODERN_PAUSE_PREVIOUS) ==
           UR_MODERN_SESSION_APPLIED);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_RESTART);

    assert(ur_modern_pause_handle_action(
               session, &menu, UR_MODERN_PAUSE_PREVIOUS) ==
           UR_MODERN_SESSION_APPLIED);
    assert(ur_modern_pause_menu_selected(&menu, 1) ==
           UR_MODERN_PAUSE_RESUME);

    assert(ur_modern_pause_handle_action(
               session, &menu, UR_MODERN_PAUSE_NEXT) ==
           UR_MODERN_SESSION_APPLIED);

    machine = {9};
    assert(ur_modern_pause_handle_action(
               session, &menu, UR_MODERN_PAUSE_ACTIVATE) ==
           UR_MODERN_SESSION_APPLIED);
    assert((machine == std::vector<std::uint8_t>{1, 2, 3}));
    assert(paused == 1);

    // Cancel resumes after a paused restart.
    assert(ur_modern_pause_handle_action(
               session, &menu, UR_MODERN_PAUSE_CANCEL) ==
           UR_MODERN_SESSION_APPLIED);
    assert(paused == 0);

    // Hotkey path reaches the same restart command while running.
    machine = {8};
    assert(ur_modern_pause_handle_action(
               session, &menu, UR_MODERN_PAUSE_RESTART_HOTKEY) ==
           UR_MODERN_SESSION_APPLIED);
    assert((machine == std::vector<std::uint8_t>{1, 2, 3}));

    ur_modern_session_destroy(session);
    return 0;
}
