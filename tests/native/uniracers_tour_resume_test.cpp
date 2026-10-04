#include "uniracers_tour_resume.hpp"

#include <array>
#include <cassert>
#include <cstdint>

using namespace ur::title;

namespace {

constexpr std::size_t kWramSize = 0x20000;
constexpr std::size_t kSramSize = 0x2000;

void seed_context(
    std::array<std::uint8_t, kWramSize>& wram,
    std::array<std::uint8_t, kSramSize>& sram,
    std::uint8_t rider,
    std::uint8_t tour,
    std::uint8_t medal) {
    wram[0x017D] = rider;
    wram[0x00D0] = tour;
    wram[0x10AD] = 1;
    sram[0x069C + 16 * tour + rider] = medal;
}

}  // namespace

int main() {
    std::array<std::uint8_t, kWramSize> wram{};
    std::array<std::uint8_t, kSramSize> sram{};
    seed_context(wram, sram, 3, 4, 1);
    sram[0x1075 + 5 * 4 + 0] = 1;
    sram[0x1075 + 5 * 4 + 2] = 1;

    const auto observed =
        observe_tour_progress(wram.data(), wram.size(), sram.data(), sram.size());
    assert(observed);
    assert(observed->rider_index == 3);
    assert(observed->tour_row == 4);
    assert(observed->medal_value == 1);
    assert((observed->qualified ==
            std::array<std::uint8_t, 5>{1, 0, 1, 0, 0}));
    assert(valid_unfinished_tour_progress(*observed));

    const TourProgress continuation = *observed;

    // Model stock rider confirmation wiping all 50 in-tour flags.
    for (std::size_t i = 0; i < 50; ++i) sram[0x1075 + i] = 0;
    assert(apply_tour_resume(
               continuation,
               wram.data(),
               wram.size(),
               sram.data(),
               sram.size()) == TourResumeApplyStatus::Applied);
    assert(sram[0x1075 + 5 * 4 + 0] == 1);
    assert(sram[0x1075 + 5 * 4 + 2] == 1);
    assert(apply_tour_resume(
               continuation,
               wram.data(),
               wram.size(),
               sram.data(),
               sram.size()) == TourResumeApplyStatus::AlreadyPresent);

    // A different rider or tour cannot consume the continuation.
    wram[0x017D] = 2;
    assert(apply_tour_resume(
               continuation,
               wram.data(),
               wram.size(),
               sram.data(),
               sram.size()) == TourResumeApplyStatus::ContextMismatch);
    wram[0x017D] = 3;

    // A medal generation change makes the continuation stale.
    sram[0x069C + 16 * 4 + 3] = 2;
    assert(apply_tour_resume(
               continuation,
               wram.data(),
               wram.size(),
               sram.data(),
               sram.size()) == TourResumeApplyStatus::MedalMismatch);

    // Existing new progress is never overwritten.
    sram[0x069C + 16 * 4 + 3] = 1;
    for (std::size_t i = 0; i < 5; ++i) sram[0x1075 + 5 * 4 + i] = 0;
    sram[0x1075 + 5 * 4 + 4] = 1;
    assert(apply_tour_resume(
               continuation,
               wram.data(),
               wram.size(),
               sram.data(),
               sram.size()) == TourResumeApplyStatus::ExistingProgress);

    // VS is outside this Modern tour-resume contract.
    wram[0x10AD] = 2;
    assert(!observe_tour_progress(
        wram.data(), wram.size(), sram.data(), sram.size()));

    return 0;
}
