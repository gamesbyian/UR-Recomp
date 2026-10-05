#pragma once

#include "host_profile_state.hpp"

#include <optional>
#include <string>
#include <string_view>

namespace ur::product {

enum class HostProfileLoadStatus {
    Loaded,
    Missing,
    Malformed,
    RejectedByPolicy,
    IoError,
};

struct HostProfileLoadResult {
    HostProfileLoadStatus status = HostProfileLoadStatus::IoError;
    std::optional<HostProfileState> state;
    std::string error;

    bool loaded() const noexcept {
        return status == HostProfileLoadStatus::Loaded && state.has_value();
    }
};

enum class HostProfileResolveStatus {
    Loaded,
    DefaultedMissing,
    DefaultedMalformed,
    RejectedByPolicy,
    IoError,
};

struct HostProfileResolveResult {
    HostProfileResolveStatus status = HostProfileResolveStatus::IoError;
    std::optional<HostProfileState> state;
    std::string error;

    explicit operator bool() const noexcept { return state.has_value(); }
};

constexpr bool host_profile_resolve_writable(
    HostProfileResolveStatus status) noexcept {
    return status == HostProfileResolveStatus::Loaded;
}

enum class HostProfileSaveStatus {
    Saved,
    Rejected,
    IoError,
};

HostProfileLoadResult load_host_profile_state_file(
    ExecutionMode mode,
    const std::string& path,
    std::string_view expected_profile_id);

HostProfileResolveResult resolve_host_profile_state_file(
    ExecutionMode mode,
    const std::string& path,
    std::string_view expected_profile_id);

HostProfileSaveStatus save_host_profile_state_file(
    ExecutionMode mode,
    const std::string& path,
    const HostProfileState& state);

}  // namespace ur::product
