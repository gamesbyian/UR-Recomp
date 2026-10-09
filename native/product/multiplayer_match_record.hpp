#pragma once

#include "completed_run_record.hpp"
#include "local_multiplayer_match_binding.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace ur::product {

constexpr std::uint32_t kMultiplayerMatchRecordSchemaVersion = 1;

struct MultiplayerMatchRecord {
    std::uint32_t schema_version = kMultiplayerMatchRecordSchemaVersion;
    std::string run_artifact_checksum;
    BoundOrdinaryTwoPlayerMatchContext context;
};

struct MultiplayerMatchDecodeResult {
    std::optional<MultiplayerMatchRecord> record;
    std::string error;

    explicit operator bool() const noexcept { return record.has_value(); }
};

bool validate_multiplayer_match_record(
    const MultiplayerMatchRecord& record,
    std::string* detail = nullptr) noexcept;

std::string encode_multiplayer_match_record(
    const MultiplayerMatchRecord& record);

MultiplayerMatchDecodeResult decode_multiplayer_match_record(
    std::string_view encoded);

std::optional<MultiplayerMatchRecord> make_multiplayer_match_record(
    const CompletedRunRecord& run,
    const BoundOrdinaryTwoPlayerMatchContext& context) noexcept;

bool multiplayer_match_record_matches_run(
    const MultiplayerMatchRecord& record,
    const CompletedRunRecord& run) noexcept;

bool save_multiplayer_match_record_file(
    const std::string& path,
    const MultiplayerMatchRecord& record,
    std::string* detail = nullptr);

MultiplayerMatchDecodeResult load_multiplayer_match_record_file(
    const std::string& path);

std::string multiplayer_match_record_path_for_run(
    std::string_view run_path);

bool save_multiplayer_match_record_for_run(
    const std::string& run_path,
    const CompletedRunRecord& run,
    const MultiplayerMatchRecord& record,
    std::string* detail = nullptr);

MultiplayerMatchDecodeResult load_multiplayer_match_record_for_run(
    const std::string& run_path,
    const CompletedRunRecord& run);

bool append_multiplayer_match_pair(
    const std::string& directory,
    const CompletedRunRecord& run,
    const MultiplayerMatchRecord& record,
    std::string* stored_run_path = nullptr,
    std::string* detail = nullptr,
    void (*after_sidecar_claim_for_test)() = nullptr);

}  // namespace ur::product
