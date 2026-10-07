#include "completed_run_catalog.hpp"

#include <algorithm>
#include <map>

namespace ur::product {

RunDataCatalog build_run_data_catalog(
    const std::vector<StoredRunRecord>& records,
    const RunPlaybackTarget& target) {
    RunDataCatalog catalog;
    catalog.entries.reserve(records.size());

    std::vector<CompletedRunRecord> compatible_records;
    compatible_records.reserve(records.size());

    std::vector<std::size_t> source_indices;
    source_indices.reserve(records.size());

    for (std::size_t i = 0; i < records.size(); ++i) {
        std::string detail;
        if (!validate_completed_run_record(records[i].record, &detail) ||
            !compatible_for_playback(records[i].record, target, &detail)) {
            continue;
        }

        source_indices.push_back(i);
        compatible_records.push_back(records[i].record);
        catalog.entries.push_back({
            i,
            records[i].path,
            records[i].record.elapsed_ticks60,
            format_run_ticks60(records[i].record.elapsed_ticks60),
            false,
            false,
            std::nullopt,
            "--",
        });
    }

    if (catalog.entries.empty()) return catalog;

    std::vector<StoredRunRecord> compatible_stored;
    compatible_stored.reserve(catalog.entries.size());
    for (const auto source_index : source_indices) {
        compatible_stored.push_back(records[source_index]);
    }

    const auto previous = select_previous_run(compatible_stored);
    if (previous && *previous < catalog.entries.size()) {
        catalog.previous_entry = *previous;
        catalog.entries[*previous].is_previous = true;
    }

    const auto personal_best =
        select_fastest_compatible_run(compatible_records, target);
    if (personal_best && *personal_best < catalog.entries.size()) {
        catalog.personal_best_entry = *personal_best;
        catalog.entries[*personal_best].is_personal_best = true;

        const auto pb_ticks =
            catalog.entries[*personal_best].elapsed_ticks60;
        for (auto& entry : catalog.entries) {
            const auto delta = exact_run_timing_delta_ticks60(
                entry.elapsed_ticks60, pb_ticks);
            if (!delta) continue;
            entry.personal_best_delta_ticks60 = *delta;
            entry.personal_best_delta_text =
                format_run_delta_ticks60(*delta);
        }
    }

    return catalog;
}

RunDataStatisticsPresentation present_run_data_statistics(
    const RunDataCatalog& catalog) {
    RunDataStatisticsPresentation stats;
    stats.completed_runs = catalog.entries.size();

    const RunDataCatalogEntry* pb = nullptr;
    const RunDataCatalogEntry* previous = nullptr;

    if (catalog.personal_best_entry &&
        *catalog.personal_best_entry < catalog.entries.size()) {
        pb = &catalog.entries[*catalog.personal_best_entry];
        stats.personal_best_available = true;
        stats.personal_best_text = pb->time_text;
    }

    if (catalog.previous_entry &&
        *catalog.previous_entry < catalog.entries.size()) {
        previous = &catalog.entries[*catalog.previous_entry];
        stats.previous_available = true;
        stats.previous_text = previous->time_text;
    }

    if (pb && previous) {
        const auto delta = exact_run_timing_delta_ticks60(
            previous->elapsed_ticks60, pb->elapsed_ticks60);
        if (delta) {
            stats.previous_comparison_available = true;
            stats.previous_vs_pb_text = format_run_delta_ticks60(*delta);
        }
    }

    return stats;
}

RunRecordsIndex build_run_records_index(
    const std::vector<StoredRunRecord>& records,
    const RunRecordsScope& scope) {
    std::map<std::string, std::vector<StoredRunRecord>> grouped;

    for (const auto& stored : records) {
        std::string detail;
        if (!validate_completed_run_record(stored.record, &detail)) continue;
        const auto& p = stored.record.provenance;
        if (p.game_id != scope.game_id ||
            p.rom_sha256 != scope.rom_sha256 ||
            p.build_compat_id != scope.build_compat_id ||
            p.mode != scope.mode) {
            continue;
        }
        grouped[p.course_id].push_back(stored);
    }

    RunRecordsIndex index;
    for (auto& pair : grouped) {
        const auto& course_id = pair.first;
        auto& course_records = pair.second;
        const RunPlaybackTarget target{
            scope.game_id,
            scope.rom_sha256,
            scope.build_compat_id,
            course_id,
            scope.mode,
        };
        auto catalog = build_run_data_catalog(course_records, target);
        if (catalog.entries.empty()) continue;

        index.total_completed_runs += catalog.entries.size();
        auto stats = present_run_data_statistics(catalog);
        index.courses.push_back({
            course_id,
            std::move(catalog),
            std::move(stats),
            std::move(course_records),
        });
    }

    return index;
}

std::optional<RunRecordsProfileSummary> present_run_records_profile_summary(
    const std::string& profile_id,
    const HostRacerIdentity& racer_identity,
    const std::vector<StoredRunRecord>& records,
    const RunRecordsScope& scope,
    std::size_t total_artifacts) {
    if (profile_id.empty()) return std::nullopt;

    const auto index = build_run_records_index(records, scope);
    const std::size_t observed_artifacts =
        total_artifacts > records.size() ? total_artifacts : records.size();
    const std::size_t unavailable =
        observed_artifacts > index.total_completed_runs
            ? observed_artifacts - index.total_completed_runs
            : 0;
    return RunRecordsProfileSummary{
        profile_id,
        racer_identity,
        index.total_completed_runs,
        index.courses.size(),
        unavailable,
    };
}

RunRecordsProfileIndex build_run_records_profile_index(
    const std::vector<RunRecordsProfileSource>& profiles,
    const RunRecordsScope& scope,
    const std::optional<std::string>& active_profile_id) {
    RunRecordsProfileIndex index;
    index.profiles.reserve(profiles.size());

    for (const auto& profile : profiles) {
        const auto summary = present_run_records_profile_summary(
            profile.profile_id,
            profile.racer_identity,
            profile.records,
            scope,
            profile.total_artifacts);
        if (!summary) continue;
        index.total_completed_runs += summary->completed_runs;
        index.total_unavailable_artifacts += summary->unavailable_artifacts;
        index.profiles.push_back(*summary);
        if (active_profile_id &&
            summary->profile_id == *active_profile_id) {
            index.active_profile = index.profiles.size() - 1;
        }
    }
    return index;
}

}  // namespace ur::product
