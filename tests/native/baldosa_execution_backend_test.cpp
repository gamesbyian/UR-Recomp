// Standalone, dependency-free product authority regression.
// Build as C++17 with -Wall -Wextra -Werror -pedantic and native/product include.
#include "baldosa_execution_backend.hpp"

#include <cassert>
#include <cstdint>

namespace {
using namespace ur::product;
constexpr std::uint32_t present = 0xc0000000u;
constexpr std::uint32_t p1_start = 1u << 3;
constexpr std::uint32_t p1_a = 1u << 8;
constexpr std::uint32_t p2_start = p1_start << 12;
constexpr std::uint32_t p2_a = p1_a << 12;
struct Host {
    bool launched = false;
    bool paused = false;
    bool returned = false;
    unsigned players = 0;
    int restarts = 0;
    bool fail = false;
};
bool launch(void* ctx, unsigned count) {
    auto& h = *static_cast<Host*>(ctx);
    if (h.fail) return false;
    h.launched = true;
    h.players = count;
    return true;
}
bool pause(void* ctx, bool state) {
    auto& h = *static_cast<Host*>(ctx);
    if (h.fail) return false;
    h.paused = state;
    return true;
}
bool restart(void* ctx) {
    auto& h = *static_cast<Host*>(ctx);
    if (h.fail) return false;
    ++h.restarts;
    return true;
}
bool exit_frontend(void* ctx) {
    auto& h = *static_cast<Host*>(ctx);
    if (h.fail) return false;
    h.returned = true;
    return true;
}
} // namespace

int main() {
    using namespace ur::product;
    // A missing host hook may not be treated as a successful pause or launch.
    BaldosaExecutionBackend absent;
    assert(absent.initialize() == BaldosaBackendStatus::Applied);
    assert(absent.select_players(3) == BaldosaBackendStatus::Rejected);
    assert(absent.select_players(2) == BaldosaBackendStatus::Applied);
    assert(absent.start_event() == BaldosaBackendStatus::MissingHook);
    assert(absent.phase() == BaldosaBackendPhase::Ready);

    Host h;
    BaldosaBackendHooks hooks{&h, launch, pause, restart, exit_frontend};
    BaldosaExecutionBackend backend(hooks);
    assert(backend.initialize() == BaldosaBackendStatus::Applied);
    assert(backend.select_players(2) == BaldosaBackendStatus::Applied);
    assert(backend.start_event() == BaldosaBackendStatus::Applied);
    assert(h.launched && h.players == 2);
    // Input comes from the mapped host word. Presence bits survive every state.
    const auto held = present | p1_start | p1_a | p2_start | p2_a;
    auto& inputs = backend.input();
    // A new event's initial sample must first see release: no held Start leak.
    assert(inputs.filter(held) == present);
    assert(inputs.filter(present) == present);
    assert(inputs.filter(held) == held);
    assert(backend.pause() == BaldosaBackendStatus::Applied);
    assert(h.paused && inputs.host_owns_input());
    assert(inputs.filter(held) == present);
    backend.observe_guest_frame();
    assert(backend.observed_guest_frames() == 0);
    assert(backend.resume() == BaldosaBackendStatus::Applied);
    assert(!h.paused && !inputs.host_owns_input());
    // Held buttons on both seats cannot become first resumed-frame actions.
    assert(inputs.filter(held) == present);
    assert(inputs.filter(present | p2_a) == present); // P1 released, P2 still held
    assert(inputs.filter(present) == present);        // both now released
    assert(inputs.filter(present | p1_a) == (present | p1_a));
    assert(inputs.filter(present | p2_start) == (present | p2_start));
    backend.observe_guest_frame();
    assert(backend.observed_guest_frames() == 1);

    // Rejected runtime actions must preserve phase, input owner and data.
    h.fail = true;
    assert(backend.pause() == BaldosaBackendStatus::Rejected);
    assert(backend.phase() == BaldosaBackendPhase::Running);
    assert(!inputs.host_owns_input());
    assert(backend.restart() == BaldosaBackendStatus::Rejected);
    assert(backend.observed_guest_frames() == 1);
    h.fail = false;
    assert(backend.restart() == BaldosaBackendStatus::Applied);
    assert(h.restarts == 1 && backend.observed_guest_frames() == 0);
    assert(inputs.filter(present | p1_start) == present);
    assert(inputs.filter(present) == present);
    assert(inputs.filter(present | p1_start) == (present | p1_start));

    assert(backend.finish_from_guest_result() == BaldosaBackendStatus::Applied);
    assert(backend.exit_to_frontend() == BaldosaBackendStatus::Applied);
    assert(h.returned && backend.phase() == BaldosaBackendPhase::Frontend);
    assert(inputs.filter(held) == present);
    assert(backend.select_players(1) == BaldosaBackendStatus::Applied);
    assert(backend.start_event() == BaldosaBackendStatus::Applied);
    assert(h.players == 1);
    assert(inputs.filter(held) == present);

    // The filter must neither invent buttons nor strip port-presence bits.
    BaldosaGuestInputAuthority authority;
    assert(authority.filter(present) == present);
    authority.host_focus(true);
    assert(authority.filter(0xff000000u | p1_a | p2_a) == 0xff000000u);
    authority.host_focus(false);
    assert(authority.filter(present | p1_a | p2_a) == present);
    assert(authority.filter(present) == present);
    assert(authority.filter(present | p1_a | p2_a) == (present | p1_a | p2_a));
    return 0;
}
