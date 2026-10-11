#include "baldosa_native_multiplayer_records_summary.hpp"

#include "multiplayer_match_catalog.hpp"
#include "multiplayer_match_summary.hpp"

#include <filesystem>
#include <system_error>
#include <vector>

namespace ur::product {

BaldosaNativeTwoPlayerRecordsSummary
inspect_baldosa_native_two_player_records_archive(
    const std::string& directory, const std::string& selected_profile_id) {
    BaldosaNativeTwoPlayerRecordsSummary out{};
    if (directory.empty() || selected_profile_id.empty()) return out;
    namespace fs = std::filesystem;
    std::error_code ec;
    const auto status = fs::symlink_status(directory, ec);
    if (status.type() == fs::file_type::not_found) {
        if (!ec || ec == std::errc::no_such_file_or_directory)
            out.directory_available = true;
        return out;
    }
    if (ec || fs::is_symlink(status) || !fs::is_directory(status))
        return out;
    out.directory_available = true;
    const auto inspected = inspect_multiplayer_match_artifacts(directory);
    std::vector<StoredMultiplayerMatch> admitted;
    for (const auto& item : inspected) {
        if (item.loaded())
            admitted.push_back(*item.stored);
        else
            ++out.unavailable_pairs;
    }
    out.validated_pairs = admitted.size();
    const auto totals = summarize_multiplayer_matches(admitted);
    const auto* selected = find_multiplayer_profile_record(
        totals, selected_profile_id);
    if (selected) {
        out.selected_profile_matches = selected->played;
        out.wins = selected->wins;
        out.losses = selected->losses;
        out.draws = selected->draws;
    }
    return out;
}

} // namespace ur::product
