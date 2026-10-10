#include "native/product/baldosa_native_records_summary.hpp"
#include "native/product/completed_run_record.hpp"
#include "native/product/completed_run_store.hpp"

#include <cassert>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <string>
#include <unistd.h>

using namespace ur::product;
int main() {
    namespace fs = std::filesystem;
    const auto root = fs::temp_directory_path() /
        ("ur-native-records-readonly-" + std::to_string(getpid()));
    const auto runs = root / "runs/native-ci-rider";
    fs::create_directories(root);
    auto missing = inspect_baldosa_native_records_archive(runs.string());
    assert(missing.directory_available);
    assert(missing.total_artifacts == 0);
    assert(missing.validated_archives == 0);
    assert(!missing.recent_course.size());

    fs::create_directories(runs);
    CompletedRunRecord record{};
    record.provenance.game_id = "uniracers";
    record.provenance.rom_sha256 = std::string(64, 'a');
    record.provenance.build_compat_id = "historic-backend-only";
    record.provenance.course_id = "course:01";
    record.provenance.mode = "race-1p";
    record.elapsed_ticks60 = 1260;
    record.frame_count = 2000;
    assert(save_completed_run_record_file((runs / "0001.urrun").string(),
                                          record));
    record.provenance.course_id = "course:02";
    record.elapsed_ticks60 = 930;
    assert(save_completed_run_record_file((runs / "0002.urrun").string(),
                                          record));
    {
        std::ofstream bad(runs / "0003.urrun");
        bad << "corrupt archive, not a run\n";
    }
    const auto result = inspect_baldosa_native_records_archive(runs.string());
    assert(result.directory_available);
    assert(result.total_artifacts == 3);
    assert(result.validated_archives == 2);
    assert(result.unavailable_artifacts == 1);
    assert(result.recent_course == "course:02");
    assert(result.recent_ticks60 == 930);

    // The native frontend never grants cross-backend replay authority or
    // rewrites any of these original existing-host artifacts.
    assert(fs::file_size(runs / "0001.urrun") != 0);
    assert(fs::file_size(runs / "0002.urrun") != 0);
    assert(fs::file_size(runs / "0003.urrun") != 0);
    assert(!fs::exists(runs / "0004.urrun"));
    const auto linked = root / "linked-runs";
    fs::create_directory_symlink(runs, linked);
    const auto unsafe = inspect_baldosa_native_records_archive(linked.string());
    assert(!unsafe.directory_available);
    assert(!unsafe.validated_archives);
    fs::remove_all(root);
    std::puts("PASS: native Records reads only canonical selected-profile archives");
}
