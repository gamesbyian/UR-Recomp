#include "completed_run_record.hpp"

#include <cassert>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>

using namespace ur::product;

namespace {

CompletedRunRecord make_record() {
    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-1p",
    };
    record.elapsed_ticks60 = 1713;
    record.frame_count = 168;
    record.splits = {{"finish", 1713}};
    record.inputs = {{0, 120, 0x080, 0}, {120, 24, 0x081, 0}};
    return record;
}

}  // namespace

int main(int argc, char** argv) {
    assert(argc == 2);
    const std::filesystem::path root(argv[1]);
    const auto valid_path = root / "valid.urrun";
    const auto big_path = root / "oversize.urrun";

    auto record = make_record();
    std::string detail;
    assert(save_completed_run_record_file(valid_path.string(), record, &detail));
    const auto original = load_completed_run_record_file(valid_path.string());
    assert(original.loaded());
    assert(original.record->inputs.size() == 2);
    assert(original.record->elapsed_ticks60 == 1713);

    const RunPlaybackTarget target{
        record.provenance.game_id,
        record.provenance.rom_sha256,
        record.provenance.build_compat_id,
        record.provenance.course_id,
        record.provenance.mode,
    };
    assert(load_completed_run_record_file(valid_path.string(), &target).loaded());

    // Test the actual disk boundary with a sparse file larger than the
    // published cap; the loader must refuse it before unbounded allocation.
    {
        std::ofstream output(big_path, std::ios::binary);
        assert(output);
        output.put('x');
    }
    std::filesystem::resize_file(big_path, kCompletedRunRecordMaxBytes + 1u);
    const auto oversized = load_completed_run_record_file(big_path.string());
    assert(oversized.status == RunRecordLoadStatus::Malformed);
    assert(oversized.detail == "run record byte limit exceeded");
    assert(!oversized.record);

    // Direct decode callers are also size-bounded, even without file I/O.
    const auto huge_text = std::string(kCompletedRunRecordMaxBytes + 1u, 'x');
    const auto decoded_oversize = decode_completed_run_record(huge_text);
    assert(decoded_oversize.status == RunRecordLoadStatus::Malformed);
    assert(decoded_oversize.detail == "run record byte limit exceeded");

    // A corrupt run cannot be promoted for playback; another existing
    // healthy artifact in the same profile directory must remain playable.
    const auto bad_path = root / "corrupt.urrun";
    {
        std::ifstream input(valid_path, std::ios::binary);
        const std::string data{std::istreambuf_iterator<char>(input),
                               std::istreambuf_iterator<char>()};
        std::string damaged = data;
        const auto offset = damaged.find("elapsed_ticks60 1713");
        assert(offset != std::string::npos);
        damaged.replace(offset, 20, "elapsed_ticks60 1714");
        std::ofstream output(bad_path, std::ios::binary);
        output << damaged;
    }
    const auto corrupt = load_completed_run_record_file(bad_path.string(), &target);
    assert(corrupt.status == RunRecordLoadStatus::Corrupt);
    assert(!corrupt.record);
    assert(load_completed_run_record_file(valid_path.string(), &target).loaded());

    return 0;
}
