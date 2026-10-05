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
    std::uint8_t rider,
    std::uint8_t tour,
    std::uint8_t medal) {
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

    ChallengeGenerationRequest gold{
        0,
        0,
        0,
        2,
    };
    assert(valid_challenge_generation_request(gold));

    auto decision = resolve_challenge_generation_snapshot(
        &gold,
        0,
        wram.data(),
        wram.size(),
        sram.data(),
        sram.size());
    assert(decision.status == ChallengeGenerationStatus::Applied);
    assert(decision.generation == 2);

    // The adapter is substitution-only. With no Modern request the exact
    // stock generation passes through unchanged.
    decision = resolve_challenge_generation_snapshot(
        nullptr,
        1,
        wram.data(),
        wram.size(),
        sram.data(),
        sram.size());
    assert(decision.status == ChallengeGenerationStatus::NoOverride);
    assert(decision.generation == 1);

    // A replay of a lower canonical tier remains possible without reducing
    // persistent completion. Persistence is not modified by this adapter.
    seed(wram, sram, 3, 4, 3);
    ChallengeGenerationRequest bronze_replay{
        3,
        4,
        3,
        0,
    };
    decision = resolve_challenge_generation_snapshot(
        &bronze_replay,
        3,
        wram.data(),
        wram.size(),
        sram.data(),
        sram.size());
    assert(decision.status == ChallengeGenerationStatus::Applied);
    assert(decision.generation == 0);
    assert(sram[0x069C + 16 * 4 + 3] == 3);

    // The Hunter tour is not a selectable-generation surface. It remains
    // canonical Gold/ANTI-UNI through stock secret progression.
    ChallengeGenerationRequest hunter{
        3,
        8,
        3,
        2,
    };
    assert(!valid_challenge_generation_request(hunter));
    decision = resolve_challenge_generation_snapshot(
        &hunter,
        3,
        wram.data(),
        wram.size(),
        sram.data(),
        sram.size());
    assert(decision.status == ChallengeGenerationStatus::InvalidRequest);
    assert(decision.generation == 3);

    seed(wram, sram, 1, 2, 1);
    ChallengeGenerationRequest silver{
        1,
        2,
        1,
        1,
    };

    // Every context mismatch fails closed to the stock value.
    wram[0x00D0] = 3;
    decision = resolve_challenge_generation_snapshot(
        &silver, 1, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeGenerationStatus::InvalidContext);
    assert(decision.generation == 1);
    wram[0x00D0] = 2;

    sram[0x0748] = 2;
    decision = resolve_challenge_generation_snapshot(
        &silver, 1, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeGenerationStatus::InvalidContext);
    sram[0x0748] = 1;

    sram[0x10AD] = 2;
    decision = resolve_challenge_generation_snapshot(
        &silver, 1, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeGenerationStatus::InvalidContext);
    sram[0x10AD] = 1;

    sram[0x069C + 16 * 2 + 1] = 2;
    decision = resolve_challenge_generation_snapshot(
        &silver, 1, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeGenerationStatus::MedalMismatch);
    sram[0x069C + 16 * 2 + 1] = 1;

    decision = resolve_challenge_generation_snapshot(
        &silver, 0, wram.data(), wram.size(), sram.data(), sram.size());
    assert(decision.status ==
           ChallengeGenerationStatus::StockGenerationMismatch);
    assert(decision.generation == 0);

    ChallengeGenerationRequest invalid_generation{
        1,
        2,
        1,
        3,
    };
    assert(!valid_challenge_generation_request(invalid_generation));

    decision = resolve_challenge_generation_snapshot(
        &silver, 1, nullptr, wram.size(), sram.data(), sram.size());
    assert(decision.status == ChallengeGenerationStatus::InvalidContext);

    return 0;
}
