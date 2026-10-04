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

}  // namespace ur::product
