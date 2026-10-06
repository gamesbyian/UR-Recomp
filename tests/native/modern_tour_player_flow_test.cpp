#include "modern_challenge_tier_selector.hpp"
#include "modern_tour_action_menu.hpp"
#include "modern_tour_continue.hpp"

#include <cassert>

using namespace ur::product;

namespace {

ModernTourContinueState drive_to_track_select(
    ModernTourContinueState state) {
    ModernTourContinueObservation observation{0xD7, 0, false};
    for (int guard = 0; guard < 512; ++guard) {
        const auto step = advance_modern_tour_continue(state, observation);
        state = step.state;
        if (step.track_select_ready) return state;

        switch (step.input) {
        case QuickPracticeMenuInput::Up:
            if (observation.selected_option >= 2) {
                observation.selected_option =
                    static_cast<std::uint8_t>(observation.selected_option - 2);
            }
            break;
        case QuickPracticeMenuInput::Down:
            observation.selected_option =
                static_cast<std::uint8_t>(observation.selected_option + 2);
            break;
        case QuickPracticeMenuInput::Left:
            if (observation.selected_option > 0) --observation.selected_option;
            break;
        case QuickPracticeMenuInput::Right:
            ++observation.selected_option;
            break;
        case QuickPracticeMenuInput::Accept:
            switch (state.stage) {
            case ModernTourContinueStage::AwaitRider:
                observation = {0x3C, 0, false};
                break;
            case ModernTourContinueStage::AwaitTour:
                observation = {0x6D, 0, false};
                break;
            case ModernTourContinueStage::AwaitTrack:
                observation = {0xF6, 0, false};
                break;
            default:
                break;
            }
            break;
        case QuickPracticeMenuInput::None:
            break;
        }
    }
    return {};
}

}  // namespace

int main() {
    const ModernTourEntryContext context{
        ExecutionMode::Modern, true, true, true};

    // The player-visible tier is derived from the existing medal authority.
    assert(default_modern_challenge_tier(0) == ModernChallengeTier::Bronze);
    assert(default_modern_challenge_tier(1) == ModernChallengeTier::Silver);
    assert(default_modern_challenge_tier(2) == ModernChallengeTier::Gold);
    assert(default_modern_challenge_tier(3) == ModernChallengeTier::Gold);

    // Resume flows from the semantic action menu into the established stock
    // route and reaches settlement still carrying restore authority.
    auto menu = make_modern_tour_action_menu(context);
    auto action = activate_modern_tour_action_menu(
        menu, context, UR_MODERN_HOST_NAV_CONFIRM);
    assert(action.intent == ModernTourEntryIntent::Resume);
    const auto resume_decision = resolve_modern_tour_entry(
        context, action.intent);
    auto resume = drive_to_track_select(
        begin_modern_tour_entry(4, resume_decision));
    assert(resume.stage == ModernTourContinueStage::Ready);
    assert(resume.intent == ModernTourEntryIntent::Resume);
    assert(resume.restore_continuation_at_track_select);
    assert(!resume.retire_continuation_after_stock_wipe);

    // Restart confirmation is cancellable and emits no destructive intent.
    menu = make_modern_tour_action_menu(context);
    menu = navigate_modern_tour_action_menu(
        menu, UR_MODERN_HOST_NAV_DOWN);
    action = activate_modern_tour_action_menu(
        menu, context, UR_MODERN_HOST_NAV_CONFIRM);
    assert(action.menu.confirming_restart);
    action = activate_modern_tour_action_menu(
        action.menu, context, UR_MODERN_HOST_NAV_BACK);
    assert(!action.menu.confirming_restart);
    assert(action.intent == ModernTourEntryIntent::None);

    // A confirmed Restart uses the same route but carries no restore
    // permission. Even after reaching TRACK_SELECT, retirement remains
    // forbidden until the title-owned stock-row proof is true.
    action = activate_modern_tour_action_menu(
        menu, context, UR_MODERN_HOST_NAV_CONFIRM);
    action = activate_modern_tour_action_menu(
        action.menu, context, UR_MODERN_HOST_NAV_CONFIRM);
    assert(action.intent == ModernTourEntryIntent::Restart);
    const auto restart_decision = resolve_modern_tour_entry(
        context, action.intent, true);
    auto restart = drive_to_track_select(
        begin_modern_tour_entry(4, restart_decision));
    assert(restart.stage == ModernTourContinueStage::Ready);
    assert(restart.intent == ModernTourEntryIntent::Restart);
    assert(!restart.restore_continuation_at_track_select);
    assert(restart.retire_continuation_after_stock_wipe);
    assert(!modern_tour_entry_may_retire_continuation(
        restart_decision, false, true));
    assert(!modern_tour_entry_may_retire_continuation(
        restart_decision, true, false));
    assert(modern_tour_entry_may_retire_continuation(
        restart_decision, true, true));

    // Route failure never manufactures a settlement boundary.
    auto failed = begin_modern_tour_entry(4, resume_decision);
    failed = advance_modern_tour_continue(
        failed, {0xD7, 0, true}).state;
    assert(failed.stage == ModernTourContinueStage::Idle);

    return 0;
}
