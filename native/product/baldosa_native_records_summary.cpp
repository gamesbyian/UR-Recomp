#include "baldosa_native_records_summary.hpp"

#include "completed_run_store.hpp"

#include <filesystem>

namespace ur::product {

BaldosaNativeRecordsSummary inspect_baldosa_native_records_archive(
    const std::string& directory) {
    BaldosaNativeRecordsSummary out{};
    if (directory.empty()) return out;
    const std::filesystem::path root(directory);
    std::error_code ec;
    // A missing first-run directory is a valid empty archive, but a
    // dangling symlink is NOT missing: exists() follows its target and
    // otherwise quietly misclassifies it as an empty profile archive.
    // Inspect the entry itself, rejecting all symlinks before reading runs.
    const auto status = std::filesystem::symlink_status(root, ec);
    if (status.type() == std::filesystem::file_type::not_found) {
        if (!ec || ec == std::errc::no_such_file_or_directory)
            out.directory_available = true;
        return out;
    }
    if (ec || std::filesystem::is_symlink(status) ||
        !std::filesystem::is_directory(status))
        return out;
    out.directory_available = true;
    const auto artifacts = inspect_completed_run_record_artifacts(directory);
    out.total_artifacts = artifacts.size();
    for (const auto& artifact : artifacts) {
        if (!artifact.loaded()) {
            ++out.unavailable_artifacts;
            continue;
        }
        ++out.validated_archives;
        // Inspection already sorts artifacts in their canonical file order.
        // This is a *historical archive*, not playback-compatible recent/PB.
        out.recent_course = artifact.record->provenance.course_id;
        out.recent_ticks60 = artifact.record->elapsed_ticks60;
    }
    return out;
}

}  // namespace ur::product
