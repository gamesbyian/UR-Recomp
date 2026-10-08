#include "modern_host_input_release_latch.hpp"

#include <cstdint>
#include <cstdio>
#include <cstdlib>

using namespace ur::product;

namespace {

// SNES joypad bits as delivered by the SNESRecomp human P1 word.
constexpr std::uint32_t kB = 0x8000u;
constexpr std::uint32_t kStart = 0x1000u;
constexpr std::uint32_t kLeft = 0x0200u;
constexpr std::uint32_t kA = 0x0080u;

void check(bool ok, const char* what) {
    if (!ok) {
        std::fprintf(stderr, "FAIL: %s\n", what);
        std::exit(1);
    }
}

}  // namespace

int main() {
    // A fresh latch is transparent.
    {
        const auto r = modern_host_input_filter({}, false, kStart | kLeft);
        check(r.inputs == (kStart | kLeft), "fresh latch passes input");
        check(r.latch.held == 0u, "fresh latch holds nothing");
    }

    // Host ownership withholds the whole word.
    {
        const auto r = modern_host_input_filter({}, true, kStart | kA);
        check(r.inputs == 0u, "host-owned word is withheld");
        check(r.latch.held == (kStart | kA), "held bits are tracked");
    }

    // Closing edge: Start was held when the Welcome panel closed. It stays
    // withheld across several held frames and only a release clears it.
    {
        auto latch = modern_host_input_filter({}, true, kStart).latch;
        for (int frame = 0; frame < 8; ++frame) {
            const auto r = modern_host_input_filter(latch, false, kStart);
            check(r.inputs == 0u, "held Start does not leak after close");
            latch = r.latch;
        }
        auto r = modern_host_input_filter(latch, false, 0u);
        check(r.inputs == 0u && r.latch.held == 0u, "release clears latch");
        r = modern_host_input_filter(r.latch, false, kStart);
        check(r.inputs == kStart, "a new Start press after release passes");
    }

    // Bits pressed after close pass even while another bit stays latched.
    {
        auto latch = modern_host_input_filter({}, true, kStart).latch;
        auto r = modern_host_input_filter(latch, false, kStart | kLeft);
        check(r.inputs == kLeft, "new Left passes while Start is latched");
        r = modern_host_input_filter(r.latch, false, kLeft);
        check(r.inputs == kLeft && r.latch.held == 0u,
              "releasing Start clears only Start");
        r = modern_host_input_filter(r.latch, false, kLeft | kStart);
        check(r.inputs == (kLeft | kStart), "Start re-press passes");
    }

    // A bit pressed and released entirely inside host ownership is not
    // withheld afterwards.
    {
        auto latch = modern_host_input_filter({}, true, kB).latch;
        latch = modern_host_input_filter(latch, true, 0u).latch;
        const auto r = modern_host_input_filter(latch, false, kB);
        check(r.inputs == kB, "press inside host ownership does not latch");
    }

    // Partial release: only the released bit is cleared from the latch.
    {
        auto latch = modern_host_input_filter({}, true, kA | kB).latch;
        auto r = modern_host_input_filter(latch, false, kA);
        check(r.inputs == 0u && r.latch.held == kA, "partial release");
        r = modern_host_input_filter(r.latch, false, kA | kB);
        check(r.inputs == kB, "released B re-press passes, A still latched");
    }

    static_assert(modern_host_input_filter({}, true, kStart).inputs == 0u);
    static_assert(modern_host_input_filter({kStart}, false, kStart).inputs == 0u);
    static_assert(modern_host_input_filter({kStart}, false, kA).inputs == kA);
    std::puts("modern_host_input_release_latch_test: ok");
    return 0;
}
