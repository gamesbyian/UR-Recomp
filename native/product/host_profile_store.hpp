#pragma once

#include "host_profile_state.hpp"

#include <optional>
#include <string>

namespace ur::product {

enum class HostProfileLoadStatus {
    Loaded,
    Missing,
    Rejected,
    IoError,
};

struct HostProfileLoadResult {
    HostProfileLoadStatus status = HostProfileLoadStatus::IoError;
    std::optional<HostProfileState> state;
    bool migrated = false;
    std::string error;

    bool loaded() const noexcept {
        return status == HostProfileLoadStatus::Loaded && state.has_value();
    }
};

enum class HostProfileSaveStatus {
    Saved,
    Rejected,
    IoError,
};

HostProfileLoadResult load_host_profile_state_file(
    ExecutionMode mode,
    const std::string& path,
    std::string_view expected_profile_id);

HostProfileSaveStatus save_host_profile_state_file(
    ExecutionMode mode,
    const std::string& path,
    const HostProfileState& state);

}  // namespace ur::product
