#include "uniracers_run_data.h"

#include <cassert>
#include <cstddef>
#include <vector>

namespace {

void write16(std::vector<unsigned char>& wram, std::size_t offset, int value) {
    wram[offset] = static_cast<unsigned char>(value & 0xFF);
    wram[offset + 1] = static_cast<unsigned char>((value >> 8) & 0xFF);
}

}  // namespace

int main() {
    std::vector<unsigned char> wram(0x20000, 0);
    write16(wram, 0x0E0F, 2);
    write16(wram, 0x0E13, 4);
    write16(wram, 0x0E17, 7);
    write16(wram, 0x0E1B, 3);
    write16(wram, 0x0E1F, 5);

    const auto valid =
        ur_uniracers_read_run_data(wram.data(), wram.size());
    assert(valid.valid);
    assert(valid.minutes == 2);
    assert(valid.tens_seconds == 4);
    assert(valid.seconds == 7);
    assert(valid.tenths == 3);
    assert(valid.sub_tick == 5);
    assert(ur_uniracers_run_data_ticks60(valid) == 10043);

    assert(!ur_uniracers_read_run_data(nullptr, wram.size()).valid);
    assert(!ur_uniracers_read_run_data(wram.data(), 0x0E20).valid);
    assert(ur_uniracers_run_data_ticks60(UrUniracersRunData{}) == -1);

    write16(wram, 0x0E13, 6);
    assert(!ur_uniracers_read_run_data(wram.data(), wram.size()).valid);

    // Line-crossing snapshots, measured on the native Dragster route: P1's
    // finish copy reads 0:28.5 with hundredths digit 6 (stock "0:28.56")
    // while the shared timer at the end of that frame is 0:28.5 + 4 ticks.
    // Slot 1 (player 2) holds 0:27.9 / 8 at the same time.
    std::vector<unsigned char> line(0x20000, 0);
    const auto write_slot = [&](int player, int h, int m, int t, int s, int d) {
        const std::size_t slot = static_cast<std::size_t>(player) * 2u;
        write16(line, 0x0E35 + slot, h);
        write16(line, 0x0E39 + slot, m);
        write16(line, 0x0E3D + slot, t);
        write16(line, 0x0E41 + slot, s);
        write16(line, 0x0E45 + slot, d);
    };
    write_slot(0, 6, 0, 2, 8, 5);
    write_slot(1, 8, 0, 2, 7, 9);
    const auto p1 = ur_uniracers_read_line_snapshot(line.data(), line.size(), 0);
    const auto p2 = ur_uniracers_read_line_snapshot(line.data(), line.size(), 1);
    assert(p1.valid && p1.minutes == 0 && p1.tens_seconds == 2 &&
           p1.seconds == 8 && p1.tenths == 5 && p1.hundredths == 6);
    assert(p2.valid && p2.seconds == 7 && p2.tenths == 9 && p2.hundredths == 8);
    assert(!ur_uniracers_line_snapshot_equal(p1, p2));
    assert(ur_uniracers_line_snapshot_equal(p1, p1));
    assert(!ur_uniracers_read_line_snapshot(line.data(), line.size(), 2).valid);
    assert(!ur_uniracers_read_line_snapshot(nullptr, line.size(), 0).valid);
    assert(!ur_uniracers_read_line_snapshot(line.data(), 0x0E48, 0).valid);

    UrUniracersRunData shared{1, 0, 2, 8, 5, 4};
    // 28 s * 60 + 5 tenths * 6 + 4 = 1714 exact ticks.
    assert(ur_uniracers_line_snapshot_ticks60(shared, p1) == 1714);
    shared.sub_tick = 0;
    assert(ur_uniracers_line_snapshot_ticks60(shared, p1) == 1710);
    // Carry after the copy: shared already at the next tenth's first tick.
    shared = UrUniracersRunData{1, 0, 2, 8, 6, 0};
    assert(ur_uniracers_line_snapshot_ticks60(shared, p1) == 1715);
    // Anything further away cannot be the same instant.
    shared.sub_tick = 1;
    assert(ur_uniracers_line_snapshot_ticks60(shared, p1) == -1);
    shared = UrUniracersRunData{1, 0, 3, 2, 5, 4};  // results-time shared timer
    assert(ur_uniracers_line_snapshot_ticks60(shared, p1) == -1);
    assert(ur_uniracers_line_snapshot_ticks60(UrUniracersRunData{}, p1) == -1);
    assert(ur_uniracers_line_snapshot_ticks60(
               UrUniracersRunData{1, 0, 2, 8, 5, 4},
               UrUniracersLineSnapshot{}) == -1);

    write16(line, 0x0EF1, 0);
    write16(line, 0x0EF3, 1);
    assert(ur_uniracers_read_laps_remaining(line.data(), line.size(), 0) == 0);
    assert(ur_uniracers_read_laps_remaining(line.data(), line.size(), 1) == 1);
    assert(ur_uniracers_read_laps_remaining(line.data(), line.size(), 2) == -1);
    assert(ur_uniracers_read_laps_remaining(nullptr, line.size(), 0) == -1);

    write16(line, 0x0E45, 10);  // tenths out of range
    assert(!ur_uniracers_read_line_snapshot(line.data(), line.size(), 0).valid);

    return 0;
}
