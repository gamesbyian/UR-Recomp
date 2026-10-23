#pragma once

#include "controller_hotplug_policy.hpp"
#include "focus_pause_policy.hpp"
#include "host_product_state.hpp"

#include <array>
#include <cstdint>

namespace ur::product {

// Host lifecycle pauses for the integrated Baldosa product: losing window
// focus, or the controller occupying a seat going away, during a live
// Modern race. Reuses the legacy host's two policies unchanged
// (controller_hotplug_policy.hpp, focus_pause_policy.hpp); this only turns
// per-frame observations into at most one pause request.
//
// Focus loss is edge-triggered: one pause per loss of focus. Pads are
// ignored while the window is unfocused (#2334), but test runs may opt back
// in to background pad input; a level-triggered pause would then make
// resuming with a pad impossible while another window has focus.
// A disconnect latches once and is consumed at the next completed frame,
// pausing only on a live race surface (never carried into a later race).
// Authentic execution never pauses. No SDL types, no guest access.

enum class BaldosaLifecyclePauseReason : std::uint8_t {
    None = 0,
    FocusLoss,
    ControllerDisconnect,
};

struct BaldosaLifecycleObservation {
    // SDL instance occupying each framework seat, or -1.
    std::array<long long, kControllerSeatCount> seat_sources{{-1, -1}};
    bool focused = true;
    ExecutionMode mode = ExecutionMode::Modern;
    // A live race with a Modern session that can pause.
    bool pause_surface = false;
    bool already_paused = false;
    // False for a scripted (automated) session: there is no player to
    // resume a focus pause, and parallel automated windows steal focus
    // from each other. Disconnects still pause; a pad is a human signal.
    bool focus_pause_eligible = true;
};

class BaldosaHostLifecyclePause {
public:
    // `load_focus_setting` returns HostSettings::pause_on_focus_loss. It is
    // read only on a focus-loss edge that could pause, so a change made in
    // another process is honoured without reading the file every frame.
    template <class LoadFocusSetting>
    BaldosaLifecyclePauseReason step(const BaldosaLifecycleObservation& in,
                                     LoadFocusSetting&& load_focus_setting) {
        disconnected_seat_ = -1;
        for (std::size_t seat = 0; seat < kControllerSeatCount; ++seat) {
            const long long now = in.seat_sources[seat] < 0 ? -1 : in.seat_sources[seat];
            const long long before = seats_[seat];
            if (now == before) continue;
            if (before >= 0) {
                const bool was_pending = hotplug_.disconnect_pause_pending;
                hotplug_ = controller_hotplug_observe(
                    hotplug_, static_cast<int>(seat),
                    static_cast<std::uint64_t>(before), false);
                if (!was_pending && hotplug_.disconnect_pause_pending)
                    disconnected_seat_ = static_cast<int>(seat);
            }
            if (now >= 0) {
                hotplug_ = controller_hotplug_observe(
                    hotplug_, static_cast<int>(seat),
                    static_cast<std::uint64_t>(now), true);
            }
            seats_[seat] = now;
        }

        const auto disconnect = controller_hotplug_take_pause(
            hotplug_, in.mode, in.pause_surface, in.already_paused);
        hotplug_ = disconnect.state;

        const bool focus_lost = focused_ && !in.focused;
        focused_ = in.focused;
        bool focus_pause = false;
        if (focus_lost && in.focus_pause_eligible && in.pause_surface &&
            !in.already_paused && policy_for(in.mode).host_settings) {
            HostSettings settings;
            settings.pause_on_focus_loss = load_focus_setting();
            focus_pause = should_pause_on_focus_loss(
                in.mode, settings, false, in.already_paused);
        }

        BaldosaLifecyclePauseReason reason = BaldosaLifecyclePauseReason::None;
        if (disconnect.pause) {
            reason = BaldosaLifecyclePauseReason::ControllerDisconnect;
        } else if (focus_pause) {
            reason = BaldosaLifecyclePauseReason::FocusLoss;
        } else if (!in.already_paused) {
            // Notices explain a pause; they retire once play resumes.
            hotplug_ = controller_hotplug_clear_notices(hotplug_);
        }
        return reason;
    }

    // The seat whose owner left on the last step(), or -1.
    int disconnected_seat() const noexcept { return disconnected_seat_; }
    const ControllerHotplugState& hotplug() const noexcept { return hotplug_; }

private:
    std::array<long long, kControllerSeatCount> seats_{{-1, -1}};
    bool focused_ = true;
    int disconnected_seat_ = -1;
    ControllerHotplugState hotplug_{};
};

constexpr const char* baldosa_lifecycle_pause_reason_name(
    BaldosaLifecyclePauseReason reason) noexcept {
    switch (reason) {
    case BaldosaLifecyclePauseReason::FocusLoss: return "focus_loss";
    case BaldosaLifecyclePauseReason::ControllerDisconnect: return "controller_disconnect";
    case BaldosaLifecyclePauseReason::None: break;
    }
    return "none";
}

}  // namespace ur::product
