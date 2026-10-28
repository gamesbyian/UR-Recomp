#include "quick_practice_launch.hpp"

#include <cassert>

using namespace ur::product;

static QuickPracticeLaunchStep settle_menu(
    QuickPracticeLaunchState state,
    QuickPracticeLaunchObservation observation
) {
    QuickPracticeLaunchStep step{};
    for (std::uint16_t i = 0; i < kQuickPracticeMenuSettleObservations; ++i) {
        step = advance_quick_practice_launch(state, observation);
        state = step.state;
        if (i + 1 < kQuickPracticeMenuSettleObservations) {
            assert(step.input == QuickPracticeLaunchInput::None);
            assert(!step.race_ready);
            assert(!step.course_mismatch);
            assert(!step.route_violation);
        }
    }
    return step;
}

static void prove_all_tracks_reach_race() {
    for (std::uint8_t track = 0; track < 45; ++track) {
        auto state = begin_quick_practice_launch(
            quick_practice_target_for_track(track));
        QuickPracticeLaunchObservation observation{0xD7, 0, false, -1};

        bool reached = false;
        for (int guard = 0; guard < 2500 && !reached; ++guard) {
            const auto step = advance_quick_practice_launch(state, observation);
            state = step.state;

            switch (step.input) {
            case QuickPracticeLaunchInput::Up:
                if (observation.menu_id == 0x6D) {
                    if (observation.selected_option >= 2) {
                        observation.selected_option =
                            static_cast<std::uint8_t>(
                                observation.selected_option - 2);
                    }
                } else if (observation.selected_option > 0) {
                    --observation.selected_option;
                }
                break;
            case QuickPracticeLaunchInput::Down:
                observation.selected_option = static_cast<std::uint8_t>(
                    observation.selected_option +
                    (observation.menu_id == 0x6D ? 2 : 1));
                break;
            case QuickPracticeLaunchInput::Left:
                if (observation.selected_option > 0) {
                    --observation.selected_option;
                }
                break;
            case QuickPracticeLaunchInput::Right:
                ++observation.selected_option;
                break;
            case QuickPracticeLaunchInput::Accept:
                switch (state.stage) {
                case QuickPracticeLaunchStage::AwaitRider:
                    observation = {0x3C, 0, false, -1};
                    break;
                case QuickPracticeLaunchStage::AwaitTour:
                    observation = {0x6D, 0, false, -1};
                    break;
                case QuickPracticeLaunchStage::AwaitTrack:
                    observation = {0xF6, 0, false, -1};
                    break;
                case QuickPracticeLaunchStage::AwaitNowPlaying:
                    observation = {
                        0x16, observation.selected_option, false, -1};
                    break;
                case QuickPracticeLaunchStage::AwaitRace:
                    observation = {0x00, 0, true, track};
                    break;
                default:
                    break;
                }
                break;
            case QuickPracticeLaunchInput::None:
                break;
            }

            assert(!step.course_mismatch);
            assert(!step.route_violation);
            if (state.stage == QuickPracticeLaunchStage::Active ||
                step.race_ready) {
                reached = true;
            }
        }

        assert(reached);
        assert(state.stage == QuickPracticeLaunchStage::Active);
    }
}

// The stock MAIN_MENU cursor may rest on 2P/VS/LEAGUE/OPTIONS. The launch
// must walk it back to 1P before confirming instead of entering another mode.
static void prove_main_menu_cursor_returns_to_one_player() {
    auto state = begin_quick_practice_launch(quick_practice_target_for_track(0));
    QuickPracticeLaunchObservation observation{0xD7, 3, false, -1};
    auto step = settle_menu(state, observation);
    for (std::uint8_t expected = 3; expected > 0; --expected) {
        assert(step.input == QuickPracticeLaunchInput::Up);
        assert(step.state.stage == QuickPracticeLaunchStage::AwaitMain);
        state = step.state;
        // No second edge until the stock cursor visibly moved.
        step = advance_quick_practice_launch(state, observation);
        assert(step.input == QuickPracticeLaunchInput::None);
        state = step.state;
        observation.selected_option = static_cast<std::uint8_t>(expected - 1);
        step = advance_quick_practice_launch(state, observation);
    }
    assert(step.input == QuickPracticeLaunchInput::Accept);
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitRider);
}

