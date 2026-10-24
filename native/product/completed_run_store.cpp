#include "completed_run_store.hpp"
#include "local_tournament_atomic_replace.hpp"
#include "local_tournament_utf8_path.hpp"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <filesystem>
#include <iomanip>
#include <sstream>
#include <system_error>
#include <utility>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

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

// A staging directory is reserved with an atomic mkdir, so even different
// processes cannot write into the same pending file. Its extension is never
// .urrun and catalog readers cannot mistake it for an admitted run.
bool reserve_staging_directory(
    const fs::path& directory, fs::path& staging) {
    static std::atomic<std::uint64_t> serial{0};
    for (unsigned attempt = 0; attempt < 64; ++attempt) {
        const auto tick = std::chrono::steady_clock::now()
                              .time_since_epoch().count();
        staging = directory /
            (".pending-urrun-" + std::to_string(tick) + "-" +
             std::to_string(serial.fetch_add(1, std::memory_order_relaxed)));
        std::error_code ec;
        if (fs::create_directory(staging, ec)) return true;
        if (ec) return false;
    }
    return false;
}

enum class PublishResult { Published, AlreadyExists, Error };

// Publishing must be both atomic and no-replace. std::filesystem::rename
// replaces an existing destination on POSIX, so it is unsuitable for the
// immutable numbered .urrun namespace.
PublishResult publish_without_replacing(
    const fs::path& staged, const fs::path& final_path) {
#if defined(_WIN32)
    // MoveFileW does not replace existing destinations (unlike MoveFileExW
    // with MOVEFILE_REPLACE_EXISTING). Both paths are on the same volume.
    if (MoveFileW(staged.c_str(), final_path.c_str()))
        return PublishResult::Published;
    const DWORD error = GetLastError();
    if (error == ERROR_FILE_EXISTS || error == ERROR_ALREADY_EXISTS)
        return PublishResult::AlreadyExists;
    return PublishResult::Error;
#else
    // Atomic create-if-absent hard link, then unlink the invisible staged
    // name. A competing writer never overwrites an existing completed run.
    std::error_code ec;
    fs::create_hard_link(staged, final_path, ec);
    if (!ec) return PublishResult::Published;
    if (ec == std::errc::file_exists)
        return PublishResult::AlreadyExists;
    return PublishResult::Error;
#endif
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
    // The product boundary receives UTF-8 even on Windows.
    const fs::path directory_path = host_native_path_from_utf8(directory);
    fs::create_directories(directory_path, ec);
    if (ec) {
        set_detail(detail, "cannot create run-record directory");
        return false;
    }

    // An explicitly selected archive directory must be a REAL local
    // directory, not a symlink to another named profile or user root.
    // create_directories() can report success through an existing link;
    // that must never authorize a record write outside this namespace.
    ec.clear();
    const auto archive_status = fs::symlink_status(directory_path, ec);
    if (ec || !fs::is_directory(archive_status) ||
        fs::is_symlink(archive_status)) {
        set_detail(detail, "run-record directory is not a direct directory");
        return false;
    }
    fs::path staging;
    if (!reserve_staging_directory(directory_path, staging)) {
        set_detail(detail, "cannot reserve run-record staging directory");
        return false;
    }

    // Close/flush the entire record before making any .urrun name visible.
    // Abandoned staging directories after a crash are ignored by catalog
    // discovery. Cleanup is best effort and never removes a published run.
    const fs::path staged_file = staging / "record.tmp";
    if (!save_completed_run_record_file(staged_file.u8string(), record, detail)) {
        fs::remove_all(staging, ec);
        return false;
    }
    // Closing the codec's ofstream drains buffered data but does not request
    // persistence from the OS. Never make a .urrun name visible if the staged
    // run itself could not be flushed to the storage device.
    if (!ur::product::detail::sync_closed_staged_file(staged_file)) {
        set_detail(detail, "cannot durably flush staged run record");
        fs::remove_all(staging, ec);
        return false;
    }

    const std::string prefix = "run-" + timestamp_prefix();
    for (unsigned suffix = 0; suffix < 10000; ++suffix) {
        std::ostringstream name;
        name << prefix << "-" << std::setw(4) << std::setfill('0') << suffix
             << ".urrun";
        const fs::path path = directory_path / name.str();
        const auto result = publish_without_replacing(staged_file, path);
        if (result == PublishResult::AlreadyExists) continue;
        if (result == PublishResult::Error) {
            set_detail(detail, "cannot publish run record");
            fs::remove_all(staging, ec);
            return false;
        }
        ur::product::detail::sync_published_directory_best_effort(directory_path);
        fs::remove_all(staging, ec);
        if (stored_path) *stored_path = path.u8string();
        return true;
    }

    set_detail(detail, "run-record filename space exhausted");
    fs::remove_all(staging, ec);
    return false;
}

std::vector<InspectedRunRecordArtifact>
inspect_completed_run_record_artifacts(const std::string& directory,
                                       bool* scan_succeeded) {
    if (scan_succeeded) *scan_succeeded = false;
    std::vector<InspectedRunRecordArtifact> out;
    std::error_code ec;
    // The generic run reader is also used outside the Baldosa Records UI:
    // do not bypass that UI's direct-directory guard through Local Runs,
    // replay-target selection or another native product consumer.
    const fs::path directory_path = host_native_path_from_utf8(directory);
    const auto directory_status = fs::symlink_status(directory_path, ec);
    if (directory_status.type() == fs::file_type::not_found &&
        (!ec || ec == std::errc::no_such_file_or_directory)) {
        if (scan_succeeded) *scan_succeeded = true;
        return out;
    }
    if (ec || !fs::is_directory(directory_status) ||
        fs::is_symlink(directory_status)) return out;

    std::vector<fs::path> paths;
    for (fs::directory_iterator it(directory_path, ec), end;
         !ec && it != end; it.increment(ec)) {
        if (it->path().extension() != ".urrun") continue;
        // directory_entry::is_regular_file() follows symlinks, silently
        // importing another player's perfectly valid run into this profile
        // archive. Keep live/dangling links as UNAVAILABLE health entries.
        std::error_code status_error;
        const auto status = it->symlink_status(status_error);
        if (!status_error && !fs::is_regular_file(status) &&
            !fs::is_symlink(status)) continue;
        paths.push_back(it->path());
    }
    if (ec) return {};

    std::sort(paths.begin(), paths.end());
    out.reserve(paths.size());
    for (const auto& path : paths) {
        InspectedRunRecordArtifact artifact;
        artifact.path = path.u8string();
        std::error_code status_error;
        const auto status = fs::symlink_status(path, status_error);
        if (status_error || !fs::is_regular_file(status) ||
            fs::is_symlink(status)) {
            artifact.status = RunRecordLoadStatus::IoError;
            artifact.detail = "run artifact is not a direct regular file";
        } else {
            auto loaded = load_completed_run_record_file(path.u8string());
            artifact.status = loaded.status;
            artifact.detail = std::move(loaded.detail);
            artifact.record = std::move(loaded.record);
        }
        out.push_back(std::move(artifact));
    }
    if (scan_succeeded) *scan_succeeded = true;
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
