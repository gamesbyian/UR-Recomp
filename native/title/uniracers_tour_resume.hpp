#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>

namespace ur::title {

constexpr std::size_t kTourTrackCount = 5;

struct TourProgress {
    std::uint8_t rider_index = 0;
    std::uint8_t tour_row = 0;
    std::uint8_t medal_value = 0;
    std::array<std::uint8_t, kTourTrackCount> qualified{};

    bool operator==(const TourProgress& other) const noexcept {
        return rider_index == other.rider_index &&
               tour_row == other.tour_row &&
               medal_value == other.medal_value &&
               qualified == other.qualified;
    }
};

enum class TourResumeApplyStatus : std::uint8_t {
    Applied = 0,
    AlreadyPresent = 1,
    InvalidState = 2,
    ContextMismatch = 3,
    MedalMismatch = 4,
    ExistingProgress = 5,
};

bool valid_unfinished_tour_progress(const TourProgress& value) noexcept;

bool tour_resume_source_matches_sram(
    const TourProgress& continuation,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept;

bool tour_resume_frontend_source_matches_sram(
    const TourProgress& continuation,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept;

bool tour_qualification_row_empty(
    std::uint8_t tour_row,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept;

std::optional<TourProgress> observe_tour_progress(
    const std::uint8_t* wram,
    std::size_t wram_size,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept;

TourResumeApplyStatus apply_tour_resume(
    const TourProgress& continuation,
    const std::uint8_t* wram,
    std::size_t wram_size,
    std::uint8_t* sram,
    std::size_t sram_size) noexcept;

}  // namespace ur::title
