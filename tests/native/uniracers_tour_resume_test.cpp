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
    sram[0x0748] = rider;
    wram[0x00D0] = tour;
    sram[0x10AD] = 1;
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
    assert(tour_resume_source_matches_sram(
        continuation, sram.data(), sram.size()));

    // Unrelated battery bytes are outside the continuation contract. Stock
    // boot is free to touch them without suppressing a valid resume.
    const auto unrelated_before = sram[0x0200];
    sram[0x0200] ^= 0x5a;
    assert(tour_resume_source_matches_sram(
        continuation, sram.data(), sram.size()));
    sram[0x0200] = unrelated_before;

    // Persisted continuation metadata must agree with its own SRAM source.
    auto stale_source = continuation;
    stale_source.medal_value = 2;
    assert(!tour_resume_source_matches_sram(
        stale_source, sram.data(), sram.size()));
    stale_source = continuation;
    stale_source.qualified[1] = 1;
    assert(!tour_resume_source_matches_sram(
        stale_source, sram.data(), sram.size()));

    sram[0x0748] = 2;
    assert(!tour_resume_source_matches_sram(
        continuation, sram.data(), sram.size()));
    sram[0x0748] = 3;
    sram[0x10AD] = 2;
    assert(!tour_resume_source_matches_sram(
        continuation, sram.data(), sram.size()));
    sram[0x10AD] = 1;

    assert(!tour_qualification_row_empty(
        continuation.tour_row, sram.data(), sram.size()));
    assert(!tour_qualification_row_empty(
        9, sram.data(), sram.size()));
    assert(!tour_qualification_row_empty(
        continuation.tour_row, nullptr, sram.size()));

    // Model stock rider confirmation wiping all 50 in-tour flags.
    for (std::size_t i = 0; i < 50; ++i) sram[0x1075 + i] = 0;
    assert(tour_qualification_row_empty(
        continuation.tour_row, sram.data(), sram.size()));
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
    sram[0x0748] = 2;
    assert(apply_tour_resume(
               continuation,
               wram.data(),
               wram.size(),
               sram.data(),
               sram.size()) == TourResumeApplyStatus::ContextMismatch);
    sram[0x0748] = 3;

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
    sram[0x10AD] = 2;
    assert(!observe_tour_progress(
        wram.data(), wram.size(), sram.data(), sram.size()));

    return 0;
}
