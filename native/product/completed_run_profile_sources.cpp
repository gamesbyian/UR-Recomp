#include "completed_run_profile_sources.hpp"

#include "completed_run_store.hpp"
#include "host_profile_catalog.hpp"

#include <filesystem>
#include <utility>

namespace ur::product {
namespace {

namespace fs = std::filesystem;

}  // namespace

std::optional<std::vector<RunRecordsProfileSource>>
load_run_records_profile_sources(const std::string& user_data_root) {
    if (user_data_root.empty()) return std::nullopt;

    const fs::path root(user_data_root);
    const auto catalog =
        load_host_profile_catalog_file((root / "profiles-v1.txt").string());
    if (!catalog) return std::nullopt;

    std::vector<RunRecordsProfileSource> out;
    out.reserve(catalog->size());
    for (const auto& entry : *catalog) {
        out.push_back({
            entry.profile_id,
            entry.identity,
            load_valid_run_records(
                (root / "runs" / entry.profile_id).string()),
        });
    }
    return out;
}

}  // namespace ur::product
