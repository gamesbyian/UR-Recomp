#include "uniracers_challenge_generation.hpp"

#include <array>
#include <cassert>
#include <cstdint>

using namespace ur::title;

namespace {
constexpr std::size_t kWramSize = 0x20000;
constexpr std::size_t kSramSize = 0x2000;

void seed(
    std::array<std::uint8_t, kWramSize>& wram,
    std::array<std::uint8_t, kSramSize>& sram,
    std::uint8_t tour,
    std::uint8_t rider,
    std::uint8_t medal) {
    wram.fill(0);
    sram.fill(0);
    wram[0x009F] = 0xF6;
    wram[0x00D0] = tour;
    sram[0x10AD] = 1;
    sram[0x0748] = rider;
    sram[0x069C + 16 * tour + rider] = medal;
    sram[0x10D1] = medal;
}
}  // namespace

int main() {
    std::array<std::uint8_t, kWramSize> wram{};
    std::array<std::uint8_t, kSramSize> sram{};
    seed(wram, sram, 0, 0, 0);

    auto before = sram;
    auto status = apply_challenge_generation(
        0, 2, wram.data(), wram.size(), sram.data(), sram.size());
    assert(status == ChallengeGenerationApplyStatus::Applied);
    assert(sram[0x10D1] == 2);
    for (std::size_t i = 0; i < sram.size(); ++i) {
        if (i == 0x10D1) continue;
        assert(sram[i] == before[i]);
    }
    assert(sram[0x069C] == 0);

    // Reapplying the same selected generation is idempotent.
    status = apply_challenge_generation(
        0, 2, wram.data(), wram.size(), sram.data(), sram.size());
    assert(status == ChallengeGenerationApplyStatus::AlreadySelected);

    seed(wram, sram, 2, 1, 1);
    status = apply_challenge_generation(
        1, 1, wram.data(), wram.size(), sram.data(), sram.size());
    assert(status == ChallengeGenerationApplyStatus::AlreadySelected);

    seed(wram, sram, 0, 0, 0);
    wram[0x009F] = 0x6D;
    assert(apply_challenge_generation(
               0, 2, wram.data(), wram.size(), sram.data(), sram.size()) ==
           ChallengeGenerationApplyStatus::ContextMismatch);

    seed(wram, sram, 0, 0, 0);
    sram[0x10AD] = 2;
    assert(apply_challenge_generation(
               0, 2, wram.data(), wram.size(), sram.data(), sram.size()) ==
           ChallengeGenerationApplyStatus::ContextMismatch);

    seed(wram, sram, 0, 0, 1);
    assert(apply_challenge_generation(
               0, 2, wram.data(), wram.size(), sram.data(), sram.size()) ==
           ChallengeGenerationApplyStatus::MedalMismatch);

    seed(wram, sram, 0, 0, 0);
    sram[0x10D1] = 1;
    assert(apply_challenge_generation(
               0, 2, wram.data(), wram.size(), sram.data(), sram.size()) ==
           ChallengeGenerationApplyStatus::SnapshotMismatch);

    seed(wram, sram, 8, 0, 0);
    assert(apply_challenge_generation(
               0, 2, wram.data(), wram.size(), sram.data(), sram.size()) ==
           ChallengeGenerationApplyStatus::UnsupportedHunter);

    seed(wram, sram, 0, 0, 0);
    assert(apply_challenge_generation(
               0, 3, wram.data(), wram.size(), sram.data(), sram.size()) ==
           ChallengeGenerationApplyStatus::InvalidState);
    assert(apply_challenge_generation(
               0, 2, nullptr, wram.size(), sram.data(), sram.size()) ==
           ChallengeGenerationApplyStatus::InvalidState);

    return 0;
}
