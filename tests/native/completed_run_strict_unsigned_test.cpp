#include "completed_run_ghost_trace.hpp"
#include "completed_run_record.hpp"

#include <cassert>
#include <cstdint>
#include <iomanip>
#include <sstream>
#include <string>

using namespace ur::product;

namespace {

std::string signed_field_with_valid_checksum(
    const std::string& encoded,
    const std::string& existing,
    const std::string& replacement,
    std::uint64_t hash_basis) {
    const auto checksum_at = encoded.rfind("checksum ");
    assert(checksum_at != std::string::npos);
    std::string body = encoded.substr(0, checksum_at);
    const auto field_at = body.find(existing);
    assert(field_at != std::string::npos);
    body.replace(field_at, existing.size(), replacement);

    std::uint64_t hash = hash_basis;
    for (unsigned char c : body) {
        hash ^= c;
        hash *= 1099511628211ull;
    }
    std::ostringstream trailer;
    trailer << "checksum " << std::hex << std::setw(16)
            << std::setfill('0') << hash << "\n";
    return body + trailer.str();
}

CompletedRunRecord make_record() {
    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-1p",
    };
    record.elapsed_ticks60 = 100;
    record.frame_count = 3;
    record.splits = {{"finish", 100}};
    record.inputs = {{0, 3, 0x080, 0}};
    return record;
}

}  // namespace

int main() {
    const auto record = make_record();
    const std::string encoded = encode_completed_run_record(record);
    assert(!encoded.empty());
    assert(decode_completed_run_record(encoded).loaded());

    constexpr std::uint64_t kRunBasis = 14695981039346656037ull;
    const auto mutate_run = [&](const std::string& from,
                                const std::string& to) {
        return signed_field_with_valid_checksum(
            encoded, from, to, kRunBasis);
    };

    // These checksums are intentionally correct. Before the fix,
    // std::stoull("-1") turned elapsed/frame counts into UINT64_MAX
    // and the v1 decoder admitted the record as a playable artifact.
    assert(decode_completed_run_record(mutate_run(
        "elapsed_ticks60 100\n", "elapsed_ticks60 -1\n")).status ==
        RunRecordLoadStatus::Malformed);
    assert(decode_completed_run_record(mutate_run(
        "frame_count 3\n", "frame_count -1\n")).status ==
        RunRecordLoadStatus::Malformed);
    assert(decode_completed_run_record(mutate_run(
        "frame_count 3\n", "frame_count +3\n")).status ==
        RunRecordLoadStatus::Malformed);
    assert(decode_completed_run_record(mutate_run(
        "input 0 3 80 0\n", "input 0 3 0x80 0\n")).status ==
        RunRecordLoadStatus::Malformed);

    CompletedRunGhostTrace trace;
    trace.run_artifact_checksum =
        completed_run_record_artifact_checksum(record);
    trace.samples = {{0, 1000, 500, 0, 0x0541, 1, 0x40, {}}};
    const std::string ghost = encode_completed_run_ghost_trace(trace);
    assert(!ghost.empty());
    assert(decode_completed_run_ghost_trace(ghost, &record).loaded());

    constexpr std::uint64_t kGhostBasis = 1469598103934665603ull;
    const auto mutate_ghost = [&](const std::string& from,
                                  const std::string& to) {
        return signed_field_with_valid_checksum(
            ghost, from, to, kGhostBasis);
    };
    // Unbound ghost decode must also reject signed frames; a negative
    // race frame otherwise parsed as an enormous unsigned sample index.
    assert(decode_completed_run_ghost_trace(mutate_ghost(
        "sample 0 ", "sample -1 ")).status ==
        CompletedRunGhostTraceLoadStatus::Malformed);
    assert(decode_completed_run_ghost_trace(mutate_ghost(
        "sample 0 ", "sample +0 ")).status ==
        CompletedRunGhostTraceLoadStatus::Malformed);
    assert(decode_completed_run_ghost_trace(mutate_ghost(
        "sample 0 1000 ", "sample 0 +1000 ")).status ==
        CompletedRunGhostTraceLoadStatus::Malformed);

    return 0;
}
