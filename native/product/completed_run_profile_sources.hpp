#pragma once

#include "completed_run_catalog.hpp"

#include <optional>
#include <string>
#include <vector>

namespace ur::product {

/* Read-only adapter from the authoritative Modern profile catalog plus each
 * profile-owned run namespace into the storage-agnostic Records profile model.
 * The caller owns user-data-root resolution; this layer never chooses a root. */
std::optional<std::vector<RunRecordsProfileSource>>
load_run_records_profile_sources(const std::string& user_data_root);

}  // namespace ur::product
