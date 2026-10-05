#pragma once

#include "completed_run_record.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace ur::product {

enum class CompletedRunBrowserEntryStatus : std::uint8_t {
    Playable = 0,
    Incompatible = 1,
    Corrupt = 2,
    Malformed = 3,
    UnsupportedVersion = 4,
    IoError = 5,
};

struct CompletedRunBrowserEntry {
    std::string path;
    std::string course_id;
    std::string date_text;
    std::string time_text;
    std::size_t chronological_order = 0;
    CompletedRunBrowserEntryStatus status =
        CompletedRunBrowserEntryStatus::Malformed;
    std::string detail;
    bool is_previous = false;
    bool is_personal_best = false;
    std::optional<CompletedRunRecord> record;

    bool playable() const noexcept {
        return status == CompletedRunBrowserEntryStatus::Playable &&
               record.has_value();
    }
};

const char* completed_run_browser_status_name(
    CompletedRunBrowserEntryStatus status) noexcept;

class CompletedRunBrowser {
public:
    void clear() noexcept;
    bool refresh(
        const std::string& directory,
        const RunPlaybackTarget& target);

    std::size_t size() const noexcept { return entries_.size(); }
    std::size_t playable_count() const noexcept;
    const std::vector<CompletedRunBrowserEntry>& entries() const noexcept {
        return entries_;
    }

    std::optional<std::size_t> selected_index() const noexcept {
        return selected_;
    }
    const CompletedRunBrowserEntry* selected() const noexcept;
    bool move(int delta) noexcept;

private:
    std::vector<CompletedRunBrowserEntry> entries_;
    std::optional<std::size_t> selected_;
};

}  // namespace ur::product
