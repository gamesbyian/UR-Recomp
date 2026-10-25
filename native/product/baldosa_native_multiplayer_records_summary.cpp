#include "baldosa_native_multiplayer_records_summary.hpp"

#include "multiplayer_match_catalog.hpp"
#include "local_tournament_utf8_path.hpp"
#include "multiplayer_match_summary.hpp"

#include <cctype>
#include <cstdio>
#include <filesystem>
#include <system_error>
#include <utility>
#include <vector>

namespace ur::product {

BaldosaNativeTwoPlayerRecordsSummary
inspect_baldosa_native_two_player_records_archive(
    const std::string& directory, const std::string& selected_profile_id) {
    BaldosaNativeTwoPlayerRecordsSummary out{};
    if (directory.empty() || selected_profile_id.empty()) return out;
    namespace fs = std::filesystem;
    std::error_code ec;
    const auto status = fs::symlink_status(host_native_path_from_utf8(directory), ec);
    if (status.type() == fs::file_type::not_found) {
        if (!ec || ec == std::errc::no_such_file_or_directory)
            out.directory_available = true;
        return out;
    }
    if (ec || fs::is_symlink(status) || !fs::is_directory(status))
        return out;
    bool scan_succeeded = false;
    auto inspected = inspect_multiplayer_match_artifacts(
        directory, &scan_succeeded);
    if (!scan_succeeded) return out;
    out.directory_available = true;
    std::vector<StoredMultiplayerMatch> admitted;
    admitted.reserve(inspected.size());
    for (auto& item : inspected) {
        if (item.loaded())
            admitted.push_back(std::move(*item.stored));
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
        // The catalog has already admitted matching checksummed run+sidecar
        // artifacts, sorted by the existing canonical filename chronology.
        // Preserve case-insensitive Windows profile identity and report the
        // latest match belonging to THIS profile, never an unrelated pair.
        const auto same_storage_id = [](const std::string& lhs,
                                        const std::string& rhs) {
            if (lhs.size() != rhs.size()) return false;
            for (std::size_t i = 0; i < lhs.size(); ++i) {
                if (std::tolower(static_cast<unsigned char>(lhs[i])) !=
                    std::tolower(static_cast<unsigned char>(rhs[i])))
                    return false;
            }
            return true;
        };
        for (auto it = admitted.rbegin(); it != admitted.rend(); ++it) {
            const auto& context = it->match.context;
            const bool first = same_storage_id(
                context.match.player1.profile_id, selected_profile_id);
            const bool second = same_storage_id(
                context.match.player2.profile_id, selected_profile_id);
            if (!first && !second) continue;
            const auto& result = context.match.result;
            const auto own_hundredths = first
                ? result.player1_hundredths : result.player2_hundredths;
            const bool draw = result.outcome ==
                ur::title::OrdinaryTwoPlayerRaceOutcome::Draw;
            const bool won = !draw &&
                (first == (result.outcome ==
                    ur::title::OrdinaryTwoPlayerRaceOutcome::Player1Win));
            const char* outcome = draw ? "DRAW" : won ? "WIN" : "LOSS";
            const auto course = context.course_id;
            const auto short_course = course.rfind("course:", 0) == 0
                ? course.substr(7) : course;
            char line[80]{};
            if (own_hundredths >=
                    ur::title::kOrdinaryTwoPlayerNoTimeHundredths) {
                std::snprintf(line, sizeof(line), "LAST %s %s DNF",
                    short_course.c_str(), outcome);
            } else {
                const unsigned hundredths = own_hundredths;
                std::snprintf(line, sizeof(line),
                    "LAST %s %s %02u:%02u.%02u",
                    short_course.c_str(), outcome,
                    hundredths / 6000u, (hundredths / 100u) % 60u,
                    hundredths % 100u);
            }
            out.latest_match_line = line;
            break;
        }
    }
    return out;
}

} // namespace ur::product
