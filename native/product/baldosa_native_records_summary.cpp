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
    // Do not follow a substituted run-directory symlink into an unrelated
    // user's records. Missing first-run directory is a valid empty archive.
    if (std::filesystem::is_symlink(root, ec) || ec) return out;
    if (!std::filesystem::exists(root, ec) && !ec) {
        out.directory_available = true;
        return out;
    }
    if (ec || !std::filesystem::is_directory(root, ec) || ec)
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
