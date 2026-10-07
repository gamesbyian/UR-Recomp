#include "completed_run_ghost_target.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    CompletedRunGhostTargetAvailability none{};

    const auto off = resolve_completed_run_ghost_target(
        CompletedRunGhostTarget::Off, none);
    assert(off.requested == CompletedRunGhostTarget::Off);
    assert(off.effective == CompletedRunGhostTarget::Off);
    assert(off.requested_available);
    assert(!off.enabled());

    const auto previous_missing = resolve_completed_run_ghost_target(
        CompletedRunGhostTarget::Previous, none);
    assert(previous_missing.requested == CompletedRunGhostTarget::Previous);
    assert(previous_missing.effective == CompletedRunGhostTarget::Off);
    assert(!previous_missing.requested_available);
    assert(!previous_missing.enabled());

    const auto pb_missing = resolve_completed_run_ghost_target(
        CompletedRunGhostTarget::PersonalBest, {true, false});
    assert(pb_missing.requested == CompletedRunGhostTarget::PersonalBest);
    assert(pb_missing.effective == CompletedRunGhostTarget::Off);
    assert(!pb_missing.requested_available);
    assert(!pb_missing.enabled());

    const auto previous = resolve_completed_run_ghost_target(
        CompletedRunGhostTarget::Previous, {true, true});
    assert(previous.requested == CompletedRunGhostTarget::Previous);
    assert(previous.effective == CompletedRunGhostTarget::Previous);
    assert(previous.requested_available);
    assert(previous.enabled());

    const auto pb = resolve_completed_run_ghost_target(
        CompletedRunGhostTarget::PersonalBest, {false, true});
    assert(pb.requested == CompletedRunGhostTarget::PersonalBest);
    assert(pb.effective == CompletedRunGhostTarget::PersonalBest);
    assert(pb.requested_available);
    assert(pb.enabled());

    // Availability is target-specific: never substitute one target for another.
    const auto no_pb_fallback = resolve_completed_run_ghost_target(
        CompletedRunGhostTarget::PersonalBest, {true, false});
    assert(no_pb_fallback.effective == CompletedRunGhostTarget::Off);

    const auto no_previous_fallback = resolve_completed_run_ghost_target(
        CompletedRunGhostTarget::Previous, {false, true});
    assert(no_previous_fallback.effective == CompletedRunGhostTarget::Off);

    const auto invalid = static_cast<CompletedRunGhostTarget>(255);
    assert(!completed_run_ghost_target_available(invalid, {true, true}));
    const auto invalid_resolution =
        resolve_completed_run_ghost_target(invalid, {true, true});
    assert(invalid_resolution.effective == CompletedRunGhostTarget::Off);
    assert(!invalid_resolution.requested_available);

    return 0;
}
