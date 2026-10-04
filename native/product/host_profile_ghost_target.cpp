#include "host_profile_ghost_target.hpp"

#include "host_profile_store.hpp"

namespace ur::product {

HostProfileGhostTargetUpdateStatus update_host_profile_ghost_target(
    ExecutionMode mode,
    const std::string& path,
    bool writable,
    HostProfileState& state,
    CompletedRunGhostTarget target) {
    if (!policy_for(mode).host_profiles) {
        return HostProfileGhostTargetUpdateStatus::RejectedByPolicy;
    }
    if (!writable) {
        return HostProfileGhostTargetUpdateStatus::ReadOnly;
    }
    if (state.ghost_target == target) {
        return HostProfileGhostTargetUpdateStatus::Unchanged;
    }

    HostProfileState candidate = state;
    candidate.ghost_target = target;

    if (save_host_profile_state_file(mode, path, candidate) !=
        HostProfileSaveStatus::Saved) {
        return HostProfileGhostTargetUpdateStatus::SaveFailed;
    }

    state = std::move(candidate);
    return HostProfileGhostTargetUpdateStatus::Saved;
}

}  // namespace ur::product