// Live stock menu IDs can be transient, with the menu cursor reused by
// unrelated scenes. A route may not treat an alien menu's cursor as proof
// its last direction was consumed or inherit the prior 60-frame settle.
static void prove_practice_scene_interruption_requires_new_settle() {
    {
        auto state = begin_quick_practice_launch(
            quick_practice_target_for_track(0));
        auto first = settle_menu(state, {0xD7, 4, false, -1});
        assert(first.input == QuickPracticeLaunchInput::Up);
        assert(first.state.waiting_for_selection_change);
        assert(first.state.menu_settled);
        auto crossed = advance_quick_practice_launch(
            first.state, {0x6D, 3, false, -1});
        assert(crossed.input == QuickPracticeLaunchInput::None);
        assert(!crossed.state.waiting_for_selection_change);
        assert(!crossed.state.menu_settled);
        assert(crossed.state.menu_settle_observations == 0);

        state = crossed.state;
        for (unsigned i = 0; i + 1 < kQuickPracticeMenuSettleObservations;
             ++i) {
            auto step = advance_quick_practice_launch(
                state, {0xD7, 0, false, -1});
            assert(step.input == QuickPracticeLaunchInput::None);
            state = step.state;
        }
        auto accepted = advance_quick_practice_launch(
            state, {0xD7, 0, false, -1});
        assert(accepted.input == QuickPracticeLaunchInput::Accept);
        assert(accepted.state.stage == QuickPracticeLaunchStage::AwaitRider);
    }

    {
        // A stock TRACK menu interrupted by NOW_PLAYING must settle again
        // before confirming the selected track. Its previous Down press
        // cannot be acknowledged by NOW_PLAYING's unrelated cursor.
        auto state = begin_quick_practice_launch(
            quick_practice_target_for_track(4));
        state.stage = QuickPracticeLaunchStage::AwaitTrack;
        auto first = settle_menu(state, {0xF6, 0, false, -1});
        assert(first.input == QuickPracticeLaunchInput::Down);
        auto crossed = advance_quick_practice_launch(
            first.state, {0x16, 1, false, -1});
        assert(crossed.input == QuickPracticeLaunchInput::None);
        assert(!crossed.state.menu_settled);
        assert(!crossed.state.waiting_for_selection_change);

        state = crossed.state;
        for (unsigned i = 0; i + 1 < kQuickPracticeMenuSettleObservations;
             ++i) {
            auto step = advance_quick_practice_launch(
                state, {0xF6, 4, false, -1});
            assert(step.input == QuickPracticeLaunchInput::None);
            state = step.state;
        }
        auto accepted = advance_quick_practice_launch(
            state, {0xF6, 4, false, -1});
        assert(accepted.input == QuickPracticeLaunchInput::Accept);
        assert(accepted.state.stage == QuickPracticeLaunchStage::AwaitNowPlaying);
    }

    {
        auto state = begin_quick_practice_launch(
            quick_practice_target_for_track(0));
        for (unsigned i = 0; i < 40; ++i) {
            auto step = advance_quick_practice_launch(
                state, {0xD7, 0, false, -1});
            assert(step.input == QuickPracticeLaunchInput::None);
            state = step.state;
        }
        assert(state.menu_settle_observations == 40);
        auto interrupted = advance_quick_practice_launch(
            state, {0x84, 0, false, -1});
        assert(interrupted.state.menu_settle_observations == 0);

        state = interrupted.state;
        for (unsigned i = 0; i + 1 < kQuickPracticeMenuSettleObservations;
             ++i) {
            auto step = advance_quick_practice_launch(
                state, {0xD7, 0, false, -1});
            assert(step.input == QuickPracticeLaunchInput::None);
            state = step.state;
        }
        auto accepted = advance_quick_practice_launch(
            state, {0xD7, 0, false, -1});
        assert(accepted.input == QuickPracticeLaunchInput::Accept);
    }
}

