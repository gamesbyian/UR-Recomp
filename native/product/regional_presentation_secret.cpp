#include "regional_presentation_secret.hpp"

#include <cctype>

namespace ur::product {
namespace {

char ascii_upper(char value) noexcept {
    const unsigned char ch = static_cast<unsigned char>(value);
    if (ch >= static_cast<unsigned char>('a') &&
        ch <= static_cast<unsigned char>('z')) {
        return static_cast<char>(ch - static_cast<unsigned char>('a') +
                                 static_cast<unsigned char>('A'));
    }
    return static_cast<char>(ch);
}

bool text_equals(
    const char* buffer,
    std::size_t size,
    const char* expected,
    std::size_t expected_size) noexcept {
    if (size != expected_size) return false;
    for (std::size_t i = 0; i < size; ++i) {
        if (buffer[i] != expected[i]) return false;
    }
    return true;
}

bool controller_equals(
    const RegionalControllerAction* buffer,
    std::size_t size,
    const RegionalControllerAction* expected,
    std::size_t expected_size) noexcept {
    if (size != expected_size) return false;
    for (std::size_t i = 0; i < size; ++i) {
        if (buffer[i] != expected[i]) return false;
    }
    return true;
}

}  // namespace

bool RegionalPresentationSecretMatcher::context_accepts(
    RegionalSecretContext context) noexcept {
    return context.modern_mode &&
           context.idle_title_surface &&
           !context.text_entry_active;
}

void RegionalPresentationSecretMatcher::reset() noexcept {
    text_size_ = 0;
    text_has_time_ = false;
    controller_size_ = 0;
    controller_has_time_ = false;
}

void RegionalPresentationSecretMatcher::expire_text(
    std::uint64_t timestamp_ms) noexcept {
    if (!text_has_time_) return;
    if (timestamp_ms < text_last_ms_ ||
        timestamp_ms - text_last_ms_ > input_timeout_ms) {
        text_size_ = 0;
        text_has_time_ = false;
    }
}

void RegionalPresentationSecretMatcher::expire_controller(
    std::uint64_t timestamp_ms) noexcept {
    if (!controller_has_time_) return;
    if (timestamp_ms < controller_last_ms_ ||
        timestamp_ms - controller_last_ms_ > input_timeout_ms) {
        controller_size_ = 0;
        controller_has_time_ = false;
    }
}

RegionalSecretResult RegionalPresentationSecretMatcher::apply_match(
    RegionalPresentation presentation) noexcept {
    reset();
    if (current_ == presentation) {
        return RegionalSecretResult::AlreadySelected;
    }
    current_ = presentation;
    return RegionalSecretResult::Switched;
}

RegionalSecretResult RegionalPresentationSecretMatcher::feed_text(
    char character,
    std::uint64_t timestamp_ms,
    RegionalSecretContext context) noexcept {
    if (!context_accepts(context)) {
        reset();
        return RegionalSecretResult::NoMatch;
    }

    expire_text(timestamp_ms);

    const char normalized = ascii_upper(character);
    if (normalized < 'A' || normalized > 'Z') {
        text_size_ = 0;
        text_has_time_ = false;
        return RegionalSecretResult::NoMatch;
    }

    if (text_size_ == 4) {
        for (std::size_t i = 1; i < 4; ++i) {
            text_[i - 1] = text_[i];
        }
        text_size_ = 3;
    }
    text_[text_size_++] = normalized;
    text_last_ms_ = timestamp_ms;
    text_has_time_ = true;

    if (text_equals(text_, text_size_, "PAL", 3)) {
        return apply_match(RegionalPresentation::Europe);
    }
    if (text_equals(text_, text_size_, "NTSC", 4)) {
        return apply_match(RegionalPresentation::NorthAmerica);
    }

    // Preserve only suffixes that can still become PAL or NTSC.
    std::size_t keep = 0;
    for (std::size_t candidate = 1; candidate <= text_size_; ++candidate) {
        const std::size_t start = text_size_ - candidate;
        bool pal_prefix = candidate <= 3;
        bool ntsc_prefix = candidate <= 4;
        for (std::size_t i = 0; i < candidate && pal_prefix; ++i) {
            pal_prefix = text_[start + i] == "PAL"[i];
        }
        for (std::size_t i = 0; i < candidate && ntsc_prefix; ++i) {
            ntsc_prefix = text_[start + i] == "NTSC"[i];
        }
        if (pal_prefix || ntsc_prefix) keep = candidate;
    }
    if (keep != text_size_) {
        const std::size_t start = text_size_ - keep;
        for (std::size_t i = 0; i < keep; ++i) {
            text_[i] = text_[start + i];
        }
        text_size_ = keep;
    }

    return RegionalSecretResult::NoMatch;
}

RegionalSecretResult RegionalPresentationSecretMatcher::feed_controller(
    RegionalControllerAction action,
    std::uint64_t timestamp_ms,
    RegionalSecretContext context) noexcept {
    if (!context_accepts(context)) {
        reset();
        return RegionalSecretResult::NoMatch;
    }

    expire_controller(timestamp_ms);

    if (action == RegionalControllerAction::Other) {
        controller_size_ = 0;
        controller_has_time_ = false;
        return RegionalSecretResult::NoMatch;
    }

    if (controller_size_ == 5) {
        for (std::size_t i = 1; i < 5; ++i) {
            controller_[i - 1] = controller_[i];
        }
        controller_size_ = 4;
    }
    controller_[controller_size_++] = action;
    controller_last_ms_ = timestamp_ms;
    controller_has_time_ = true;

    static constexpr RegionalControllerAction kEurope[] = {
        RegionalControllerAction::Left,
        RegionalControllerAction::Left,
        RegionalControllerAction::Left,
        RegionalControllerAction::ShoulderL,
        RegionalControllerAction::Accept,
    };
    static constexpr RegionalControllerAction kNorthAmerica[] = {
        RegionalControllerAction::Right,
        RegionalControllerAction::Right,
        RegionalControllerAction::Right,
        RegionalControllerAction::ShoulderR,
        RegionalControllerAction::Accept,
    };

    if (controller_equals(controller_, controller_size_, kEurope, 5)) {
        return apply_match(RegionalPresentation::Europe);
    }
    if (controller_equals(controller_, controller_size_, kNorthAmerica, 5)) {
        return apply_match(RegionalPresentation::NorthAmerica);
    }

    // As with keyboard text, retain only a suffix that is still a valid
    // prefix of one of the two controller secrets. This permits immediate
    // recovery from an unrelated/wrong first direction without consuming it.
    std::size_t keep = 0;
    for (std::size_t candidate = 1; candidate <= controller_size_; ++candidate) {
        const std::size_t start = controller_size_ - candidate;
        bool europe_prefix = candidate <= 5;
        bool north_america_prefix = candidate <= 5;
        for (std::size_t i = 0; i < candidate && europe_prefix; ++i) {
            europe_prefix = controller_[start + i] == kEurope[i];
        }
        for (std::size_t i = 0; i < candidate && north_america_prefix; ++i) {
            north_america_prefix =
                controller_[start + i] == kNorthAmerica[i];
        }
        if (europe_prefix || north_america_prefix) keep = candidate;
    }
    if (keep != controller_size_) {
        const std::size_t start = controller_size_ - keep;
        for (std::size_t i = 0; i < keep; ++i) {
            controller_[i] = controller_[start + i];
        }
        controller_size_ = keep;
    }

    return RegionalSecretResult::NoMatch;
}

}  // namespace ur::product
