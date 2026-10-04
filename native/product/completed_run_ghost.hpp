#pragma once

#include "completed_run_store.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <utility>
#include <vector>

namespace ur::product {

enum class CompletedRunGhostKind {
    Previous,
    PersonalBest,
};

/* Read-only presentation state derived from durable completed-run artifacts.
 *
 * This object deliberately owns copies of selected records and exposes only
 * record metadata and race-relative controller lookup. It has no guest-memory
 * pointer, simulator callback, or mutation path.
 */
class CompletedRunGhostState {
public:
    void bind(
        const std::vector<StoredRunRecord>& records,
        const RunPlaybackTarget& target);
    void clear();

    bool has(CompletedRunGhostKind kind) const;
    const CompletedRunRecord* record(CompletedRunGhostKind kind) const;

    std::pair<std::uint16_t, std::uint16_t> input_at(
        CompletedRunGhostKind kind,
        std::uint64_t race_relative_frame) const;

    std::size_t compatible_count() const { return compatible_count_; }

private:
    std::optional<CompletedRunRecord> previous_;
    std::optional<CompletedRunRecord> personal_best_;
    std::size_t compatible_count_ = 0;
};

}  // namespace ur::product
