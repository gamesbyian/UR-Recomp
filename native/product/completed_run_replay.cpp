#include "completed_run_replay.hpp"

#include <atomic>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <system_error>
#include <utility>

namespace ur::product {
namespace {

void set_detail(std::string* detail, const std::string& value) {
    if (detail) *detail = value;
}

}  // namespace

bool CompletedRunReplayInputStage::reserve(
    const std::string& user_data_root) {
    clear();
    if (user_data_root.empty()) return false;
    namespace fs = std::filesystem;
    const fs::path parent = fs::path(user_data_root) / "replay";
    std::error_code ec;
    fs::create_directories(parent, ec);
    if (ec) return false;

    // Atomic directory creation is exclusive across independent processes.
    // A simultaneous name collision retries without overwriting an input.
    static std::atomic<std::uint64_t> serial{0};
    for (unsigned attempt = 0; attempt < 64; ++attempt) {
        const auto tick = std::chrono::steady_clock::now()
                              .time_since_epoch().count();
        const fs::path staging = parent /
            (".pending-replay-" + std::to_string(tick) + "-" +
             std::to_string(serial.fetch_add(1, std::memory_order_relaxed)));
        ec.clear();
        if (fs::create_directory(staging, ec)) {
            directory_ = staging.string();
            input_path_ = (staging / "selected-run.input").string();
            return true;
        }
        if (ec) return false;
    }
    return false;
}

void CompletedRunReplayInputStage::clear() noexcept {
    if (directory_.empty()) return;
    std::error_code ec;
    std::filesystem::remove_all(directory_, ec);
    directory_.clear();
    input_path_.clear();
}

std::optional<CompletedRunRecord> reload_matching_completed_run_replay_record(
    const std::string& path,
    const CompletedRunRecord& selected,
    const RunPlaybackTarget& target) {
    const std::string expected = encode_completed_run_record(selected);
    if (expected.empty()) return std::nullopt;
    auto loaded = load_completed_run_record_file(path, &target);
    if (!loaded.loaded() ||
        encode_completed_run_record(*loaded.record) != expected)
        return std::nullopt;
    return std::move(*loaded.record);
}

bool stage_completed_run_replay_input_file(
    const std::string& path,
    const CompletedRunRecord& record,
    std::string* detail) {
    const std::string input = encode_completed_run_input_file(record);
    if (input.empty()) {
        set_detail(detail, "record is not valid for deterministic replay");
        return false;
    }

    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) {
        set_detail(detail, "cannot open replay input path");
        return false;
    }
    out.write(input.data(), static_cast<std::streamsize>(input.size()));
    if (!out) {
        set_detail(detail, "cannot write replay input");
        return false;
    }
    // The live input loader opens this file immediately after staging.
    // Report a buffered close/flush failure rather than accepting a truncated
    // replay as the saved run's authoritative controller stream.
    out.close();
    if (!out) {
        set_detail(detail, "cannot finish replay input");
        return false;
    }
    return true;
}

bool CompletedRunReplayFlow::begin() noexcept {
    if (active_) return false;
    active_ = true;
    saw_active_race_ = false;
    return true;
}

CompletedRunReplayTransition CompletedRunReplayFlow::observe(
    bool active_race,
    bool results,
    bool retired) noexcept {
    if (!active_) return CompletedRunReplayTransition::None;
    if (active_race) saw_active_race_ = true;

    if (results && saw_active_race_) {
        active_ = false;
        return CompletedRunReplayTransition::ReturnToBrowser;
    }
    if (retired && saw_active_race_) {
        active_ = false;
        return CompletedRunReplayTransition::Cancelled;
    }
    return CompletedRunReplayTransition::None;
}

}  // namespace ur::product
