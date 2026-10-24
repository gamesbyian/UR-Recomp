#include "native/product/modern_root_physical_edges.hpp"

#include <cassert>
#include <cstdio>

int main() {
    ur::product::ModernRootPhysicalEdges nav{};

    // Physical keyboard auto-repeat never traverses multiple destinations.
    assert(nav.keyboard(1, true));
    for (int i = 0; i < 30; ++i) assert(!nav.keyboard(1, true));
    assert(!nav.keyboard(1, false));
    assert(nav.keyboard(1, true));
    assert(!nav.keyboard(1, false));

    // Independent held keys never block legitimate other navigation.
    assert(nav.keyboard(0, true));
    assert(nav.keyboard(2, true));
    assert(!nav.keyboard(0, true));
    assert(!nav.keyboard(2, true));
    assert(!nav.keyboard(0, false));
    assert(!nav.keyboard(2, false));

    // Reopening the host root with Escape/B consumes that physical press.
    // The next repeat remains held until released even if host focus moves.
    assert(nav.keyboard(3, true));
    assert(!nav.keyboard(3, true));
    assert(!nav.keyboard(3, true));
    assert(!nav.keyboard(3, false));
    assert(nav.keyboard(3, true));

    // Independent P1 button latches: A and Start are separate Confirm keys.
    assert(nav.p1_gamepad(2, true));
    assert(!nav.p1_gamepad(2, true));
    assert(nav.p1_gamepad(3, true));
    assert(!nav.p1_gamepad(3, true));
    assert(!nav.p1_gamepad(2, false));
    assert(nav.p1_gamepad(2, true));
    assert(nav.p1_gamepad(4, true));
    assert(!nav.p1_gamepad(4, true));
    assert(!nav.p1_gamepad(4, false));
    assert(nav.p1_gamepad(4, true));

    // New first-racer X uses its own release latch. It must neither
    // auto-repeat a create nor consume normal A/B player navigation.
    assert(nav.keyboard(4, true));
    assert(!nav.keyboard(4, true));
    assert(!nav.keyboard(4, false));
    assert(nav.keyboard(4, true));
    assert(nav.p1_gamepad(5, true));
    assert(!nav.p1_gamepad(5, true));
    assert(!nav.p1_gamepad(5, false));
    assert(nav.p1_gamepad(5, true));

    // LEFT/RIGHT (native OPTIONS value changes) latch independently of every
    // other key: holding one never auto-repeats and never blocks navigation.
    assert(nav.keyboard(5, true));
    assert(!nav.keyboard(5, true));
    assert(nav.keyboard(6, true));
    assert(!nav.keyboard(6, true));
    assert(!nav.keyboard(5, false));
    assert(nav.keyboard(5, true));
    assert(nav.p1_gamepad(6, true));
    assert(!nav.p1_gamepad(6, true));
    assert(nav.p1_gamepad(7, true));
    assert(!nav.p1_gamepad(7, true));
    assert(!nav.p1_gamepad(6, false));
    assert(nav.p1_gamepad(6, true));
    assert(!nav.keyboard(7, true));   // one past the last keyboard slot
    assert(!nav.p1_gamepad(8, true)); // one past the last pad slot

    // Invalid physical slots cannot create a ghost press or cross seats.
    assert(!nav.keyboard(99, true));
    assert(!nav.p1_gamepad(99, true));

    nav.reset();
    assert(nav.keyboard(3, true));
    assert(nav.p1_gamepad(4, true));
    // P2's orphan-reentry B edge uses its existing join-seat latch,
    // independent of P1 navigation. A held B cannot reopen on repeat, and
    // an intervening release is required for a new attempt at stock main.
    ur::product::ModernRootPhysicalEdges p2_join{};
    assert(p2_join.p1_gamepad(4, true));
    assert(!p2_join.p1_gamepad(4, true));
    assert(!p2_join.p1_gamepad(4, true));
    assert(!p2_join.p1_gamepad(4, false));
    assert(p2_join.p1_gamepad(4, true));
    assert(!p2_join.p1_gamepad(4, false));
    // A disconnected/rejoined source can start a fresh edge after the
    // existing root/seat reset; it never mutates P1's separate latch.
    p2_join.reset();
    assert(p2_join.p1_gamepad(4, true));
    assert(!nav.p1_gamepad(4, true));

    std::puts("PASS: native Modern root keyboard/P1 physical release edge authority");
}
