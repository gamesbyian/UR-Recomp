#pragma once

#include "completed_run_comparison.hpp"

#include <cstdint>
#include <optional>
#include <string>

namespace ur::product {

enum class RunDataTargetKind {
    Previous,
    PersonalBest,
};

struct RunDataTargetPresentation {
    RunDataTargetKind kind = RunDataTargetKind::PersonalBest;
    std::uint64_t elapsed_ticks60 = 0;
    std::string label;
    std::string time_text;
};

struct RunDataDeltaPresentation {
    std::string id;
    std::uint64_t current_ticks60 = 0;
    std::uint64_t target_ticks60 = 0;
    std::int64_t delta_ticks60 = 0;
    std::string current_text;
    std::string target_text;
    std::string delta_text;
};

enum class RunTimingPresentationPoint {
    Live,
    Split,
    Finish,
};

struct RunTimingPanelPresentation {
    std::string clock_label;
    std::string clock_text;
    std::string target_label;
    std::string target_text;
    std::string comparison_label;
    std::string comparison_text;
    bool target_available = false;
    bool comparison_available = false;
};

/* Exact display form for the authoritative 60 Hz clock.
 * Example: 1713 ticks -> "0:28.33/60". */
std::string format_run_ticks60(std::uint64_t ticks60);

/* Signed exact display form. Negative means ahead/faster.
 * Example: -6 ticks -> "-0:00.06/60". */
std::string format_run_delta_ticks60(std::int64_t delta_ticks60);

std::optional<RunDataTargetPresentation> present_run_target(
    const CompletedRunRecord& target,
    RunDataTargetKind kind);

std::optional<RunDataDeltaPresentation> present_run_split_delta(
    const CompletedRunRecord& target,
    const std::string& split_id,
    std::uint64_t current_ticks60);

std::optional<RunDataDeltaPresentation> present_run_finish_delta(
    const CompletedRunRecord& target,
    std::uint64_t current_ticks60);

/* Build one compact player-facing timing view from authoritative current time
 * plus an optional already-compatible PB record. Live timing deliberately does
 * not compare current elapsed time to a finish target; exact signed comparison
 * appears only at a named split or finish. */
RunTimingPanelPresentation present_run_timing_panel(
    std::uint64_t current_ticks60,
    const CompletedRunRecord* personal_best,
    RunTimingPresentationPoint point,
    const std::string& split_id = {});

/* Product-availability gate for the host timing surface. Authentic execution,
 * unsupported event types, and non-race/results surfaces remain inert. */
bool should_present_run_timing(
    bool modern_execution,
    bool supported_timed_run,
    bool race_or_results_surface) noexcept;

}  // namespace ur::product
