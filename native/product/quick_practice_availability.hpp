#pragma once

#include "quick_practice_catalog.hpp"
#include "quick_practice_picker.hpp"

#include <cstdint>

namespace ur::product {

struct QuickPracticeAvailability {
    std::uint64_t track_bits = 0;
};

constexpr QuickPracticeAvailability quick_practice_no_tracks() noexcept {
    return {};
}

constexpr QuickPracticeAvailability quick_practice_all_tracks() noexcept {
    return {(std::uint64_t{1} << 45) - 1};
}

constexpr QuickPracticeAvailability quick_practice_normal_tours_only() noexcept {
    // Tracks 0..39 are the eight normal tours. Hunter (40..44) stays hidden
    // unless the caller deliberately marks it available.
    return {(std::uint64_t{1} << 40) - 1};
}


constexpr bool quick_practice_track_available(
    QuickPracticeAvailability availability,
    std::uint8_t track_id
) noexcept {
    return track_id < 45 &&
        (availability.track_bits & (std::uint64_t{1} << track_id)) != 0;
}

constexpr QuickPracticeAvailability quick_practice_set_track_available(
    QuickPracticeAvailability availability,
    std::uint8_t track_id,
    bool available
) noexcept {
    if (track_id >= 45) return availability;
    const auto bit = std::uint64_t{1} << track_id;
    if (available) availability.track_bits |= bit;
    else availability.track_bits &= ~bit;
    return availability;
}

constexpr QuickPracticeAvailability quick_practice_availability_from_tour_options(
    std::uint16_t visible_tour_options
) noexcept {
    QuickPracticeAvailability availability{};
    for (std::size_t block = 0; block < kQuickPracticeTourOptions.size(); ++block) {
        const auto option = kQuickPracticeTourOptions[block];
        if ((visible_tour_options & (std::uint16_t{1} << option)) == 0) {
            continue;
        }
        for (std::uint8_t slot = 0; slot < 5; ++slot) {
            const auto track = static_cast<std::uint8_t>(block * 5 + slot);
            availability = quick_practice_set_track_available(
                availability, track, true);
        }
    }
    return availability;
}

constexpr int quick_practice_available_count(
    QuickPracticeAvailability availability
) noexcept {
    int count = 0;
    for (std::uint8_t i = 0; i < 45; ++i) {
        if (quick_practice_track_available(availability, i)) ++count;
    }
    return count;
}

constexpr QuickPracticePickerState quick_practice_normalize_available_picker(
    QuickPracticePickerState state,
    QuickPracticeAvailability availability
) noexcept {
    if (quick_practice_track_available(availability, state.track_id)) {
        return state;
    }
    for (std::uint8_t i = 0; i < 45; ++i) {
        if (quick_practice_track_available(availability, i)) {
            state.track_id = i;
            return state;
        }
    }
    state.track_id = 0;
    return state;
}

constexpr QuickPracticePickerState quick_practice_available_course_step(
    QuickPracticePickerState state,
    QuickPracticeAvailability availability,
    int direction
) noexcept {
    state = quick_practice_normalize_available_picker(state, availability);
    if (quick_practice_available_count(availability) == 0 || direction == 0) {
        return state;
    }
    const int delta = direction > 0 ? 1 : -1;
    auto candidate = state.track_id;
    for (int i = 0; i < 45; ++i) {
        candidate = quick_practice_wrap_track(
            static_cast<int>(candidate) + delta);
        if (quick_practice_track_available(availability, candidate)) {
            state.track_id = candidate;
            return state;
        }
    }
    return state;
}

constexpr bool quick_practice_picker_launchable(
    QuickPracticePickerState state,
    QuickPracticeAvailability availability
) noexcept {
    return quick_practice_track_available(availability, state.track_id) &&
        quick_practice_picker_target(state).valid;
}

}  // namespace ur::product
