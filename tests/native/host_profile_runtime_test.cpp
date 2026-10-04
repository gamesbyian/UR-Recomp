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
    return 0;
}
