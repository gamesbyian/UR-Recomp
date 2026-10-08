#pragma once

#include "completed_run_record.hpp"

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace ur::product {

struct StoredRunRecord {
    std::string path;
    CompletedRunRecord record;
};

struct InspectedRunRecordArtifact {
    std::string path;
    RunRecordLoadStatus status = RunRecordLoadStatus::Malformed;
    std::string detail;
    std::optional<CompletedRunRecord> record;

    bool loaded() const noexcept {
        return status == RunRecordLoadStatus::Loaded && record.has_value();
    }
};

struct RunRecordArtifactHealth {
    std::size_t total_artifacts = 0;
    std::size_t loaded_artifacts = 0;
    std::size_t io_errors = 0;
    std::size_t malformed_artifacts = 0;
    std::size_t unsupported_artifacts = 0;
    std::size_t corrupt_artifacts = 0;

    std::size_t unavailable_artifacts() const noexcept {
        return total_artifacts - loaded_artifacts;
    }
};

/* Append one immutable run artifact to a directory. The filename is
 * host-owned ordering metadata; the record body remains the authoritative
 * portable artifact. The fully closed file is published atomically with
 * no-replace semantics; uncommitted staging paths are invisible to scans. */
bool append_completed_run_record(
    const std::string& directory,
    const CompletedRunRecord& record,
    std::string* stored_path = nullptr,
    std::string* detail = nullptr);

/* Inspect every .urrun artifact in filename order without granting invalid
 * artifacts record authority. Callers may surface health/status information
 * while statistics/replay continue to consume only loaded records. */
std::vector<InspectedRunRecordArtifact> inspect_completed_run_record_artifacts(
    const std::string& directory);

RunRecordArtifactHealth summarize_run_record_artifact_health(
    const std::vector<InspectedRunRecordArtifact>& artifacts);

/* Load compatible records in filename order. Malformed/corrupt/incompatible
 * files are ignored rather than poisoning the usable catalog. */
std::vector<StoredRunRecord> load_compatible_run_records(
    const std::string& directory,
    const RunPlaybackTarget& target);

/* Load every valid completed-run artifact in filename order, without applying
 * a course-specific playback target. Invalid/corrupt artifacts remain excluded
 * from authoritative statistics; inspection UIs may enumerate them separately. */
std::vector<StoredRunRecord> load_valid_run_records(
    const std::string& directory);

std::optional<std::size_t> select_previous_run(
    const std::vector<StoredRunRecord>& records);

}  // namespace ur::product
