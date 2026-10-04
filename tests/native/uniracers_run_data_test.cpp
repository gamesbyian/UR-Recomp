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

    return 0;
}
