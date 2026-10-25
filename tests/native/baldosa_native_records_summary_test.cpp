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
    assert(format_baldosa_native_record_ticks60(0) == "00:00.00");
    assert(format_baldosa_native_record_ticks60(59) == "00:00.98");
    assert(format_baldosa_native_record_ticks60(60) == "00:01.00");
    assert(format_baldosa_native_record_ticks60(930) == "00:15.50");
    // The portable codec permits UINT64 historical ticks; multiplication
    // first overflowed at large values and silently fabricated a time.
    assert(format_baldosa_native_record_ticks60(
        UINT64_MAX) == "5124095576030431:00.25");
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

    // A byte-identical direct external run cannot be smuggled into 1P
    // archive history, even through a live link; a dangling link is also
    // reported as unavailable rather than treated as a missing record.
    const auto foreign_run = root / "foreign-run.urrun";
    fs::copy_file(runs / "0002.urrun", foreign_run);
    fs::create_symlink(foreign_run, runs / "0004-alias.urrun");
    fs::create_symlink(root / "missing-run.urrun",
                       runs / "0005-dangling.urrun");
    const auto aliases =
        inspect_completed_run_record_artifacts(runs.string());
    assert(aliases.size() == 5);
    assert(aliases[3].status == RunRecordLoadStatus::IoError);
    assert(aliases[4].status == RunRecordLoadStatus::IoError);
    assert(load_valid_run_records(runs.string()).size() == 2);
    const auto protected_result =
        inspect_baldosa_native_records_archive(runs.string());
    assert(protected_result.directory_available);
    assert(protected_result.total_artifacts == 5);
    assert(protected_result.validated_archives == 2);
    assert(protected_result.unavailable_artifacts == 3);
    assert(protected_result.recent_course == "course:02");
    assert(protected_result.recent_ticks60 == 930);

    // The native Records summary must resolve the same UTF-8 root that the
    // canonical writer and run catalog already support. On Windows, using
    // filesystem::path(utf8) silently loses non-ACP user-directory names.
    {
        const auto unicode_root = fs::temp_directory_path() /
            fs::u8path(u8"ur-native-records-路径-🌈");
        fs::remove_all(unicode_root);
        const auto unicode_runs = unicode_root / "runs/rider-1";
        std::string stored_path;
        assert(append_completed_run_record(
            unicode_runs.u8string(), record, &stored_path));
        const auto unicode_view = inspect_baldosa_native_records_archive(
            unicode_runs.u8string());
        assert(unicode_view.directory_available);
        assert(unicode_view.total_artifacts == 1);
        assert(unicode_view.validated_archives == 1);
        assert(unicode_view.recent_course == "course:02");
        assert(unicode_view.recent_ticks60 == 930);
        fs::remove_all(unicode_root);
    }

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
    // A broken directory symlink must not masquerade as a valid empty
    // first-run archive. This is distinct from an actually absent path.
    const auto dangling = root / "dangling-runs";
    fs::create_directory_symlink(root / "missing-target", dangling);
    const auto broken = inspect_baldosa_native_records_archive(dangling.string());
    assert(!broken.directory_available);
    assert(broken.total_artifacts == 0);
    assert(broken.validated_archives == 0);
    // An ordinary file is likewise an invalid profile archive root.
    const auto regular = root / "regular-file";
    { std::ofstream file(regular); file << "not a directory"; }
    const auto non_directory = inspect_baldosa_native_records_archive(regular.string());
    assert(!non_directory.directory_available);
    assert(non_directory.total_artifacts == 0);
    fs::remove_all(root);
    std::puts("PASS: native Records reads only canonical selected-profile archives");
}
