#include "multiplayer_match_presentation.hpp"

#include "run_artifact_date.hpp"

#include <cstdio>

namespace ur::product {
namespace {

std::string participant_text(const HostProfileCatalogEntry& participant) {
    return participant.identity.name + " / " + participant.profile_id;
}

std::string outcome_text(
    ur::title::OrdinaryTwoPlayerRaceOutcome outcome) {
    switch (outcome) {
    case ur::title::OrdinaryTwoPlayerRaceOutcome::Player1Win:
        return "PLAYER 1 WIN";
    case ur::title::OrdinaryTwoPlayerRaceOutcome::Player2Win:
        return "PLAYER 2 WIN";
    case ur::title::OrdinaryTwoPlayerRaceOutcome::Draw:
    default:
        return "DRAW";
    }
}

}  // namespace

std::string format_multiplayer_result_hundredths(std::uint16_t hundredths) {
    if (hundredths == ur::title::kOrdinaryTwoPlayerNoTimeHundredths) {
        return "NO TIME";
    }
    const unsigned minutes = hundredths / 6000u;
    const unsigned seconds = (hundredths / 100u) % 60u;
    const unsigned centis = hundredths % 100u;
    char text[32];
    std::snprintf(
        text, sizeof(text), "%u:%02u.%02u", minutes, seconds, centis);
    return text;
}

MultiplayerMatchRowPresentation present_multiplayer_match_row(
    const StoredMultiplayerMatch& match) {
    return {
        run_artifact_date_text(match.run_path),
        match.match.context.course_id,
        participant_text(match.match.context.match.player1),
        participant_text(match.match.context.match.player2),
        outcome_text(match.match.context.match.result.outcome),
    };
}

MultiplayerMatchDetailPresentation present_multiplayer_match_detail(
    const StoredMultiplayerMatch& match) {
    MultiplayerMatchDetailPresentation detail;
    detail.summary = present_multiplayer_match_row(match);
    detail.player1_result_text = format_multiplayer_result_hundredths(
        match.match.context.match.result.player1_hundredths);
    detail.player2_result_text = format_multiplayer_result_hundredths(
        match.match.context.match.result.player2_hundredths);
    detail.outcome_text =
        outcome_text(match.match.context.match.result.outcome);
    return detail;
}

}  // namespace ur::product
