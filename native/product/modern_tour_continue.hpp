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
    // Next Event only: after the Resume restore has settled at TRACK_SELECT,
    // keep input ownership and drive the stock cursor to the derived slot.
    SelectNextEvent,
    AwaitNextEventNowPlaying,
    AwaitNextEventRace,
};

constexpr std::uint32_t kModernTourContinueMaxObservations = 3600;
// Each routed menu press is held for two frames. After the stock cursor has
// moved, wait long enough for that press to be released before the next
// directional edge so consecutive presses can never merge into one hold.
constexpr std::uint8_t kModernTourNextEventReleaseObservations = 4;

struct ModernTourContinueState {
    ModernTourContinueStage stage = ModernTourContinueStage::Idle;
    ModernTourEntryIntent intent = ModernTourEntryIntent::None;
    std::uint8_t tour_row = 0;
    std::uint8_t tour_option = 0;
    bool restore_continuation_at_track_select = false;
    bool retire_continuation_after_stock_wipe = false;
    std::uint8_t next_event_slot = 0;
    // Results navigation reuses this router but may intentionally stop on the
    // settled stock TOUR_SELECT surface instead of choosing a tour.
    bool stop_at_tour_select = false;
    std::uint8_t release_observations = 0;
    bool waiting_for_selection_change = false;
    std::uint8_t selection_before_input = 0;
    bool menu_settled = false;
    std::uint16_t menu_settle_observations = 0;
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
    bool tour_select_ready = false;
    bool timed_out = false;
    // The stock NOW_PLAYING confirm entered an active race for Next Event.
    // The route is finished; the caller verifies course identity.
    bool next_event_race_entered = false;
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

constexpr ModernTourContinueState begin_modern_tour_next_event(
    std::uint8_t tour_row,
    ModernTourEntryDecision decision,
    std::uint8_t next_event_slot
) noexcept {
    if (decision.intent != ModernTourEntryIntent::NextEvent ||
        next_event_slot >= 5) {
        return {};
    }
    auto state = begin_modern_tour_entry(tour_row, decision);
    if (state.stage == ModernTourContinueStage::Idle) return {};
    state.next_event_slot = next_event_slot;
    return state;
}

// Called by the host only after the Resume restore has been applied at a
// settled TRACK_SELECT. Any other state is returned unchanged.
constexpr ModernTourContinueState enter_modern_tour_next_event_selection(
    ModernTourContinueState state
) noexcept {
    if (state.intent != ModernTourEntryIntent::NextEvent ||
        state.stage != ModernTourContinueStage::Ready ||
        state.next_event_slot >= 5) {
        return state;
    }
    state.stage = ModernTourContinueStage::SelectNextEvent;
    state.release_observations = kModernTourNextEventReleaseObservations;
    state.menu_settled = true;
    state.menu_settle_observations = 0;
    state.waiting_for_selection_change = false;
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

constexpr ModernTourContinueState begin_modern_tour_results_route(
    std::uint8_t tour_row,
    bool stop_at_tour_select,
    bool restore_continuation
) noexcept {
    auto state = begin_modern_tour_entry(
        tour_row,
        {
            ModernTourEntryIntent::Resume,
            true,
            restore_continuation,
            false,
        });
    state.stop_at_tour_select = stop_at_tour_select;
    return state;
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
        out.next_event_race_entered =
            state.stage == ModernTourContinueStage::AwaitNextEventRace;
        out.state = {};
        return out;
    }

    if (state.waiting_for_selection_change) {
        if (observation.selected_option == state.selection_before_input) {
            return out;
        }
        out.state.waiting_for_selection_change = false;
        out.state.release_observations = 0;
    }

    // Stock exposes frontend menu bytes before those surfaces are guaranteed
    // to accept a confirm edge. Reuse the same 60-frame settle contract proven
    // by Quick Practice instead of racing first visibility.
    std::uint8_t expected_menu = 0;
    switch (out.state.stage) {
    case ModernTourContinueStage::AwaitMain: expected_menu = 0xD7; break;
    case ModernTourContinueStage::AwaitRider: expected_menu = 0x3C; break;
    case ModernTourContinueStage::AwaitTour: expected_menu = 0x6D; break;
    case ModernTourContinueStage::AwaitTrack: expected_menu = 0xF6; break;
    case ModernTourContinueStage::SelectNextEvent: expected_menu = 0xF6; break;
    case ModernTourContinueStage::AwaitNextEventNowPlaying:
        expected_menu = 0x16;
        break;
    case ModernTourContinueStage::AwaitNextEventRace:
    case ModernTourContinueStage::Ready:
    case ModernTourContinueStage::Idle:
        break;
    }

    if (expected_menu != 0 && !out.state.menu_settled) {
        if (observation.menu_id != expected_menu) {
            out.state.menu_settle_observations = 0;
            return out;
        }
        if (++out.state.menu_settle_observations <
            kQuickPracticeMenuSettleObservations) {
            return out;
        }
        out.state.menu_settled = true;
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
            const auto desired =
                stock_main_menu_one_player_input(observation.selected_option);
            if (desired != QuickPracticeMenuInput::Accept) {
                return emit_selection_input(desired);
            }
            out.input = QuickPracticeMenuInput::Accept;
            out.state.stage = ModernTourContinueStage::AwaitRider;
            out.state.menu_settled = false;
            out.state.menu_settle_observations = 0;
        }
        break;
    case ModernTourContinueStage::AwaitRider:
        if (observation.menu_id == 0x3C) {
            out.input = QuickPracticeMenuInput::Accept;
            out.state.stage = ModernTourContinueStage::AwaitTour;
            out.state.menu_settled = false;
            out.state.menu_settle_observations = 0;
        }
        break;
    case ModernTourContinueStage::AwaitTour:
        if (observation.menu_id == 0x6D) {
            if (out.state.stop_at_tour_select) {
                out.state.stage = ModernTourContinueStage::Ready;
                out.tour_select_ready = true;
                break;
            }
            const auto desired = quick_practice_tour_input(
                out.state.tour_option,
                observation.selected_option);
            if (desired == QuickPracticeMenuInput::Accept) {
                out.input = QuickPracticeMenuInput::Accept;
                out.state.stage = ModernTourContinueStage::AwaitTrack;
                out.state.menu_settled = false;
                out.state.menu_settle_observations = 0;
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
    case ModernTourContinueStage::SelectNextEvent:
        if (out.state.release_observations <
            kModernTourNextEventReleaseObservations) {
            ++out.state.release_observations;
            return out;
        }
        // Never confirm off TRACK_SELECT; a surface change waits for the
        // bounded observation budget instead of guessing.
        if (observation.menu_id == 0xF6) {
            const auto desired = quick_practice_track_input(
                out.state.next_event_slot,
                observation.selected_option);
            if (desired == QuickPracticeMenuInput::Accept) {
                out.input = QuickPracticeMenuInput::Accept;
                out.state.stage =
                    ModernTourContinueStage::AwaitNextEventNowPlaying;
                out.state.menu_settled = false;
                out.state.menu_settle_observations = 0;
            } else {
                return emit_selection_input(desired);
            }
        }
        break;
    case ModernTourContinueStage::AwaitNextEventNowPlaying:
        if (observation.menu_id == 0x16) {
            out.input = QuickPracticeMenuInput::Accept;
            out.state.stage = ModernTourContinueStage::AwaitNextEventRace;
            out.state.menu_settled = false;
            out.state.menu_settle_observations = 0;
        }
        break;
    case ModernTourContinueStage::AwaitNextEventRace:
    case ModernTourContinueStage::Idle:
        break;
    }

    return out;
}

}  // namespace ur::product
