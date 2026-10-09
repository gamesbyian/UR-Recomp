#pragma once
#include "modern_racer_identity.hpp"
#include "host_profile_state.hpp"

#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace ur::product {

struct HostProfileCatalogEntry {
    std::string profile_id;
    HostRacerIdentity identity;

    bool operator==(const HostProfileCatalogEntry& other) const noexcept {
        return profile_id == other.profile_id && identity == other.identity;
    }
};

std::string encode_host_profile_catalog(
    const std::vector<HostProfileCatalogEntry>& entries);
std::optional<std::vector<HostProfileCatalogEntry>> decode_host_profile_catalog(
    std::string_view encoded);
bool save_host_profile_catalog_file(
    const std::string& path,
    const std::vector<HostProfileCatalogEntry>& entries);

enum class HostProfileCatalogSaveStatus {
    Saved,
    Conflict, // the canonical roster has changed since the caller read it
    Rejected,
    IoError,
};

HostProfileCatalogSaveStatus save_host_profile_catalog_file_if_current(
    const std::string& path,
    const std::vector<HostProfileCatalogEntry>& expected_current,
    const std::vector<HostProfileCatalogEntry>& next);
std::optional<std::vector<HostProfileCatalogEntry>> load_host_profile_catalog_file(
    const std::string& path);
std::string make_profile_id(
    std::string_view racer_name,
    const std::vector<HostProfileCatalogEntry>& existing);

bool catalog_entry_matches_profile_state(
    const HostProfileCatalogEntry& entry,
    const HostProfileState& state) noexcept;

bool profile_catalog_authorizes_state(
    const std::vector<HostProfileCatalogEntry>& entries,
    const HostProfileState& state) noexcept;

}  // namespace ur::product
