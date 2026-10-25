#include "baldosa_native_records_summary.hpp"

#include "completed_run_store.hpp"
#include "local_tournament_utf8_path.hpp"

#include <cstdio>
#include <filesystem>
#include <system_error>

namespace ur::product {

std::string format_baldosa_native_record_ticks60(std::uint64_t ticks60) {
    // floor ticks + round leftover 1/60 second to a hundredth. The
    // intermediate residual is at most 59, so even UINT64_MAX is safe.
    const std::uint64_t minutes = ticks60 / 3600u;
    const std::uint64_t seconds = (ticks60 / 60u) % 60u;
    const std::uint64_t hundredths = ((ticks60 % 60u) * 100u + 30u) / 60u;
    char buffer[64]{};
    std::snprintf(buffer, sizeof(buffer), "%02llu:%02llu.%02llu",
        static_cast<unsigned long long>(minutes),
        static_cast<unsigned long long>(seconds),
        static_cast<unsigned long long>(hundredths));
    return buffer;
}

BaldosaNativeRecordsSummary inspect_baldosa_native_records_archive(
    const std::string& directory) {
    BaldosaNativeRecordsSummary out{};
    if (directory.empty()) return out;
    // Product directory APIs carry UTF-8; a narrow path constructor on
    // Windows interprets these bytes using the active ANSI code page.
    const std::filesystem::path root = host_native_path_from_utf8(directory);
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
    // An existing directory can still refuse enumeration (permissions,
    // I/O failure or a concurrent removal). Do not report an empty Records
    // history when the canonical inspector could not finish its scan.
    bool scan_succeeded = false;
    const auto artifacts = inspect_completed_run_record_artifacts(
        directory, &scan_succeeded);
    if (!scan_succeeded) return out;
    out.directory_available = true;
    out.total_artifacts = artifacts.size();
    for (const auto& artifact : artifacts) {
        // The portable codec validates syntax, not game ownership or mode.
        // Foreign-game and 2P/Practice files must not become earned
        // Uniracers 1P history or displace its latest course/time.
        if (!artifact.loaded() ||
            artifact.record->provenance.game_id != "uniracers" ||
            artifact.record->provenance.mode != "race-1p") {
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
