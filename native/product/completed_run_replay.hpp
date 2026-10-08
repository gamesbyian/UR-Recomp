#pragma once

#include "completed_run_record.hpp"

#include <cstdint>
#include <string>

namespace ur::product {

enum class CompletedRunReplayTransition : std::uint8_t {
    None = 0,
    ReturnToBrowser = 1,
    Cancelled = 2,
};

bool stage_completed_run_replay_input_file(
    const std::string& path,
    const CompletedRunRecord& record,
    std::string* detail = nullptr);

// Reserve a private staging namespace beneath the user-data replay directory.
// Never overwrite another running game's selected replay input. The path stays
// alive through the complete playback session, then is cleaned on exit/cancel.
class CompletedRunReplayInputStage {
public:
    CompletedRunReplayInputStage() = default;
    ~CompletedRunReplayInputStage() { clear(); }
    CompletedRunReplayInputStage(const CompletedRunReplayInputStage&) = delete;
    CompletedRunReplayInputStage& operator=(const CompletedRunReplayInputStage&) = delete;

    bool reserve(const std::string& user_data_root);
    void clear() noexcept;
    const std::string& input_path() const noexcept { return input_path_; }

private:
    std::string directory_;
    std::string input_path_;
};

class CompletedRunReplayFlow {
public:
    bool begin() noexcept;
    void cancel() noexcept { active_ = false; }
    bool active() const noexcept { return active_; }

    CompletedRunReplayTransition observe(
        bool active_race,
        bool results,
        bool retired) noexcept;

private:
    bool active_ = false;
    bool saw_active_race_ = false;
};

}  // namespace ur::product
