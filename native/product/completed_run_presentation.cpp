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

RunTimingPanelPresentation present_run_timing_panel(
    std::uint64_t current_ticks60,
    const CompletedRunRecord* personal_best,
    RunTimingPresentationPoint point,
    const std::string& split_id) {
    RunTimingPanelPresentation panel;
    panel.clock_label =
        point == RunTimingPresentationPoint::Finish ? "FINISH" : "TIME";
    panel.clock_text = format_run_ticks60(current_ticks60);
    panel.target_label = "PB";
    panel.target_text = "--";
    panel.comparison_label =
        point == RunTimingPresentationPoint::Split ? "SPLIT" : "DELTA";
    panel.comparison_text = "--";

    if (!personal_best) return panel;

    const auto target =
        present_run_target(*personal_best, RunDataTargetKind::PersonalBest);
    if (!target) return panel;

    panel.target_available = true;
    panel.target_text = target->time_text;

    std::optional<RunDataDeltaPresentation> delta;
    if (point == RunTimingPresentationPoint::Split && !split_id.empty()) {
        delta = present_run_split_delta(
            *personal_best, split_id, current_ticks60);
    } else if (point == RunTimingPresentationPoint::Finish) {
        delta = present_run_finish_delta(*personal_best, current_ticks60);
    }

    if (delta) {
        panel.comparison_available = true;
        panel.comparison_text = delta->delta_text;
    }
    return panel;
}

bool should_present_run_timing(
    bool modern_execution,
    bool supported_timed_run,
    bool race_or_results_surface) noexcept {
    return modern_execution && supported_timed_run && race_or_results_surface;
}

std::optional<RunTimingSplitTablePresentation> present_run_split_table(
    const CompletedRunRecord& current,
    const CompletedRunRecord& target,
    RunDataTargetKind kind) {
    const auto comparison = compare_completed_run_timing(current, target);
    if (!comparison) return std::nullopt;

    RunTimingSplitTablePresentation table;
    table.target_label =
        kind == RunDataTargetKind::PersonalBest ? "PB" : "PREVIOUS";
    table.rows.reserve(comparison->splits.size());

    for (const auto& split : comparison->splits) {
        table.rows.push_back({
            split.id,
            format_run_ticks60(split.current_ticks60),
            format_run_ticks60(split.target_ticks60),
            format_run_delta_ticks60(split.delta_ticks60),
        });
    }
    return table;
}

std::optional<RunResultSummaryPresentation> present_run_result_summary_against(
    const CompletedRunRecord& current,
    const CompletedRunRecord& target,
    RunDataTargetKind kind) {
    std::string detail;
    if (!validate_completed_run_record(current, &detail)) {
        return std::nullopt;
    }

    const RunPlaybackTarget compatibility_target{
        current.provenance.game_id,
        current.provenance.rom_sha256,
        current.provenance.build_compat_id,
        current.provenance.course_id,
        current.provenance.mode,
    };
    if (!compatible_for_playback(target, compatibility_target, &detail)) {
        return std::nullopt;
    }

    const auto target_presentation = present_run_target(target, kind);
    const auto finish_delta =
        present_run_finish_delta(target, current.elapsed_ticks60);
    if (!target_presentation || !finish_delta) return std::nullopt;

    const auto splits = present_run_split_table(current, target, kind);

    RunResultSummaryPresentation summary;
    summary.finish.clock_label = "FINISH";
    summary.finish.clock_text = format_run_ticks60(current.elapsed_ticks60);
    summary.finish.target_label = target_presentation->label;
    summary.finish.target_text = target_presentation->time_text;
    summary.finish.comparison_label = "DELTA";
    summary.finish.comparison_text = finish_delta->delta_text;
    summary.finish.target_available = true;
    summary.finish.comparison_available = true;
    if (splits) summary.splits = splits->rows;
    return summary;
}

std::optional<RunResultSummaryPresentation> present_run_result_summary(
    const CompletedRunRecord& current,
    const CompletedRunRecord* personal_best) {
    std::string detail;
    if (!validate_completed_run_record(current, &detail)) {
        return std::nullopt;
    }

    RunResultSummaryPresentation summary;
    summary.finish = present_run_timing_panel(
        current.elapsed_ticks60,
        personal_best,
        RunTimingPresentationPoint::Finish);

    if (!personal_best) return summary;

    const auto splits = present_run_split_table(
        current,
        *personal_best,
        RunDataTargetKind::PersonalBest);
    if (splits) {
        summary.splits = splits->rows;
    }
    return summary;
}

}  // namespace ur::product
