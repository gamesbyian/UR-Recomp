#include "baldosa_native_run_record_admission.hpp"

#include "run_record_capture_policy.hpp"

#include <cstdio>
#include <utility>

namespace ur::product {

std::optional<CompletedRunRecord> assemble_baldosa_native_run_record(
    const BaldosaSettledResult& observed,
    const BaldosaRunRecordAuthority& authority) {
    if (!authority.selected_named_profile_verified ||
        observed.course_index < 1 || observed.course_index > 45 ||
        observed.first_race_host_frame == 0 ||
        observed.first_race_host_frame >= observed.observed_result_host_frame ||
        observed.captured_input_frames == 0 ||
        observed.captured_input_frames !=
            observed.observed_result_host_frame -
            observed.first_race_host_frame)
        return std::nullopt;

    const int tour_slot = ((observed.course_index - 1) % 5) + 1;
    if (tour_slot != 1 && tour_slot != 4) return std::nullopt;
    const bool one_player =
        observed.kind == BaldosaSettledResultKind::TimedOnePlayerRace;
    const bool two_player =
        observed.kind == BaldosaSettledResultKind::OrdinaryTwoPlayerRace;

    std::uint64_t elapsed_ticks60 = 0;
    if (one_player) {
        if (observed.two_player || !observed.p1_finish_ticks60 ||
            observed.p1_finish_ticks60 > 35999u)
            return std::nullopt;
        elapsed_ticks60 = observed.p1_finish_ticks60;
    } else if (two_player) {
        if (!authority.multiplayer_participants_bound ||
            !observed.two_player || observed.p1_finish_ticks60 != 0 ||
            (!observed.two_player->player1_finished() &&
             !observed.two_player->player2_finished()))
            return std::nullopt;
        // Revalidate the source result's internally consistent rider and
        // outcome fields before admitting a carrier record. A typed object
        // passed from outside the actual guest observer is not, by itself,
        // proof that the result was authored by the cartridge.
        const auto& match = *observed.two_player;
        const auto no_time = ur::title::kOrdinaryTwoPlayerNoTimeHundredths;
        if (match.player1_rider >= 16u || match.player2_rider >= 16u ||
            match.player1_hundredths > no_time ||
            match.player2_hundredths > no_time ||
            match.player1_hundredths == 0 ||
            match.player2_hundredths == 0)
            return std::nullopt;
        ur::title::OrdinaryTwoPlayerRaceOutcome expected{};
        if (match.player1_hundredths == match.player2_hundredths) {
            expected = ur::title::OrdinaryTwoPlayerRaceOutcome::Draw;
        } else if (match.player1_hundredths == no_time) {
            expected = ur::title::OrdinaryTwoPlayerRaceOutcome::Player2Win;
        } else if (match.player2_hundredths == no_time ||
                   match.player1_hundredths < match.player2_hundredths) {
            expected = ur::title::OrdinaryTwoPlayerRaceOutcome::Player1Win;
        } else {
            expected = ur::title::OrdinaryTwoPlayerRaceOutcome::Player2Win;
        }
        if (match.outcome != expected) return std::nullopt;
        elapsed_ticks60 =
            ordinary_two_player_carrier_elapsed_ticks60(match);
        if (!elapsed_ticks60) return std::nullopt;
    } else {
        return std::nullopt;
    }

    char course[16]{};
    std::snprintf(course, sizeof(course), "course:%02d",
                  observed.course_index);
    CompletedRunRecord record{};
    record.provenance = {
        "uniracers-usa",
        "859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478",
        kBaldosaNativeRunCompatId,
        course,
        one_player ? "race-1p" : "race-2p",
    };
    record.elapsed_ticks60 = elapsed_ticks60;
    record.frame_count = observed.captured_input_frames;
    record.inputs = observed.mapped_inputs;
    if (one_player)
        record.splits.push_back({"finish", elapsed_ticks60});
    return validate_completed_run_record(record)
        ? std::optional<CompletedRunRecord>(std::move(record))
        : std::nullopt;
}

} // namespace ur::product
