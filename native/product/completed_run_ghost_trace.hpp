#pragma once

#include "completed_run_ghost.hpp"
#include "completed_run_ghost_world_sample.hpp"
#include "completed_run_record.hpp"

#include <optional>
#include <string>
#include <vector>

namespace ur::product {

constexpr std::uint32_t kCompletedRunGhostTraceSchemaVersion = 1;

struct CompletedRunGhostTrace {
    std::uint32_t schema_version = kCompletedRunGhostTraceSchemaVersion;
    std::string run_artifact_checksum;
    std::vector<CompletedRunGhostWorldSample> samples;
};

enum class CompletedRunGhostTraceLoadStatus {
    Loaded,
    IoError,
    Malformed,
    UnsupportedVersion,
    Corrupt,
    Incompatible,
};

class CompletedRunGhostTraceCapture {
public:
    bool begin_attempt();
    bool observe(const CompletedRunGhostWorldSample& sample);

    std::optional<CompletedRunGhostTrace> complete(
        const CompletedRunRecord& completed_run);

    void abort_attempt();
    bool capturing() const { return capturing_; }
    std::size_t sample_count() const { return samples_.size(); }

private:
    bool capturing_ = false;
    std::vector<CompletedRunGhostWorldSample> samples_;
};

struct CompletedRunGhostTraceLoadResult {
    CompletedRunGhostTraceLoadStatus status =
        CompletedRunGhostTraceLoadStatus::Malformed;
    std::optional<CompletedRunGhostTrace> trace;
    std::string detail;

    bool loaded() const {
        return status == CompletedRunGhostTraceLoadStatus::Loaded &&
               trace.has_value();
    }
};

bool validate_completed_run_ghost_trace(
    const CompletedRunGhostTrace& trace,
    const CompletedRunRecord* bound_record = nullptr,
    std::string* detail = nullptr);

std::string encode_completed_run_ghost_trace(
    const CompletedRunGhostTrace& trace);

CompletedRunGhostTraceLoadResult decode_completed_run_ghost_trace(
    const std::string& text,
    const CompletedRunRecord* bound_record = nullptr);

bool save_completed_run_ghost_trace_file(
    const std::string& path,
    const CompletedRunGhostTrace& trace,
    std::string* detail = nullptr);

CompletedRunGhostTraceLoadResult load_completed_run_ghost_trace_file(
    const std::string& path,
    const CompletedRunRecord* bound_record = nullptr);

CompletedRunGhostTraceLoadResult load_selected_completed_run_ghost_trace(
    const CompletedRunGhostState& state,
    CompletedRunGhostKind kind);

const CompletedRunGhostWorldSample* completed_run_ghost_trace_sample_at(
    const CompletedRunGhostTrace& trace,
    std::uint64_t race_frame);

}  // namespace ur::product