// The production Windows host waits 20 frames after an injected menu edge.
// Scene identity must still be sampled while the state machine is not driven,
// otherwise a one-frame alien menu during that gap escapes the 60-frame gate.
static void prove_release_gap_observes_intermediate_stock_scene() {
    auto state = begin_quick_practice_launch(
        quick_practice_target_for_track(0));
    auto first = settle_menu(state, {0xD7, 4, false, -1});
    assert(first.input == QuickPracticeLaunchInput::Up);
    assert(first.state.menu_settled);
    assert(first.state.waiting_for_selection_change);
    state = first.state;

    // Exactly the Windows host's release-gap path, with no input emitted.
    for (unsigned frame = 0; frame < 20; ++frame) {
        state = quick_practice_launch_observe_source_menu(
            state, frame == 3 ? 0x6Du : 0xD7u);
    }
    assert(!state.menu_settled);
    assert(!state.waiting_for_selection_change);
    assert(state.menu_settle_observations == 0);

    for (unsigned i = 0; i + 1 < kQuickPracticeMenuSettleObservations; ++i) {
        auto step = advance_quick_practice_launch(
            state, {0xD7, 0, false, -1});
        assert(step.input == QuickPracticeLaunchInput::None);
        state = step.state;
    }
    auto accepted = advance_quick_practice_launch(
        state, {0xD7, 0, false, -1});
    assert(accepted.input == QuickPracticeLaunchInput::Accept);
    assert(accepted.state.stage == QuickPracticeLaunchStage::AwaitRider);
}

