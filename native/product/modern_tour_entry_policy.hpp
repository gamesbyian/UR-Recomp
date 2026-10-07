#pragma once

#include "host_product_state.hpp"

#include <cstdint>

namespace ur::product {

enum class ModernTourEntryIntent : std::uint8_t {
    None = 0,
    Resume = 1,
    Restart = 2,
    // Resume, then select the one event the restored row leaves unfinished.
    NextEvent = 3,
};

struct ModernTourEntryContext {
    ExecutionMode mode = ExecutionMode::Authentic;
    bool authoritative_profile = false;
    bool unfinished_tour = false;
    bool continuation_source_matches = false;
    // True only when the saved row has exactly one unqualified event (see
    // next_event_derivation.hpp); ambiguous rows remain a player choice.
    bool next_event_unique = false;
};

struct ModernTourEntryActions {
    bool resume_available = false;
    bool restart_available = false;
    bool restart_requires_confirmation = false;
    bool next_event_available = false;
};

constexpr ModernTourEntryActions modern_tour_entry_actions(
    ModernTourEntryContext context) noexcept {
    if (context.mode != ExecutionMode::Modern ||
        !context.authoritative_profile ||
        !context.unfinished_tour ||
        !context.continuation_source_matches) {
        return {};
    }
    return {true, true, true, context.next_event_unique};
}

struct ModernTourEntryDecision {
    ModernTourEntryIntent intent = ModernTourEntryIntent::None;
    bool route_stock_frontend = false;
    bool restore_continuation_at_track_select = false;
    bool retire_continuation_after_stock_wipe = false;
};

constexpr ModernTourEntryDecision resolve_modern_tour_entry(
    ModernTourEntryContext context,
    ModernTourEntryIntent requested,
    bool restart_confirmed = false) noexcept {
    const auto actions = modern_tour_entry_actions(context);
    switch (requested) {
    case ModernTourEntryIntent::Resume:
        if (!actions.resume_available) return {};
        return {
            ModernTourEntryIntent::Resume,
            true,
            true,
            false,
        };
    case ModernTourEntryIntent::NextEvent:
        // Same restore contract as Resume; only the post-restore selection
        // differs, and it is driven through ordinary stock menu input.
        if (!actions.next_event_available) return {};
        return {
            ModernTourEntryIntent::NextEvent,
            true,
            true,
            false,
        };
    case ModernTourEntryIntent::Restart:
        if (!actions.restart_available || !restart_confirmed) return {};
        return {
            ModernTourEntryIntent::Restart,
            true,
            false,
            true,
        };
    case ModernTourEntryIntent::None:
        return {};
    }
    return {};
}

constexpr bool modern_tour_entry_may_retire_continuation(
    ModernTourEntryDecision decision,
    bool settled_track_select,
    bool stock_qualification_row_empty) noexcept {
    return decision.intent == ModernTourEntryIntent::Restart &&
           decision.route_stock_frontend &&
           !decision.restore_continuation_at_track_select &&
           decision.retire_continuation_after_stock_wipe &&
           settled_track_select &&
           stock_qualification_row_empty;
}

}  // namespace ur::product
