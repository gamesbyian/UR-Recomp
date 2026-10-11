#include "baldosa_native_run_publish_retry.hpp"

#include <cassert>
#include <cstdio>
#include <cstdint>
#include <utility>

using namespace ur::product;

namespace {
BaldosaSettledResult settled(std::uint64_t frame) {
    BaldosaSettledResult event{};
    event.kind = BaldosaSettledResultKind::TimedOnePlayerRace;
    event.first_race_host_frame = frame - 60u;
    event.observed_result_host_frame = frame;
    event.p1_finish_ticks60 = 1234;
    event.course_index = 1;
    event.captured_input_frames = 60;
    event.mapped_inputs = {{0, 60, 0x100, 0}};
    return event;
}

void check_revoke(unsigned players, bool racing, std::uint8_t menu) {
    BaldosaPendingOnePlayerRun pending;
    assert(pending.defer_failed_publication(settled(200), 200));
    assert(pending.pending());
    assert(!pending.ready_for_retry(players, racing, menu, 230));
    assert(!pending.pending());
    assert(pending.failed_attempts() == 0);
}
} // namespace

int main() {
    BaldosaPendingOnePlayerRun pending;
    assert(!pending.pending());
    assert(!pending.ready_for_retry(1, false, 0x99, 999));
    auto invalid = settled(200);
    invalid.kind = BaldosaSettledResultKind::OrdinaryTwoPlayerRace;
    assert(!pending.defer_failed_publication(std::move(invalid), 200));
    assert(!pending.defer_failed_publication(settled(200), 201));
    assert(!pending.pending());

    assert(pending.defer_failed_publication(settled(200), 200));
    assert(!pending.defer_failed_publication(settled(201), 201));
    assert(pending.pending());
    assert(pending.failed_attempts() == 1);
    assert(!pending.ready_for_retry(1, false, 0x99, 229));
    const auto* retry = pending.ready_for_retry(1, false, 0x99, 230);
    assert(retry);
    assert(retry->captured_input_frames == 60);
    assert(retry->mapped_inputs.size() == 1);
    assert(retry->mapped_inputs[0].p1_mask == 0x100);
    assert(pending.after_retry(true, 230) == BaldosaRunRetryOutcome::Saved);
    assert(!pending.pending());
    assert(!pending.ready_for_retry(1, false, 0x99, 999));

    // No retry after a new race, wrong player handoff, stock menu change,
    // or frontend revocation. This guards against publication into a later
    // session with stale source-result/input/provenance authority.
    check_revoke(1, true, 0x99);
    check_revoke(1, false, 0xd7);
    check_revoke(2, false, 0x99);
    check_revoke(0, false, 0x99);

    assert(pending.defer_failed_publication(settled(200), 200));
    for (unsigned i = 1; i < BaldosaPendingOnePlayerRun::kMaxTotalAttempts; ++i) {
        const auto frame = 200u +
            i * BaldosaPendingOnePlayerRun::kRetryIntervalHostFrames;
        assert(!pending.ready_for_retry(1, false, 0x99, frame - 1));
        assert(pending.ready_for_retry(1, false, 0x99, frame));
        const auto outcome = pending.after_retry(false, frame);
        assert(outcome ==
            (i + 1 == BaldosaPendingOnePlayerRun::kMaxTotalAttempts
                ? BaldosaRunRetryOutcome::Exhausted
                : BaldosaRunRetryOutcome::Pending));
    }
    assert(!pending.pending());
    assert(pending.failed_attempts() == 0);
    assert(!pending.ready_for_retry(1, false, 0x99, 10000));

    std::puts("PASS: Baldosa native run receipt retry is bounded and session-scoped");
}
