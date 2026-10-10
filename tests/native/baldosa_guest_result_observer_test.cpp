#include "baldosa_guest_result_observer.hpp"

#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>

using ur::product::BaldosaGuestResultObserver;
using ur::product::BaldosaSettledResultKind;

namespace {
void write16(std::array<std::uint8_t, 0x20000>& mem,
             std::size_t offset, unsigned n) {
    mem[offset] = static_cast<std::uint8_t>(n & 0xffu);
    mem[offset + 1] = static_cast<std::uint8_t>(n >> 8u);
}
void write_sram16(std::array<std::uint8_t, 8192>& mem,
                  std::size_t offset, unsigned n) {
    mem[offset] = static_cast<std::uint8_t>(n & 0xffu);
    mem[offset + 1] = static_cast<std::uint8_t>(n >> 8u);
}
} // namespace

int main() {
    std::array<std::uint8_t, 0x20000> ram{};
    std::array<std::uint8_t, 8192> sram{};
    BaldosaGuestResultObserver observer{};
    const auto poll = [&](unsigned players, std::uint64_t frame,
                          std::uint32_t word = 0) {
        return observer.observe(players, ram.data(), ram.size(),
                                sram.data(), sram.size(), frame, word);
    };

    // Canonical decoded USA Race course:01, source course signature.
    // mode=0, A=(68,50), B=(68,50), dimensions=(256,4).
    write16(ram, 0x10000u + 0x03u, 68);
    write16(ram, 0x10000u + 0x05u, 50);
    write16(ram, 0x10000u + 0x07u, 68);
    write16(ram, 0x10000u + 0x09u, 50);
    ram[0x10000u + 0x0Du] = 0;  // decoded 256
    ram[0x10000u + 0x0Eu] = 4;

    // A results-looking guest without a witnessed real race is not a run.
    ram[0x009f] = 0x99;
    assert(!poll(1, 4));
    assert(!poll(2, 5));
    ram[0x0313] = 1;
    ram[0x009f] = 0x16;
    write16(ram, 0x0EF1, 3);
    assert(!poll(1, 10));
    assert(observer.race_seen());
    // No finish line was written, even if the menu claims RESULTS.
    ram[0x0313] = 0;
    ram[0x009f] = 0x99;
    assert(!poll(1, 11));
    // Back to the race. This must NOT replace the original entry stamp.
    ram[0x0313] = 1;
    ram[0x009f] = 0x16;
    assert(!poll(1, 12, 0x0015u));

    // Authoritative per-racer line snapshot on the frame laps reach zero,
    // with the *same-frame* shared sub-tick. Guest time 0:12.3 + 2/60.
    write16(ram, 0x0E13, 1); // tens-of-seconds digit
    write16(ram, 0x0E17, 2);
    write16(ram, 0x0E1B, 3);
    write16(ram, 0x0E1F, 2);
    write16(ram, 0x0E3D, 1); // saved finish tens-of-seconds
    write16(ram, 0x0E41, 2);
    write16(ram, 0x0E45, 3);
    write16(ram, 0x0E35, 5);
    write16(ram, 0x0EF1, 0);
    assert(!poll(1, 13, 0x0015u));
    // No settled result merely because a finish line was crossed.
    ram[0x0313] = 0;
    ram[0x009f] = 0x84;
    assert(!poll(1, 14));
    ram[0x009f] = 0x99;
    const auto p1 = poll(1, 15);
    assert(p1 && p1->kind == BaldosaSettledResultKind::TimedOnePlayerRace);
    assert(p1->first_race_host_frame == 10);
    assert(p1->observed_result_host_frame == 15);
    assert(p1->p1_finish_ticks60 == 740u);
    assert(p1->course_index == 1);
    assert(!p1->two_player);
    assert(p1->captured_input_frames == 5);
    assert(p1->mapped_inputs.size() == 1);
    assert(p1->mapped_inputs[0].start_frame == 1);
    assert(p1->mapped_inputs[0].duration == 2);
    assert(p1->mapped_inputs[0].p1_mask == 0x0015u);
    assert(p1->mapped_inputs[0].p2_mask == 0);
    assert(!poll(1, 16)); // same result must never emit twice

    // A guest that stopped without a new start can't emit another result.
    ram[0x009f] = 0x3c;
    assert(!poll(1, 17));
    ram[0x009f] = 0x99;
    assert(!poll(1, 18));

    // P2 spectator/guest result is NOT an ordinary 2P Race unless the
    // source-observed 2P stock handoff and active race are both present.
    ram[0x0313] = 1;
    assert(!poll(2, 30));
    ram[0x0313] = 0;
    ram[0x009f] = 0xf9;
    ram[0x017d] = 0; // Mike
    ram[0x017f] = 1; // Andrew
    assert(!poll(2, 31, 0x010002u)); // 0/0 SRAM is transient, not a draw.
    write_sram16(sram, 0x0618, 874);
    write_sram16(sram, 0x061a, 913);
    const auto two = poll(2, 32, 0x010002u);
    assert(two && two->kind ==
        BaldosaSettledResultKind::OrdinaryTwoPlayerRace);
    assert(two->first_race_host_frame == 30);
    assert(two->observed_result_host_frame == 32);
    assert(two->p1_finish_ticks60 == 0);
    assert(two->course_index == 1);
    assert(two->two_player);
    assert(two->two_player->player1_hundredths == 874);
    assert(two->two_player->player2_hundredths == 913);
    assert(two->two_player->outcome ==
        ur::title::OrdinaryTwoPlayerRaceOutcome::Player1Win);
    assert(two->captured_input_frames == 2);
    assert(two->mapped_inputs.size() == 1);
    assert(two->mapped_inputs[0].duration == 2);
    assert(two->mapped_inputs[0].p1_mask == 2);
    assert(two->mapped_inputs[0].p2_mask == 0x10u);
    assert(!poll(2, 33));

    // Missing host ownership, short guest memory and stock menu alone are
    // insufficient evidence, and no old result is carried between seats.
    observer.reset();
    assert(!poll(0, 34));
    assert(!observer.race_seen());
    assert(!observer.observe(2, ram.data(), 40, sram.data(),
                             sram.size(), 35));
    assert(!poll(2, 36));
    // A new 2P race invalidates the previous P1 result.
    ram[0x0313] = 1;
    assert(!poll(2, 40));
    ram[0x0313] = 0;
    ram[0x009f] = 0x99; // wrong 2P terminal, reject
    assert(!poll(2, 41));
    ram[0x009f] = 0xf9;
    ram[0x017f] = 255; // invalid rider, reject
    assert(!poll(2, 42));
    ram[0x017f] = 1;
    assert(poll(2, 43));

    // Unlike stale terminal screens, an entirely new genuine guest race
    // legitimately starts another single-result observation.
    ram[0x0313] = 1;
    assert(!poll(2, 44));
    assert(!poll(0, 45)); // frontend reentry revokes prior authority
    // Source-identified course:02 is a Circuit, not a Race. Even valid
    // 0x99/0xF9 plus SRAM time is not ordinary Race evidence there.
    write16(ram, 0x10000u + 0x03u, 575);
    write16(ram, 0x10000u + 0x05u, 93);
    write16(ram, 0x10000u + 0x07u, 575);
    write16(ram, 0x10000u + 0x09u, 93);
    ram[0x10000u + 0x0Du] = 64;
    ram[0x10000u + 0x0Eu] = 16;
    ram[0x0313] = 1;
    assert(!poll(2, 46));
    ram[0x0313] = 0;
    ram[0x009f] = 0xf9;
    assert(!poll(2, 47));
    // Now an invalid decoded-course header likewise fails closed.
    observer.reset();
    ram[0x10000u + 0x0Du] = 99;
    ram[0x0313] = 1;
    assert(!poll(2, 48));
    ram[0x0313] = 0;
    assert(!poll(2, 49));
    std::puts("PASS: source-backed Baldosa native result bridge rejects stale/partial outcomes");
}
