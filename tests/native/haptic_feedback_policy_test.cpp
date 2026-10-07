#include "haptic_feedback_policy.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    HostSettings settings;
    assert(settings.vibration_enabled);  // existing persisted default

    const HapticContext live{ExecutionMode::Modern, true, true, false};
    assert(haptic_pulse_for(settings, live, HapticEvent::Checkpoint) ==
           kCheckpointPulse);
    assert(haptic_pulse_for(settings, live, HapticEvent::Finish) ==
           kFinishPulse);
    // The finish is the stronger, longer pulse.
    assert(kFinishPulse.duration_ms > kCheckpointPulse.duration_ms);
    assert(kFinishPulse.low_frequency > kCheckpointPulse.low_frequency);

    // The player's setting turns every pulse off.
    HostSettings off = settings;
    off.vibration_enabled = false;
    assert(!haptic_pulse_for(off, live, HapticEvent::Checkpoint));
    assert(!haptic_pulse_for(off, live, HapticEvent::Finish));

    // Authentic never vibrates, whatever the stored setting says.
    HapticContext authentic = live;
    authentic.mode = ExecutionMode::Authentic;
    assert(!haptic_pulse_for(settings, authentic, HapticEvent::Finish));

    // No split ownership (2P/VS, Practice, replay), no controller, or paused.
    HapticContext unsupported = live;
    unsupported.one_player_timed_race = false;
    assert(!haptic_pulse_for(settings, unsupported, HapticEvent::Checkpoint));
    HapticContext keyboard = live;
    keyboard.p1_controller_seated = false;
    assert(!haptic_pulse_for(settings, keyboard, HapticEvent::Finish));
    HapticContext paused = live;
    paused.paused = true;
    assert(!haptic_pulse_for(settings, paused, HapticEvent::Checkpoint));

    return 0;
}
