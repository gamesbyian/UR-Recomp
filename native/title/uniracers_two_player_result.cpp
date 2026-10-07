#include "uniracers_two_player_result.hpp"

namespace ur::title {
namespace {

constexpr std::size_t kCurrentMenu = 0x009Fu;
constexpr std::size_t kPlayer1Rider = 0x017Du;
constexpr std::size_t kPlayer2Rider = 0x017Fu;
constexpr std::size_t kLastRaceResultP1 = 0x0618u;
constexpr std::size_t kLastRaceResultP2 = 0x061Au;
constexpr std::uint8_t kMultiplayerRaceResultMenu = 0xF9u;
constexpr std::uint8_t kStockRiderCount = 16u;

std::uint16_t read_le16(const std::uint8_t* data, std::size_t offset) noexcept {
    return static_cast<std::uint16_t>(
        static_cast<std::uint16_t>(data[offset]) |
        (static_cast<std::uint16_t>(data[offset + 1u]) << 8u));
}

}  // namespace

std::optional<OrdinaryTwoPlayerRaceResult>
observe_ordinary_two_player_race_result(
    bool ordinary_two_player,
    const std::uint8_t* wram,
    std::size_t wram_size,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept {
    if (!ordinary_two_player || !wram || !sram ||
        wram_size <= kPlayer2Rider ||
        sram_size < kLastRaceResultP2 + 2u ||
        wram[kCurrentMenu] != kMultiplayerRaceResultMenu) {
        return std::nullopt;
    }

    const std::uint8_t p1_rider = wram[kPlayer1Rider];
    const std::uint8_t p2_rider = wram[kPlayer2Rider];
    if (p1_rider >= kStockRiderCount || p2_rider >= kStockRiderCount) {
        return std::nullopt;
    }

    const std::uint16_t p1 = read_le16(sram, kLastRaceResultP1);
    const std::uint16_t p2 = read_le16(sram, kLastRaceResultP2);
    if (p1 > kOrdinaryTwoPlayerNoTimeHundredths ||
        p2 > kOrdinaryTwoPlayerNoTimeHundredths) {
        return std::nullopt;
    }

    OrdinaryTwoPlayerRaceResult result;
    result.player1_rider = p1_rider;
    result.player2_rider = p2_rider;
    result.player1_hundredths = p1;
    result.player2_hundredths = p2;

    if (p1 == p2) {
        result.outcome = OrdinaryTwoPlayerRaceOutcome::Draw;
    } else if (p1 == kOrdinaryTwoPlayerNoTimeHundredths) {
        result.outcome = OrdinaryTwoPlayerRaceOutcome::Player2Win;
    } else if (p2 == kOrdinaryTwoPlayerNoTimeHundredths || p1 < p2) {
        result.outcome = OrdinaryTwoPlayerRaceOutcome::Player1Win;
    } else {
        result.outcome = OrdinaryTwoPlayerRaceOutcome::Player2Win;
    }
    return result;
}

}  // namespace ur::title
