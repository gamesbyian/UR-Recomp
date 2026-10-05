#pragma once

#include "uniracers_challenge_generation.hpp"

#include <cstddef>
#include <cstdint>

namespace ur::title {

enum class ChallengeGenerationArmStatus : std::uint8_t {
    Armed = 0,
    InvalidRequest = 1,
    InvalidBuffers = 2,
    AlreadyArmed = 3,
};

ChallengeGenerationArmStatus arm_challenge_generation_override(
    const ChallengeGenerationRequest& request,
    const std::uint8_t* wram,
    std::size_t wram_size,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept;

void clear_challenge_generation_override() noexcept;

bool challenge_generation_override_active() noexcept;

ChallengeGenerationStatus
challenge_generation_override_last_status() noexcept;

}  // namespace ur::title
