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

}  // namespace ur::product
