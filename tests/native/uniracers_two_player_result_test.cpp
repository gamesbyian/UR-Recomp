#include "uniracers_two_player_result.hpp"

#include <array>
#include <cassert>
#include <cstdint>

using namespace ur::title;

namespace {

void write_le16(
    std::array<std::uint8_t, 8192>& sram,
    std::size_t offset,
    std::uint16_t value) {
    sram[offset] = static_cast<std::uint8_t>(value & 0xffu);
    sram[offset + 1u] = static_cast<std::uint8_t>(value >> 8u);
}

}  // namespace

int main() {
    std::array<std::uint8_t, 65536> wram{};
    std::array<std::uint8_t, 8192> sram{};

    wram[0x009F] = 0xF9;
    wram[0x017D] = 0;
    wram[0x017F] = 1;

    // Promoted ordinary-2P fixture: MIKE finishes in 28.76, ANDREW has NO TIME.
    write_le16(sram, 0x0618, 2876);
    write_le16(sram, 0x061A, kOrdinaryTwoPlayerNoTimeHundredths);
    const auto p1 = observe_ordinary_two_player_race_result(
        true, wram.data(), wram.size(), sram.data(), sram.size());
    assert(p1);
    assert(p1->player1_rider == 0);
    assert(p1->player2_rider == 1);
    assert(p1->player1_finished());
    assert(!p1->player2_finished());
    assert(p1->outcome == OrdinaryTwoPlayerRaceOutcome::Player1Win);

    write_le16(sram, 0x0618, 3100);
    write_le16(sram, 0x061A, 3000);
    const auto p2 = observe_ordinary_two_player_race_result(
        true, wram.data(), wram.size(), sram.data(), sram.size());
    assert(p2);
    assert(p2->outcome == OrdinaryTwoPlayerRaceOutcome::Player2Win);

    write_le16(sram, 0x0618, kOrdinaryTwoPlayerNoTimeHundredths);
    write_le16(sram, 0x061A, kOrdinaryTwoPlayerNoTimeHundredths);
    const auto draw = observe_ordinary_two_player_race_result(
        true, wram.data(), wram.size(), sram.data(), sram.size());
    assert(draw);
    assert(draw->outcome == OrdinaryTwoPlayerRaceOutcome::Draw);

    write_le16(sram, 0x0618, 3000);
    write_le16(sram, 0x061A, 3000);
    const auto tied_finish = observe_ordinary_two_player_race_result(
        true, wram.data(), wram.size(), sram.data(), sram.size());
    assert(tied_finish);
    assert(tied_finish->outcome == OrdinaryTwoPlayerRaceOutcome::Draw);

    assert(!observe_ordinary_two_player_race_result(
        false, wram.data(), wram.size(), sram.data(), sram.size()));

    wram[0x009F] = 0x99;
    assert(!observe_ordinary_two_player_race_result(
        true, wram.data(), wram.size(), sram.data(), sram.size()));
    wram[0x009F] = 0xF9;

    wram[0x017F] = 16;
    assert(!observe_ordinary_two_player_race_result(
        true, wram.data(), wram.size(), sram.data(), sram.size()));
    wram[0x017F] = 1;

    write_le16(sram, 0x0618, 60001);
    assert(!observe_ordinary_two_player_race_result(
        true, wram.data(), wram.size(), sram.data(), sram.size()));

    return 0;
}
