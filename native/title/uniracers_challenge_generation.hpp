#pragma once

#include <cstddef>
#include <cstdint>

namespace ur::title {

struct ChallengeGenerationRequest {
    std::uint8_t rider_index = 0;
    std::uint8_t tour_row = 0;
    std::uint8_t expected_persisted_medal = 0;
    std::uint8_t selected_generation = 0;
};

enum class ChallengeGenerationStatus : std::uint8_t {
    Applied = 0,
    NoOverride = 1,
    InvalidRequest = 2,
    InvalidContext = 3,
    MedalMismatch = 4,
    StockGenerationMismatch = 5,
};

struct ChallengeGenerationDecision {
    ChallengeGenerationStatus status =
        ChallengeGenerationStatus::InvalidRequest;
    std::uint8_t generation = 0;

    bool applied() const noexcept {
        return status == ChallengeGenerationStatus::Applied;
    }
};

bool valid_challenge_generation_request(
    const ChallengeGenerationRequest& request) noexcept;

ChallengeGenerationDecision resolve_challenge_generation_snapshot(
    const ChallengeGenerationRequest* request,
    std::uint8_t stock_generation,
    const std::uint8_t* wram,
    std::size_t wram_size,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept;

}  // namespace ur::title
