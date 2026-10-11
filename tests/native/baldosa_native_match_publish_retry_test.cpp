#include "baldosa_native_match_publish_retry.hpp"

#include <cassert>
#include <cstdint>
#include <cstdio>
#include <limits>

using namespace ur::product;
namespace {

BaldosaSettledResult result(std::uint64_t frame) {
    BaldosaSettledResult r{};
    r.kind = BaldosaSettledResultKind::OrdinaryTwoPlayerRace;
    r.first_race_host_frame = frame - 60;
    r.observed_result_host_frame = frame;
    r.course_index = 1;
    r.captured_input_frames = 60;
    r.mapped_inputs = {{0, 30, 0x10u, 0x20u}, {30, 30, 0x11u, 0x21u}};
    ur::title::OrdinaryTwoPlayerRaceResult pair{};
    pair.player1_rider = 0;
    pair.player2_rider = 1;
    pair.player1_hundredths = 2866;
    pair.player2_hundredths = 2977;
    pair.outcome = ur::title::OrdinaryTwoPlayerRaceOutcome::Player1Win;
    r.two_player = pair;
    return r;
}
const HostProfileCatalogEntry p1{"rider-1", {"MIKE", 0}};
const HostProfileCatalogEntry p2{"rider-2", {"ANDREW", 1}};

void revoke(unsigned players, bool racing, std::uint8_t menu,
            bool has_source, bool has_profiles, bool change_source,
            bool change_profiles) {
    BaldosaPendingTwoPlayerMatch p;
    auto witnessed = result(200);
    assert(p.defer_failed_publication(witnessed, p1, p2, 200));
    auto live = *witnessed.two_player;
    auto selected = p2;
    if (change_source) live.player2_hundredths++;
    if (change_profiles) selected.identity.name = "IMPOSTOR";
    assert(!p.ready_for_retry(
        players, racing, menu, 230, has_source ? &live : nullptr,
        has_profiles ? &p1 : nullptr,
        has_profiles ? &selected : nullptr));
    assert(!p.pending());
}
} // namespace

int main() {
    BaldosaPendingTwoPlayerMatch pending;
    assert(!pending.pending());
    assert(!pending.ready_for_retry(2, false, 0xf9, 500, nullptr, nullptr, nullptr));
    auto incorrect = result(200);
    incorrect.kind = BaldosaSettledResultKind::TimedOnePlayerRace;
    assert(!pending.defer_failed_publication(incorrect, p1, p2, 200));
    incorrect = result(200);
    incorrect.two_player.reset();
    assert(!pending.defer_failed_publication(incorrect, p1, p2, 200));
    incorrect = result(200);
    assert(!pending.defer_failed_publication(incorrect, p1, p2, 201));
    assert(!pending.defer_failed_publication(incorrect, p1, p1, 200));

    auto witnessed = result(200);
    assert(pending.defer_failed_publication(witnessed, p1, p2, 200));
    assert(!pending.defer_failed_publication(result(201), p1, p2, 201));
    auto live = *witnessed.two_player;
    assert(!pending.ready_for_retry(2, false, 0xf9, 229,
                                    &live, &p1, &p2));
    const auto* attempt = pending.ready_for_retry(2, false, 0xf9, 230,
                                                  &live, &p1, &p2);
    assert(attempt);
    assert(attempt->player1 == p1 && attempt->player2 == p2);
    assert(attempt->result.mapped_inputs.size() == 2);
    assert(attempt->result.mapped_inputs[1].p2_mask == 0x21u);
    assert(pending.after_retry(true, 230) == BaldosaRunRetryOutcome::Saved);
    assert(!pending.pending());

    // Source-preserving current result, same session, and BOTH unchanged
    // independently selected identities are essential for every attempt.
    revoke(0, false, 0xf9, true, true, false, false);
    revoke(1, false, 0xf9, true, true, false, false);
    revoke(2, true, 0xf9, true, true, false, false);
    revoke(2, false, 0xd7, true, true, false, false);
    revoke(2, false, 0x99, true, true, false, false);
    revoke(2, false, 0xf9, false, true, false, false);
    revoke(2, false, 0xf9, true, false, false, false);
    revoke(2, false, 0xf9, true, true, true, false);
    revoke(2, false, 0xf9, true, true, false, true);

    assert(pending.defer_failed_publication(result(200), p1, p2, 200));
    for (unsigned i = 1; i < BaldosaPendingTwoPlayerMatch::kMaxTotalAttempts; ++i) {
        const auto frame = 200 +
            i * BaldosaPendingTwoPlayerMatch::kRetryIntervalHostFrames;
        assert(!pending.ready_for_retry(2, false, 0xf9, frame - 1,
                                       &live, &p1, &p2));
        assert(pending.ready_for_retry(2, false, 0xf9, frame,
                                       &live, &p1, &p2));
        const auto outcome = pending.after_retry(false, frame);
        assert(outcome ==
            (i + 1 == BaldosaPendingTwoPlayerMatch::kMaxTotalAttempts
                ? BaldosaRunRetryOutcome::Exhausted
                : BaldosaRunRetryOutcome::Pending));
    }
    assert(!pending.pending());
    assert(!pending.ready_for_retry(2, false, 0xf9, 999,
                                    &live, &p1, &p2));
    assert(!pending.defer_failed_publication(
        result(std::numeric_limits<std::uint64_t>::max()), p1, p2,
        std::numeric_limits<std::uint64_t>::max()));

    std::puts("PASS: 2P source-result and two-profile retry is bounded, revocable, and immutable");
}
