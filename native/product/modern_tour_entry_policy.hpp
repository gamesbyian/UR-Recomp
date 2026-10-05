#pragma once

#include "host_product_state.hpp"

#include <cstdint>

namespace ur::product {

enum class ModernTourEntryIntent : std::uint8_t {
    None = 0,
    Resume = 1,
    Restart = 2,
};

struct ModernTourEntryContext {
    ExecutionMode mode = ExecutionMode::Authentic;
    bool authoritative_profile = false;
    bool unfinished_tour = false;
    bool continuation_source_matches = false;
};

struct ModernTourEntryActions {
    bool resume_available = false;
    bool restart_available = false;
    bool restart_requires_confirmation = false;
};

constexpr ModernTourEntryActions modern_tour_entry_actions(
    ModernTourEntryContext context) noexcept {
    if (context.mode != ExecutionMode::Modern ||
        !context.authoritative_profile ||
        !context.unfinished_tour ||
        !context.continuation_source_matches) {
        return {};
    }
    return {true, true, true};
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

}  // namespace ur::product
