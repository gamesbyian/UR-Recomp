#pragma once

#include "completed_run_record.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace ur::product {

struct RunTimingDelta {
    std::string id;
    std::uint64_t current_ticks60 = 0;
    std::uint64_t target_ticks60 = 0;
    std::int64_t delta_ticks60 = 0; /* negative means current is ahead/faster */
};

struct CompletedRunTimingComparison {
    std::int64_t finish_delta_ticks60 = 0;
    std::vector<RunTimingDelta> splits;
};

/* Compare timing metadata only when both records describe the same replay
 * domain and expose the same ordered split identities. No simulation state is
 * read or mutated. Returns nullopt rather than inventing a comparison. */
std::optional<CompletedRunTimingComparison> compare_completed_run_timing(
    const CompletedRunRecord& current,
    const CompletedRunRecord& target);

}  // namespace ur::product
