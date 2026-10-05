#pragma once

#include "completed_run_ghost.hpp"
#include "completed_run_ghost_target.hpp"

#include <optional>
#include <string_view>

namespace ur::product {

struct CompletedRunGhostSelection {
    CompletedRunGhostTarget target = CompletedRunGhostTarget::Off;
    std::optional<CompletedRunGhostKind> kind;
    const CompletedRunRecord* record = nullptr;

    bool active() const {
        return kind.has_value() && record != nullptr;
    }
};

/* Stable machine vocabulary for persistence and diagnostics. */
const char* completed_run_ghost_target_name(CompletedRunGhostTarget target);

/* Player-facing label. Keep this separate from the machine token so UI polish
 * cannot silently change persisted profile vocabulary. */
const char* completed_run_ghost_target_label(CompletedRunGhostTarget target);
std::optional<CompletedRunGhostTarget> parse_completed_run_ghost_target(
    std::string_view value);

/* Resolve exactly the requested presentation target.
 *
 * Missing Previous/PB data fails closed. This deliberately does not fall back
 * from PB to Previous (or vice versa), because such a fallback would silently
 * change the user's comparison target.
 */
CompletedRunGhostSelection select_completed_run_ghost_target(
    const CompletedRunGhostState& state,
    CompletedRunGhostTarget target);

}  // namespace ur::product
