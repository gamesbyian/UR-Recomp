#pragma once

#include "uniracers_challenge_award.hpp"
#include "uniracers_challenge_qualification.hpp"

#include <cstddef>
#include <cstdint>

namespace ur::title {

enum class ChallengeCompletionArmStatus : std::uint8_t {
    Armed = 0,
    InvalidQualificationRequest = 1,
    InvalidAwardRequest = 2,
    InvalidBuffers = 3,
    AlreadyArmed = 4,
};

ChallengeCompletionArmStatus arm_challenge_completion_overrides(
    const ChallengeQualificationRequest& qualification,
    const ChallengeAwardRequest* award,
    const std::uint8_t* wram,
    std::size_t wram_size,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept;

void clear_challenge_completion_overrides() noexcept;

bool challenge_completion_overrides_active() noexcept;

ChallengeQualificationStatus
challenge_completion_last_qualification_status() noexcept;

ChallengeAwardStatus
challenge_completion_last_award_status() noexcept;

}  // namespace ur::title
