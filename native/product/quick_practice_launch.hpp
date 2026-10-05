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

struct QuickPracticeLaunchState {
    QuickPracticeLaunchStage stage = QuickPracticeLaunchStage::Idle;
    QuickPracticeTarget target{};
    bool waiting_for_selection_change = false;
    std::uint8_t selection_before_input = 0;
};

struct QuickPracticeLaunchStep {
    QuickPracticeLaunchState state{};
    QuickPracticeLaunchInput input = QuickPracticeLaunchInput::None;
    bool race_ready = false;
    bool course_mismatch = false;
};

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
    return state;
}

constexpr QuickPracticeLaunchStep advance_quick_practice_launch(
    QuickPracticeLaunchState state,
    QuickPracticeLaunchObservation observation
) noexcept {
    QuickPracticeLaunchStep out;
    out.state = state;

    if (state.stage == QuickPracticeLaunchStage::Idle) return out;

    if (observation.in_race) {
        // Active-race state alone is insufficient for a target-aware launch.
        // Wait for the authoritative decoded-course identity, then accept only
        // the requested course. A different valid course fails closed.
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
        }
        break;
    case QuickPracticeLaunchStage::AwaitRider:
        if (observation.menu_id == 0x3C) {
            out.input = QuickPracticeLaunchInput::Accept;
            out.state.stage = QuickPracticeLaunchStage::AwaitTour;
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
            } else {
                return emit_selection_input(desired);
            }
        }
        break;
    case QuickPracticeLaunchStage::AwaitNowPlaying:
        if (observation.menu_id == 0x16) {
            out.input = QuickPracticeLaunchInput::Accept;
            out.state.stage = QuickPracticeLaunchStage::AwaitRace;
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
