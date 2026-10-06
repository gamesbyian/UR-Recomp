#include "uniracers_challenge_award.hpp"

namespace ur::title {
namespace {

constexpr std::size_t kWramTourRow = 0x00D0;
constexpr std::size_t kSramRiderIndex = 0x0748;
constexpr std::size_t kSramMedalBase = 0x069C;
constexpr std::size_t kSramPlayMode = 0x10AD;
constexpr std::uint8_t kTourPlayMode = 1;
constexpr std::size_t kRiderCount = 16;
constexpr std::size_t kOrdinaryTourCount = 8;
constexpr std::size_t kMedalRowStride = 16;
constexpr std::uint8_t kMaxPersistedMedal = 3;
constexpr std::uint8_t kMaxEffectivePreviousMedal = 2;

std::size_t medal_offset(
    std::uint8_t rider,
    std::uint8_t tour) noexcept {
    return kSramMedalBase +
           static_cast<std::size_t>(tour) * kMedalRowStride +
           static_cast<std::size_t>(rider);
}

}  // namespace

bool valid_challenge_award_request(
    const ChallengeAwardRequest& request) noexcept {
    return request.rider_index < kRiderCount &&
           request.tour_row < kOrdinaryTourCount &&
           request.expected_persisted_medal <= kMaxPersistedMedal &&
           request.effective_previous_medal <= kMaxEffectivePreviousMedal;
}

ChallengeAwardDecision resolve_challenge_award_previous_medal(
    const ChallengeAwardRequest* request,
    std::uint8_t stock_previous_medal,
    const std::uint8_t* wram,
    std::size_t wram_size,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept {
    if (!request) {
        return {
            ChallengeAwardStatus::NoOverride,
            stock_previous_medal,
        };
    }
    if (!valid_challenge_award_request(*request)) {
        return {
            ChallengeAwardStatus::InvalidRequest,
            stock_previous_medal,
        };
    }
    if (!wram || !sram ||
        wram_size <= kWramTourRow ||
        sram_size <= kSramPlayMode ||
        wram[kWramTourRow] != request->tour_row ||
        sram[kSramRiderIndex] != request->rider_index ||
        sram[kSramPlayMode] != kTourPlayMode) {
        return {
            ChallengeAwardStatus::InvalidContext,
            stock_previous_medal,
        };
    }

    const auto medal =
        medal_offset(request->rider_index, request->tour_row);
    if (medal >= sram_size ||
        sram[medal] != request->expected_persisted_medal) {
        return {
            ChallengeAwardStatus::MedalMismatch,
            stock_previous_medal,
        };
    }
    if (stock_previous_medal != request->expected_persisted_medal) {
        return {
            ChallengeAwardStatus::StockPreviousMismatch,
            stock_previous_medal,
        };
    }

    return {
        ChallengeAwardStatus::Applied,
        request->effective_previous_medal,
    };
}

}  // namespace ur::title
