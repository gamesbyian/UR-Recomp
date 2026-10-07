#pragma once

#include "completed_run_record.hpp"
#include "local_multiplayer_match_binding.hpp"

#include <cstdint>
#include <optional>
#include <string>

namespace ur::product {

constexpr std::uint32_t kCompletedRunMatchMetadataSchemaVersion = 1;

struct CompletedRunMatchMetadata {
    std::uint32_t schema_version = kCompletedRunMatchMetadataSchemaVersion;
    std::string run_artifact_checksum;
    std::string course_id;
    HostProfileCatalogEntry player1;
    HostProfileCatalogEntry player2;
    std::uint16_t player1_hundredths =
        ur::title::kOrdinaryTwoPlayerNoTimeHundredths;
    std::uint16_t player2_hundredths =
        ur::title::kOrdinaryTwoPlayerNoTimeHundredths;
    ur::title::OrdinaryTwoPlayerRaceOutcome outcome =
        ur::title::OrdinaryTwoPlayerRaceOutcome::Draw;
};

enum class CompletedRunMatchMetadataLoadStatus : std::uint8_t {
    Loaded = 0,
    IoError = 1,
    Malformed = 2,
    UnsupportedVersion = 3,
    Corrupt = 4,
    Incompatible = 5,
};

struct CompletedRunMatchMetadataLoadResult {
    CompletedRunMatchMetadataLoadStatus status =
        CompletedRunMatchMetadataLoadStatus::Malformed;
    std::optional<CompletedRunMatchMetadata> metadata;
    std::string detail;

    bool loaded() const noexcept {
        return status == CompletedRunMatchMetadataLoadStatus::Loaded &&
               metadata.has_value();
    }
};

/* Build product metadata from the already-authoritative match tuple and bind
 * it to one immutable completed-run artifact. The run's own replay schema is
 * unchanged; course identity must agree across both artifacts. */
std::optional<CompletedRunMatchMetadata> make_completed_run_match_metadata(
    const BoundOrdinaryTwoPlayerMatchContext& context,
    const CompletedRunRecord& run) noexcept;

bool validate_completed_run_match_metadata(
    const CompletedRunMatchMetadata& metadata,
    const CompletedRunRecord* bound_run = nullptr,
    std::string* detail = nullptr) noexcept;

std::string encode_completed_run_match_metadata(
    const CompletedRunMatchMetadata& metadata);

CompletedRunMatchMetadataLoadResult decode_completed_run_match_metadata(
    const std::string& text,
    const CompletedRunRecord* bound_run = nullptr);

bool save_completed_run_match_metadata_file(
    const std::string& path,
    const CompletedRunMatchMetadata& metadata,
    std::string* detail = nullptr);

CompletedRunMatchMetadataLoadResult load_completed_run_match_metadata_file(
    const std::string& path,
    const CompletedRunRecord* bound_run = nullptr);

}  // namespace ur::product
