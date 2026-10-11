#pragma once

// Read-only adapter over the existing canonical checksum/course-bound 2P
// run+match catalog. No new match codec, native 2P producer or win authority.
#include <cstddef>
#include <string>

namespace ur::product {

struct BaldosaNativeTwoPlayerRecordsSummary {
    bool directory_available = false;
    std::size_t validated_pairs = 0;
    std::size_t unavailable_pairs = 0;
    std::size_t selected_profile_matches = 0;
    std::size_t wins = 0;
    std::size_t losses = 0;
    std::size_t draws = 0;
};

BaldosaNativeTwoPlayerRecordsSummary
inspect_baldosa_native_two_player_records_archive(
    const std::string& directory, const std::string& selected_profile_id);

}  // namespace ur::product
