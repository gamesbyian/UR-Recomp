#include "modern_tournament_p2_guest_input.hpp"
#include <cstdio>
#include <cstdlib>
using namespace ur::product;
namespace {
void check(bool good, const char* reason) {
    if (!good) { std::fprintf(stderr, "FAIL %s\n", reason); std::exit(1); }
}
}
int main() {
    constexpr std::uint32_t A = 0x010u, B = 0x020u, START = 0x080u;
    auto filter = tournament_p2_guest_filter({}, false, A | START);
    check(filter.inputs == (A | START) && filter.state.awaiting_release == 0,
          "unarmed guest P2 word is transparent");

    auto state = tournament_p2_guest_arm();
    check(state.awaiting_release == 0x0fff, "panel arms entire P2 physical word");
    // The guest can be held with zero guest frames observed while the panel
    // is visible. Entering the closed state still suppresses a previously
    // held P2 A and Start before ordinary guest processing resumes.
    filter = tournament_p2_guest_filter(state, true, A | START);
    check(filter.inputs == 0 && filter.state.awaiting_release == 0x0fff,
          "modal input withheld without losing release-guard state");
    filter = tournament_p2_guest_filter(filter.state, false, A | START);
    check(filter.inputs == 0 && filter.state.awaiting_release == (A | START),
          "first guest frame after modal sees no stale P2 held bits");
    filter = tournament_p2_guest_filter(filter.state, false, A | START | B);
    check(filter.inputs == B && filter.state.awaiting_release == (A | START),
          "new P2 B passes while other P2 buttons await release");
    filter = tournament_p2_guest_filter(filter.state, false, START | B);
    check(filter.inputs == B && filter.state.awaiting_release == START,
          "A release clears A latch only");
    filter = tournament_p2_guest_filter(filter.state, false, START | B | A);
    check(filter.inputs == (A | B), "A repress passes while Start still held");
    filter = tournament_p2_guest_filter(filter.state, false, A | B);
    check(filter.state.awaiting_release == 0 && filter.inputs == (A | B),
          "all earlier held bits eventually clear");

    state = tournament_p2_guest_arm();
    filter = tournament_p2_guest_filter(state, false, 0u);
    check(filter.state.awaiting_release == 0, "zero first resumed word clears guard");
    filter = tournament_p2_guest_filter(filter.state, false, START);
    check(filter.inputs == START, "fresh Start after release is never stuck");
    state = tournament_p2_guest_arm();
    filter = tournament_p2_guest_filter(state, false, 0xf000u);
    check(filter.inputs == 0xf000u, "unrelated high flag bits pass through");
    static_assert(tournament_p2_guest_arm().awaiting_release == 0x0fff);
    static_assert(tournament_p2_guest_filter({}, false, 0x023).inputs == 0x023);
    std::puts("modern_tournament_p2_guest_input_test: ok");
    return 0;
}
