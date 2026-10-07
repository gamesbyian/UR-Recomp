#pragma once

#include "widescreen_output_composition.hpp"
#include "uniracers_two_player_result.hpp"

#include <cstdint>
#include <string_view>

namespace ur::product {

enum class RunRecordCaptureKind : std::uint8_t {
    Disabled = 0,
    OnePlayerTimedRace = 1,
    OrdinaryTwoPlayerRace = 2,
};

struct RunRecordCapturePlan {
    RunRecordCaptureKind kind = RunRecordCaptureKind::Disabled;
    std::string_view provenance_mode{};
    bool capture_resolved_inputs = false;
    bool enable_one_player_timing = false;
    bool enable_one_player_ghosts = false;
    bool require_match_record = false;

    constexpr bool enabled() const noexcept {
        return kind != RunRecordCaptureKind::Disabled &&
               capture_resolved_inputs &&
               !provenance_mode.empty();
    }
};

/*
 * Pure product admission for the existing CompletedRunCapture carrier.
 *
 * The record codec already retains both P1 and P2 resolved 12-bit controller
 * words. This policy decides only which bounded product contexts may use that
 * carrier and which downstream product consumers have authority.
 *
 * ordinary_race_course is supplied by the title/course layer. False covers
 * event types whose completion semantics are not elapsed-time Race semantics
 * (Circuit/Stunt and any unclassified course).
 *
 * Ordinary 2P deliberately does not inherit the 1P timing HUD, PB/Previous
 * ghost selection, or ghost trace path. Its terminal result belongs to the
 * authoritative 2P result observer and checksum-bound match sidecar.
 */
constexpr RunRecordCapturePlan resolve_run_record_capture_plan(
    bool modern_mode,
    bool practice_active,
    HostRacePresentationMode race_mode,
    bool participants_ready,
    bool ordinary_race_course) noexcept {
    if (!modern_mode || practice_active || !ordinary_race_course) {
        return {};
    }

    switch (race_mode) {
    case HostRacePresentationMode::OnePlayer:
        return {
            RunRecordCaptureKind::OnePlayerTimedRace,
            "race-1p",
            true,
            true,
            true,
            false,
        };

    case HostRacePresentationMode::TwoPlayer:
        if (!participants_ready) return {};
        return {
            RunRecordCaptureKind::OrdinaryTwoPlayerRace,
            "race-2p",
            true,
            false,
            false,
            true,
        };

    case HostRacePresentationMode::Vs:
    case HostRacePresentationMode::Unknown:
    default:
        return {};
    }
}

/*
 * CompletedRunRecord requires one elapsed_ticks60 carrier value even though
 * ordinary 2P standings are owned by the stock result pair in hundredths.
 * Use the earliest authoritative result value only as replay-carrier timing.
 * This value must never be used for multiplayer ranking/PB semantics.
 */
constexpr std::uint64_t ordinary_two_player_carrier_elapsed_ticks60(
    const ur::title::OrdinaryTwoPlayerRaceResult& result) noexcept {
    const std::uint16_t decisive_hundredths =
        result.player1_hundredths < result.player2_hundredths
            ? result.player1_hundredths
            : result.player2_hundredths;
    return (
        static_cast<std::uint64_t>(decisive_hundredths) * 60u + 50u) / 100u;
}

}  // namespace ur::product
