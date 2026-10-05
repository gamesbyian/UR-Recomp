#include "completed_run_catalog.hpp"

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

}  // namespace ur::product
