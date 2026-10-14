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

UrUniracersLineSnapshot finish_line() {
    UrUniracersLineSnapshot line{};
    line.valid = 1;
    line.seconds = 3;
    line.tenths = 4;
    line.hundredths = 56;
    return line;
}

void check_revoke(unsigned players, bool racing, std::uint8_t menu) {
    BaldosaPendingOnePlayerRun pending;
    const auto source = finish_line();
    assert(pending.defer_failed_publication(settled(200), 200, source, 0));
    assert(pending.pending());
    assert(!pending.ready_for_retry(players, racing, menu, 230,
                                    &source, 0));
    assert(!pending.pending());
    assert(pending.failed_attempts() == 0);
}
} // namespace

int main() {
    const auto source = finish_line();
    BaldosaPendingOnePlayerRun pending;
    assert(!pending.pending());
    assert(!pending.ready_for_retry(1, false, 0x99, 999, nullptr, 0));
    auto invalid = settled(200);
    invalid.kind = BaldosaSettledResultKind::OrdinaryTwoPlayerRace;
    assert(!pending.defer_failed_publication(std::move(invalid), 200, source, 0));
    assert(!pending.defer_failed_publication(settled(200), 201, source, 0));
    assert(!pending.pending());

    assert(pending.defer_failed_publication(settled(200), 200, source, 0));
    assert(!pending.defer_failed_publication(settled(201), 201, source, 0));
    assert(pending.pending());
    assert(pending.failed_attempts() == 1);
    assert(!pending.ready_for_retry(1, false, 0x99, 229, &source, 0));
    const auto* retry = pending.ready_for_retry(1, false, 0x99, 230, &source, 0);
    assert(retry);
    assert(retry->captured_input_frames == 60);
    assert(retry->mapped_inputs.size() == 1);
    assert(retry->mapped_inputs[0].p1_mask == 0x100);
    assert(pending.after_retry(true, 230) == BaldosaRunRetryOutcome::Saved);
    assert(!pending.pending());
    assert(!pending.ready_for_retry(1, false, 0x99, 999, nullptr, 0));

    // A changed or absent original finish line must revoke a pending run
    // even while the exact 1P stock result menu remains visible.
    assert(pending.defer_failed_publication(settled(200), 200, source, 0));
    auto changed_line = source;
    changed_line.hundredths++;
    assert(!pending.ready_for_retry(1, false, 0x99, 230,
                                    &changed_line, 0));
    assert(!pending.pending());
    assert(pending.defer_failed_publication(settled(200), 200, source, 0));
    assert(!pending.ready_for_retry(1, false, 0x99, 230,
                                    nullptr, 0));
    assert(!pending.pending());
    assert(pending.defer_failed_publication(settled(200), 200, source, 0));
    assert(!pending.ready_for_retry(1, false, 0x99, 230,
                                    &source, 1));
    assert(!pending.pending());
    assert(!pending.defer_failed_publication(settled(200), 200, source, 1));
    auto invalid_line = source;
    invalid_line.valid = 0;
    assert(!pending.defer_failed_publication(settled(200), 200,
                                             invalid_line, 0));

    // No retry after a new race, wrong player handoff, stock menu change,
    // or frontend revocation. This guards against publication into a later
    // session with stale source-result/input/provenance authority.
    check_revoke(1, true, 0x99);
    check_revoke(1, false, 0xd7);
    check_revoke(2, false, 0x99);
    check_revoke(0, false, 0x99);

    assert(pending.defer_failed_publication(settled(200), 200, source, 0));
    for (unsigned i = 1; i < BaldosaPendingOnePlayerRun::kMaxTotalAttempts; ++i) {
        const auto frame = 200u +
            i * BaldosaPendingOnePlayerRun::kRetryIntervalHostFrames;
        assert(!pending.ready_for_retry(1, false, 0x99, frame - 1, &source, 0));
        assert(pending.ready_for_retry(1, false, 0x99, frame, &source, 0));
        const auto outcome = pending.after_retry(false, frame);
        assert(outcome ==
            (i + 1 == BaldosaPendingOnePlayerRun::kMaxTotalAttempts
                ? BaldosaRunRetryOutcome::Exhausted
                : BaldosaRunRetryOutcome::Pending));
    }
    assert(!pending.pending());
    assert(pending.failed_attempts() == 0);
    assert(!pending.ready_for_retry(1, false, 0x99, 10000, &source, 0));

    std::puts("PASS: Baldosa native run receipt retry is bounded and session-scoped");
}
