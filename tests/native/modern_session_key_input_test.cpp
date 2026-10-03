#include "modern_session_c_api.h"

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
        1,
        64,
        &save_snapshot,
        &load_snapshot,
        &set_paused,
        &is_paused,
        nullptr,
        nullptr,
        nullptr);
    assert(session);

    // Restart is unavailable until the active-race anchor exists.
    assert(ur_modern_session_handle_key(
               session, UR_MODERN_SESSION_KEY_RESTART) ==
           UR_MODERN_SESSION_REJECTED_BY_RUNTIME);

    // Escape opens the host-owned pause gate, Enter resumes it.
    assert(ur_modern_session_handle_key(
               session, UR_MODERN_SESSION_KEY_ESCAPE) ==
           UR_MODERN_SESSION_APPLIED);
    assert(paused == 1);
    assert(ur_modern_session_is_paused(session));

    assert(ur_modern_session_handle_key(
               session, UR_MODERN_SESSION_KEY_ACCEPT) ==
           UR_MODERN_SESSION_APPLIED);
    assert(paused == 0);

    // Enter while running is an explicit no-op.
    assert(ur_modern_session_handle_key(
               session, UR_MODERN_SESSION_KEY_ACCEPT) ==
           UR_MODERN_SESSION_NO_OP);

    // A supported race arms Restart.
    ur_modern_session_observe_race_active(session, 1);
    assert(ur_modern_session_restart_available(session));

    machine = {9, 9};
    assert(ur_modern_session_handle_key(
               session, UR_MODERN_SESSION_KEY_RESTART) ==
           UR_MODERN_SESSION_APPLIED);
    assert((machine == std::vector<std::uint8_t>{1, 2, 3}));
    assert(paused == 0);

    // Restart while paused keeps the host pause gate paused.
    assert(ur_modern_session_handle_key(
               session, UR_MODERN_SESSION_KEY_ESCAPE) ==
           UR_MODERN_SESSION_APPLIED);
    assert(paused == 1);
    machine = {7};
    assert(ur_modern_session_handle_key(
               session, UR_MODERN_SESSION_KEY_RESTART) ==
           UR_MODERN_SESSION_APPLIED);
    assert((machine == std::vector<std::uint8_t>{1, 2, 3}));
    assert(paused == 1);

    // Escape resumes from pause.
    assert(ur_modern_session_handle_key(
               session, UR_MODERN_SESSION_KEY_ESCAPE) ==
           UR_MODERN_SESSION_APPLIED);
    assert(paused == 0);

    ur_modern_session_destroy(session);

    // Authentic mode remains inert.
    UrModernSession* authentic = ur_modern_session_create(
        0,
        64,
        &save_snapshot,
        &load_snapshot,
        &set_paused,
        &is_paused,
        nullptr,
        nullptr,
        nullptr);
    assert(authentic);
    assert(ur_modern_session_handle_key(
               authentic, UR_MODERN_SESSION_KEY_ESCAPE) ==
           UR_MODERN_SESSION_REJECTED_BY_POLICY);
    assert(ur_modern_session_handle_key(
               authentic, UR_MODERN_SESSION_KEY_RESTART) ==
           UR_MODERN_SESSION_REJECTED_BY_RUNTIME);
    ur_modern_session_destroy(authentic);

    return 0;
}
