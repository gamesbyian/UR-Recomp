#include "uniracers_challenge_qualification.hpp"

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
    std::uint8_t rider,
    std::uint8_t tour,
    std::uint8_t medal) {
    wram.fill(0);
    sram.fill(0);
    wram[0x00D0] = tour;
    sram[0x0748] = rider;
    sram[0x10AD] = 1;
    sram[0x069C + 16 * tour + rider] = medal;
}
}  // namespace

int main() {
    std::array<std::uint8_t, kWramSize> wram{};
    std::array<std::uint8_t, kSramSize> sram{};
    seed(wram, sram, 0, 0, 0);

    ChallengeQualificationRequest gold{0, 0, 0, 2};
    auto decision = resolve_stunt_qualification_generation(
        &gold, 0, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeQualificationStatus::Applied);
    assert(decision.generation == 2);

    // Stock Gold completion medal 3 maps back to challenge generation 2.
    seed(wram, sram, 1, 4, 3);
    ChallengeQualificationRequest bronze_replay{1, 4, 3, 0};
    decision = resolve_stunt_qualification_generation(
        &bronze_replay, 2,
        wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeQualificationStatus::Applied);
    assert(decision.generation == 0);
    assert(sram[0x069C + 16 * 4 + 1] == 3);

    decision = resolve_stunt_qualification_generation(
        nullptr, 1, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeQualificationStatus::NoOverride);
    assert(decision.generation == 1);

    ChallengeQualificationRequest hunter{1, 8, 3, 2};
    assert(!valid_challenge_qualification_request(hunter));

    seed(wram, sram, 2, 3, 1);
    ChallengeQualificationRequest silver{2, 3, 1, 1};

    wram[0x00D0] = 4;
    decision = resolve_stunt_qualification_generation(
        &silver, 1, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeQualificationStatus::InvalidContext);
    wram[0x00D0] = 3;

    sram[0x069C + 16 * 3 + 2] = 2;
    decision = resolve_stunt_qualification_generation(
        &silver, 1, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeQualificationStatus::MedalMismatch);
    sram[0x069C + 16 * 3 + 2] = 1;

    decision = resolve_stunt_qualification_generation(
        &silver, 0, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status ==
           ChallengeQualificationStatus::StockGenerationMismatch);
    assert(decision.generation == 0);

    return 0;
}
