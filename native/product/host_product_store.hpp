#pragma once

#include "host_product_state.hpp"

#include <optional>
#include <string>

namespace ur::product {

enum class HostProductLoadStatus {
    Loaded,
    Missing,
    Rejected,
    IoError,
};

struct HostProductLoadResult {
    HostProductLoadStatus status = HostProductLoadStatus::IoError;
    std::optional<HostProductState> state;
    std::string error;

    bool loaded() const noexcept {
        return status == HostProductLoadStatus::Loaded && state.has_value();
    }
};

enum class HostProductSaveStatus {
    Saved,
    Rejected,
    IoError,
    Conflict, // another process replaced our exact expected host state
};

HostProductLoadResult load_host_product_state_file(const std::string& path);
HostProductSaveStatus save_host_product_state_file(
    const std::string& path,
    const HostProductState& state);

// Compare the complete typed global settings/profile-selector state while
// holding an OS-handle-owned per-path interprocess lock through publication.
// std::nullopt is create-only, never an unconditional overwrite.
HostProductSaveStatus save_host_product_state_file_if_current(
    const std::string& path,
    const std::optional<HostProductState>& expected_current,
    const HostProductState& next);

}  // namespace ur::product
