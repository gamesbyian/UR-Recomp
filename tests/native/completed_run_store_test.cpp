#include "completed_run_store.hpp"
#include "completed_run_capture.hpp"

#include <cassert>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

using namespace ur::product;

namespace {

CompletedRunRecord run(std::uint64_t ticks) {
    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-1p",
    };
    record.elapsed_ticks60 = ticks;
    record.splits = {{"finish", ticks}};
    return record;
}

RunPlaybackTarget target() {
    const auto p = run(1).provenance;
    return {p.game_id, p.rom_sha256, p.build_compat_id, p.course_id, p.mode};
}

}  // namespace

int main(int argc, char** argv) {
    assert(argc == 2);
    const std::filesystem::path dir = argv[1];

    std::string path1, path2, detail;
    assert(append_completed_run_record(dir.string(), run(1800), &path1, &detail));
    assert(append_completed_run_record(dir.string(), run(1713), &path2, &detail));
    assert(path1 != path2);

    const auto records = load_compatible_run_records(dir.string(), target());
    assert(records.size() == 2);
    const auto previous = select_previous_run(records);
    assert(previous && *previous == 1);

    std::vector<CompletedRunRecord> plain;
    for (const auto& stored : records) plain.push_back(stored.record);
    const auto best = select_fastest_compatible_run(plain, target());
    assert(best && plain[*best].elapsed_ticks60 == 1713);

    auto other_course = run(1600);
    other_course.provenance.course_id = "course:02";
    std::string path3;
    assert(append_completed_run_record(
        dir.string(), other_course, &path3, &detail));

    {
        std::ofstream bad(dir / "run-9999999999999998-9998.urrun");
        bad << "not a completed run\n";
    }
    {
        std::string corrupt = encode_completed_run_record(run(1500));
        assert(!corrupt.empty());
        const auto checksum = corrupt.rfind("checksum ");
        assert(checksum != std::string::npos);
        corrupt[checksum + 9] = corrupt[checksum + 9] == '0' ? '1' : '0';
        std::ofstream bad(dir / "run-9999999999999999-9999.urrun");
        bad << corrupt;
    }

    // A damaged oversized artifact remains visible in Records health, but
    // cannot block valid neighbors or become PB/Previous replay authority.
    const auto oversized_path = dir / "run-9999999999999997-9997.urrun";
    {
        std::ofstream oversized(oversized_path, std::ios::binary);
        assert(oversized);
        oversized.put('x');
    }
    std::filesystem::resize_file(
        oversized_path, kCompletedRunRecordMaxBytes + 1u);

    const auto artifacts = inspect_completed_run_record_artifacts(dir.string());
    assert(artifacts.size() == 6);
    assert(artifacts[0].loaded());
    assert(artifacts[1].loaded());
    assert(artifacts[2].loaded());
    assert(artifacts[3].path == oversized_path.string());
    assert(artifacts[3].status == RunRecordLoadStatus::Malformed);
    assert(artifacts[3].detail == "run record byte limit exceeded");
    assert(!artifacts[3].record);
    assert(artifacts[4].status == RunRecordLoadStatus::Malformed);
    assert(!artifacts[4].record);
    assert(artifacts[5].status == RunRecordLoadStatus::Corrupt);
    assert(!artifacts[5].record);

    const auto health = summarize_run_record_artifact_health(artifacts);
    assert(health.total_artifacts == 6);
    assert(health.loaded_artifacts == 3);
    assert(health.malformed_artifacts == 2);
    assert(health.corrupt_artifacts == 1);
    assert(health.io_errors == 0);
    assert(health.unsupported_artifacts == 0);
    assert(health.unavailable_artifacts() == 3);

    const auto all_valid = load_valid_run_records(dir.string());
    assert(all_valid.size() == 3);
    assert(all_valid[0].path == path1);
    assert(all_valid[1].path == path2);
    assert(all_valid[2].path == path3);
    assert(all_valid[2].record.provenance.course_id == "course:02");

    auto wrong = target();
    wrong.course_id = "course:02";
    const auto course2 = load_compatible_run_records(dir.string(), wrong);
    assert(course2.size() == 1);
    assert(course2[0].record.elapsed_ticks60 == 1600);

    return 0;
}
