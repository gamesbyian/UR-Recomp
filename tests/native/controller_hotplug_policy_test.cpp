#include "controller_hotplug_policy.hpp"

#include <cassert>
#include <cstring>

using namespace ur::product;

namespace {

bool same_text(const char* lhs, const char* rhs) {
    if (!lhs || !rhs) return lhs == rhs;
    return std::strcmp(lhs, rhs) == 0;
}

void connect_and_disconnect_latches_one_pause() {
    ControllerHotplugState state;
    state = controller_hotplug_observe(state, 0, 41u, true);
    assert(state.seats[0].connected);
    assert(state.seats[0].source_id == 41u);
    assert(!state.disconnect_pause_pending);
    assert(!controller_hotplug_any_notice(state));

    state = controller_hotplug_observe(state, 0, 41u, false);
    assert(!state.seats[0].connected);
    assert(state.disconnect_pause_pending);
    assert(same_text(
        controller_hotplug_notice_text(state), "P1 CONTROLLER DISCONNECTED"));

    auto decision = controller_hotplug_take_pause(
        state, ExecutionMode::Modern, true, false);
    assert(decision.pause);
    assert(!decision.state.disconnect_pause_pending);

    // The latch is consumed exactly once.
    decision = controller_hotplug_take_pause(
        decision.state, ExecutionMode::Modern, true, false);
    assert(!decision.pause);
}

void pause_is_gated_by_mode_surface_and_existing_pause() {
    ControllerHotplugState state;
    state = controller_hotplug_observe(state, 1, 7u, true);
    state = controller_hotplug_observe(state, 1, 7u, false);
    assert(state.disconnect_pause_pending);

    auto authentic = controller_hotplug_take_pause(
        state, ExecutionMode::Authentic, true, false);
    assert(!authentic.pause);
    assert(!authentic.state.disconnect_pause_pending);

    auto off_surface = controller_hotplug_take_pause(
        state, ExecutionMode::Modern, false, false);
    assert(!off_surface.pause);
    // A disconnect on a menu does not leave a stale pause armed for the race.
    assert(!off_surface.state.disconnect_pause_pending);

    auto already = controller_hotplug_take_pause(
        state, ExecutionMode::Modern, true, true);
    assert(!already.pause);
}

void stale_or_unknown_removals_are_ignored() {
    ControllerHotplugState state;
    // Removal before any connect.
    state = controller_hotplug_observe(state, 0, 9u, false);
    assert(!state.disconnect_pause_pending);
    assert(!controller_hotplug_any_notice(state));

    // Removal of a different source than the seat owner.
    state = controller_hotplug_observe(state, 0, 9u, true);
    state = controller_hotplug_observe(state, 0, 10u, false);
    assert(state.seats[0].connected);
    assert(!state.disconnect_pause_pending);

    // Seats outside the framework's two are ignored entirely.
    const auto before = state;
    state = controller_hotplug_observe(state, -1, 9u, false);
    state = controller_hotplug_observe(state, 2, 9u, true);
    assert(state.seats[0].connected == before.seats[0].connected);
    assert(!state.seats[1].connected);
    assert(!state.disconnect_pause_pending);
}

void reconnect_updates_notice_without_inventing_assignment() {
    ControllerHotplugState state;
    state = controller_hotplug_observe(state, 0, 3u, true);
    state = controller_hotplug_observe(state, 0, 3u, false);
    // Reconnect may arrive with a new framework instance id; the framework,
    // not this model, chose the seat.
    state = controller_hotplug_observe(state, 0, 5u, true);
    assert(state.seats[0].connected);
    assert(state.seats[0].source_id == 5u);
    assert(same_text(
        controller_hotplug_notice_text(state), "P1 CONTROLLER RECONNECTED"));

    state = controller_hotplug_clear_notices(state);
    assert(!controller_hotplug_any_notice(state));
    assert(controller_hotplug_notice_text(state) == nullptr);
    // A fresh connect without a prior disconnect raises no notice.
    state = controller_hotplug_observe(state, 1, 8u, true);
    assert(!controller_hotplug_any_notice(state));
}

void disconnected_seat_outranks_reconnected_seat() {
    ControllerHotplugState state;
    state = controller_hotplug_observe(state, 0, 1u, true);
    state = controller_hotplug_observe(state, 1, 2u, true);
    state = controller_hotplug_observe(state, 0, 1u, false);
    state = controller_hotplug_observe(state, 0, 11u, true);
    state = controller_hotplug_observe(state, 1, 2u, false);
    assert(same_text(
        controller_hotplug_notice_text(state), "P2 CONTROLLER DISCONNECTED"));
}

}  // namespace

int main() {
    connect_and_disconnect_latches_one_pause();
    pause_is_gated_by_mode_surface_and_existing_pause();
    stale_or_unknown_removals_are_ignored();
    reconnect_updates_notice_without_inventing_assignment();
    disconnected_seat_outranks_reconnected_seat();
    return 0;
}
