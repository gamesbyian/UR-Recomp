#include "completed_run_store.hpp"

#include <algorithm>
#include <chrono>
#include <filesystem>
#include <iomanip>
#include <sstream>
#include <utility>

namespace ur::product {
namespace {

namespace fs = std::filesystem;

std::string timestamp_prefix() {
    const auto now = std::chrono::system_clock::now().time_since_epoch();
    const auto ms =
        std::chrono::duration_cast<std::chrono::milliseconds>(now).count();
    std::ostringstream out;
    out << std::setw(16) << std::setfill('0') << ms;
    return out.str();
}

void set_detail(std::string* detail, const std::string& value) {
    if (detail) *detail = value;
}

}  // namespace

bool append_completed_run_record(
    const std::string& directory,
    const CompletedRunRecord& record,
    std::string* stored_path,
    std::string* detail) {
    std::string validation;
    if (!validate_completed_run_record(record, &validation)) {
        set_detail(detail, validation);
        return false;
    }

    std::error_code ec;
    fs::create_directories(directory, ec);
    if (ec) {
        set_detail(detail, "cannot create run-record directory");
        return false;
    }

    const std::string prefix = "run-" + timestamp_prefix();
    for (unsigned suffix = 0; suffix < 10000; ++suffix) {
        std::ostringstream name;
        name << prefix << "-" << std::setw(4) << std::setfill('0') << suffix
             << ".urrun";
        const fs::path path = fs::path(directory) / name.str();
        if (fs::exists(path, ec)) {
            if (ec) {
                set_detail(detail, "cannot inspect run-record path");
                return false;
            }
            continue;
        }

        if (!save_completed_run_record_file(path.string(), record, detail)) {
            return false;
        }
        if (stored_path) *stored_path = path.string();
        return true;
    }

    set_detail(detail, "run-record filename space exhausted");
    return false;
}

std::vector<InspectedRunRecordArtifact>
inspect_completed_run_record_artifacts(const std::string& directory) {
    std::vector<InspectedRunRecordArtifact> out;
    std::error_code ec;
    if (!fs::exists(directory, ec) || ec) return out;

    std::vector<fs::path> paths;
    for (fs::directory_iterator it(directory, ec), end;
         !ec && it != end; it.increment(ec)) {
        if (!it->is_regular_file()) continue;
        if (it->path().extension() == ".urrun") paths.push_back(it->path());
    }
    if (ec) return {};

    std::sort(paths.begin(), paths.end());
    out.reserve(paths.size());
    for (const auto& path : paths) {
        auto loaded = load_completed_run_record_file(path.string());
        InspectedRunRecordArtifact artifact;
        artifact.path = path.string();
        artifact.status = loaded.status;
        artifact.detail = std::move(loaded.detail);
        artifact.record = std::move(loaded.record);
        out.push_back(std::move(artifact));
    }
    return out;
}

RunRecordArtifactHealth summarize_run_record_artifact_health(
    const std::vector<InspectedRunRecordArtifact>& artifacts) {
    RunRecordArtifactHealth health;
    health.total_artifacts = artifacts.size();
    for (const auto& artifact : artifacts) {
        switch (artifact.status) {
        case RunRecordLoadStatus::Loaded:
            if (artifact.record) ++health.loaded_artifacts;
            else ++health.malformed_artifacts;
            break;
        case RunRecordLoadStatus::IoError:
            ++health.io_errors;
            break;
        case RunRecordLoadStatus::UnsupportedVersion:
            ++health.unsupported_artifacts;
            break;
        case RunRecordLoadStatus::Corrupt:
            ++health.corrupt_artifacts;
            break;
        case RunRecordLoadStatus::Malformed:
        case RunRecordLoadStatus::Incompatible:
        default:
            ++health.malformed_artifacts;
            break;
        }
    }
    return health;
}

std::vector<StoredRunRecord> load_valid_run_records(
    const std::string& directory) {
    std::vector<StoredRunRecord> out;
    auto artifacts = inspect_completed_run_record_artifacts(directory);
    out.reserve(artifacts.size());
    for (auto& artifact : artifacts) {
        if (!artifact.loaded()) continue;
        out.push_back({artifact.path, std::move(*artifact.record)});
    }
    return out;
}

std::vector<StoredRunRecord> load_compatible_run_records(
    const std::string& directory,
    const RunPlaybackTarget& target) {
    std::vector<StoredRunRecord> out;
    auto valid = load_valid_run_records(directory);
    out.reserve(valid.size());

    for (auto& stored : valid) {
        std::string detail;
        if (!compatible_for_playback(stored.record, target, &detail)) continue;
        out.push_back(std::move(stored));
    }
    return out;
}

std::optional<std::size_t> select_previous_run(
    const std::vector<StoredRunRecord>& records) {
    if (records.empty()) return std::nullopt;
    return records.size() - 1;
}

}  // namespace ur::product
