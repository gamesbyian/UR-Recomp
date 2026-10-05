#pragma once

#include <cstddef>
#include <cstdint>

namespace ur::title {

enum class ChallengeGenerationApplyStatus : std::uint8_t {
    Applied = 0,
    AlreadySelected = 1,
    InvalidState = 2,
    ContextMismatch = 3,
    MedalMismatch = 4,
    SnapshotMismatch = 5,
    UnsupportedHunter = 6,
};

ChallengeGenerationApplyStatus apply_challenge_generation(
    std::uint8_t expected_persisted_medal,
    std::uint8_t selected_generation,
    const std::uint8_t* wram,
    std::size_t wram_size,
    std::uint8_t* sram,
    std::size_t sram_size) noexcept;

}  // namespace ur::title
