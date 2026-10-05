#pragma once

#include <cstddef>
#include <cstdint>

#include "regional_presentation.hpp"

namespace ur::product {

enum class RegionalControllerAction : std::uint8_t {
    Left = 0,
    Right = 1,
    ShoulderL = 2,
    ShoulderR = 3,
    Accept = 4,
    Other = 5,
};

enum class RegionalSecretResult : std::uint8_t {
    NoMatch = 0,
    Switched = 1,
    AlreadySelected = 2,
};

struct RegionalSecretContext {
    bool modern_mode = false;
    bool idle_title_surface = false;
    bool text_entry_active = false;
};

/*
 * Pure regional-presentation secret recognizer.
 *
 * Platform adapters translate physical keyboard/controller events into text
 * characters or RegionalControllerAction values before calling this class.
 * The matcher owns no SDL/platform concepts and never mutates guest state.
 */
class RegionalPresentationSecretMatcher {
public:
    static constexpr std::uint64_t input_timeout_ms = 1500;

    RegionalPresentation current() const noexcept { return current_; }
    bool text_pending() const noexcept { return text_size_ != 0; }
    bool controller_pending() const noexcept { return controller_size_ != 0; }
    void set_current(RegionalPresentation presentation) noexcept {
        current_ = presentation;
        reset();
    }

    RegionalSecretResult feed_text(
        char character,
        std::uint64_t timestamp_ms,
        RegionalSecretContext context) noexcept;

    RegionalSecretResult feed_controller(
        RegionalControllerAction action,
        std::uint64_t timestamp_ms,
        RegionalSecretContext context) noexcept;

    void reset() noexcept;

private:
    static bool context_accepts(RegionalSecretContext context) noexcept;
    RegionalSecretResult apply_match(RegionalPresentation presentation) noexcept;
    void expire_text(std::uint64_t timestamp_ms) noexcept;
    void expire_controller(std::uint64_t timestamp_ms) noexcept;

    RegionalPresentation current_ = RegionalPresentation::NorthAmerica;

    char text_[4]{};
    std::size_t text_size_ = 0;
    std::uint64_t text_last_ms_ = 0;
    bool text_has_time_ = false;

    RegionalControllerAction controller_[5]{};
    std::size_t controller_size_ = 0;
    std::uint64_t controller_last_ms_ = 0;
    bool controller_has_time_ = false;
};

}  // namespace ur::product
