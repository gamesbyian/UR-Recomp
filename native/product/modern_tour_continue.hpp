#pragma once

#include "quick_practice_route.hpp"
#include "modern_tour_entry_policy.hpp"

#include <cstdint>

namespace ur::product {

enum class ModernTourContinueStage {
    Idle,
    AwaitMain,
    AwaitRider,
    AwaitTour,
    AwaitTrack,
    Ready,
};

constexpr std::uint32_t kModernTourContinueMaxObservations = 3600;

struct ModernTourContinueState {
    ModernTourContinueStage stage = ModernTourContinueStage::Idle;
    ModernTourEntryIntent intent = ModernTourEntryIntent::None;
    std::uint8_t tour_row = 0;
    std::uint8_t tour_option = 0;
    bool restore_continuation_at_track_select = false;
    bool retire_continuation_after_stock_wipe = false;
    bool waiting_for_selection_change = false;
    std::uint8_t selection_before_input = 0;
    std::uint32_t observations_remaining = 0;
};

struct ModernTourContinueObservation {
    std::uint8_t menu_id = 0;
    std::uint8_t selected_option = 0;
    bool in_race = false;
};

struct ModernTourContinueStep {
    ModernTourContinueState state{};
    QuickPracticeMenuInput input = QuickPracticeMenuInput::None;
    bool track_select_ready = false;
    bool timed_out = false;
};

constexpr ModernTourContinueState begin_modern_tour_entry(
    std::uint8_t tour_row,
    ModernTourEntryDecision decision
) noexcept {
    ModernTourContinueState state;
    if (tour_row >= kQuickPracticeTourOptions.size() ||
        !decision.route_stock_frontend ||
        decision.intent == ModernTourEntryIntent::None) {
        return state;
    }
    state.stage = ModernTourContinueStage::AwaitMain;
    state.intent = decision.intent;
    state.tour_row = tour_row;
    state.tour_option = kQuickPracticeTourOptions[tour_row];
    state.restore_continuation_at_track_select =
        decision.restore_continuation_at_track_select;
    state.retire_continuation_after_stock_wipe =
        decision.retire_continuation_after_stock_wipe;
    state.observations_remaining = kModernTourContinueMaxObservations;
    return state;
}

constexpr ModernTourContinueState begin_modern_tour_continue(
    std::uint8_t tour_row
) noexcept {
    return begin_modern_tour_entry(
        tour_row,
        {
            ModernTourEntryIntent::Resume,
            true,
            true,
            false,
        });
}

constexpr ModernTourContinueStep advance_modern_tour_continue(
    ModernTourContinueState state,
    ModernTourContinueObservation observation
) noexcept {
    ModernTourContinueStep out;
    out.state = state;

    if (state.stage == ModernTourContinueStage::Idle) return out;
    if (state.observations_remaining == 0) {
        out.state = {};
        out.timed_out = true;
        return out;
    }
    --out.state.observations_remaining;
    if (observation.in_race) {
        out.state = {};
        return out;
    }

    if (state.waiting_for_selection_change) {
        if (observation.selected_option == state.selection_before_input) {
            return out;
        }
        out.state.waiting_for_selection_change = false;
    }

    const auto emit_selection_input = [&](
        QuickPracticeMenuInput desired
    ) constexpr -> ModernTourContinueStep {
        ModernTourContinueStep step;
        step.state = out.state;
        step.input = desired;
        if (desired != QuickPracticeMenuInput::None &&
            desired != QuickPracticeMenuInput::Accept) {
            step.state.waiting_for_selection_change = true;
            step.state.selection_before_input = observation.selected_option;
        }
        return step;
    };

    switch (out.state.stage) {
    case ModernTourContinueStage::AwaitMain:
        if (observation.menu_id == 0xD7) {
            out.input = QuickPracticeMenuInput::Accept;
            out.state.stage = ModernTourContinueStage::AwaitRider;
        }
        break;
    case ModernTourContinueStage::AwaitRider:
        if (observation.menu_id == 0x3C) {
            out.input = QuickPracticeMenuInput::Accept;
            out.state.stage = ModernTourContinueStage::AwaitTour;
        }
        break;
    case ModernTourContinueStage::AwaitTour:
        if (observation.menu_id == 0x6D) {
            const auto desired = quick_practice_tour_input(
                out.state.tour_option,
                observation.selected_option);
            if (desired == QuickPracticeMenuInput::Accept) {
                out.input = QuickPracticeMenuInput::Accept;
                out.state.stage = ModernTourContinueStage::AwaitTrack;
            } else {
                return emit_selection_input(desired);
            }
        }
        break;
    case ModernTourContinueStage::AwaitTrack:
        if (observation.menu_id == 0xF6) {
            out.state.stage = ModernTourContinueStage::Ready;
            out.track_select_ready = true;
        }
        break;
    case ModernTourContinueStage::Ready:
        out.track_select_ready = observation.menu_id == 0xF6;
        break;
    case ModernTourContinueStage::Idle:
        break;
    }

    return out;
}

}  // namespace ur::product
