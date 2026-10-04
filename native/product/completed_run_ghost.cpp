#include "completed_run_ghost.hpp"

#include <string>

namespace ur::product {

void CompletedRunGhostState::bind(
    const std::vector<StoredRunRecord>& records,
    const RunPlaybackTarget& target) {
    clear();

    std::uint64_t best_ticks = 0;
    for (const auto& stored : records) {
        std::string detail;
        if (!validate_completed_run_record(stored.record, &detail) ||
            !compatible_for_playback(stored.record, target, &detail)) {
            continue;
        }

        ++compatible_count_;
        previous_ = stored;

        if (!personal_best_ ||
            stored.record.elapsed_ticks60 <= best_ticks) {
            personal_best_ = stored;
            best_ticks = stored.record.elapsed_ticks60;
        }
    }
}

void CompletedRunGhostState::clear() {
    previous_.reset();
    personal_best_.reset();
    compatible_count_ = 0;
}

bool CompletedRunGhostState::has(CompletedRunGhostKind kind) const {
    return record(kind) != nullptr;
}

const StoredRunRecord* CompletedRunGhostState::stored(
    CompletedRunGhostKind kind) const {
    switch (kind) {
    case CompletedRunGhostKind::Previous:
        return previous_ ? &*previous_ : nullptr;
    case CompletedRunGhostKind::PersonalBest:
        return personal_best_ ? &*personal_best_ : nullptr;
    }
    return nullptr;
}

const CompletedRunRecord* CompletedRunGhostState::record(
    CompletedRunGhostKind kind) const {
    const StoredRunRecord* selected = stored(kind);
    return selected ? &selected->record : nullptr;
}

std::pair<std::uint16_t, std::uint16_t> CompletedRunGhostState::input_at(
    CompletedRunGhostKind kind,
    std::uint64_t race_relative_frame) const {
    const CompletedRunRecord* selected = record(kind);
    if (!selected) return {0, 0};
    return run_record_input_at(*selected, race_relative_frame);
}

}  // namespace ur::product
