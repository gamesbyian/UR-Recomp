#include "host_profile_runtime.hpp"

namespace ur::product {
namespace {

std::string canonical_windows_component(std::string_view value) {
    std::string out(value);
    for (char& ch : out) {
        if (ch >= 'A' && ch <= 'Z') {
            ch = static_cast<char>(ch - 'A' + 'a');
        }
    }
    while (!out.empty() && out.back() == '.') out.pop_back();
    return out;
}

bool windows_reserved_component(std::string_view value) {
    const std::string canonical = canonical_windows_component(value);
    const auto dot = canonical.find('.');
    const std::string_view stem =
        dot == std::string::npos
            ? std::string_view(canonical)
            : std::string_view(canonical).substr(0, dot);
    if (stem == "con" || stem == "prn" ||
        stem == "aux" || stem == "nul") {
        return true;
    }
    if (stem.size() == 4 &&
        stem[3] >= '1' && stem[3] <= '9') {
        const std::string_view prefix(stem.data(), 3);
        return prefix == "com" || prefix == "lpt";
    }
    return false;
}

}  // namespace

bool is_safe_profile_storage_id(std::string_view value) noexcept {
    if (!is_valid_profile_id(value)) return false;
    const std::string canonical = canonical_windows_component(value);
    return !canonical.empty() &&
           canonical.size() == value.size() &&
           !windows_reserved_component(value);
}

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
    if (!is_safe_profile_storage_id(*active_profile_id)) {
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
        "saves/profile-" + *active_profile_id,
        {}};
}

}  // namespace ur::product
