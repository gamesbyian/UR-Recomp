#include "completed_run_presentation.hpp"

#include <iomanip>
#include <limits>
#include <sstream>

namespace ur::product {
namespace {

std::uint64_t delta_magnitude(std::int64_t value) {
    if (value >= 0) return static_cast<std::uint64_t>(value);
    if (value == std::numeric_limits<std::int64_t>::min()) {
        return static_cast<std::uint64_t>(
            std::numeric_limits<std::int64_t>::max()) + 1u;
    }
    return static_cast<std::uint64_t>(-value);
}

RunDataDeltaPresentation make_delta(
    const std::string& id,
    std::uint64_t current_ticks60,
    std::uint64_t target_ticks60,
    std::int64_t delta_ticks60) {
    return {
        id,
        current_ticks60,
        target_ticks60,
        delta_ticks60,
        format_run_ticks60(current_ticks60),
        format_run_ticks60(target_ticks60),
        format_run_delta_ticks60(delta_ticks60),
    };
}

}  // namespace

std::string format_run_ticks60(std::uint64_t ticks60) {
    const std::uint64_t total_seconds = ticks60 / 60u;
    const std::uint64_t frames = ticks60 % 60u;
    const std::uint64_t minutes = total_seconds / 60u;
    const std::uint64_t seconds = total_seconds % 60u;

    std::ostringstream out;
    out << minutes << ':'
        << std::setw(2) << std::setfill('0') << seconds
        << '.'
        << std::setw(2) << std::setfill('0') << frames
        << "/60";
    return out.str();
}

std::string format_run_delta_ticks60(std::int64_t delta_ticks60) {
    const char sign = delta_ticks60 < 0 ? '-' : '+';
    return std::string(1, sign) +
           format_run_ticks60(delta_magnitude(delta_ticks60));
}

std::optional<RunDataTargetPresentation> present_run_target(
    const CompletedRunRecord& target,
    RunDataTargetKind kind) {
    std::string detail;
    if (!validate_completed_run_record(target, &detail)) return std::nullopt;

    return RunDataTargetPresentation{
        kind,
        target.elapsed_ticks60,
        kind == RunDataTargetKind::PersonalBest ? "PB" : "PREVIOUS",
        format_run_ticks60(target.elapsed_ticks60),
    };
}

std::optional<RunDataDeltaPresentation> present_run_split_delta(
    const CompletedRunRecord& target,
    const std::string& split_id,
    std::uint64_t current_ticks60) {
    std::string detail;
    if (!validate_completed_run_record(target, &detail)) return std::nullopt;

    for (const auto& split : target.splits) {
        if (split.id != split_id) continue;
        const auto delta = exact_run_timing_delta_ticks60(
            current_ticks60, split.ticks60);
        if (!delta) return std::nullopt;
        return make_delta(
            split_id, current_ticks60, split.ticks60, *delta);
    }
    return std::nullopt;
}

std::optional<RunDataDeltaPresentation> present_run_finish_delta(
    const CompletedRunRecord& target,
    std::uint64_t current_ticks60) {
    std::string detail;
    if (!validate_completed_run_record(target, &detail)) return std::nullopt;
    const auto delta = exact_run_timing_delta_ticks60(
        current_ticks60, target.elapsed_ticks60);
    if (!delta) return std::nullopt;
    return make_delta(
        "finish", current_ticks60, target.elapsed_ticks60, *delta);
}

}  // namespace ur::product
