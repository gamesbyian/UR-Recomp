#include "regional_presentation_secret.hpp"

#include <cassert>

using namespace ur::product;

namespace {

constexpr RegionalSecretContext kModernTitle{true, true, false};
constexpr RegionalSecretContext kAuthenticTitle{false, true, false};
constexpr RegionalSecretContext kModernElsewhere{true, false, false};
constexpr RegionalSecretContext kModernTextEntry{true, true, true};

RegionalSecretResult type(
    RegionalPresentationSecretMatcher& matcher,
    const char* text,
    std::uint64_t start_ms,
    std::uint64_t step_ms,
    RegionalSecretContext context = kModernTitle) {
    RegionalSecretResult result = RegionalSecretResult::NoMatch;
    for (std::size_t i = 0; text[i] != '\0'; ++i) {
        result = matcher.feed_text(
            text[i], start_ms + static_cast<std::uint64_t>(i) * step_ms,
            context);
    }
    return result;
}

RegionalSecretResult press(
    RegionalPresentationSecretMatcher& matcher,
    const RegionalControllerAction* actions,
    std::size_t count,
    std::uint64_t start_ms,
    std::uint64_t step_ms,
    RegionalSecretContext context = kModernTitle) {
    RegionalSecretResult result = RegionalSecretResult::NoMatch;
    for (std::size_t i = 0; i < count; ++i) {
        result = matcher.feed_controller(
            actions[i], start_ms + static_cast<std::uint64_t>(i) * step_ms,
            context);
    }
    return result;
}

}  // namespace

int main() {
    RegionalPresentationSecretMatcher matcher;
    assert(matcher.current() == RegionalPresentation::NorthAmerica);

    // Keyboard recognition is case-insensitive.
    assert(type(matcher, "pal", 100, 100) == RegionalSecretResult::Switched);
    assert(matcher.current() == RegionalPresentation::Europe);
    assert(type(matcher, "PAL", 1000, 100) ==
           RegionalSecretResult::AlreadySelected);
    assert(type(matcher, "nTsC", 2000, 100) == RegionalSecretResult::Switched);
    assert(matcher.current() == RegionalPresentation::NorthAmerica);

    // Wrong-prefix text recovers through suffix matching.
    assert(type(matcher, "XXPAL", 3000, 50) == RegionalSecretResult::Switched);
    assert(matcher.current() == RegionalPresentation::Europe);

    // A timeout destroys a partial sequence.
    matcher.set_current(RegionalPresentation::NorthAmerica);
    assert(matcher.feed_text('P', 4000, kModernTitle) ==
           RegionalSecretResult::NoMatch);
    assert(matcher.feed_text(
        'A', 4000 + RegionalPresentationSecretMatcher::input_timeout_ms + 1,
        kModernTitle) == RegionalSecretResult::NoMatch);
    assert(matcher.feed_text('L', 5600, kModernTitle) ==
           RegionalSecretResult::NoMatch);
    assert(matcher.current() == RegionalPresentation::NorthAmerica);

    // Invalid contexts reset partial progress and never switch.
    assert(matcher.feed_text('P', 6000, kModernTitle) ==
           RegionalSecretResult::NoMatch);
    assert(matcher.feed_text('A', 6100, kAuthenticTitle) ==
           RegionalSecretResult::NoMatch);
    assert(matcher.feed_text('L', 6200, kModernTitle) ==
           RegionalSecretResult::NoMatch);
    assert(matcher.current() == RegionalPresentation::NorthAmerica);
    assert(type(matcher, "PAL", 7000, 50, kModernElsewhere) ==
           RegionalSecretResult::NoMatch);
    assert(type(matcher, "PAL", 8000, 50, kModernTextEntry) ==
           RegionalSecretResult::NoMatch);

    static constexpr RegionalControllerAction kPal[] = {
        RegionalControllerAction::Left,
        RegionalControllerAction::Left,
        RegionalControllerAction::Left,
        RegionalControllerAction::ShoulderL,
        RegionalControllerAction::Accept,
    };
    static constexpr RegionalControllerAction kNtsc[] = {
        RegionalControllerAction::Right,
        RegionalControllerAction::Right,
        RegionalControllerAction::Right,
        RegionalControllerAction::ShoulderR,
        RegionalControllerAction::Accept,
    };

    assert(press(matcher, kPal, 5, 9000, 100) ==
           RegionalSecretResult::Switched);
    assert(matcher.current() == RegionalPresentation::Europe);
    assert(press(matcher, kPal, 5, 10000, 100) ==
           RegionalSecretResult::AlreadySelected);
    assert(press(matcher, kNtsc, 5, 11000, 100) ==
           RegionalSecretResult::Switched);
    assert(matcher.current() == RegionalPresentation::NorthAmerica);

    // A wrong leading action does not prevent a later valid suffix.
    static constexpr RegionalControllerAction kRecover[] = {
        RegionalControllerAction::Left,
        RegionalControllerAction::Right,
        RegionalControllerAction::Right,
        RegionalControllerAction::Right,
        RegionalControllerAction::ShoulderR,
        RegionalControllerAction::Accept,
    };
    assert(press(matcher, kRecover, 6, 12000, 50) ==
           RegionalSecretResult::AlreadySelected);

    // Other input explicitly resets a partial controller secret.
    matcher.feed_controller(
        RegionalControllerAction::Left, 13000, kModernTitle);
    matcher.feed_controller(
        RegionalControllerAction::Left, 13100, kModernTitle);
    matcher.feed_controller(
        RegionalControllerAction::Other, 13200, kModernTitle);
    matcher.feed_controller(
        RegionalControllerAction::Left, 13300, kModernTitle);
    matcher.feed_controller(
        RegionalControllerAction::ShoulderL, 13400, kModernTitle);
    assert(matcher.feed_controller(
        RegionalControllerAction::Accept, 13500, kModernTitle) ==
        RegionalSecretResult::NoMatch);
    assert(matcher.current() == RegionalPresentation::NorthAmerica);

    // Controller timeout is deterministic and cannot complete stale input.
    matcher.feed_controller(
        RegionalControllerAction::Left, 14000, kModernTitle);
    matcher.feed_controller(
        RegionalControllerAction::Left, 14100, kModernTitle);
    assert(matcher.feed_controller(
        RegionalControllerAction::Left,
        14100 + RegionalPresentationSecretMatcher::input_timeout_ms + 1,
        kModernTitle) == RegionalSecretResult::NoMatch);
    matcher.feed_controller(
        RegionalControllerAction::ShoulderL, 16000, kModernTitle);
    assert(matcher.feed_controller(
        RegionalControllerAction::Accept, 16100, kModernTitle) ==
        RegionalSecretResult::NoMatch);

    // Explicitly loading persisted state does not synthesize a secret event.
    matcher.set_current(RegionalPresentation::Europe);
    assert(matcher.current() == RegionalPresentation::Europe);
    matcher.reset();
    assert(matcher.current() == RegionalPresentation::Europe);

    return 0;
}
