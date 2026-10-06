#include "uniracers_challenge_award.hpp"

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

    // Selected Gold from an unmedalled profile asks stock to perform its
    // ordinary authoritative 2 -> 3 transaction.
    seed(wram, sram, 0, 0, 0);
    ChallengeAwardRequest gold{0, 0, 0, 2};
    auto decision = resolve_challenge_award_previous_medal(
        &gold, 0, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeAwardStatus::Applied);
    assert(decision.previous_medal == 2);
    assert(sram[0x069C] == 0);

    // Selected Silver similarly lets stock perform 1 -> 2.
    ChallengeAwardRequest silver{0, 0, 0, 1};
    decision = resolve_challenge_award_previous_medal(
        &silver, 0, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeAwardStatus::Applied);
    assert(decision.previous_medal == 1);

    // Natural sequential Bronze remains 0 -> 1.
    ChallengeAwardRequest bronze{0, 0, 0, 0};
    decision = resolve_challenge_award_previous_medal(
        &bronze, 0, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeAwardStatus::Applied);
    assert(decision.previous_medal == 0);

    decision = resolve_challenge_award_previous_medal(
        nullptr, 2, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeAwardStatus::NoOverride);
    assert(decision.previous_medal == 2);

    // Hunter is not an ordinary selectable-tier award surface.
    ChallengeAwardRequest hunter{0, 8, 0, 2};
    assert(!valid_challenge_award_request(hunter));

    // Stale progression never gets overwritten by a selected-tier request.
    sram[0x069C] = 1;
    decision = resolve_challenge_award_previous_medal(
        &gold, 1, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeAwardStatus::MedalMismatch);
    assert(decision.previous_medal == 1);
    sram[0x069C] = 0;

    decision = resolve_challenge_award_previous_medal(
        &gold, 1, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeAwardStatus::StockPreviousMismatch);
    assert(decision.previous_medal == 1);

    wram[0x00D0] = 1;
    decision = resolve_challenge_award_previous_medal(
        &gold, 0, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeAwardStatus::InvalidContext);

    return 0;
}
