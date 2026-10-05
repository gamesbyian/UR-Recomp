#include "uniracers_challenge_generation_runtime.hpp"
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

    const ChallengeGenerationRequest gold{0, 0, 0, 2};
    assert(arm_challenge_generation_override(
               gold,
               wram.data(),
               wram.size(),
               sram.data(),
               sram.size()) == ChallengeGenerationArmStatus::Armed);
    assert(challenge_generation_override_active());

    // A second arm cannot replace an in-flight request.
    assert(arm_challenge_generation_override(
               gold,
               wram.data(),
               wram.size(),
               sram.data(),
               sram.size()) == ChallengeGenerationArmStatus::AlreadyArmed);

    // The generated writer bridge consumes the request once.
    assert(ur_uniracers_challenge_generation_filter(0) == 2);
    assert(!challenge_generation_override_active());
    assert(challenge_generation_override_last_status() ==
           ChallengeGenerationStatus::Applied);

    // Later stock writers are exact pass-through.
    assert(ur_uniracers_challenge_generation_filter(0) == 0);
    assert(ur_uniracers_challenge_generation_filter(1) == 1);

    // A stale context also consumes the request but fails closed to stock.
    assert(arm_challenge_generation_override(
               gold,
               wram.data(),
               wram.size(),
               sram.data(),
               sram.size()) == ChallengeGenerationArmStatus::Armed);
    wram[0x00D0] = 1;
    assert(ur_uniracers_challenge_generation_filter(0) == 0);
    assert(!challenge_generation_override_active());
    assert(challenge_generation_override_last_status() ==
           ChallengeGenerationStatus::InvalidContext);

    // Explicit cancellation restores stock behavior before any writer.
    wram[0x00D0] = 0;
    assert(arm_challenge_generation_override(
               gold,
               wram.data(),
               wram.size(),
               sram.data(),
               sram.size()) == ChallengeGenerationArmStatus::Armed);
    clear_challenge_generation_override();
    assert(!challenge_generation_override_active());
    assert(ur_uniracers_challenge_generation_filter(0) == 0);

    const ChallengeGenerationRequest hunter{0, 8, 0, 2};
    assert(arm_challenge_generation_override(
               hunter,
               wram.data(),
               wram.size(),
               sram.data(),
               sram.size()) ==
           ChallengeGenerationArmStatus::InvalidRequest);
    assert(arm_challenge_generation_override(
               gold, nullptr, wram.size(), sram.data(), sram.size()) ==
           ChallengeGenerationArmStatus::InvalidBuffers);

    return 0;
}
