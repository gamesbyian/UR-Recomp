#include "host_profile_runtime.hpp"

#include <cassert>
#include <optional>
#include <string>

using namespace ur::product;

int main() {
    {
        const auto d = resolve_host_profile_save_root(
            ExecutionMode::Authentic, std::string("alpha"));
        assert(d.status == HostProfileSaveRootStatus::DefaultRoot);
        assert(d.save_root == "saves");
        assert(!d.isolated());
    }
    {
        const auto d = resolve_host_profile_save_root(
            ExecutionMode::Modern, std::nullopt);
        assert(d.status == HostProfileSaveRootStatus::DefaultRoot);
        assert(d.save_root == "saves");
        assert(!d.isolated());
    }
    {
        const auto d = resolve_host_profile_save_root(
            ExecutionMode::Modern, std::string("alpha"));
        assert(d.status == HostProfileSaveRootStatus::IsolatedProfileRoot);
        assert(d.save_root == "saves/profile-alpha");
        assert(d.isolated());
    }
    {
        const auto d = resolve_host_profile_save_root(
            ExecutionMode::Modern,
            std::string("alpha"),
            "/tmp/ur-profile-alpha");
        assert(d.status == HostProfileSaveRootStatus::IsolatedProfileRoot);
        assert(d.save_root == "/tmp/ur-profile-alpha");
        assert(d.isolated());
    }
    {
        const auto d = resolve_host_profile_save_root(
            ExecutionMode::Modern, std::string("bad/profile"));
        assert(d.status == HostProfileSaveRootStatus::Rejected);
        assert(d.save_root.empty());
        assert(!d.error.empty());
    }
    {
        const auto d = resolve_host_profile_save_root(
            ExecutionMode::Modern, std::string("CON"));
        assert(d.status == HostProfileSaveRootStatus::Rejected);
        assert(!is_safe_profile_storage_id("CON"));
        assert(!is_safe_profile_storage_id("nul.save"));
        assert(!is_safe_profile_storage_id("COM1.profile"));
        assert(!is_safe_profile_storage_id("LPT9"));
        assert(!is_safe_profile_storage_id("alpha."));
        assert(is_safe_profile_storage_id("alpha"));
        assert(is_safe_profile_storage_id("ALPHA"));
        assert(is_safe_profile_storage_id("profile.alpha"));
    }
    return 0;
}
