#include "output_resolution_runtime_policy.hpp"

namespace ur::product {

OutputResolutionApplyResult apply_output_resolution_policy(
    HostDisplayMode display_mode,
    const HostOutputResolution& resolution,
    const std::vector<HostOutputMode>& modes,
    const HostOutputMode& native_mode,
    ApplyOutputModeFn apply_mode,
    void* context) {
    if (display_mode != HostDisplayMode::Fullscreen) {
        return {OutputResolutionApplyStatus::NotApplicable, std::nullopt};
    }

    const auto selected =
        resolve_fullscreen_output_mode(resolution, modes, native_mode);
    if (!selected) {
        return {OutputResolutionApplyStatus::Unsupported, std::nullopt};
    }

    if (!apply_mode || !apply_mode(context, *selected)) {
        return {OutputResolutionApplyStatus::HostRejected, selected};
    }

    return {OutputResolutionApplyStatus::Applied, selected};
}

}  // namespace ur::product
