#include "uniracers_challenge_completion_runtime.hpp"
#include "uniracers_challenge_generation_bridge.h"

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

    ChallengeQualificationRequest gold_q{0, 0, 0, 2};
    ChallengeAwardRequest gold_a{0, 0, 0, 2};
    assert(arm_challenge_completion_overrides(
               gold_q, &gold_a,
               wram.data(), wram.size(),
               sram.data(), sram.size()) ==
           ChallengeCompletionArmStatus::Armed);
    assert(challenge_completion_overrides_active());

    // Stunt threshold generation remains selected-tier aware for every stunt
    // event in the tour.
    assert(ur_uniracers_challenge_qualification_generation_filter(0) == 2);
    assert(challenge_completion_overrides_active());
    assert(ur_uniracers_challenge_qualification_generation_filter(0) == 2);
    assert(challenge_completion_overrides_active());

    // The stock award boundary consumes the completion override and retires
    // the entire selected-tour title context.
    assert(ur_uniracers_challenge_award_previous_medal_filter(0) == 2);
    assert(!challenge_completion_overrides_active());
    assert(challenge_completion_last_award_status() ==
           ChallengeAwardStatus::Applied);
    assert(ur_uniracers_challenge_qualification_generation_filter(0) == 0);
    assert(ur_uniracers_challenge_award_previous_medal_filter(0) == 0);

    // A lower-tier replay needs its stunt threshold override but no medal
    // override. The award boundary still retires the context.
    seed(wram, sram, 1, 2, 3);
    ChallengeQualificationRequest bronze_q{1, 2, 3, 0};
    assert(arm_challenge_completion_overrides(
               bronze_q, nullptr,
               wram.data(), wram.size(),
               sram.data(), sram.size()) ==
           ChallengeCompletionArmStatus::Armed);
    assert(ur_uniracers_challenge_qualification_generation_filter(2) == 0);
    assert(ur_uniracers_challenge_award_previous_medal_filter(3) == 3);
    assert(!challenge_completion_overrides_active());
    assert(challenge_completion_last_award_status() ==
           ChallengeAwardStatus::NoOverride);

    // Context drift during a tour fails closed and clears both later seams.
    seed(wram, sram, 2, 3, 1);
    ChallengeQualificationRequest silver_q{2, 3, 1, 1};
    ChallengeAwardRequest silver_a{2, 3, 1, 1};
    assert(arm_challenge_completion_overrides(
               silver_q, &silver_a,
               wram.data(), wram.size(),
               sram.data(), sram.size()) ==
           ChallengeCompletionArmStatus::Armed);
    wram[0x00D0] = 4;
    assert(ur_uniracers_challenge_qualification_generation_filter(1) == 1);
    assert(!challenge_completion_overrides_active());
    assert(challenge_completion_last_qualification_status() ==
           ChallengeQualificationStatus::InvalidContext);
    assert(ur_uniracers_challenge_award_previous_medal_filter(1) == 1);

    // Mismatched qualification/award identities cannot be armed together.
    wram[0x00D0] = 3;
    ChallengeAwardRequest wrong_tour{2, 4, 1, 1};
    assert(arm_challenge_completion_overrides(
               silver_q, &wrong_tour,
               wram.data(), wram.size(),
               sram.data(), sram.size()) ==
           ChallengeCompletionArmStatus::InvalidAwardRequest);

    return 0;
}
