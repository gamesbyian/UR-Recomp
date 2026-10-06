#pragma once

#include <cstddef>
#include <cstdint>

namespace ur::title {

struct ChallengeAwardRequest {
    std::uint8_t rider_index = 0;
    std::uint8_t tour_row = 0;
    std::uint8_t expected_persisted_medal = 0;
    std::uint8_t effective_previous_medal = 0;
};

enum class ChallengeAwardStatus : std::uint8_t {
    Applied = 0,
    NoOverride = 1,
    InvalidRequest = 2,
    InvalidContext = 3,
    MedalMismatch = 4,
    StockPreviousMismatch = 5,
};

struct ChallengeAwardDecision {
    ChallengeAwardStatus status = ChallengeAwardStatus::InvalidRequest;
    std::uint8_t previous_medal = 0;

    bool applied() const noexcept {
        return status == ChallengeAwardStatus::Applied;
    }
};

bool valid_challenge_award_request(
    const ChallengeAwardRequest& request) noexcept;

ChallengeAwardDecision resolve_challenge_award_previous_medal(
    const ChallengeAwardRequest* request,
    std::uint8_t stock_previous_medal,
    const std::uint8_t* wram,
    std::size_t wram_size,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept;

}  // namespace ur::title
