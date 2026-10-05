#include "regional_presentation_input_coordinator.hpp"

#include "regional_presentation_input_policy.hpp"

namespace ur::product {

bool RegionalPresentationInputCoordinator::secret_letter(char ch) noexcept {
    if (ch >= 'a' && ch <= 'z') {
        ch = static_cast<char>(ch - 'a' + 'A');
    }
    switch (ch) {
    case 'P':
    case 'A':
    case 'L':
    case 'N':
    case 'T':
    case 'S':
    case 'C':
        return true;
    default:
        return false;
    }
}

std::size_t RegionalPresentationInputCoordinator::action_index(
    RegionalControllerAction action) noexcept {
    switch (action) {
    case RegionalControllerAction::Left: return 0;
    case RegionalControllerAction::Right: return 1;
    case RegionalControllerAction::ShoulderL: return 2;
    case RegionalControllerAction::ShoulderR: return 3;
    case RegionalControllerAction::Accept: return 4;
    case RegionalControllerAction::Other: return 5;
    }
    return 5;
}

RegionalInputDecision RegionalPresentationInputCoordinator::keyboard_key(
    HostProductState& state,
    int key,
    std::uint64_t timestamp_ms,
    RegionalSecretContext context) noexcept {
    char ch = 0;
    if (!regional_secret_keyboard_character(key, ch)) {
        runtime_.reset();
        return {};
    }

    const bool pending_before = runtime_.text_pending();
    const RegionalPresentationUpdate update =
        runtime_.feed_text(state, ch, timestamp_ms, context);
    const bool pending_after = runtime_.text_pending();

    return {
        context.idle_title_surface &&
            (update == RegionalPresentationUpdate::SaveRequired ||
             pending_after ||
             (pending_before && secret_letter(ch))),
        update,
    };
}

RegionalInputDecision RegionalPresentationInputCoordinator::controller_button(
    HostProductState& state,
    RegionalControllerAction action,
    bool pressed,
    std::uint64_t timestamp_ms,
    RegionalSecretContext context) noexcept {
    const std::size_t index = action_index(action);

    if (!pressed) {
        if (index < owned_controller_release_.size() &&
            owned_controller_release_[index]) {
            owned_controller_release_[index] = false;
            return {true, RegionalPresentationUpdate::NoChange};
        }
        return {};
    }

    const bool pending_before = runtime_.controller_pending();
    const RegionalPresentationUpdate update =
        runtime_.feed_controller(state, action, timestamp_ms, context);
    const bool pending_after = runtime_.controller_pending();

    const bool relevant = action != RegionalControllerAction::Other;
    const bool consume =
        context.idle_title_surface &&
        (update == RegionalPresentationUpdate::SaveRequired ||
         pending_after ||
         (pending_before && relevant));

    if (consume && index < owned_controller_release_.size()) {
        owned_controller_release_[index] = true;
    }
    return {consume, update};
}

void RegionalPresentationInputCoordinator::reset() noexcept {
    runtime_.reset();
    owned_controller_release_.fill(false);
}

}  // namespace ur::product
