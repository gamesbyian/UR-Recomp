#pragma once

#include "host_product_state.hpp"
#include "output_resolution_policy.hpp"

#include <optional>
#include <vector>

namespace ur::product {

enum class OutputResolutionApplyStatus {
    NotApplicable,
    Applied,
    Unsupported,
    HostRejected,
};

struct OutputResolutionApplyResult {
    OutputResolutionApplyStatus status =
        OutputResolutionApplyStatus::NotApplicable;
    std::optional<HostOutputMode> selected_mode;

    explicit operator bool() const noexcept {
        return status == OutputResolutionApplyStatus::Applied ||
               status == OutputResolutionApplyStatus::NotApplicable;
    }
};

using ApplyOutputModeFn = bool (*)(void* context, const HostOutputMode& mode);

OutputResolutionApplyResult apply_output_resolution_policy(
    HostDisplayMode display_mode,
    const HostOutputResolution& resolution,
    const std::vector<HostOutputMode>& modes,
    const HostOutputMode& native_mode,
    ApplyOutputModeFn apply_mode,
    void* context);

}  // namespace ur::product
