#include "completed_run_record.hpp"

#include <cassert>
#include <cstdio>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string>

using namespace ur::product;

namespace {

CompletedRunRecord representative_dragster_run() {
    CompletedRunRecorder recorder;
    for (std::uint64_t f = 0; f < 180; ++f) recorder.observe_input_frame(f, 0x100);
    for (std::uint64_t f = 180; f < 204; ++f) recorder.observe_input_frame(f, 0x101);
    for (std::uint64_t f = 204; f < 228; ++f) recorder.observe_input_frame(f, 0x100);
    for (std::uint64_t f = 228; f < 252; ++f) recorder.observe_input_frame(f, 0x101);

    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "crawler.dragster",
        "race-1p",
    };
    record.elapsed_ticks60 = 1713;
    record.terminal_simulation_digest =
        "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";
    record.splits = {{"start", 0}, {"mid", 840}, {"finish", 1713}};
    record.inputs = recorder.inputs();
    return record;
}

std::uint64_t fnv1a64(const std::string& text) {
    std::uint64_t hash = 1469598103934665603ull;
    for (unsigned char c : text) {
        hash ^= c;
        hash *= 1099511628211ull;
    }
    return hash;
}

std::string with_version(const std::string& encoded, unsigned version) {
    const auto checksum_pos = encoded.rfind("checksum ");
    assert(checksum_pos != std::string::npos);
    std::string body = encoded.substr(0, checksum_pos);
    const auto newline = body.find('\n');
    body.replace(0, newline, "URRUN " + std::to_string(version));
    std::ostringstream checksum;
    checksum << std::hex << std::setw(16) << std::setfill('0') << fnv1a64(body);
    return body + "checksum " + checksum.str() + "\n";
}

}  // namespace

int main() {
    const auto original = representative_dragster_run();
    std::string detail;
    assert(validate_completed_run_record(original, &detail));
    assert(original.inputs.size() == 4);

    // The primary replay stream is the same per-frame 12-bit controller word
    // semantics used by the deterministic INPUT_FILE fixture machinery.
    assert(run_record_input_at(original, 0).first == 0x100);
    assert(run_record_input_at(original, 179).first == 0x100);
    assert(run_record_input_at(original, 180).first == 0x101);
    assert(run_record_input_at(original, 204).first == 0x100);
    assert(run_record_input_at(original, 228).first == 0x101);
    assert(run_record_input_at(original, 252).first == 0);

    const std::string encoded = encode_completed_run_record(original);
    assert(!encoded.empty());

    const auto decoded = decode_completed_run_record(encoded);
    assert(decoded.loaded());
    assert(decoded.record->elapsed_ticks60 == original.elapsed_ticks60);
    assert(decoded.record->splits.size() == 3);
    assert(decoded.record->inputs.size() == original.inputs.size());

    // Persist/reload through the filesystem to exercise the fresh-process
    // artifact boundary rather than an in-memory round trip only.
    const std::string path = "completed-run-record-test.urrun";
    assert(save_completed_run_record_file(path, original, &detail));
    const RunPlaybackTarget target{
        original.provenance.game_id,
        original.provenance.rom_sha256,
        original.provenance.build_compat_id,
        original.provenance.course_id,
        original.provenance.mode,
    };
    const auto loaded = load_completed_run_record_file(path, &target);
    assert(loaded.loaded());
    std::remove(path.c_str());

    // Re-driving the loaded record yields the exact same controller stream.
    for (std::uint64_t frame = 0; frame < 300; ++frame) {
        assert(run_record_input_at(*loaded.record, frame) ==
               run_record_input_at(original, frame));
    }

    auto incompatible = target;
    incompatible.course_id = "crawler.bowl";
    const std::string path2 = "completed-run-record-test-incompatible.urrun";
    assert(save_completed_run_record_file(path2, original, &detail));
    const auto rejected = load_completed_run_record_file(path2, &incompatible);
    assert(rejected.status == RunRecordLoadStatus::Incompatible);
    assert(!rejected.record.has_value());
    std::remove(path2.c_str());

    std::string corrupt = encoded;
    const auto pos = corrupt.find("elapsed_ticks60 1713");
    assert(pos != std::string::npos);
    corrupt.replace(pos, std::string("elapsed_ticks60 1713").size(), "elapsed_ticks60 1714");
    assert(decode_completed_run_record(corrupt).status == RunRecordLoadStatus::Corrupt);

    const auto future = decode_completed_run_record(with_version(encoded, 2));
    assert(future.status == RunRecordLoadStatus::UnsupportedVersion);

    return 0;
}
