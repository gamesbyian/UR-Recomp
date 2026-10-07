#pragma once

#include "multiplayer_match_catalog.hpp"

#include <string>

namespace ur::product {

struct MultiplayerMatchRowPresentation {
    std::string course_text;
    std::string player1_text;
    std::string player2_text;
    std::string result_text;
};

struct MultiplayerMatchDetailPresentation {
    MultiplayerMatchRowPresentation summary;
    std::string player1_result_text;
    std::string player2_result_text;
    std::string outcome_text;
};

std::string format_multiplayer_result_hundredths(std::uint16_t hundredths);

MultiplayerMatchRowPresentation present_multiplayer_match_row(
    const StoredMultiplayerMatch& match);

MultiplayerMatchDetailPresentation present_multiplayer_match_detail(
    const StoredMultiplayerMatch& match);

}  // namespace ur::product
