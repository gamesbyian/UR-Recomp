#include "completed_run_replay.hpp"

#include <fstream>

namespace ur::product {
namespace {

void set_detail(std::string* detail, const std::string& value) {
    if (detail) *detail = value;
}

}  // namespace

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
