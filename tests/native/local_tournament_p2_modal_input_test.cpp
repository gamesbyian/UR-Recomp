#include "local_tournament_p2_modal_input.hpp"

#include <cstdint>
#include <cstdio>
#include <cstdlib>

using namespace ur::product;

namespace {
constexpr std::uint32_t kA = 1u << 0;
constexpr std::uint32_t kStart = 1u << 6;
constexpr std::uint32_t kDpadLeft = 1u << 13;

void check(bool value, const char* description) {
    if (!value) {
        std::fprintf(stderr, "FAIL %s\n", description);
        std::exit(EXIT_FAILURE);
    }
}
} // namespace

int main() {
    auto r = tournament_p2_modal_input(0u, false, kA, true);
    check(!r.consume_event && r.consumed_buttons == 0u,
          "unowned P2 ordinary press passes");

    r = tournament_p2_modal_input(0u, true, kA, true);
    check(r.consume_event && r.consumed_buttons == kA,
          "P2 A press swallowed during tournament panel");
    // Closing the panel does not constitute a physical release. Its subsequent
    // release edge is still suppressed, so guest input never sees a release
    // of a button whose press was not delivered.
    r = tournament_p2_modal_input(r.consumed_buttons, false, kA, false);
    check(r.consume_event && r.consumed_buttons == 0u,
          "P2 release swallowed after closing panel");
    r = tournament_p2_modal_input(r.consumed_buttons, false, kA, true);
    check(!r.consume_event, "new P2 A press after release passes");

    r = tournament_p2_modal_input(0u, true, kStart, true);
    r = tournament_p2_modal_input(r.consumed_buttons, true, kDpadLeft, true);
    check(r.consumed_buttons == (kStart | kDpadLeft),
          "multiple P2 held bits tracked independently");
    r = tournament_p2_modal_input(r.consumed_buttons, true, kStart, false);
    check(r.consume_event && r.consumed_buttons == kDpadLeft,
          "P2 partial release while panel open");
    r = tournament_p2_modal_input(r.consumed_buttons, false, kDpadLeft, false);
    check(r.consume_event && r.consumed_buttons == 0u,
          "remaining post-close release swallowed");

    r = tournament_p2_modal_input(0u, true, 0u, true);
    check(r.consume_event && r.consumed_buttons == 0u,
          "unknown button does not escape panel or corrupt bit mask");
    r = tournament_p2_modal_input(0u, true, kA, true);
    r = tournament_p2_modal_input(r.consumed_buttons, true, kA, false);
    r = tournament_p2_modal_input(r.consumed_buttons, false, kA, true);
    check(!r.consume_event, "press released inside panel does not block later press");

    static_assert(tournament_p2_modal_input(0u, true, kA, true).consume_event);
    static_assert(tournament_p2_modal_input(kA, false, kA, false).consume_event);
    static_assert(!tournament_p2_modal_input(0u, false, kA, true).consume_event);
    std::puts("local_tournament_p2_modal_input_test: ok");
    return EXIT_SUCCESS;
}
