#include "baldosa_host_lifecycle_pause.hpp"

#include <cassert>
#include <cstring>

using namespace ur::product;

namespace {

int g_setting_reads;
bool g_setting = true;
bool load_setting() {
    ++g_setting_reads;
    return g_setting;
}

BaldosaLifecycleObservation race(long long p1, long long p2) {
    BaldosaLifecycleObservation in;
    in.seat_sources = {{p1, p2}};
    in.pause_surface = true;
    return in;
}

void a_seat_owner_leaving_mid_race_pauses_once() {
    BaldosaHostLifecyclePause lifecycle;
    assert(lifecycle.step(race(7, 8), load_setting) == BaldosaLifecyclePauseReason::None);
    assert(lifecycle.step(race(7, -1), load_setting) ==
           BaldosaLifecyclePauseReason::ControllerDisconnect);
    assert(lifecycle.disconnected_seat() == 1);
    assert(std::strcmp(controller_hotplug_notice_text(lifecycle.hotplug()),
                       "P2 CONTROLLER DISCONNECTED") == 0);
    // Consumed: the next frame (now paused) does not ask again.
    auto paused = race(7, -1);
    paused.already_paused = true;
    assert(lifecycle.step(paused, load_setting) == BaldosaLifecyclePauseReason::None);
    assert(lifecycle.disconnected_seat() == -1);
    // Reconnect while paused turns the notice into RECONNECTED ...
    paused.seat_sources = {{7, 9}};
    assert(lifecycle.step(paused, load_setting) == BaldosaLifecyclePauseReason::None);
    assert(std::strcmp(controller_hotplug_notice_text(lifecycle.hotplug()),
                       "P2 CONTROLLER RECONNECTED") == 0);
    // ... which retires once play resumes.
    assert(lifecycle.step(race(7, 9), load_setting) == BaldosaLifecyclePauseReason::None);
    assert(!controller_hotplug_any_notice(lifecycle.hotplug()));
}

void a_disconnect_outside_a_race_is_never_carried_into_one() {
    BaldosaHostLifecyclePause lifecycle;
    auto menu = race(7, -1);
    menu.pause_surface = false;
    lifecycle.step(menu, load_setting);
    menu.seat_sources = {{-1, -1}};
    assert(lifecycle.step(menu, load_setting) == BaldosaLifecyclePauseReason::None);
    // The race begins later: no stale pause.
    assert(lifecycle.step(race(-1, -1), load_setting) == BaldosaLifecyclePauseReason::None);
}

void a_seat_swap_reports_the_old_owner_leaving() {
    BaldosaHostLifecyclePause lifecycle;
    lifecycle.step(race(7, -1), load_setting);
    // Instance 7 replaced by 11 between two frames (remove + reclaim).
    assert(lifecycle.step(race(11, -1), load_setting) ==
           BaldosaLifecyclePauseReason::ControllerDisconnect);
    assert(lifecycle.disconnected_seat() == 0);
}

void focus_loss_pauses_once_per_loss() {
    g_setting = true;
    g_setting_reads = 0;
    BaldosaHostLifecyclePause lifecycle;
    lifecycle.step(race(7, -1), load_setting);
    auto unfocused = race(7, -1);
    unfocused.focused = false;
    assert(lifecycle.step(unfocused, load_setting) == BaldosaLifecyclePauseReason::FocusLoss);
    assert(g_setting_reads == 1);
    // The player resumes with a pad while another window keeps focus:
    // no re-pause every frame.
    assert(lifecycle.step(unfocused, load_setting) == BaldosaLifecyclePauseReason::None);
    assert(lifecycle.step(unfocused, load_setting) == BaldosaLifecyclePauseReason::None);
    assert(g_setting_reads == 1);
    // Focus returns, then is lost again: one more pause.
    lifecycle.step(race(7, -1), load_setting);
    assert(lifecycle.step(unfocused, load_setting) == BaldosaLifecyclePauseReason::FocusLoss);
}

void focus_setting_off_and_non_race_surfaces_do_not_pause() {
    g_setting = false;
    g_setting_reads = 0;
    BaldosaHostLifecyclePause lifecycle;
    auto unfocused = race(-1, -1);
    unfocused.focused = false;
    assert(lifecycle.step(unfocused, load_setting) == BaldosaLifecyclePauseReason::None);
    assert(g_setting_reads == 1);
    g_setting = true;
    BaldosaHostLifecyclePause menu;
    auto menu_unfocused = unfocused;
    menu_unfocused.pause_surface = false;
    assert(menu.step(menu_unfocused, load_setting) == BaldosaLifecyclePauseReason::None);
    // Already paused: no request and no file read.
    g_setting_reads = 0;
    BaldosaHostLifecyclePause paused;
    auto already = unfocused;
    already.already_paused = true;
    assert(paused.step(already, load_setting) == BaldosaLifecyclePauseReason::None);
    assert(g_setting_reads == 0);
}

void a_scripted_session_does_not_pause_on_focus_loss() {
    g_setting = true;
    g_setting_reads = 0;
    BaldosaHostLifecyclePause lifecycle;
    auto in = race(7, -1);
    in.focus_pause_eligible = false;
    lifecycle.step(in, load_setting);
    in.focused = false;
    assert(lifecycle.step(in, load_setting) == BaldosaLifecyclePauseReason::None);
    assert(g_setting_reads == 0);
    // ...but a seat owner leaving still pauses it.
    in.seat_sources = {{-1, -1}};
    assert(lifecycle.step(in, load_setting) ==
           BaldosaLifecyclePauseReason::ControllerDisconnect);
}

void authentic_never_pauses() {
    g_setting = true;
    g_setting_reads = 0;
    BaldosaHostLifecyclePause lifecycle;
    auto in = race(7, 8);
    in.mode = ExecutionMode::Authentic;
    lifecycle.step(in, load_setting);
    in.seat_sources = {{-1, -1}};
    in.focused = false;
    assert(lifecycle.step(in, load_setting) == BaldosaLifecyclePauseReason::None);
    assert(g_setting_reads == 0);
}

void disconnect_wins_over_simultaneous_focus_loss() {
    g_setting = true;
    BaldosaHostLifecyclePause lifecycle;
    lifecycle.step(race(7, -1), load_setting);
    auto both = race(-1, -1);
    both.focused = false;
    assert(lifecycle.step(both, load_setting) ==
           BaldosaLifecyclePauseReason::ControllerDisconnect);
    assert(std::strcmp(baldosa_lifecycle_pause_reason_name(
        BaldosaLifecyclePauseReason::ControllerDisconnect), "controller_disconnect") == 0);
    assert(std::strcmp(baldosa_lifecycle_pause_reason_name(
        BaldosaLifecyclePauseReason::FocusLoss), "focus_loss") == 0);
}

}  // namespace

int main() {
    a_seat_owner_leaving_mid_race_pauses_once();
    a_disconnect_outside_a_race_is_never_carried_into_one();
    a_seat_swap_reports_the_old_owner_leaving();
    focus_loss_pauses_once_per_loss();
    focus_setting_off_and_non_race_surfaces_do_not_pause();
    a_scripted_session_does_not_pause_on_focus_loss();
    authentic_never_pauses();
    disconnect_wins_over_simultaneous_focus_loss();
    return 0;
}
