#pragma once

#include <cstdint>

namespace ur::product {

enum class CompletedRunGhostTarget : std::uint8_t {
    Off,
    Previous,
    PersonalBest,
};

struct CompletedRunGhostTargetAvailability {
    bool previous = false;
    bool personal_best = false;
};

struct CompletedRunGhostTargetResolution {
    CompletedRunGhostTarget requested = CompletedRunGhostTarget::Off;
    CompletedRunGhostTarget effective = CompletedRunGhostTarget::Off;
    bool requested_available = true;

    constexpr bool enabled() const noexcept {
        return effective != CompletedRunGhostTarget::Off;
    }
};

constexpr bool completed_run_ghost_target_available(
    CompletedRunGhostTarget target,
    CompletedRunGhostTargetAvailability availability) noexcept {
    switch (target) {
    case CompletedRunGhostTarget::Off:
        return true;
    case CompletedRunGhostTarget::Previous:
        return availability.previous;
    case CompletedRunGhostTarget::PersonalBest:
        return availability.personal_best;
    }
    return false;
}

/*
 * Preserve the profile's requested preference even when the current
 * course/session has no compatible artifact. An unavailable requested target
 * becomes effectively Off for this binding only. Do not silently substitute
 * Previous for Personal Best (or vice versa), and do not rewrite persistence
 * merely because one course has no history.
 */
constexpr CompletedRunGhostTargetResolution resolve_completed_run_ghost_target(
    CompletedRunGhostTarget requested,
    CompletedRunGhostTargetAvailability availability) noexcept {
    const bool available =
        completed_run_ghost_target_available(requested, availability);
    return {
        requested,
        available ? requested : CompletedRunGhostTarget::Off,
        available,
    };
}

}  // namespace ur::product
