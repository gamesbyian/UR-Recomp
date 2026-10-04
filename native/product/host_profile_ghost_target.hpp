#pragma once

#include "host_profile_state.hpp"

#include <string>

namespace ur::product {

enum class HostProfileGhostTargetUpdateStatus {
    Saved,
    Unchanged,
    RejectedByPolicy,
    ReadOnly,
    SaveFailed,
};

/* Persist one profile-owned ghost preference without touching guest SRAM.
 *
 * The caller supplies the already-resolved profile state and its writable
 * status. autosave_generation, stock SRAM and tour continuation are preserved
 * byte-for-byte; state is replaced only after the candidate saves
 * successfully.
 */
HostProfileGhostTargetUpdateStatus update_host_profile_ghost_target(
    ExecutionMode mode,
    const std::string& path,
    bool writable,
    HostProfileState& state,
    CompletedRunGhostTarget target);

}  // namespace ur::product
