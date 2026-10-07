#include "completed_run_browser.hpp"

#include "completed_run_catalog.hpp"
#include "completed_run_presentation.hpp"
#include "completed_run_store.hpp"

#include <algorithm>
#include <chrono>
#include <cctype>
#include <ctime>
#include <filesystem>
#include <utility>

namespace ur::product {
namespace {

namespace fs = std::filesystem;

std::string run_date_text(const fs::path& path) {
    const std::string name = path.filename().string();
    constexpr std::size_t kPrefixSize = 4;
    constexpr std::size_t kTimestampSize = 16;
    if (name.size() < kPrefixSize + kTimestampSize + 1 ||
        name.compare(0, kPrefixSize, "run-") != 0 ||
        name[kPrefixSize + kTimestampSize] != '-') {
        return "--";
    }

    const std::string digits =
        name.substr(kPrefixSize, kTimestampSize);
    if (!std::all_of(
            digits.begin(), digits.end(),
            [](unsigned char ch) { return std::isdigit(ch) != 0; })) {
        return "--";
    }

    std::uint64_t milliseconds = 0;
    for (char ch : digits) {
        milliseconds =
            milliseconds * 10u + static_cast<unsigned>(ch - '0');
    }

    const auto point = std::chrono::system_clock::time_point(
        std::chrono::milliseconds(milliseconds));
    const std::time_t seconds =
        std::chrono::system_clock::to_time_t(point);
    std::tm local{};
#ifdef _WIN32
    if (localtime_s(&local, &seconds) != 0) return "--";
#else
    if (!localtime_r(&seconds, &local)) return "--";
#endif

    char text[16];
    if (std::strftime(text, sizeof(text), "%Y-%m-%d", &local) == 0) {
        return "--";
    }
    return text;
}

CompletedRunBrowserEntryStatus browser_status(RunRecordLoadStatus status) {
    switch (status) {
    case RunRecordLoadStatus::Loaded:
        return CompletedRunBrowserEntryStatus::Playable;
    case RunRecordLoadStatus::Incompatible:
        return CompletedRunBrowserEntryStatus::Incompatible;
    case RunRecordLoadStatus::Corrupt:
        return CompletedRunBrowserEntryStatus::Corrupt;
    case RunRecordLoadStatus::UnsupportedVersion:
        return CompletedRunBrowserEntryStatus::UnsupportedVersion;
    case RunRecordLoadStatus::IoError:
        return CompletedRunBrowserEntryStatus::IoError;
    case RunRecordLoadStatus::Malformed:
    default:
        return CompletedRunBrowserEntryStatus::Malformed;
    }
}

struct InspectedArtifact {
    std::string path;
    RunRecordLoadStatus status = RunRecordLoadStatus::Malformed;
    std::string detail;
    std::optional<CompletedRunRecord> record;
};

}  // namespace

void CompletedRunRecordsBrowser::clear() noexcept {
    index_ = {};
    artifact_health_ = {};
    view_ = CompletedRunRecordsView::Courses;
    selected_course_.reset();
    selected_run_.reset();
    detail_target_kind_ = RunDataTargetKind::PersonalBest;
}

bool CompletedRunRecordsBrowser::refresh(
    const std::string& directory,
    const RunRecordsScope& scope) {
    clear();
    auto artifacts = inspect_completed_run_record_artifacts(directory);
    artifact_health_ = summarize_run_record_artifact_health(artifacts);

    std::vector<StoredRunRecord> records;
    records.reserve(artifacts.size());
    for (auto& artifact : artifacts) {
        if (!artifact.loaded()) continue;
        records.push_back({artifact.path, std::move(*artifact.record)});
    }
    index_ = build_run_records_index(records, scope);
    if (!index_.courses.empty()) {
        selected_course_ = 0;
    }
    return true;
}

const RunRecordsCourseIndexEntry*
CompletedRunRecordsBrowser::selected_course() const noexcept {
    if (!selected_course_ || *selected_course_ >= index_.courses.size()) {
        return nullptr;
    }
    return &index_.courses[*selected_course_];
}

const RunDataCatalogEntry*
CompletedRunRecordsBrowser::selected_run() const noexcept {
    const auto* course = selected_course();
    if (!course || !selected_run_ ||
        *selected_run_ >= course->catalog.entries.size()) {
        return nullptr;
    }
    return &course->catalog.entries[*selected_run_];
}

const CompletedRunRecord*
CompletedRunRecordsBrowser::selected_run_record() const noexcept {
    const auto* course = selected_course();
    const auto* entry = selected_run();
    if (!course || !entry || entry->source_index >= course->records.size()) {
        return nullptr;
    }
    return &course->records[entry->source_index].record;
}

const CompletedRunRecord*
CompletedRunRecordsBrowser::personal_best_run_record() const noexcept {
    const auto* course = selected_course();
    if (!course || !course->catalog.personal_best_entry ||
        *course->catalog.personal_best_entry >= course->catalog.entries.size()) {
        return nullptr;
    }
    const auto& entry =
        course->catalog.entries[*course->catalog.personal_best_entry];
    if (entry.source_index >= course->records.size()) return nullptr;
    return &course->records[entry.source_index].record;
}

const CompletedRunRecord*
CompletedRunRecordsBrowser::previous_run_record() const noexcept {
    const auto* course = selected_course();
    if (!course || !course->catalog.previous_entry ||
        *course->catalog.previous_entry >= course->catalog.entries.size()) {
        return nullptr;
    }
    const auto& entry =
        course->catalog.entries[*course->catalog.previous_entry];
    if (entry.source_index >= course->records.size()) return nullptr;
    return &course->records[entry.source_index].record;
}

std::optional<RunResultSummaryPresentation>
CompletedRunRecordsBrowser::selected_run_summary() const {
    const auto* course = selected_course();
    const auto* current = selected_run_record();
    if (!course || !current || !course->catalog.personal_best_entry ||
        *course->catalog.personal_best_entry >=
            course->catalog.entries.size()) {
        return current
            ? present_run_result_summary(*current, nullptr)
            : std::nullopt;
    }

    const auto& pb_entry =
        course->catalog.entries[*course->catalog.personal_best_entry];
    if (pb_entry.source_index >= course->records.size()) {
        return present_run_result_summary(*current, nullptr);
    }
    return present_run_result_summary(
        *current,
        &course->records[pb_entry.source_index].record);
}

std::optional<RunDataDeltaPresentation>
CompletedRunRecordsBrowser::selected_run_previous_delta() const {
    const auto* current = selected_run_record();
    const auto* previous = previous_run_record();
    if (!current || !previous) return std::nullopt;
    return present_run_finish_delta(*previous, current->elapsed_ticks60);
}

std::optional<RunResultSummaryPresentation>
CompletedRunRecordsBrowser::selected_run_target_summary(
    RunDataTargetKind kind) const {
    const auto* current = selected_run_record();
    if (!current) return std::nullopt;
    const auto* target = kind == RunDataTargetKind::PersonalBest
        ? personal_best_run_record()
        : previous_run_record();
    if (!target) return std::nullopt;
    return present_run_result_summary_against(*current, *target, kind);
}

bool CompletedRunRecordsBrowser::adjust_detail_target(int delta) noexcept {
    if (view_ != CompletedRunRecordsView::Detail || delta == 0) return false;

    const RunDataTargetKind requested =
        detail_target_kind_ == RunDataTargetKind::PersonalBest
            ? RunDataTargetKind::Previous
            : RunDataTargetKind::PersonalBest;
    if (!selected_run_target_summary(requested)) return false;

    detail_target_kind_ = requested;
    return true;
}

bool CompletedRunRecordsBrowser::move(int delta) noexcept {
    if (delta == 0) {
        return view_ == CompletedRunRecordsView::Courses
            ? selected_course_.has_value()
            : selected_run_.has_value();
    }

    if (view_ == CompletedRunRecordsView::Detail) {
        return selected_run_.has_value();
    }

    const int step = delta > 0 ? 1 : -1;
    if (view_ == CompletedRunRecordsView::Courses) {
        if (!selected_course_ || index_.courses.empty()) return false;
        const std::size_t count = index_.courses.size();
        *selected_course_ = step > 0
            ? (*selected_course_ + 1) % count
            : (*selected_course_ == 0 ? count - 1 : *selected_course_ - 1);
        selected_run_.reset();
        return true;
    }

    const auto* course = selected_course();
    if (!course || !selected_run_ || course->catalog.entries.empty()) {
        return false;
    }
    const std::size_t count = course->catalog.entries.size();
    *selected_run_ = step > 0
        ? (*selected_run_ + 1) % count
        : (*selected_run_ == 0 ? count - 1 : *selected_run_ - 1);
    return true;
}

bool CompletedRunRecordsBrowser::open_selected_course() noexcept {
    const auto* course = selected_course();
    if (!course || course->catalog.entries.empty()) return false;

    view_ = CompletedRunRecordsView::Runs;
    selected_run_ = course->catalog.previous_entry.value_or(0);
    if (*selected_run_ >= course->catalog.entries.size()) {
        selected_run_ = 0;
    }
    return true;
}

bool CompletedRunRecordsBrowser::open_selected_run_detail() noexcept {
    if (view_ != CompletedRunRecordsView::Runs ||
        !selected_run_record()) {
        return false;
    }
    view_ = CompletedRunRecordsView::Detail;
    detail_target_kind_ = RunDataTargetKind::PersonalBest;
    return true;
}

bool CompletedRunRecordsBrowser::back_to_runs() noexcept {
    if (view_ != CompletedRunRecordsView::Detail) return false;
    view_ = CompletedRunRecordsView::Runs;
    return true;
}

bool CompletedRunRecordsBrowser::back_to_courses() noexcept {
    if (view_ != CompletedRunRecordsView::Runs) return false;
    view_ = CompletedRunRecordsView::Courses;
    selected_run_.reset();
    return true;
}

std::string completed_run_browser_date_text(const std::string& path) {
    return run_date_text(fs::path(path));
}

const char* completed_run_browser_status_name(
    CompletedRunBrowserEntryStatus status) noexcept {
    switch (status) {
    case CompletedRunBrowserEntryStatus::Playable:
        return "PLAYABLE";
    case CompletedRunBrowserEntryStatus::Incompatible:
        return "INCOMPATIBLE";
    case CompletedRunBrowserEntryStatus::Corrupt:
        return "CORRUPT";
    case CompletedRunBrowserEntryStatus::Malformed:
        return "MALFORMED";
    case CompletedRunBrowserEntryStatus::UnsupportedVersion:
        return "UNSUPPORTED";
    case CompletedRunBrowserEntryStatus::IoError:
        return "IO ERROR";
    }
    return "INVALID";
}

void CompletedRunBrowser::clear() noexcept {
    entries_.clear();
    selected_.reset();
}

std::size_t CompletedRunBrowser::playable_count() const noexcept {
    return static_cast<std::size_t>(std::count_if(
        entries_.begin(), entries_.end(),
        [](const CompletedRunBrowserEntry& entry) {
            return entry.playable();
        }));
}

const CompletedRunBrowserEntry* CompletedRunBrowser::selected() const noexcept {
    if (!selected_ || *selected_ >= entries_.size()) return nullptr;
    return &entries_[*selected_];
}

bool CompletedRunBrowser::refresh(
    const std::string& directory,
    const RunPlaybackTarget& target) {
    clear();

    std::error_code ec;
    if (!fs::exists(directory, ec) || ec) {
        return !ec;
    }

    std::vector<fs::path> paths;
    for (fs::directory_iterator it(directory, ec), end;
         !ec && it != end;
         it.increment(ec)) {
        if (!it->is_regular_file()) continue;
        if (it->path().extension() == ".urrun") {
            paths.push_back(it->path());
        }
    }
    if (ec) {
        clear();
        return false;
    }
    std::sort(paths.begin(), paths.end());

    std::vector<InspectedArtifact> inspected;
    inspected.reserve(paths.size());
    std::vector<StoredRunRecord> compatible;
    compatible.reserve(paths.size());

    for (const auto& path : paths) {
        InspectedArtifact item;
        item.path = path.string();

        auto loaded = load_completed_run_record_file(item.path);
        item.status = loaded.status;
        item.detail = loaded.detail;
        if (loaded.loaded()) {
            item.record = *loaded.record;
            std::string compatibility_detail;
            if (!compatible_for_playback(
                    *item.record, target, &compatibility_detail)) {
                item.status = RunRecordLoadStatus::Incompatible;
                item.detail = compatibility_detail;
            } else {
                compatible.push_back({item.path, *item.record});
            }
        }
        inspected.push_back(std::move(item));
    }

    const auto catalog = build_run_data_catalog(compatible, target);
    entries_.reserve(inspected.size());

    for (std::size_t reverse = inspected.size(); reverse > 0; --reverse) {
        const std::size_t source = reverse - 1;
        const auto& item = inspected[source];

        CompletedRunBrowserEntry entry;
        entry.path = item.path;
        entry.date_text = run_date_text(fs::path(item.path));
        entry.chronological_order = source + 1;
        entry.status = browser_status(item.status);
        entry.detail = item.detail;

        if (item.record) {
            entry.course_id = item.record->provenance.course_id;
            entry.time_text = format_run_ticks60(item.record->elapsed_ticks60);
        } else {
            entry.course_id = "--";
            entry.time_text = "--";
        }

        if (item.status == RunRecordLoadStatus::Loaded && item.record) {
            entry.record = *item.record;
            for (const auto& catalog_entry : catalog.entries) {
                if (catalog_entry.path != item.path) continue;
                entry.is_previous = catalog_entry.is_previous;
                entry.is_personal_best = catalog_entry.is_personal_best;
                entry.personal_best_delta_ticks60 =
                    catalog_entry.personal_best_delta_ticks60;
                entry.personal_best_delta_text =
                    catalog_entry.personal_best_delta_text;
                break;
            }
        }

        entries_.push_back(std::move(entry));
    }

    const CompletedRunRecord* personal_best = nullptr;
    for (const auto& entry : entries_) {
        if (entry.playable() && entry.is_personal_best && entry.record) {
            personal_best = &*entry.record;
            break;
        }
    }
    if (personal_best) {
        for (auto& entry : entries_) {
            if (!entry.playable() || !entry.record) continue;
            const auto split_table = present_run_split_table(
                *entry.record,
                *personal_best,
                RunDataTargetKind::PersonalBest);
            if (split_table) {
                entry.personal_best_splits = split_table->rows;
            }
        }
    }

    for (std::size_t i = 0; i < entries_.size(); ++i) {
        if (entries_[i].playable()) {
            selected_ = i;
            break;
        }
    }
    return true;
}

bool CompletedRunBrowser::move(int delta) noexcept {
    if (!selected_ || entries_.empty() || delta == 0) {
        return selected_.has_value();
    }

    const int step = delta > 0 ? 1 : -1;
    std::size_t index = *selected_;
    for (std::size_t tries = 0; tries < entries_.size(); ++tries) {
        if (step > 0) {
            index = (index + 1) % entries_.size();
        } else {
            index = index == 0 ? entries_.size() - 1 : index - 1;
        }
        if (entries_[index].playable()) {
            selected_ = index;
            return true;
        }
    }
    return false;
}

}  // namespace ur::product
