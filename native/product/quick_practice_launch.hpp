#pragma once

#include "quick_practice_route.hpp"

#include <cstdint>

namespace ur::product {

enum class QuickPracticeLaunchStage {
    Idle,
    AwaitMain,
    AwaitRider,
    AwaitTour,
    AwaitTrack,
    AwaitNowPlaying,
    AwaitRace,
    Active,
};

enum class QuickPracticeLaunchInput {
    None,
    Up,
    Down,
    Left,
    Right,
    Accept,
};

struct QuickPracticeLaunchObservation {
    std::uint8_t menu_id = 0;
    std::uint8_t selected_option = 0;
    bool in_race = false;
    // Canonical zero-based Quick Practice track id from the authoritative
    // decoded-course identity, or -1 while identity is not yet available.
    int active_track_id = -1;
};

constexpr std::uint16_t kQuickPracticeMenuSettleObservations = 60;
constexpr std::uint32_t kQuickPracticeLaunchMaxObservations = 3600;

struct QuickPracticeLaunchState {
    QuickPracticeLaunchStage stage = QuickPracticeLaunchStage::Idle;
    QuickPracticeTarget target{};
    bool waiting_for_selection_change = false;
    std::uint8_t selection_before_input = 0;
    bool menu_settled = false;
    std::uint16_t menu_settle_observations = 0;
    std::uint32_t observations_remaining = 0;
};

struct QuickPracticeLaunchStep {
    QuickPracticeLaunchState state{};
    QuickPracticeLaunchInput input = QuickPracticeLaunchInput::None;
    bool race_ready = false;
    bool course_mismatch = false;
    bool route_violation = false;
    bool timed_out = false;
};

constexpr bool quick_practice_launch_owns_player_input(
    const QuickPracticeLaunchState& state
) noexcept {
    return state.stage != QuickPracticeLaunchStage::Idle &&
           state.stage != QuickPracticeLaunchStage::Active;
}

// When a host-side effect requested by one observation (input transport or
// abort/reboot request) fails, retry the same semantic state on the next host
// frame but still consume that observation from the bounded routing budget.
constexpr QuickPracticeLaunchState quick_practice_launch_retry_state(
    QuickPracticeLaunchState state
) noexcept {
    if (quick_practice_launch_owns_player_input(state) &&
        state.observations_remaining > 0) {
        --state.observations_remaining;
    }
    return state;
}

constexpr QuickPracticeLaunchInput launch_input_from_menu_input(
    QuickPracticeMenuInput input
) noexcept {
    switch (input) {
    case QuickPracticeMenuInput::Up: return QuickPracticeLaunchInput::Up;
    case QuickPracticeMenuInput::Down: return QuickPracticeLaunchInput::Down;
    case QuickPracticeMenuInput::Left: return QuickPracticeLaunchInput::Left;
    case QuickPracticeMenuInput::Right: return QuickPracticeLaunchInput::Right;
    case QuickPracticeMenuInput::Accept: return QuickPracticeLaunchInput::Accept;
    case QuickPracticeMenuInput::None: return QuickPracticeLaunchInput::None;
    }
    return QuickPracticeLaunchInput::None;
}

constexpr QuickPracticeLaunchState begin_quick_practice_launch(
    QuickPracticeTarget target
) noexcept {
    QuickPracticeLaunchState state;
    if (!target.valid) return state;
    state.stage = QuickPracticeLaunchStage::AwaitMain;
    state.target = target;
    state.observations_remaining = kQuickPracticeLaunchMaxObservations;
    return state;
}

constexpr QuickPracticeLaunchStep advance_quick_practice_launch(
    QuickPracticeLaunchState state,
    QuickPracticeLaunchObservation observation
) noexcept {
    QuickPracticeLaunchStep out;
    out.state = state;

    if (state.stage == QuickPracticeLaunchStage::Idle) return out;
    if (state.stage != QuickPracticeLaunchStage::Active) {
        if (state.observations_remaining == 0) {
            out.state = {};
            out.timed_out = true;
            return out;
        }
        --out.state.observations_remaining;
    }

    if (observation.in_race) {
        // A target-aware launch must reach race state only after the router has
        // issued the Now Playing confirmation. This rejects attract/demo races
        // or any other frontend escape that merely happens to become active.
        if (out.state.stage != QuickPracticeLaunchStage::AwaitRace &&
            out.state.stage != QuickPracticeLaunchStage::Active) {
            out.state = {};
            out.route_violation = true;
            return out;
        }

        // Active-race state alone is still insufficient. Wait for the
        // authoritative decoded-course identity, then accept only the exact
        // requested course. A different valid course fails closed.
        if (observation.active_track_id < 0) return out;
        if (observation.active_track_id !=
            static_cast<int>(out.state.target.track_id)) {
            out.state = {};
            out.course_mismatch = true;
            return out;
        }
        out.state.stage = QuickPracticeLaunchStage::Active;
        out.state.waiting_for_selection_change = false;
        out.race_ready = true;
        return out;
    }

    if (state.waiting_for_selection_change) {
        if (observation.selected_option == state.selection_before_input) {
            return out;
        }
        out.state.waiting_for_selection_change = false;
    }

    // Stock exposes menu-state bytes before the newly visible menu is
    // guaranteed to accept an input edge. The native deterministic route has
    // proven a 60-frame settle window at each frontend surface. Encode that
    // evidence here instead of racing first visibility.
    std::uint8_t expected_menu = 0;
    switch (out.state.stage) {
    case QuickPracticeLaunchStage::AwaitMain: expected_menu = 0xD7; break;
    case QuickPracticeLaunchStage::AwaitRider: expected_menu = 0x3C; break;
    case QuickPracticeLaunchStage::AwaitTour: expected_menu = 0x6D; break;
    case QuickPracticeLaunchStage::AwaitTrack: expected_menu = 0xF6; break;
    case QuickPracticeLaunchStage::AwaitNowPlaying: expected_menu = 0x16; break;
    case QuickPracticeLaunchStage::AwaitRace:
    case QuickPracticeLaunchStage::Active:
    case QuickPracticeLaunchStage::Idle:
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
    ) constexpr -> QuickPracticeLaunchStep {
        QuickPracticeLaunchStep step;
        step.state = out.state;
        step.input = launch_input_from_menu_input(desired);
        if (desired != QuickPracticeMenuInput::None &&
            desired != QuickPracticeMenuInput::Accept) {
            step.state.waiting_for_selection_change = true;
            step.state.selection_before_input = observation.selected_option;
        }
        return step;
    };

    switch (out.state.stage) {
    case QuickPracticeLaunchStage::AwaitMain:
        if (observation.menu_id == 0xD7) {
            out.input = QuickPracticeLaunchInput::Accept;
            out.state.stage = QuickPracticeLaunchStage::AwaitRider;
            out.state.menu_settled = false;
            out.state.menu_settle_observations = 0;
        }
        break;
    case QuickPracticeLaunchStage::AwaitRider:
        if (observation.menu_id == 0x3C) {
            out.input = QuickPracticeLaunchInput::Accept;
            out.state.stage = QuickPracticeLaunchStage::AwaitTour;
            out.state.menu_settled = false;
            out.state.menu_settle_observations = 0;
        }
        break;
    case QuickPracticeLaunchStage::AwaitTour:
        if (observation.menu_id == 0x6D) {
            const auto desired = quick_practice_tour_input(
                out.state.target.tour_option,
                observation.selected_option);
            if (desired == QuickPracticeMenuInput::Accept) {
                out.input = QuickPracticeLaunchInput::Accept;
                out.state.stage = QuickPracticeLaunchStage::AwaitTrack;
                out.state.menu_settled = false;
                out.state.menu_settle_observations = 0;
            } else {
                return emit_selection_input(desired);
            }
        }
        break;
    case QuickPracticeLaunchStage::AwaitTrack:
        if (observation.menu_id == 0xF6) {
            const auto desired = quick_practice_track_input(
                out.state.target.track_slot,
                observation.selected_option);
            if (desired == QuickPracticeMenuInput::Accept) {
                out.input = QuickPracticeLaunchInput::Accept;
                out.state.stage = QuickPracticeLaunchStage::AwaitNowPlaying;
                out.state.menu_settled = false;
                out.state.menu_settle_observations = 0;
            } else {
                return emit_selection_input(desired);
            }
        }
        break;
    case QuickPracticeLaunchStage::AwaitNowPlaying:
        if (observation.menu_id == 0x16) {
            out.input = QuickPracticeLaunchInput::Accept;
            out.state.stage = QuickPracticeLaunchStage::AwaitRace;
            out.state.menu_settled = false;
            out.state.menu_settle_observations = 0;
        }
        break;
    case QuickPracticeLaunchStage::AwaitRace:
        break;
    case QuickPracticeLaunchStage::Active:
        out.race_ready = true;
        break;
    case QuickPracticeLaunchStage::Idle:
        break;
    }

    return out;
}

}  // namespace ur::product
