#pragma once

#include "host_product_state.hpp"

#include <cstdint>
#include <optional>

namespace ur::product {

// Host-originated controller vibration. The stock title emits no rumble, so
// every pulse is a Modern presentation choice tied to an event the host has
// already observed authoritatively. Pulses never feed back into guest input,
// timing or simulation.
enum class HapticEvent : std::uint8_t {
    // A new authoritative checkpoint split in a supported 1P timed race.
    Checkpoint,
    // The same race reached the stock results surface.
    Finish,
};

struct HapticPulse {
    std::uint16_t low_frequency = 0;
    std::uint16_t high_frequency = 0;
    std::uint32_t duration_ms = 0;

    constexpr bool operator==(const HapticPulse& other) const noexcept {
        return low_frequency == other.low_frequency &&
               high_frequency == other.high_frequency &&
               duration_ms == other.duration_ms;
    }
};

struct HapticContext {
    ExecutionMode mode = ExecutionMode::Authentic;
    // Only the timed one-player race has authoritative split ownership for
    // the P1 seat; 2P/VS, Practice and replays stay silent.
    bool one_player_timed_race = false;
    // A physical controller occupies the P1 framework seat.
    bool p1_controller_seated = false;
    bool paused = false;
};

inline constexpr HapticPulse kCheckpointPulse{0x3000, 0x5000, 60};
inline constexpr HapticPulse kFinishPulse{0x8000, 0x6000, 220};

constexpr std::optional<HapticPulse> haptic_pulse_for(
    const HostSettings& settings,
    HapticContext context,
    HapticEvent event) noexcept {
    if (!policy_for(context.mode).host_settings ||
        !settings.vibration_enabled ||
        !context.one_player_timed_race ||
        !context.p1_controller_seated ||
        context.paused) {
        return std::nullopt;
    }
    switch (event) {
    case HapticEvent::Checkpoint:
        return kCheckpointPulse;
    case HapticEvent::Finish:
        return kFinishPulse;
    }
    return std::nullopt;
}

}  // namespace ur::product
