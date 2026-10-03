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
};

HostProductLoadResult load_host_product_state_file(const std::string& path);
HostProductSaveStatus save_host_product_state_file(
    const std::string& path,
    const HostProductState& state);

}  // namespace ur::product
