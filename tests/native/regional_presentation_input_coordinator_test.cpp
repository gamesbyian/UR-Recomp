#include "regional_presentation_input_coordinator.hpp"

#include <cassert>

using namespace ur::product;

namespace {

constexpr RegionalSecretContext kTitle{true, true, false};
constexpr RegionalSecretContext kElsewhere{true, false, false};

}  // namespace

int main() {
    HostProductState state;
    RegionalPresentationInputCoordinator input(state);

    // Unrelated title keys remain guest-owned.
    auto d = input.keyboard_key(state, 'X', 0, kTitle);
    assert(!d.consume);
    assert(d.update == RegionalPresentationUpdate::NoChange);

    // PAL candidate letters are owned once a sequence starts.
    d = input.keyboard_key(state, 'P', 100, kTitle);
    assert(d.consume);
    d = input.keyboard_key(state, 'A', 200, kTitle);
    assert(d.consume);
    d = input.keyboard_key(state, 'L', 300, kTitle);
    assert(d.consume);
    assert(d.update == RegionalPresentationUpdate::SaveRequired);
    assert(state.regional_presentation == RegionalPresentation::Europe);

    // Same-region secret is recognized but does not require another save.
    d = input.keyboard_key(state, 'P', 400, kTitle);
    assert(d.consume);
    d = input.keyboard_key(state, 'A', 500, kTitle);
    assert(d.consume);
    d = input.keyboard_key(state, 'L', 600, kTitle);
    assert(!d.consume || d.update == RegionalPresentationUpdate::NoChange);
    assert(state.regional_presentation == RegionalPresentation::Europe);

    // Off-title input never becomes product-owned.
    d = input.keyboard_key(state, 'N', 700, kElsewhere);
    assert(!d.consume);

    // Controller A alone remains ordinary title input.
    d = input.controller_button(
        state, RegionalControllerAction::Accept, true, 1000, kTitle);
    assert(!d.consume);
    d = input.controller_button(
        state, RegionalControllerAction::Accept, false, 1010, kTitle);
    assert(!d.consume);

    // Candidate direction presses and their releases are paired and consumed.
    for (int i = 0; i < 3; ++i) {
        d = input.controller_button(
            state, RegionalControllerAction::Right, true,
            1100 + static_cast<std::uint64_t>(i) * 100, kTitle);
        assert(d.consume);
        d = input.controller_button(
            state, RegionalControllerAction::Right, false,
            1150 + static_cast<std::uint64_t>(i) * 100, kTitle);
        assert(d.consume);
    }
    d = input.controller_button(
        state, RegionalControllerAction::ShoulderR, true, 1400, kTitle);
    assert(d.consume);
    assert(input.controller_button(
        state, RegionalControllerAction::ShoulderR, false, 1450, kTitle).consume);
    d = input.controller_button(
        state, RegionalControllerAction::Accept, true, 1500, kTitle);
    assert(d.consume);
    assert(d.update == RegionalPresentationUpdate::SaveRequired);
    assert(state.regional_presentation == RegionalPresentation::NorthAmerica);
    assert(input.controller_button(
        state, RegionalControllerAction::Accept, false, 1550, kTitle).consume);

    // A wrong unrelated action resets a partial code without swallowing it.
    assert(input.controller_button(
        state, RegionalControllerAction::Left, true, 2000, kTitle).consume);
    assert(input.controller_button(
        state, RegionalControllerAction::Left, false, 2010, kTitle).consume);
    d = input.controller_button(
        state, RegionalControllerAction::Other, true, 2100, kTitle);
    assert(!d.consume);

    return 0;
}
