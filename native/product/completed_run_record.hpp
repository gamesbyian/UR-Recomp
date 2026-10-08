#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace ur::product {

constexpr std::uint32_t kCompletedRunRecordSchemaVersion = 1;

// Maximum persisted canonical .urrun artifact size, independent of how long
// the guest race ran. No cap is imposed on guest frame/timing authority.
// Existing records are typically kilobytes; this protects Local Runs, Records
// and replay startup from unbounded malformed on-disk artifacts.
constexpr std::size_t kCompletedRunRecordMaxBytes = 64u * 1024u * 1024u;

struct RunRecordProvenance {
    std::string game_id;
    std::string rom_sha256;
    std::string build_compat_id;
    std::string course_id;
    std::string mode;
};

struct RunRecordSplit {
    std::string id;
    std::uint64_t ticks60 = 0;
};

struct RunRecordInputRun {
    std::uint64_t start_frame = 0;
    std::uint64_t duration = 0;
    std::uint16_t p1_mask = 0;
    std::uint16_t p2_mask = 0;

    std::uint64_t end_frame() const { return start_frame + duration; }
};

struct CompletedRunRecord {
    std::uint32_t schema_version = kCompletedRunRecordSchemaVersion;
    RunRecordProvenance provenance;
    std::uint64_t elapsed_ticks60 = 0;
    std::uint64_t frame_count = 0;
    std::string terminal_simulation_digest;
    std::vector<RunRecordSplit> splits;
    std::vector<RunRecordInputRun> inputs;
};

enum class RunRecordLoadStatus {
    Loaded,
    IoError,
    Malformed,
    UnsupportedVersion,
    Corrupt,
    Incompatible,
};

struct RunRecordLoadResult {
    RunRecordLoadStatus status = RunRecordLoadStatus::Malformed;
    std::optional<CompletedRunRecord> record;
    std::string detail;

    bool loaded() const { return status == RunRecordLoadStatus::Loaded && record.has_value(); }
};

struct RunPlaybackTarget {
    std::string game_id;
    std::string rom_sha256;
    std::string build_compat_id;
    std::string course_id;
    std::string mode;
};

class CompletedRunRecorder {
public:
    void observe_input_frame(std::uint64_t frame, std::uint16_t p1_mask, std::uint16_t p2_mask = 0);
    void reset();
    const std::vector<RunRecordInputRun>& inputs() const { return inputs_; }

private:
    std::vector<RunRecordInputRun> inputs_;
};

bool validate_completed_run_record(const CompletedRunRecord& record, std::string* detail = nullptr);
bool compatible_for_playback(const CompletedRunRecord& record, const RunPlaybackTarget& target, std::string* detail = nullptr);

std::string encode_completed_run_record(const CompletedRunRecord& record);
/* Return the canonical 16-hex artifact checksum used by the encoded record. */
std::string completed_run_record_artifact_checksum(const CompletedRunRecord& record);
/* Emit the existing deterministic INPUT_FILE grammar verbatim. */
std::string encode_completed_run_input_file(
    const CompletedRunRecord& record,
    std::uint64_t frame_offset = 0);
RunRecordLoadResult decode_completed_run_record(const std::string& text);
bool save_completed_run_record_file(const std::string& path, const CompletedRunRecord& record, std::string* detail = nullptr);
RunRecordLoadResult load_completed_run_record_file(const std::string& path, const RunPlaybackTarget* target = nullptr);

/* Random-access the resolved 12-bit P1/P2 words from a validated,
 * sorted RLE run in O(log input runs), returning zero in gaps or past finish. */
std::pair<std::uint16_t, std::uint16_t> run_record_input_at(
    const CompletedRunRecord& record,
    std::uint64_t frame);

}  // namespace ur::product
