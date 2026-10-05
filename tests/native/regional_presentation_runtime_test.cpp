#include "regional_presentation_runtime.hpp"

#include <cassert>
#include <string>

using namespace ur::product;

namespace {

constexpr RegionalSecretContext kModernTitle{true, true, false};
constexpr RegionalSecretContext kAuthenticTitle{false, true, false};

RegionalPresentationUpdate type(
    RegionalPresentationRuntime& runtime,
    HostProductState& state,
    const char* text,
    std::uint64_t start_ms) {
    RegionalPresentationUpdate update = RegionalPresentationUpdate::NoChange;
    for (std::size_t i = 0; text[i] != '\0'; ++i) {
        update = runtime.feed_text(
            state, text[i], start_ms + static_cast<std::uint64_t>(i) * 100,
            kModernTitle);
    }
    return update;
}

}  // namespace

int main() {
    HostProductState state;
    state.active_profile_id = "alpha";
    state.settings.pause_on_focus_loss = false;
    const HostSettings original_settings = state.settings;

    RegionalPresentationRuntime runtime(state);
    assert(runtime.current() == RegionalPresentation::NorthAmerica);

    // Partial input never asks the store to write.
    assert(runtime.feed_text(state, 'P', 100, kModernTitle) ==
           RegionalPresentationUpdate::NoChange);
    assert(state.regional_presentation == RegionalPresentation::NorthAmerica);

    // A completed secret changes only the global regional field.
    assert(type(runtime, state, "PAL", 1000) ==
           RegionalPresentationUpdate::SaveRequired);
    assert(state.regional_presentation == RegionalPresentation::Europe);
    assert(state.active_profile_id &&
           *state.active_profile_id == std::string("alpha"));
    assert(state.settings == original_settings);

    // Re-entering the active secret is a no-op and should not cause disk churn.
    assert(type(runtime, state, "PAL", 2000) ==
           RegionalPresentationUpdate::NoChange);
    assert(state.regional_presentation == RegionalPresentation::Europe);

    // Authentic context cannot alter even a persisted Modern preference.
    assert(runtime.feed_text(state, 'N', 3000, kAuthenticTitle) ==
           RegionalPresentationUpdate::NoChange);
    assert(runtime.feed_text(state, 'T', 3100, kAuthenticTitle) ==
           RegionalPresentationUpdate::NoChange);
    assert(runtime.feed_text(state, 'S', 3200, kAuthenticTitle) ==
           RegionalPresentationUpdate::NoChange);
    assert(runtime.feed_text(state, 'C', 3300, kAuthenticTitle) ==
           RegionalPresentationUpdate::NoChange);
    assert(state.regional_presentation == RegionalPresentation::Europe);

    // New runtime instances start from the durable host-state choice.
    RegionalPresentationRuntime reloaded(state);
    assert(reloaded.current() == RegionalPresentation::Europe);
    assert(type(reloaded, state, "NTSC", 4000) ==
           RegionalPresentationUpdate::SaveRequired);
    assert(state.regional_presentation == RegionalPresentation::NorthAmerica);

    // Controller path uses the same state/persistence authority.
    static constexpr RegionalControllerAction kPal[] = {
        RegionalControllerAction::Left,
        RegionalControllerAction::Left,
        RegionalControllerAction::Left,
        RegionalControllerAction::ShoulderL,
        RegionalControllerAction::Accept,
    };
    RegionalPresentationUpdate update = RegionalPresentationUpdate::NoChange;
    for (std::size_t i = 0; i < 5; ++i) {
        update = reloaded.feed_controller(
            state, kPal[i], 5000 + static_cast<std::uint64_t>(i) * 100,
            kModernTitle);
    }
    assert(update == RegionalPresentationUpdate::SaveRequired);
    assert(state.regional_presentation == RegionalPresentation::Europe);

    // External host-state replacement is authoritative and resets matcher state.
    state.regional_presentation = RegionalPresentation::NorthAmerica;
    assert(reloaded.feed_text(state, 'P', 6000, kModernTitle) ==
           RegionalPresentationUpdate::NoChange);
    assert(reloaded.current() == RegionalPresentation::NorthAmerica);

    return 0;
}
