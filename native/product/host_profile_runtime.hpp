#pragma once

#include "host_product_state.hpp"

#include <optional>
#include <string>
#include <string_view>

namespace ur::product {

enum class HostProfileSaveRootStatus {
    DefaultRoot,
    IsolatedProfileRoot,
    Rejected,
};

bool is_safe_profile_storage_id(std::string_view value) noexcept;

struct HostProfileSaveRootDecision {
    HostProfileSaveRootStatus status = HostProfileSaveRootStatus::Rejected;
    std::string save_root;
    std::string error;

    bool isolated() const noexcept {
        return status == HostProfileSaveRootStatus::IsolatedProfileRoot;
    }
};

HostProfileSaveRootDecision resolve_host_profile_save_root(
    ExecutionMode mode,
    const std::optional<std::string>& active_profile_id,
    std::string_view override_root = {});

}  // namespace ur::product
