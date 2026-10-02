#include "racer_guest_snapshot.hpp"

#include <array>
#include <cassert>
#include <cstdint>

using namespace ur::presentation;

namespace {

void write_le16(std::array<std::uint8_t, 0x20000>& wram, std::size_t offset, std::uint16_t value) {
    wram[offset] = static_cast<std::uint8_t>(value & 0xFF);
    wram[offset + 1] = static_cast<std::uint8_t>(value >> 8);
}

std::array<std::uint8_t, 0x20000> exact_fixture() {
    std::array<std::uint8_t, 0x20000> wram{};
    write_le16(wram, 0x0FE9, 0x0541);
    write_le16(wram, 0x0FEB, 0x0540);
    write_le16(wram, 0x0D3F, 0x0D0D);
    write_le16(wram, 0x0D41, 0x0000);
    write_le16(wram, 0x0C83, 0x0000);
    write_le16(wram, 0x0C85, 0x0000);
    write_le16(wram, 0x0D1B, 0x0001);
    write_le16(wram, 0x0D1D, 0x0000);
    return wram;
}

}  // namespace

int main() {
    const auto wram = exact_fixture();
    const auto snapshot = read_racer_guest_snapshot(wram.data(), wram.size());
    assert(snapshot.has_value());
    assert(snapshot->p1_semantic_frame_id == 0x0541);
    assert(snapshot->p2_semantic_frame_id == 0x0540);
    assert(snapshot->composition.p1_companion == 0x0D0D);
    assert(snapshot->composition.p1_companion_gate_word == 0x0001);

    const auto p1 = select_racer_presentation_from_wram(
        GraphicsPack::Remastered, wram.data(), wram.size(), 1
    );
    assert(p1.uses_replacement());
    assert(p1.selected_pack == GraphicsPack::Remastered);

    const auto p2 = select_racer_presentation_from_wram(
        GraphicsPack::Remastered, wram.data(), wram.size(), 2
    );
    assert(!p2.uses_replacement());
    assert(p2.selected_pack == GraphicsPack::Original);
    assert(p2.fallback_reason == FallbackReason::UnregisteredSemanticFrame);

    auto mismatch = wram;
    write_le16(mismatch, 0x0D1B, 0x0000);
    const auto mismatch_result = select_racer_presentation_from_wram(
        GraphicsPack::Remastered, mismatch.data(), mismatch.size(), 1
    );
    assert(!mismatch_result.uses_replacement());
    assert(mismatch_result.fallback_reason == FallbackReason::CompositionMismatch);

    const auto short_result = select_racer_presentation_from_wram(
        GraphicsPack::Remastered, wram.data(), 0x1000, 1
    );
    assert(!short_result.uses_replacement());
    assert(short_result.selected_pack == GraphicsPack::Original);

    const auto invalid_player = select_racer_presentation_from_wram(
        GraphicsPack::Remastered, wram.data(), wram.size(), 3
    );
    assert(!invalid_player.uses_replacement());
    assert(invalid_player.selected_pack == GraphicsPack::Original);

    return 0;
}
