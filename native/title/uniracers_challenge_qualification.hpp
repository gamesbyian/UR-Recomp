#pragma once

#include <cstddef>
#include <cstdint>

namespace ur::title {

struct ChallengeQualificationRequest {
    std::uint8_t rider_index = 0;
    std::uint8_t tour_row = 0;
    std::uint8_t expected_persisted_medal = 0;
    std::uint8_t selected_generation = 0;
};

enum class ChallengeQualificationStatus : std::uint8_t {
    Applied = 0,
    NoOverride = 1,
    InvalidRequest = 2,
    InvalidContext = 3,
    MedalMismatch = 4,
    StockGenerationMismatch = 5,
};

struct ChallengeQualificationDecision {
    ChallengeQualificationStatus status =
        ChallengeQualificationStatus::InvalidRequest;
    std::uint8_t generation = 0;

    bool applied() const noexcept {
        return status == ChallengeQualificationStatus::Applied;
    }
};

bool valid_challenge_qualification_request(
    const ChallengeQualificationRequest& request) noexcept;

ChallengeQualificationDecision resolve_stunt_qualification_generation(
    const ChallengeQualificationRequest* request,
    std::uint8_t stock_generation,
    const std::uint8_t* wram,
    std::size_t wram_size,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept;

}  // namespace ur::title
