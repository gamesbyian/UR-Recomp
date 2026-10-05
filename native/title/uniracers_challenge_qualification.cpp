#include "uniracers_challenge_qualification.hpp"

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
constexpr std::uint8_t kMaxChallengeGeneration = 2;

std::size_t medal_offset(
    std::uint8_t rider,
    std::uint8_t tour) noexcept {
    return kSramMedalBase +
           static_cast<std::size_t>(tour) * kMedalRowStride +
           static_cast<std::size_t>(rider);
}

std::uint8_t stock_generation_from_medal(
    std::uint8_t medal) noexcept {
    return medal >= 3 ? 2 : medal;
}

}  // namespace

bool valid_challenge_qualification_request(
    const ChallengeQualificationRequest& request) noexcept {
    return request.rider_index < kRiderCount &&
           request.tour_row < kOrdinaryTourCount &&
           request.expected_persisted_medal <= kMaxPersistedMedal &&
           request.selected_generation <= kMaxChallengeGeneration;
}

ChallengeQualificationDecision resolve_stunt_qualification_generation(
    const ChallengeQualificationRequest* request,
    std::uint8_t stock_generation,
    const std::uint8_t* wram,
    std::size_t wram_size,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept {
    if (!request) {
        return {
            ChallengeQualificationStatus::NoOverride,
            stock_generation,
        };
    }
    if (!valid_challenge_qualification_request(*request)) {
        return {
            ChallengeQualificationStatus::InvalidRequest,
            stock_generation,
        };
    }
    if (!wram || !sram ||
        wram_size <= kWramTourRow ||
        sram_size <= kSramPlayMode ||
        wram[kWramTourRow] != request->tour_row ||
        sram[kSramRiderIndex] != request->rider_index ||
        sram[kSramPlayMode] != kTourPlayMode) {
        return {
            ChallengeQualificationStatus::InvalidContext,
            stock_generation,
        };
    }

    const auto medal =
        medal_offset(request->rider_index, request->tour_row);
    if (medal >= sram_size ||
        sram[medal] != request->expected_persisted_medal) {
        return {
            ChallengeQualificationStatus::MedalMismatch,
            stock_generation,
        };
    }

    const auto expected_stock_generation =
        stock_generation_from_medal(request->expected_persisted_medal);
    if (stock_generation != expected_stock_generation) {
        return {
            ChallengeQualificationStatus::StockGenerationMismatch,
            stock_generation,
        };
    }

    return {
        ChallengeQualificationStatus::Applied,
        request->selected_generation,
    };
}

}  // namespace ur::title
