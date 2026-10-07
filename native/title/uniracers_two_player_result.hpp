#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>

namespace ur::title {

constexpr std::uint16_t kOrdinaryTwoPlayerNoTimeHundredths = 60000u;

enum class OrdinaryTwoPlayerRaceOutcome : std::uint8_t {
    Draw = 0,
    Player1Win = 1,
    Player2Win = 2,
};

struct OrdinaryTwoPlayerRaceResult {
    std::uint8_t player1_rider = 0;
    std::uint8_t player2_rider = 0;
    std::uint16_t player1_hundredths = kOrdinaryTwoPlayerNoTimeHundredths;
    std::uint16_t player2_hundredths = kOrdinaryTwoPlayerNoTimeHundredths;
    OrdinaryTwoPlayerRaceOutcome outcome = OrdinaryTwoPlayerRaceOutcome::Draw;

    bool player1_finished() const noexcept {
        return player1_hundredths < kOrdinaryTwoPlayerNoTimeHundredths;
    }
    bool player2_finished() const noexcept {
        return player2_hundredths < kOrdinaryTwoPlayerNoTimeHundredths;
    }
};

/*
 * Read-only observer for the validated ordinary two-player Race result.
 *
 * The caller owns session classification and must pass ordinary_two_player=true
 * only for the established stock ordinary-2P route. The observer independently
 * requires the verified multiplayer Race result menu (0xF9), stock rider
 * identities, and the stock last-result pair in SRAM.
 *
 * It never writes guest memory and deliberately does not interpret Circuit or
 * Stunt result values as race times.
 */
std::optional<OrdinaryTwoPlayerRaceResult>
observe_ordinary_two_player_race_result(
    bool ordinary_two_player,
    const std::uint8_t* wram,
    std::size_t wram_size,
    const std::uint8_t* sram,
    std::size_t sram_size) noexcept;

}  // namespace ur::title
