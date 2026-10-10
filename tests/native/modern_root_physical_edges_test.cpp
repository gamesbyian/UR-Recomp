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

    // Invalid physical slots cannot create a ghost press or cross seats.
    assert(!nav.keyboard(99, true));
    assert(!nav.p1_gamepad(99, true));

    nav.reset();
    assert(nav.keyboard(3, true));
    assert(nav.p1_gamepad(4, true));
    std::puts("PASS: native Modern root keyboard/P1 physical release edge authority");
}
