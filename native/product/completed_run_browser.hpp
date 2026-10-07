#pragma once

#include "completed_run_catalog.hpp"
#include "completed_run_presentation.hpp"

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
    std::optional<std::int64_t> personal_best_delta_ticks60;
    std::string personal_best_delta_text = "--";
    std::vector<RunTimingSplitRowPresentation> personal_best_splits;
    std::optional<CompletedRunRecord> record;

    bool playable() const noexcept {
        return status == CompletedRunBrowserEntryStatus::Playable &&
               record.has_value();
    }
};

const char* completed_run_browser_status_name(
    CompletedRunBrowserEntryStatus status) noexcept;

std::string completed_run_browser_date_text(const std::string& path);

enum class CompletedRunRecordsView : std::uint8_t {
    Courses = 0,
    Runs = 1,
    Detail = 2,
};

class CompletedRunRecordsBrowser {
public:
    void clear() noexcept;
    bool refresh(
        const std::string& directory,
        const RunRecordsScope& scope);

    CompletedRunRecordsView view() const noexcept { return view_; }
    const RunRecordsIndex& index() const noexcept { return index_; }
    const RunRecordArtifactHealth& artifact_health() const noexcept {
        return artifact_health_;
    }
    std::size_t unavailable_artifact_count() const noexcept {
        return artifact_health_.total_artifacts > index_.total_completed_runs
            ? artifact_health_.total_artifacts - index_.total_completed_runs
            : 0;
    }
    std::optional<std::size_t> selected_course_index() const noexcept {
        return selected_course_;
    }
    std::optional<std::size_t> selected_run_index() const noexcept {
        return selected_run_;
    }
    const RunRecordsCourseIndexEntry* selected_course() const noexcept;
    const RunDataCatalogEntry* selected_run() const noexcept;
    const CompletedRunRecord* selected_run_record() const noexcept;
    const CompletedRunRecord* personal_best_run_record() const noexcept;
    const CompletedRunRecord* previous_run_record() const noexcept;
    std::optional<RunResultSummaryPresentation>
    selected_run_summary() const;
    std::optional<RunDataDeltaPresentation>
    selected_run_previous_delta() const;
    std::optional<RunResultSummaryPresentation>
    selected_run_target_summary(RunDataTargetKind kind) const;
    RunDataTargetKind detail_target_kind() const noexcept {
        return detail_target_kind_;
    }
    bool adjust_detail_target(int delta) noexcept;
    std::size_t detail_split_offset() const noexcept {
        return detail_split_offset_;
    }
    bool adjust_detail_split_offset(int delta);

    bool move(int delta) noexcept;
    bool open_selected_course() noexcept;
    bool open_selected_run_detail() noexcept;
    bool back_to_runs() noexcept;
    bool back_to_courses() noexcept;

private:
    RunRecordsIndex index_;
    RunRecordArtifactHealth artifact_health_;
    CompletedRunRecordsView view_ = CompletedRunRecordsView::Courses;
    std::optional<std::size_t> selected_course_;
    std::optional<std::size_t> selected_run_;
    RunDataTargetKind detail_target_kind_ = RunDataTargetKind::PersonalBest;
    std::size_t detail_split_offset_ = 0;
};

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
