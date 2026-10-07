#include "modern_pause_input.h"

#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace {
std::vector<std::uint8_t> machine;
int paused = 0;
unsigned exit_calls = 0;
bool exit_result = true;

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
bool exit_to_frontend() { ++exit_calls; return exit_result; }

void move_to(UrModernSession* session, UrModernPauseMenu* menu, UrModernPauseItem target) {
    for (int i = 0; i < 8; ++i) {
        if (ur_modern_pause_menu_selected(
                menu, ur_modern_session_restart_available(session)) == target) return;
        assert(ur_modern_pause_handle_action(session, menu, UR_MODERN_PAUSE_NEXT) ==
               UR_MODERN_SESSION_APPLIED);
    }
    assert(false);
}
}  // namespace

int main() {
    machine = {1, 2, 3};
    UrModernSession* session = ur_modern_session_create(
        1, 64, &save_snapshot, &load_snapshot,
        &set_paused, &is_paused, nullptr, nullptr, &exit_to_frontend);
    assert(session);

    UrModernPauseMenu menu{};
    ur_modern_pause_menu_reset(&menu);
    assert(ur_modern_pause_handle_action(session, &menu, UR_MODERN_PAUSE_NEXT) ==
           UR_MODERN_SESSION_NO_OP);
    assert(ur_modern_pause_handle_action(session, &menu, UR_MODERN_PAUSE_TOGGLE) ==
           UR_MODERN_SESSION_APPLIED);
    assert(paused == 1);

    for (const auto host_only : {
             UR_MODERN_PAUSE_OPTIONS,
             UR_MODERN_PAUSE_CONTROLS,
             UR_MODERN_PAUSE_RUN_DATA,
             UR_MODERN_PAUSE_RECORDS,
         }) {
        move_to(session, &menu, host_only);
        assert(ur_modern_pause_handle_action(session, &menu, UR_MODERN_PAUSE_ACTIVATE) ==
               UR_MODERN_SESSION_NO_OP);
        assert(paused == 1);
    }

    move_to(session, &menu, UR_MODERN_PAUSE_EXIT_FRONTEND);
    exit_result = false;
    assert(ur_modern_pause_handle_action(session, &menu, UR_MODERN_PAUSE_ACTIVATE) ==
           UR_MODERN_SESSION_REJECTED_BY_RUNTIME);
    assert(paused == 1);
    assert(exit_calls == 1);

    exit_result = true;
    assert(ur_modern_pause_handle_action(session, &menu, UR_MODERN_PAUSE_ACTIVATE) ==
           UR_MODERN_SESSION_APPLIED);
    assert(paused == 0);
    assert(exit_calls == 2);

    assert(ur_modern_pause_handle_action(session, &menu, UR_MODERN_PAUSE_TOGGLE) ==
           UR_MODERN_SESSION_APPLIED);
    move_to(session, &menu, UR_MODERN_PAUSE_QUIT);
    assert(ur_modern_pause_handle_action(session, &menu, UR_MODERN_PAUSE_ACTIVATE) ==
           UR_MODERN_SESSION_NO_OP);
    assert(paused == 1);
    assert(ur_modern_pause_handle_action(session, &menu, UR_MODERN_PAUSE_CANCEL) ==
           UR_MODERN_SESSION_APPLIED);
    assert(paused == 0);

    ur_modern_session_observe_race_active(session, 1);
    assert(ur_modern_session_restart_available(session));
    machine = {9};
    assert(ur_modern_pause_handle_action(session, &menu, UR_MODERN_PAUSE_RESTART_HOTKEY) ==
           UR_MODERN_SESSION_APPLIED);
    assert((machine == std::vector<std::uint8_t>{1, 2, 3}));

    ur_modern_session_destroy(session);
    return 0;
}
