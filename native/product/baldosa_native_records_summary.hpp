#pragma once

// Read-only, profile-scoped native Records summary. The canonical run-store
// inspector decides artifact validity; no new format, playback compatibility,
// Personal Best, course ranking, ghost or guest-result authority is introduced.
#include <cstddef>
#include <cstdint>
#include <string>

namespace ur::product {

struct BaldosaNativeRecordsSummary {
    bool directory_available = false;
    std::size_t total_artifacts = 0;
    std::size_t validated_archives = 0;
    std::size_t unavailable_artifacts = 0;
    std::string recent_course;
    std::uint64_t recent_ticks60 = 0;
};

BaldosaNativeRecordsSummary inspect_baldosa_native_records_archive(
    const std::string& directory);

}  // namespace ur::product
