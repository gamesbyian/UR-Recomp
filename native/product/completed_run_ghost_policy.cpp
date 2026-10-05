#include "completed_run_ghost_policy.hpp"

namespace ur::product {

const char* completed_run_ghost_target_name(CompletedRunGhostTarget target) {
    switch (target) {
    case CompletedRunGhostTarget::Off:
        return "off";
    case CompletedRunGhostTarget::Previous:
        return "previous";
    case CompletedRunGhostTarget::PersonalBest:
        return "personal-best";
    }
    return "off";
}

const char* completed_run_ghost_target_label(CompletedRunGhostTarget target) {
    switch (target) {
    case CompletedRunGhostTarget::Off:
        return "OFF";
    case CompletedRunGhostTarget::Previous:
        return "PREVIOUS";
    case CompletedRunGhostTarget::PersonalBest:
        return "PERSONAL BEST";
    }
    return "OFF";
}

std::optional<CompletedRunGhostTarget> parse_completed_run_ghost_target(
    std::string_view value) {
    if (value == "off") return CompletedRunGhostTarget::Off;
    if (value == "previous") return CompletedRunGhostTarget::Previous;
    if (value == "personal-best") {
        return CompletedRunGhostTarget::PersonalBest;
    }
    return std::nullopt;
}

CompletedRunGhostSelection select_completed_run_ghost_target(
    const CompletedRunGhostState& state,
    CompletedRunGhostTarget target) {
    CompletedRunGhostSelection out;
    out.target = target;

    switch (target) {
    case CompletedRunGhostTarget::Off:
        return out;
    case CompletedRunGhostTarget::Previous:
        out.kind = CompletedRunGhostKind::Previous;
        break;
    case CompletedRunGhostTarget::PersonalBest:
        out.kind = CompletedRunGhostKind::PersonalBest;
        break;
    }

    out.record = state.record(*out.kind);
    if (!out.record) out.kind.reset();
    return out;
}

}  // namespace ur::product
