#include "regional_presentation_runtime.hpp"

namespace ur::product {

void RegionalPresentationRuntime::reconcile_external_state(
    const HostProductState& state) noexcept {
    if (matcher_.current() != state.regional_presentation) {
        matcher_.set_current(state.regional_presentation);
    }
}

RegionalPresentationUpdate RegionalPresentationRuntime::apply_result(
    HostProductState& state,
    RegionalSecretResult result) noexcept {
    if (result != RegionalSecretResult::Switched) {
        return RegionalPresentationUpdate::NoChange;
    }
    state.regional_presentation = matcher_.current();
    return RegionalPresentationUpdate::SaveRequired;
}

RegionalPresentationUpdate RegionalPresentationRuntime::feed_text(
    HostProductState& state,
    char character,
    std::uint64_t timestamp_ms,
    RegionalSecretContext context) noexcept {
    reconcile_external_state(state);
    return apply_result(
        state,
        matcher_.feed_text(character, timestamp_ms, context));
}

RegionalPresentationUpdate RegionalPresentationRuntime::feed_controller(
    HostProductState& state,
    RegionalControllerAction action,
    std::uint64_t timestamp_ms,
    RegionalSecretContext context) noexcept {
    reconcile_external_state(state);
    return apply_result(
        state,
        matcher_.feed_controller(action, timestamp_ms, context));
}

}  // namespace ur::product
