#pragma once

// Read-only, source-backed result admission for one actual Baldosa guest.
// This bridges established title observers to the existing Modern record
// authority. It is NOT a new Records store or permission to grant trophies.
//
// Called exactly once AFTER a real guest frame; the native root supplies
// its already-acknowledged stock one-/two-player handoff.
#include "uniracers_run_data.h"
#include "uniracers_two_player_result.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>

namespace ur::product {

enum class BaldosaSettledResultKind : std::uint8_t {
    TimedOnePlayerRace,
    OrdinaryTwoPlayerRace,
};

struct BaldosaSettledResult {
    BaldosaSettledResultKind kind = BaldosaSettledResultKind::TimedOnePlayerRace;
    std::uint64_t first_race_host_frame = 0;
    std::uint64_t observed_result_host_frame = 0;
    // The official P1 finish line, not the clock at the results screen.
    std::uint64_t p1_finish_ticks60 = 0;
    // Populated only for ordinary 2P Race, from genuine result SRAM.
    std::optional<ur::title::OrdinaryTwoPlayerRaceResult> two_player;
};

class BaldosaGuestResultObserver {
public:
    void reset() noexcept;

    // Zero players revokes all state. 1/2 must come from a source-observed
    // title handoff, not from an arbitrary transient menu state.
    std::optional<BaldosaSettledResult> observe(
        unsigned players, const std::uint8_t* wram, std::size_t wram_size,
        const std::uint8_t* sram, std::size_t sram_size,
        std::uint64_t host_frame) noexcept;

    bool race_seen() const noexcept { return saw_race_; }

private:
    unsigned players_ = 0;
    bool saw_race_ = false;
    bool emitted_ = false;
    std::uint64_t first_race_frame_ = 0;
    UrUniracersLineSnapshot previous_line_{};
    std::optional<std::uint64_t> p1_finish_ticks60_;
};

} // namespace ur::product
