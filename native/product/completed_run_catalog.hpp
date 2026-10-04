#pragma once

#include "completed_run_capture.hpp"
#include "completed_run_presentation.hpp"
#include "completed_run_store.hpp"

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
};

struct RunDataCatalog {
    std::vector<RunDataCatalogEntry> entries;
    std::optional<std::size_t> previous_entry;
    std::optional<std::size_t> personal_best_entry;
};

/* Build presentation metadata over an already compatibility-filtered store
 * catalog. Selection delegates to the canonical previous/PB selectors; this
 * layer adds no new ranking or replay rules. */
RunDataCatalog build_run_data_catalog(
    const std::vector<StoredRunRecord>& records,
    const RunPlaybackTarget& target);

}  // namespace ur::product
