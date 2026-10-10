// Link the REAL shipped C ABI bridge against a fake acknowledgement only.
// This asserts whether a failed pause can wrongly steal P1/P2 guest input.
#include <cassert>
#include <cstdint>

extern "C" std::uint32_t ur_baldosa_product_filter_human_frame_inputs(
    std::uint32_t word, unsigned frame);
extern "C" int ur_baldosa_product_set_paused(int paused);
extern "C" void ur_baldosa_product_set_host_focus(int owned);
extern "C" int ur_baldosa_product_queue_stock_menu_input(std::uint16_t mask);
extern "C" void ur_baldosa_product_guest_restarted(void);

namespace {
bool reject;
bool paused;
int requests;
}
extern "C" int snesrecomp_desktop_product_set_paused(int wanted) {
    ++requests;
    if (reject) return 0;
    paused = wanted != 0;
    return 1;
}

int main() {
    constexpr std::uint32_t ports = 0xc0000000u;
    constexpr std::uint32_t start = 1u << 3;
    constexpr std::uint32_t p2_start = start << 12;
    constexpr std::uint32_t p1_a = 1u << 8;
    constexpr std::uint32_t held = ports | start | p2_start;
    assert(ur_baldosa_product_filter_human_frame_inputs(held, 0) == held);
    reject = true;
    assert(!ur_baldosa_product_set_paused(1));
    assert(!paused && requests == 1);
    assert(ur_baldosa_product_filter_human_frame_inputs(held, 1) == held);
    reject = false;
    assert(ur_baldosa_product_set_paused(1));
    assert(paused);
    assert(ur_baldosa_product_filter_human_frame_inputs(held, 2) == ports);
    reject = true;
    assert(!ur_baldosa_product_set_paused(0));
    assert(paused);
    assert(ur_baldosa_product_filter_human_frame_inputs(held, 3) == ports);
    reject = false;
    assert(ur_baldosa_product_set_paused(0));
    assert(!paused);
    // A held P1/P2 Start is withheld across resume until observed key-up,
    // including independently released seats.
    assert(ur_baldosa_product_filter_human_frame_inputs(held, 4) == ports);
    assert(ur_baldosa_product_filter_human_frame_inputs(
               ports | p2_start, 5) == ports);
    assert(ur_baldosa_product_filter_human_frame_inputs(ports, 6) == ports);
    assert(ur_baldosa_product_filter_human_frame_inputs(
               ports | start, 7) == (ports | start));
    assert(ur_baldosa_product_filter_human_frame_inputs(
               ports | p2_start, 8) == (ports | p2_start));
    ur_baldosa_product_guest_restarted();
    assert(ur_baldosa_product_filter_human_frame_inputs(
               ports | p1_a, 9) == ports);
    assert(ur_baldosa_product_filter_human_frame_inputs(ports, 10) == ports);
    assert(ur_baldosa_product_filter_human_frame_inputs(
               ports | p1_a, 11) == (ports | p1_a));

    // Restart while the real host remains paused MUST NOT return guest focus.
    assert(ur_baldosa_product_set_paused(1));
    assert(ur_baldosa_product_filter_human_frame_inputs(held, 12) == ports);
    ur_baldosa_product_guest_restarted();
    assert(ur_baldosa_product_filter_human_frame_inputs(held, 13) == ports);
    assert(ur_baldosa_product_set_paused(0));
    assert(ur_baldosa_product_filter_human_frame_inputs(held, 14) == ports);
    assert(ur_baldosa_product_filter_human_frame_inputs(ports, 15) == ports);
    assert(ur_baldosa_product_filter_human_frame_inputs(
               ports | p2_start, 16) == (ports | p2_start));

    // Stock 1P/2P routing crosses exactly the already-owned human input seam.
    // No guest writes, no second pad/SDL loop, no carried button on release.
    assert(!ur_baldosa_product_queue_stock_menu_input(0x0100u));
    ur_baldosa_product_set_host_focus(1);
    assert(!ur_baldosa_product_queue_stock_menu_input(0xffffu));
    assert(!ur_baldosa_product_queue_stock_menu_input(0u));
    assert(ur_baldosa_product_queue_stock_menu_input(0x0100u));
    assert(!ur_baldosa_product_queue_stock_menu_input(0x0020u));
    assert(ur_baldosa_product_filter_human_frame_inputs(
               ports | held, 17) == (ports | 0x0100u));
    assert(ur_baldosa_product_filter_human_frame_inputs(
               ports | held, 18) == ports);
    assert(ur_baldosa_product_queue_stock_menu_input(0x0020u));
    ur_baldosa_product_set_host_focus(0);
    assert(!ur_baldosa_product_queue_stock_menu_input(0x0100u));
    assert(ur_baldosa_product_filter_human_frame_inputs(
               ports | held, 19) == ports);
    return 0;
}
