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
    Conflict, // another process replaced the expected snapshot
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

// Compare-and-replace under the same persistent per-path OS handle lock
// used by launch-checkpoint retirement. A rollback is authorized only if the
// disk still contains the exact intermediate state it is undoing. std::nullopt
// means create-only: a missing target must remain missing until publication.
HostProfileSaveStatus save_host_profile_state_file_if_current(
    ExecutionMode mode,
    const std::string& path,
    const std::optional<HostProfileState>& expected_current,
    const HostProfileState& next);

// Retire a profile file only while it still matches the exact snapshot this
// process created. Prevents catalog-create failure cleanup from deleting an
// unrelated process's subsequent valid state.
HostProfileSaveStatus remove_host_profile_state_file_if_current(
    ExecutionMode mode,
    const std::string& path,
    const HostProfileState& expected_current);

// A failed catalog registration can leave the persistent OS lock pathname
// behind even after conditional cleanup removed its profile file. A new
// explicit creation may safely reuse only that inert lock-only directory.
// Never infer recoverability from a root containing SRAM, profile, staging,
// symlinks, or other unknown preexisting data.
bool reusable_aborted_profile_creation_root(const std::string& root_path);

}  // namespace ur::product
