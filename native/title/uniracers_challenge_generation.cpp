#include "uniracers_challenge_generation.hpp"

namespace ur::title {
namespace {

constexpr std::size_t kWramMenu = 0x009F;
constexpr std::size_t kWramTourRow = 0x00D0;
constexpr std::uint8_t kTrackSelectMenu = 0xF6;

constexpr std::size_t kSramMedalBase = 0x069C;
constexpr std::size_t kSramRiderIndex = 0x0748;
constexpr std::size_t kSramGenerationSnapshot = 0x10D1;
constexpr std::size_t kSramPlayMode = 0x10AD;
constexpr std::uint8_t kTourPlayMode = 1;

constexpr std::size_t kRiderCount = 16;
constexpr std::size_t kTourCount = 9;
constexpr std::uint8_t kHunterTourRow = 8;
constexpr std::uint8_t kMaxPersistentMedal = 3;
constexpr std::uint8_t kMaxSelectableGeneration = 2;

std::size_t medal_offset(
    std::uint8_t rider,
    std::uint8_t tour) noexcept {
    return kSramMedalBase +
           static_cast<std::size_t>(tour) * kRiderCount +
           static_cast<std::size_t>(rider);
}

}  // namespace

ChallengeGenerationApplyStatus apply_challenge_generation(
    std::uint8_t expected_persisted_medal,
    std::uint8_t selected_generation,
    const std::uint8_t* wram,
    std::size_t wram_size,
    std::uint8_t* sram,
    std::size_t sram_size) noexcept {
    if (!wram || !sram ||
        wram_size <= kWramTourRow ||
        sram_size <= kSramPlayMode ||
        expected_persisted_medal > kMaxPersistentMedal ||
        selected_generation > kMaxSelectableGeneration) {
        return ChallengeGenerationApplyStatus::InvalidState;
    }

    if (wram[kWramMenu] != kTrackSelectMenu ||
        sram[kSramPlayMode] != kTourPlayMode) {
        return ChallengeGenerationApplyStatus::ContextMismatch;
    }

    const std::uint8_t tour = wram[kWramTourRow];
    const std::uint8_t rider = sram[kSramRiderIndex];
    if (tour >= kTourCount || rider >= kRiderCount) {
        return ChallengeGenerationApplyStatus::InvalidState;
    }
    if (tour == kHunterTourRow) {
        return ChallengeGenerationApplyStatus::UnsupportedHunter;
    }

    const auto medal = medal_offset(rider, tour);
    if (medal >= sram_size ||
        kSramGenerationSnapshot >= sram_size) {
        return ChallengeGenerationApplyStatus::InvalidState;
    }
    if (sram[medal] != expected_persisted_medal) {
        return ChallengeGenerationApplyStatus::MedalMismatch;
    }

    // Stock tour confirmation snapshots the persistent medal generation into
    // 0x10D1. Accept only that exact expected source state so a stale selector
    // cannot rewrite an already-diverged tour context.
    if (sram[kSramGenerationSnapshot] != expected_persisted_medal) {
        if (sram[kSramGenerationSnapshot] == selected_generation) {
            return ChallengeGenerationApplyStatus::AlreadySelected;
        }
        return ChallengeGenerationApplyStatus::SnapshotMismatch;
    }

    if (selected_generation == expected_persisted_medal) {
        return ChallengeGenerationApplyStatus::AlreadySelected;
    }

    // 0x10D1 is outside the checksum-protected persistent medal region.
    // This adapter intentionally writes one transient stock-owned byte only.
    sram[kSramGenerationSnapshot] = selected_generation;
    return ChallengeGenerationApplyStatus::Applied;
}

}  // namespace ur::title
