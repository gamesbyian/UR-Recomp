#include "uniracers_challenge_generation.hpp"

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

}  // namespace

bool valid_challenge_generation_request(
    const ChallengeGenerationRequest& request) noexcept {
    return request.rider_index < kRiderCount &&
           request.tour_row < kOrdinaryTourCount &&
           request.expected_persisted_medal <= kMaxPersistedMedal &&
           request.selected_generation <= kMaxChallengeGeneration;
}

ChallengeGenerationDecision resolve_challenge_generation_snapshot(
    const ChallengeGenerationRequest* request,
    std::uint8_t stock_generation,
    const std::uint8_t* wram,
    std::size_t wram_size,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept {
    // No Modern request means stock owns the writer exactly as before.
    if (!request) {
        return {
            ChallengeGenerationStatus::NoOverride,
            stock_generation,
        };
    }
    if (!valid_challenge_generation_request(*request)) {
        return {
            ChallengeGenerationStatus::InvalidRequest,
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
            ChallengeGenerationStatus::InvalidContext,
            stock_generation,
        };
    }

    const auto medal =
        medal_offset(request->rider_index, request->tour_row);
    if (medal >= sram_size ||
        sram[medal] != request->expected_persisted_medal) {
        return {
            ChallengeGenerationStatus::MedalMismatch,
            stock_generation,
        };
    }
    if (stock_generation != request->expected_persisted_medal) {
        return {
            ChallengeGenerationStatus::StockGenerationMismatch,
            stock_generation,
        };
    }

    return {
        ChallengeGenerationStatus::Applied,
        request->selected_generation,
    };
}

}  // namespace ur::title
