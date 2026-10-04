#include "completed_run_ghost_world_sample.hpp"

#include <array>
#include <cassert>
#include <cstdint>

using namespace ur::product;

namespace {

void write_le16(
    std::array<std::uint8_t, 0x20000>& wram,
    std::size_t offset,
    std::uint16_t value) {
    wram[offset] = static_cast<std::uint8_t>(value & 0xFFu);
    wram[offset + 1] = static_cast<std::uint8_t>(value >> 8);
}

}  // namespace

int main() {
    std::array<std::uint8_t, 0x20000> wram{};
    write_le16(wram, 0x0411, 1655);
    write_le16(wram, 0x0415, 797);
    write_le16(wram, 0x04C7, 0x0037);
    wram[0x0BA1] = 1;
    write_le16(wram, 0x0FE9, 0x0541);
    write_le16(wram, 0x0FEB, 0x0540);
    write_le16(wram, 0x0D3F, 0x0D0D);
    write_le16(wram, 0x0D41, 0x0000);
    write_le16(wram, 0x0C83, 0);
    write_le16(wram, 0x0C85, 0);
    write_le16(wram, 0x0D1B, 0x0001);
    write_le16(wram, 0x0D1D, 0x0000);
    wram[0x150C] = 0x66;

    const auto sample =
        read_completed_run_ghost_world_sample(wram.data(), wram.size(), 123);
    assert(sample);
    assert(sample->race_frame == 123);
    assert(sample->world_x == 1655);
    assert(sample->world_y == 797);
    assert(sample->pitch_angle == 0x0037);
    assert(sample->semantic_frame_id == 0x0541);
    assert(sample->facing == 1);
    assert(sample->sprite_attr == 0x66);
    assert(sample->composition.p1_primary == 0x0541);
    assert(sample->composition.p2_primary == 0x0540);
    assert(sample->composition.p1_companion == 0x0D0D);
    assert(sample->composition.p2_companion == 0x0000);
    assert(sample->composition.p1_selector == 0);
    assert(sample->composition.p2_selector == 0);
    assert(sample->composition.p1_companion_gate_word == 0x0001);
    assert(sample->composition.p2_companion_gate_word == 0x0000);

    assert(!read_completed_run_ghost_world_sample(nullptr, wram.size(), 0));
    assert(!read_completed_run_ghost_world_sample(
        wram.data(), 0x0FEA, 0));

    return 0;
}