int main() {
    prove_release_gap_observes_intermediate_stock_scene();
    prove_practice_scene_interruption_requires_new_settle();
    prove_main_menu_cursor_returns_to_one_player();
    QuickPracticeLaunchState ownership{};
    assert(!quick_practice_launch_owns_player_input(ownership));
    ownership.stage = QuickPracticeLaunchStage::AwaitMain;
    assert(quick_practice_launch_owns_player_input(ownership));
    ownership.stage = QuickPracticeLaunchStage::AwaitRider;
    assert(quick_practice_launch_owns_player_input(ownership));
    ownership.stage = QuickPracticeLaunchStage::AwaitTour;
    assert(quick_practice_launch_owns_player_input(ownership));
    ownership.stage = QuickPracticeLaunchStage::AwaitTrack;
    assert(quick_practice_launch_owns_player_input(ownership));
    ownership.stage = QuickPracticeLaunchStage::AwaitNowPlaying;
    assert(quick_practice_launch_owns_player_input(ownership));
    ownership.stage = QuickPracticeLaunchStage::AwaitRace;
    assert(quick_practice_launch_owns_player_input(ownership));
    ownership.stage = QuickPracticeLaunchStage::Active;
    assert(!quick_practice_launch_owns_player_input(ownership));

    QuickPracticeLaunchState retry_budget =
        begin_quick_practice_launch(quick_practice_target_for_track(0));
    retry_budget.observations_remaining = 2;
    retry_budget = quick_practice_launch_retry_state(retry_budget);
    assert(retry_budget.observations_remaining == 1);
    retry_budget = quick_practice_launch_retry_state(retry_budget);
    assert(retry_budget.observations_remaining == 0);
    retry_budget = quick_practice_launch_retry_state(retry_budget);
    assert(retry_budget.observations_remaining == 0);
    retry_budget.stage = QuickPracticeLaunchStage::Active;
    retry_budget.observations_remaining = 2;
    retry_budget = quick_practice_launch_retry_state(retry_budget);
    assert(retry_budget.observations_remaining == 2);

    prove_all_tracks_reach_race();

    const auto target =
        quick_practice_target_for_track(12);  // Shuffler / slot 3.
    auto state = begin_quick_practice_launch(target);
    assert(state.stage == QuickPracticeLaunchStage::AwaitMain);

    auto step = settle_menu(state, {0xD7, 0, false, -1});
    assert(step.input == QuickPracticeLaunchInput::Accept);
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitRider);
    state = step.state;

    step = settle_menu(state, {0x3C, 0, false, -1});
    assert(step.input == QuickPracticeLaunchInput::Accept);
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitTour);
    state = step.state;

    step = settle_menu(state, {0x6D, 0, false, -1});
    assert(step.input == QuickPracticeLaunchInput::Down);
    assert(step.state.waiting_for_selection_change);

    auto held = advance_quick_practice_launch(
        step.state, {0x6D, 0, false, -1});
    assert(held.input == QuickPracticeLaunchInput::None);
    assert(held.state.waiting_for_selection_change);

    step = advance_quick_practice_launch(
        held.state, {0x6D, 2, false, -1});
    assert(step.input == QuickPracticeLaunchInput::Accept);
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitTrack);
    state = step.state;

    step = settle_menu(state, {0xF6, 0, false, -1});
    assert(step.input == QuickPracticeLaunchInput::Down);
    assert(step.state.waiting_for_selection_change);

    held = advance_quick_practice_launch(
        step.state, {0xF6, 0, false, -1});
    assert(held.input == QuickPracticeLaunchInput::None);

    step = advance_quick_practice_launch(
        held.state, {0xF6, 1, false, -1});
    assert(step.input == QuickPracticeLaunchInput::Down);
    assert(step.state.waiting_for_selection_change);

    step = advance_quick_practice_launch(
        step.state, {0xF6, 2, false, -1});
    assert(step.input == QuickPracticeLaunchInput::Accept);
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitNowPlaying);
    state = step.state;

    step = settle_menu(state, {0x16, 2, false, -1});
    assert(step.input == QuickPracticeLaunchInput::Accept);
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitRace);

    // Race-active without decoded-course identity waits rather than guessing.
    step = advance_quick_practice_launch(
        step.state, {0x00, 0, true, -1});
    assert(step.state.stage == QuickPracticeLaunchStage::AwaitRace);
    assert(!step.race_ready);
    assert(!step.course_mismatch);
    assert(!step.route_violation);

    step = advance_quick_practice_launch(
        step.state, {0x00, 0, true, target.track_id});
    assert(step.input == QuickPracticeLaunchInput::None);
    assert(step.state.stage == QuickPracticeLaunchStage::Active);
    assert(step.race_ready);

    // A race reached before the router has completed Now Playing is not a
    // successful Practice launch, even if its course happens to match.
    state = begin_quick_practice_launch(
        quick_practice_target_for_track(0));
    step = advance_quick_practice_launch(
        state, {0x00, 0, true, 0});
    assert(step.state.stage == QuickPracticeLaunchStage::Idle);
    assert(!step.race_ready);
    assert(step.route_violation);

    // A different authoritative course after the correct frontend route also
    // fails closed.
    state = begin_quick_practice_launch(
        quick_practice_target_for_track(0));
    state.stage = QuickPracticeLaunchStage::AwaitRace;
    step = advance_quick_practice_launch(
        state, {0x00, 0, true, 1});
    assert(step.state.stage == QuickPracticeLaunchStage::Idle);
    assert(!step.race_ready);
    assert(step.course_mismatch);
    assert(!step.route_violation);

    // A stalled route cannot own player input forever.
    state = begin_quick_practice_launch(
        quick_practice_target_for_track(0));
    state.observations_remaining = 1;
    step = advance_quick_practice_launch(
        state, {0x00, 0, false, -1});
    assert(!step.timed_out);
    assert(step.state.observations_remaining == 0);
    step = advance_quick_practice_launch(
        step.state, {0x00, 0, false, -1});
    assert(step.timed_out);
    assert(step.state.stage == QuickPracticeLaunchStage::Idle);
    assert(!quick_practice_launch_owns_player_input(step.state));

    // Invalid targets fail closed.
    state = begin_quick_practice_launch({});
    assert(state.stage == QuickPracticeLaunchStage::Idle);
    step = advance_quick_practice_launch(
        state, {0xD7, 0, false, -1});
    assert(step.input == QuickPracticeLaunchInput::None);

    // Valid flag alone is not authority for mismatched tour/slot identities.
    const auto canonical = quick_practice_target_for_track(12);
    assert(canonical.valid);
    auto bad = canonical;
    bad.track_id = 45;
    assert(begin_quick_practice_launch(bad).stage ==
           QuickPracticeLaunchStage::Idle);
    bad = canonical;
    bad.tour_option = 9;
    assert(begin_quick_practice_launch(bad).stage ==
           QuickPracticeLaunchStage::Idle);
    bad = canonical;
    bad.track_slot = 4;
    assert(begin_quick_practice_launch(bad).stage ==
           QuickPracticeLaunchStage::Idle);
    assert(begin_quick_practice_launch(canonical).stage ==
           QuickPracticeLaunchStage::AwaitMain);

    // Results-time Repeat Practice must reject a missing, changed or
    // corrupted retained course before any guest Restart is dispatched.
    const int repeat_tracks[] = {0, 12, 44};
    for (int track_id : repeat_tracks) {
        auto repeat = begin_quick_practice_launch(
            quick_practice_target_for_track(
                static_cast<std::uint8_t>(track_id)));
        assert(!quick_practice_repeat_target_ready(repeat, track_id));
        repeat.stage = QuickPracticeLaunchStage::Active;
        assert(quick_practice_repeat_target_ready(repeat, track_id));
        assert(!quick_practice_repeat_target_ready(repeat, -1));
        assert(!quick_practice_repeat_target_ready(repeat, 45));
        assert(!quick_practice_repeat_target_ready(
            repeat, (track_id + 1) % 45));
        auto corrupted = repeat;
        corrupted.target.valid = false;
        assert(!quick_practice_repeat_target_ready(corrupted, track_id));
        corrupted = repeat;
        corrupted.target.tour_option = 8;  // unsupported stock tour
        assert(!quick_practice_repeat_target_ready(corrupted, track_id));
        corrupted = repeat;
        corrupted.target.track_slot =
            static_cast<std::uint8_t>((track_id + 1) % 5);
        assert(!quick_practice_repeat_target_ready(corrupted, track_id));
        corrupted = repeat;
        corrupted.target.track_id = 45;
        assert(!quick_practice_repeat_target_ready(corrupted, track_id));
        corrupted = repeat;
        corrupted.stage = QuickPracticeLaunchStage::AwaitRace;
        assert(!quick_practice_repeat_target_ready(corrupted, track_id));
    }
    assert(!quick_practice_repeat_target_ready({}, 0));

    // The handoff contains only canonical track identity. It cannot dispatch
    // a stock launch before a new frontend appears, and cannot wait forever.
    for (std::uint8_t track = 0; track < 45; ++track) {
        auto launch = begin_quick_practice_launch(
            quick_practice_target_for_track(track));
        launch.stage = QuickPracticeLaunchStage::Active;
        for (int cycle = 0; cycle < 2; ++cycle) {
            auto route = begin_quick_practice_rematch_route(launch, track);
            assert(route.pending && route.track_id == track);
            auto waiting = advance_quick_practice_rematch_route(route, false);
            assert(!waiting.begin_stock_route && !waiting.timed_out);
            assert(waiting.route.pending);
            auto ready = advance_quick_practice_rematch_route(
                waiting.route, true);
            assert(ready.begin_stock_route && !ready.route.pending);
            assert(ready.track_id == track);
            assert(!advance_quick_practice_rematch_route(
                ready.route, true).begin_stock_route);
        }
        assert(!begin_quick_practice_rematch_route(
            launch, (track + 1) % 45).pending);
        auto corrupted = launch;
        corrupted.target.track_slot = 9;
        assert(!begin_quick_practice_rematch_route(corrupted, track).pending);
    }
    auto timeout = begin_quick_practice_launch(
        quick_practice_target_for_track(0));
    timeout.stage = QuickPracticeLaunchStage::Active;
    auto handoff = begin_quick_practice_rematch_route(timeout, 0);
    handoff.observations_remaining = 1;
    const auto expired = advance_quick_practice_rematch_route(handoff, false);
    assert(expired.timed_out && !expired.route.pending);
    assert(!advance_quick_practice_rematch_route(
        expired.route, true).begin_stock_route);
    assert(!begin_quick_practice_rematch_route({}, 0).pending);

    return 0;
}
