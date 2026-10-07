#pragma once

#include <cstddef>
#include <cstdint>

#include "regional_presentation.hpp"

namespace ur::product {

enum class RegionalTitlePresentationResult : std::uint8_t {
    Canonical = 0,
    EuropeApplied = 1,
    FailedClosed = 2,
};

RegionalTitlePresentationResult apply_regional_title_presentation(
    RegionalPresentation presentation,
    bool idle_title_surface,
    std::uint8_t* pixels,
    std::size_t pitch,
    int width,
    int height,
    int presentation_scale = 1) noexcept;

std::uint64_t regional_title_visible_crop_digest(
    const std::uint8_t* pixels,
    std::size_t pitch,
    int width,
    int height,
    int presentation_scale = 1) noexcept;

}  // namespace ur::product
