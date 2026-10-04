#include "host_profile_runtime.hpp"

namespace ur::product {

HostProfileSaveRootDecision resolve_host_profile_save_root(
    ExecutionMode mode,
    const std::optional<std::string>& active_profile_id,
    std::string_view override_root) {
    if (!policy_for(mode).host_profiles) {
        return {HostProfileSaveRootStatus::DefaultRoot, "saves", {}};
    }
    if (!active_profile_id) {
        return {HostProfileSaveRootStatus::DefaultRoot, "saves", {}};
    }
    if (!is_valid_profile_id(*active_profile_id)) {
        return {
            HostProfileSaveRootStatus::Rejected,
            {},
            "invalid active profile identifier"};
    }

    if (!override_root.empty()) {
        return {
            HostProfileSaveRootStatus::IsolatedProfileRoot,
            std::string(override_root),
            {}};
    }

    return {
        HostProfileSaveRootStatus::IsolatedProfileRoot,
        "saves/profiles/" + *active_profile_id,
        {}};
}

}  // namespace ur::product
