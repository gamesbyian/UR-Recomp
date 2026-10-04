#include "uniracers_tour_resume.hpp"

namespace ur::title {
namespace {

constexpr std::size_t kWramTourRow = 0x00D0;
constexpr std::size_t kWramRiderIndex = 0x017D;
constexpr std::size_t kSramMedalBase = 0x069C;
constexpr std::size_t kSramTourFlagsBase = 0x1075;
constexpr std::size_t kSramPlayMode = 0x10AD;
constexpr std::uint8_t kTourPlayMode = 1;
constexpr std::size_t kRiderCount = 16;
constexpr std::size_t kTourCount = 9;

std::size_t medal_offset(std::uint8_t rider, std::uint8_t tour) noexcept {
    return kSramMedalBase +
           static_cast<std::size_t>(tour) * kRiderCount +
           static_cast<std::size_t>(rider);
}

std::size_t flags_offset(std::uint8_t tour) noexcept {
    return kSramTourFlagsBase +
           static_cast<std::size_t>(tour) * kTourTrackCount;
}

unsigned qualified_count(
    const std::array<std::uint8_t, kTourTrackCount>& flags) noexcept {
    unsigned count = 0;
    for (const auto flag : flags) {
        if (flag > 1) return kTourTrackCount + 1;
        count += flag;
    }
    return count;
}

}  // namespace

bool valid_unfinished_tour_progress(const TourProgress& value) noexcept {
    if (value.rider_index >= kRiderCount ||
        value.tour_row >= kTourCount ||
        value.medal_value > 3) {
        return false;
    }
    const unsigned count = qualified_count(value.qualified);
    return count > 0 && count < kTourTrackCount;
}

std::optional<TourProgress> observe_tour_progress(
    const std::uint8_t* wram,
    std::size_t wram_size,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept {
    if (!wram || !sram ||
        wram_size <= kWramRiderIndex ||
        sram_size <= kSramPlayMode) {
        return std::nullopt;
    }
    if (sram[kSramPlayMode] != kTourPlayMode) {
        return std::nullopt;
    }

    TourProgress out;
    out.rider_index = wram[kWramRiderIndex];
    out.tour_row = wram[kWramTourRow];
    if (out.rider_index >= kRiderCount || out.tour_row >= kTourCount) {
        return std::nullopt;
    }

    const auto medal = medal_offset(out.rider_index, out.tour_row);
    const auto flags = flags_offset(out.tour_row);
    if (medal >= sram_size || flags + kTourTrackCount > sram_size) {
        return std::nullopt;
    }

    out.medal_value = sram[medal];
    for (std::size_t i = 0; i < kTourTrackCount; ++i) {
        out.qualified[i] = sram[flags + i];
        if (out.qualified[i] > 1) return std::nullopt;
    }
    if (out.medal_value > 3) return std::nullopt;
    return out;
}

TourResumeApplyStatus apply_tour_resume(
    const TourProgress& continuation,
    const std::uint8_t* wram,
    std::size_t wram_size,
    std::uint8_t* sram,
    std::size_t sram_size) noexcept {
    if (!valid_unfinished_tour_progress(continuation)) {
        return TourResumeApplyStatus::InvalidState;
    }

    const auto current =
        observe_tour_progress(wram, wram_size, sram, sram_size);
    if (!current) return TourResumeApplyStatus::InvalidState;

    if (current->rider_index != continuation.rider_index ||
        current->tour_row != continuation.tour_row) {
        return TourResumeApplyStatus::ContextMismatch;
    }
    if (current->medal_value != continuation.medal_value) {
        return TourResumeApplyStatus::MedalMismatch;
    }
    if (current->qualified == continuation.qualified) {
        return TourResumeApplyStatus::AlreadyPresent;
    }
    if (qualified_count(current->qualified) != 0) {
        return TourResumeApplyStatus::ExistingProgress;
    }

    const auto flags = flags_offset(continuation.tour_row);
    for (std::size_t i = 0; i < kTourTrackCount; ++i) {
        sram[flags + i] = continuation.qualified[i];
    }
    return TourResumeApplyStatus::Applied;
}

}  // namespace ur::title
