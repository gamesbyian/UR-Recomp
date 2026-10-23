#include "baldosa_host_lifecycle_pause.hpp"
#include <cassert>
#include <cstring>
#include <cstdio>

using namespace ur::product;

BaldosaLifecycleObservation observation(long long p1, long long p2,
                                        bool paused = false) {
    BaldosaLifecycleObservation in;
    in.seat_sources = {{p1, p2}};
    in.pause_surface = true;
    in.already_paused = paused;
    return in;
}

int main() {
    BaldosaHostLifecyclePause lifecycle;
    auto setting = [] { return true; };
    assert(lifecycle.step(observation(101, 202), setting) ==
           BaldosaLifecyclePauseReason::None);
    assert(lifecycle.disconnected_seats_mask() == 0);
    assert(lifecycle.step(observation(-1, -1), setting) ==
           BaldosaLifecyclePauseReason::ControllerDisconnect);
    assert(lifecycle.disconnected_seats_mask() == 0x3);
    assert(lifecycle.disconnected_seat() == 0);
    assert(std::strcmp(controller_hotplug_notice_text(lifecycle.hotplug()),
                       "P1 CONTROLLER DISCONNECTED") == 0);
    assert(lifecycle.step(observation(-1, -1, true), setting) ==
           BaldosaLifecyclePauseReason::None);
    assert(lifecycle.disconnected_seats_mask() == 0);
    assert(lifecycle.disconnected_seat() == -1);

    // Both replacements can arrive in the same frame. They still count as
    // two departures but trigger just one pause, never a stale second pause.
    BaldosaHostLifecyclePause replaced;
    replaced.step(observation(101, 202), setting);
    assert(replaced.step(observation(303, 404), setting) ==
           BaldosaLifecyclePauseReason::ControllerDisconnect);
    assert(replaced.disconnected_seats_mask() == 0x3);
    assert(replaced.step(observation(303, 404, true), setting) ==
           BaldosaLifecyclePauseReason::None);
    assert(replaced.disconnected_seats_mask() == 0);

    // No guest/Authentic pause is authorized, but source-loss evidence
    // still describes the actual two-seat transition.
    BaldosaHostLifecyclePause authentic;
    auto a = observation(101, 202);
    a.mode = ExecutionMode::Authentic;
    authentic.step(a, setting);
    a.seat_sources = {{-1, -1}};
    assert(authentic.step(a, setting) == BaldosaLifecyclePauseReason::None);
    assert(authentic.disconnected_seats_mask() == 0x3);
    std::puts("PASS: dual-disconnect source mask and single-pause semantics");
}
