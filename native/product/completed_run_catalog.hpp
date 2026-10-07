#pragma once

#include "completed_run_capture.hpp"
#include "completed_run_presentation.hpp"
#include "completed_run_store.hpp"
#include "host_profile_catalog.hpp"

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace ur::product {

struct RunDataCatalogEntry {
    std::size_t source_index = 0;
    std::string path;
    std::uint64_t elapsed_ticks60 = 0;
    std::string time_text;
    bool is_previous = false;
    bool is_personal_best = false;
    std::optional<std::int64_t> personal_best_delta_ticks60;
    std::string personal_best_delta_text = "--";
};

struct RunDataCatalog {
    std::vector<RunDataCatalogEntry> entries;
    std::optional<std::size_t> previous_entry;
    std::optional<std::size_t> personal_best_entry;
};

struct RunDataStatisticsPresentation {
    std::size_t completed_runs = 0;
    std::string personal_best_text = "--";
    std::string previous_text = "--";
    std::string previous_vs_pb_text = "--";
    bool personal_best_available = false;
    bool previous_available = false;
    bool previous_comparison_available = false;
};

struct RunRecordsScope {
    std::string game_id;
    std::string rom_sha256;
    std::string build_compat_id;
    std::string mode;
};

struct RunRecordsCourseIndexEntry {
    std::string course_id;
    RunDataCatalog catalog;
    RunDataStatisticsPresentation statistics;
    std::vector<StoredRunRecord> records;
};

struct RunRecordsIndex {
    std::size_t total_completed_runs = 0;
    std::vector<RunRecordsCourseIndexEntry> courses;
};

struct RunRecordsProfileSummary {
    std::string profile_id;
    HostRacerIdentity racer_identity;
    std::size_t completed_runs = 0;
    std::size_t tracks_with_runs = 0;
};

/* Build presentation metadata over an already compatibility-filtered store
 * catalog. Selection delegates to the canonical previous/PB selectors; this
 * layer adds no new ranking or replay rules. */
RunDataCatalog build_run_data_catalog(
    const std::vector<StoredRunRecord>& records,
    const RunPlaybackTarget& target);

/* Prepare compact per-target statistics from the canonical catalog. This adds
 * no alternate selection rule: PB and Previous come only from catalog flags. */
RunDataStatisticsPresentation present_run_data_statistics(
    const RunDataCatalog& catalog);

/* Build the course-independent Runs/Replays index for one authoritative
 * game/ROM/build/mode scope. Records are grouped by their stored course_id and
 * each group delegates PB/Previous selection to build_run_data_catalog(). */
RunRecordsIndex build_run_records_index(
    const std::vector<StoredRunRecord>& records,
    const RunRecordsScope& scope);

std::optional<RunRecordsProfileSummary> present_run_records_profile_summary(
    const HostProfileCatalogEntry& profile,
    const std::vector<StoredRunRecord>& records,
    const RunRecordsScope& scope);

}  // namespace ur::product
