#include "completed_run_comparison.hpp"

#include <limits>

namespace ur::product {
namespace {

RunPlaybackTarget target_for(const CompletedRunRecord& record) {
    return {
        record.provenance.game_id,
        record.provenance.rom_sha256,
        record.provenance.build_compat_id,
        record.provenance.course_id,
        record.provenance.mode,
    };
}

}  // namespace

std::optional<std::int64_t> exact_run_timing_delta_ticks60(
    std::uint64_t current,
    std::uint64_t target) {
    if (current >= target) {
        const std::uint64_t diff = current - target;
        if (diff > static_cast<std::uint64_t>(
                std::numeric_limits<std::int64_t>::max())) {
            return std::nullopt;
        }
        return static_cast<std::int64_t>(diff);
    }

    const std::uint64_t diff = target - current;
    const std::uint64_t negative_limit =
        static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()) + 1u;
    if (diff > negative_limit) return std::nullopt;
    if (diff == negative_limit) return std::numeric_limits<std::int64_t>::min();
    return -static_cast<std::int64_t>(diff);
}

std::optional<CompletedRunTimingComparison> compare_completed_run_timing(
    const CompletedRunRecord& current,
    const CompletedRunRecord& target) {
    std::string detail;
    if (!validate_completed_run_record(current, &detail) ||
        !validate_completed_run_record(target, &detail) ||
        !compatible_for_playback(current, target_for(target), &detail) ||
        current.splits.size() != target.splits.size()) {
        return std::nullopt;
    }

    CompletedRunTimingComparison comparison;
    const auto finish_delta =
        exact_run_timing_delta_ticks60(
            current.elapsed_ticks60, target.elapsed_ticks60);
    if (!finish_delta) return std::nullopt;
    comparison.finish_delta_ticks60 = *finish_delta;

    comparison.splits.reserve(current.splits.size());
    for (std::size_t i = 0; i < current.splits.size(); ++i) {
        if (current.splits[i].id != target.splits[i].id) return std::nullopt;
        const auto delta =
            exact_run_timing_delta_ticks60(
                current.splits[i].ticks60, target.splits[i].ticks60);
        if (!delta) return std::nullopt;
        comparison.splits.push_back({
            current.splits[i].id,
            current.splits[i].ticks60,
            target.splits[i].ticks60,
            *delta,
        });
    }
    return comparison;
}

}  // namespace ur::product
