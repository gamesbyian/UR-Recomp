#pragma once

#include "completed_run_record.hpp"

#include <optional>
#include <string>
#include <vector>

namespace ur::product {

struct StoredRunRecord {
    std::string path;
    CompletedRunRecord record;
};

/* Append one immutable run artifact to a directory. The filename is
 * host-owned ordering metadata; the record body remains the authoritative
 * portable artifact. */
bool append_completed_run_record(
    const std::string& directory,
    const CompletedRunRecord& record,
    std::string* stored_path = nullptr,
    std::string* detail = nullptr);

/* Load compatible records in filename order. Malformed/corrupt/incompatible
 * files are ignored rather than poisoning the usable catalog. */
std::vector<StoredRunRecord> load_compatible_run_records(
    const std::string& directory,
    const RunPlaybackTarget& target);

std::optional<std::size_t> select_previous_run(
    const std::vector<StoredRunRecord>& records);

}  // namespace ur::product
