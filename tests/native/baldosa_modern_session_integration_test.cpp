// Exercise the actual Modern C ABI and Baldosa backend lifecycle seam.
// This uses an acknowledged fake native guest, not a complete-game oracle.
#include "baldosa_modern_session_binding.hpp"

#include <cassert>
#include <cstdint>

using namespace ur::product;

namespace {
struct Guest {
    unsigned players = 0;
    unsigned restarts = 0;
    bool paused = false;
    bool settled = false;
    bool returned = false;
    bool refuse_pause = false;
    bool refuse_resume = false;
    bool refuse_restart = false;
    bool refuse_return = false;
};

bool launch(void* ctx, unsigned players) {
    auto& guest = *static_cast<Guest*>(ctx);
    guest.players = players;
    guest.settled = false;
    return true;
}
bool pause(void* ctx, bool value) {
    auto& guest = *static_cast<Guest*>(ctx);
    if (value ? guest.refuse_pause : guest.refuse_resume) return false;
    guest.paused = value;
    return true;
}
bool restart(void* ctx) {
    auto& guest = *static_cast<Guest*>(ctx);
    if (guest.refuse_restart) return false;
    ++guest.restarts;
    guest.settled = false;
    return true;
}
bool exit_frontend(void* ctx) {
    auto& guest = *static_cast<Guest*>(ctx);
    if (guest.refuse_return) return false;
    // Real host exit includes the complete unpause/ownership transaction.
    guest.paused = false;
    guest.returned = true;
    return true;
}
bool settled(void* ctx) {
    return static_cast<Guest*>(ctx)->settled;
}
} // namespace

int main() {
    assert(!ur_modern_session_create_native(1, nullptr));
    Guest guest;
    BaldosaExecutionBackend backend({
        &guest, &launch, &pause, &restart, &exit_frontend, &settled});
    assert(backend.initialize() == BaldosaBackendStatus::Applied);
    assert(backend.select_players(2) == BaldosaBackendStatus::Applied);
    assert(backend.start_event() == BaldosaBackendStatus::Applied);
    assert(guest.players == 2);
    const auto hooks = baldosa_modern_session_hooks(backend);
    UrModernSession* session = ur_modern_session_create_native(1, &hooks);
    assert(session);
    assert(ur_modern_session_restart_available(session));

    constexpr std::uint32_t present = 0xc0000000u;
    constexpr std::uint32_t p1_start = 1u << 3;
    constexpr std::uint32_t p2_start = p1_start << 12;
    constexpr std::uint32_t p2_a = 1u << (12 + 8);
    const auto held = present | p1_start | p2_start;
    // New event requires physical release on BOTH pads before passing input.
    assert(backend.input().filter(held) == present);
    assert(backend.input().filter(present) == present);
    assert(backend.input().filter(held) == held);

    guest.refuse_pause = true;
    assert(ur_modern_session_handle_key(
        session, UR_MODERN_SESSION_KEY_ESCAPE) ==
        UR_MODERN_SESSION_REJECTED_BY_RUNTIME);
    assert(!ur_modern_session_is_paused(session));
    assert(!guest.paused && backend.phase() == BaldosaBackendPhase::Running);
    assert(backend.input().filter(held) == held);

    guest.refuse_pause = false;
    assert(ur_modern_session_handle_key(
        session, UR_MODERN_SESSION_KEY_ESCAPE) == UR_MODERN_SESSION_APPLIED);
    assert(ur_modern_session_is_paused(session) && guest.paused);
    assert(backend.phase() == BaldosaBackendPhase::Paused);
    assert(backend.input().filter(held | p2_a) == present);
    guest.refuse_resume = true;
    assert(ur_modern_session_handle_key(
        session, UR_MODERN_SESSION_KEY_ACCEPT) ==
        UR_MODERN_SESSION_REJECTED_BY_RUNTIME);
    assert(ur_modern_session_is_paused(session) && guest.paused);
    assert(backend.input().filter(held) == present);
    guest.refuse_resume = false;

    // Restart through the existing Modern key entrypoint preserves host pause.
    guest.refuse_restart = true;
    assert(ur_modern_session_handle_key(
        session, UR_MODERN_SESSION_KEY_RESTART) ==
        UR_MODERN_SESSION_REJECTED_BY_RUNTIME);
    assert(guest.restarts == 0 && guest.paused);
    guest.refuse_restart = false;
    assert(ur_modern_session_handle_key(
        session, UR_MODERN_SESSION_KEY_RESTART) == UR_MODERN_SESSION_APPLIED);
    assert(guest.restarts == 1 && guest.paused);
    assert(backend.phase() == BaldosaBackendPhase::Paused);
    assert(backend.input().filter(held | p2_a) == present);
    assert(ur_modern_session_handle_key(
        session, UR_MODERN_SESSION_KEY_ACCEPT) == UR_MODERN_SESSION_APPLIED);
    assert(!ur_modern_session_is_paused(session) && !guest.paused);
    assert(backend.input().filter(held | p2_a) == present);
    assert(backend.input().filter(present) == present);
    assert(backend.input().filter(present | p2_a) == (present | p2_a));

    // No manufactured completion: only a guest-authoritative result can
    // transition the Baldosa backend to Finished or permit a result Retry.
    assert(backend.finish_from_guest_result() == BaldosaBackendStatus::Rejected);
    assert(backend.phase() == BaldosaBackendPhase::Running);
    guest.settled = true;
    assert(backend.finish_from_guest_result() == BaldosaBackendStatus::Applied);
    assert(ur_modern_session_restart_available(session));
    assert(ur_modern_session_handle_key(
        session, UR_MODERN_SESSION_KEY_RESTART) == UR_MODERN_SESSION_APPLIED);
    assert(backend.phase() == BaldosaBackendPhase::Running);
    assert(guest.restarts == 2 && !guest.settled);

    // Failed frontend exit must retain host ownership and Modern phase.
    assert(ur_modern_session_pause(session) == UR_MODERN_SESSION_APPLIED);
    guest.refuse_return = true;
    assert(ur_modern_session_exit_to_frontend(session) ==
           UR_MODERN_SESSION_REJECTED_BY_RUNTIME);
    assert(ur_modern_session_is_paused(session) && guest.paused);
    assert(backend.phase() == BaldosaBackendPhase::Paused);
    guest.refuse_return = false;
    assert(ur_modern_session_exit_to_frontend(session) ==
           UR_MODERN_SESSION_APPLIED);
    assert(!ur_modern_session_is_paused(session) && !guest.paused);
    assert(backend.phase() == BaldosaBackendPhase::Frontend);
    assert(!ur_modern_session_restart_available(session));
    assert(backend.input().filter(held) == present);

    // Fresh 1P launch reuses the same host APIs, no second storage namespace.
    assert(backend.select_players(1) == BaldosaBackendStatus::Applied);
    assert(backend.start_event() == BaldosaBackendStatus::Applied);
    assert(guest.players == 1);
    assert(ur_modern_session_restart_available(session));
    assert(backend.input().filter(held) == present);
    ur_modern_session_destroy(session);
    return 0;
}
