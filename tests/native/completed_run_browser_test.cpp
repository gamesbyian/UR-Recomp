#include "completed_run_browser.hpp"

#include <cassert>
#include <filesystem>
#include <fstream>
#include <string>

using namespace ur::product;

namespace {

CompletedRunRecord run(
    std::uint64_t ticks,
    const std::string& course = "course:01",
    std::uint64_t checkpoint = 840) {
    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        course,
        "race-1p",
    };
    record.elapsed_ticks60 = ticks;
    record.frame_count = 2;
    record.splits = {
        {"checkpoint-1", checkpoint},
        {"finish", ticks},
    };
    record.inputs = {{0, 2, 0x100, 0}};
    return record;
}

RunPlaybackTarget target() {
    const auto p = run(1).provenance;
    return {p.game_id, p.rom_sha256, p.build_compat_id, p.course_id, p.mode};
}

void write_record(
    const std::filesystem::path& path,
    const CompletedRunRecord& record) {
    std::string detail;
    assert(save_completed_run_record_file(path.string(), record, &detail));
}

}  // namespace

int main(int argc, char** argv) {
    assert(argc == 2);

    const std::filesystem::path root(argv[1]);
    std::filesystem::create_directories(root);

    write_record(
        root / "run-0000000000000000-0001.urrun", run(1800));
    write_record(
        root / "run-0000000000000000-0002.urrun", run(1713));
    write_record(
        root / "run-0000000000000000-0003.urrun", run(1713));
    write_record(
        root / "run-0000000000000000-0004.urrun",
        run(1750, "course:01", 850));
    write_record(
        root / "run-0000000000000000-0005.urrun",
        run(900, "course:02"));

    std::string corrupt = encode_completed_run_record(run(1600));
    assert(!corrupt.empty());
    const auto checksum = corrupt.rfind("checksum ");
    assert(checksum != std::string::npos);
    corrupt[checksum + 9] = corrupt[checksum + 9] == '0' ? '1' : '0';
    {
        std::ofstream out(
            root / "run-0000000000000000-0006.urrun",
            std::ios::binary);
        out << corrupt;
    }

    CompletedRunBrowser browser;
    assert(browser.refresh(root.string(), target()));
    assert(browser.size() == 6);
    assert(browser.playable_count() == 4);

    assert(browser.entries()[0].chronological_order == 6);
    assert(browser.entries()[0].status ==
           CompletedRunBrowserEntryStatus::Corrupt);
    assert(!browser.entries()[0].playable());

    assert(browser.entries()[1].chronological_order == 5);
    assert(browser.entries()[1].status ==
           CompletedRunBrowserEntryStatus::Incompatible);
    assert(browser.entries()[1].course_id == "course:02");
    assert(!browser.entries()[1].playable());

    assert(browser.selected());
    assert(browser.selected()->chronological_order == 4);
    assert(browser.selected()->date_text.size() == 10);
    assert(browser.selected()->date_text != "--");
    assert(browser.selected()->is_previous);
    assert(!browser.selected()->is_personal_best);
    assert(browser.selected()->time_text == "0:29.10/60");
    assert(browser.selected()->personal_best_delta_ticks60 == 37);
    assert(browser.selected()->personal_best_delta_text == "+0:00.37/60");
    assert(browser.selected()->personal_best_splits.size() == 2);
    assert(browser.selected()->personal_best_splits[0].id == "checkpoint-1");
    assert(browser.selected()->personal_best_splits[0].delta_text == "+0:00.10/60");

    assert(browser.move(1));
    assert(browser.selected()->chronological_order == 3);
    assert(browser.selected()->is_personal_best);
    assert(browser.selected()->time_text == "0:28.33/60");
    assert(browser.selected()->personal_best_delta_ticks60 == 0);
    assert(browser.selected()->personal_best_delta_text == "+0:00.00/60");
    assert(browser.selected()->personal_best_splits.size() == 2);

    assert(browser.move(-1));
    assert(browser.selected()->chronological_order == 4);

    // Returning from an older run must not teleport the list selection to
    // newest, including when a new completed run arrived during playback.
    assert(browser.move(1));
    const std::string older_selection = browser.selected()->path;
    assert(browser.refresh(root.string(), target()));
    assert(browser.selected() && browser.selected()->path == older_selection);
    const auto arriving_path =
        root / "run-0000000000000000-0008.urrun";
    write_record(arriving_path, run(1699));
    assert(browser.refresh(root.string(), target()));
    assert(browser.selected() && browser.selected()->path == older_selection);

    // The same filename becoming corrupt must lose its selection authority
    // immediately; fall back to the next playable artifact instead.
    std::string selected_corrupt = encode_completed_run_record(run(1713));
    const auto selected_checksum = selected_corrupt.rfind("checksum ");
    assert(selected_checksum != std::string::npos);
    selected_corrupt[selected_checksum + 9] =
        selected_corrupt[selected_checksum + 9] == '0' ? '1' : '0';
    {
        std::ofstream damaged(older_selection, std::ios::binary | std::ios::trunc);
        damaged << selected_corrupt;
        assert(static_cast<bool>(damaged));
    }
    assert(browser.refresh(root.string(), target()));
    assert(browser.selected() && browser.selected()->path ==
           arriving_path.string());

    // Restore the fixture before unrelated Records assertions below.
    write_record(older_selection, run(1713));
    std::filesystem::remove(arriving_path);
    assert(browser.refresh(root.string(), target()));
    assert(browser.selected());
    assert(browser.selected()->chronological_order == 4);

    assert(!browser.entries()[0].personal_best_delta_ticks60);
    assert(browser.entries()[0].personal_best_delta_text == "--");
    assert(!browser.entries()[1].personal_best_delta_ticks60);
    assert(browser.entries()[1].personal_best_delta_text == "--");

    auto incompatible_scope = run(1400, "course:03");
    incompatible_scope.provenance.build_compat_id = "other-build";
    write_record(
        root / "run-0000000000000000-0007.urrun", incompatible_scope);

    CompletedRunRecordsBrowser records_browser;
    const RunRecordsScope records_scope{
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "race-1p",
    };
    assert(records_browser.refresh(root.string(), records_scope));
    assert(records_browser.view() == CompletedRunRecordsView::Courses);
    assert(records_browser.index().total_completed_runs == 5);
    assert(records_browser.index().courses.size() == 2);
    assert(records_browser.artifact_health().total_artifacts == 7);
    assert(records_browser.artifact_health().loaded_artifacts == 6);
    assert(records_browser.artifact_health().corrupt_artifacts == 1);
    assert(records_browser.unavailable_artifact_count() == 2);
    assert(records_browser.selected_course());
    assert(records_browser.selected_course()->course_id == "course:01");
    assert(records_browser.selected_course()->statistics.completed_runs == 4);
    assert(records_browser.selected_course()->statistics.personal_best_text ==
           "0:28.33/60");

    assert(records_browser.move(1));
    assert(records_browser.selected_course()->course_id == "course:02");
    assert(records_browser.move(1));
    assert(records_browser.selected_course()->course_id == "course:01");
    assert(records_browser.move(-1));
    assert(records_browser.selected_course()->course_id == "course:02");
    assert(records_browser.move(1));

    assert(records_browser.open_selected_course());
    assert(records_browser.view() == CompletedRunRecordsView::Runs);
    assert(records_browser.selected_run());
    assert(records_browser.selected_run()->is_previous);
    const auto selected_date = completed_run_browser_date_text(
        records_browser.selected_run()->path);
    assert(selected_date.size() == 10);
    assert(selected_date != "--");
    assert(records_browser.selected_run()->personal_best_delta_text ==
           "+0:00.37/60");
    assert(records_browser.selected_run_record());
    assert(records_browser.selected_run_record()->elapsed_ticks60 == 1750);
    const auto run_summary = records_browser.selected_run_summary();
    assert(run_summary);
    assert(run_summary->finish.clock_text == "0:29.10/60");
    assert(run_summary->finish.target_text == "0:28.33/60");
    assert(run_summary->finish.comparison_text == "+0:00.37/60");
    assert(run_summary->splits.size() == 2);
    assert(run_summary->splits[0].delta_text == "+0:00.10/60");
    assert(records_browser.previous_run_record());
    assert(records_browser.previous_run_record()->elapsed_ticks60 == 1750);
    const auto previous_delta = records_browser.selected_run_previous_delta();
    assert(previous_delta);
    assert(previous_delta->target_text == "0:29.10/60");
    assert(previous_delta->delta_text == "+0:00.00/60");

    assert(records_browser.open_selected_run_detail());
    assert(records_browser.view() == CompletedRunRecordsView::Detail);
    assert(records_browser.detail_target_kind() ==
           RunDataTargetKind::PersonalBest);
    const auto pb_detail =
        records_browser.selected_run_target_summary(
            RunDataTargetKind::PersonalBest);
    assert(pb_detail);
    assert(pb_detail->finish.target_label == "PB");
    assert(pb_detail->splits[0].delta_text == "+0:00.10/60");
    assert(records_browser.adjust_detail_target(1));
    assert(records_browser.detail_target_kind() == RunDataTargetKind::Previous);
    assert(records_browser.adjust_detail_target(1));
    assert(records_browser.detail_target_kind() == RunDataTargetKind::Previous);
    const auto previous_detail =
        records_browser.selected_run_target_summary(
            RunDataTargetKind::Previous);
    assert(previous_detail);
    assert(previous_detail->finish.target_label == "PREVIOUS");
    assert(previous_detail->finish.comparison_text == "+0:00.00/60");
    assert(previous_detail->splits[0].delta_text == "+0:00.00/60");
    assert(records_browser.adjust_detail_target(-1));
    assert(records_browser.detail_target_kind() ==
           RunDataTargetKind::PersonalBest);
    assert(records_browser.move(1));
    assert(records_browser.selected_run()->personal_best_delta_text ==
           "+0:00.37/60");
    assert(records_browser.back_to_runs());
    assert(records_browser.view() == CompletedRunRecordsView::Runs);

    const auto first_run_path = records_browser.selected_run()->path;
    assert(records_browser.move(1));
    assert(records_browser.selected_run());
    assert(records_browser.selected_run()->path != first_run_path);
    const auto historical_previous_delta =
        records_browser.selected_run_previous_delta();
    assert(historical_previous_delta);
    assert(historical_previous_delta->target_text == "0:29.10/60");
    assert(historical_previous_delta->delta_text == "+0:00.50/60");
    assert(records_browser.back_to_courses());
    assert(records_browser.view() == CompletedRunRecordsView::Courses);
    assert(!records_browser.selected_run_index());

    const auto scroll_root = root / "scroll";
    std::filesystem::create_directories(scroll_root);
    auto scroll_pb = run(1680, "course:01", 1600);
    scroll_pb.splits = {
        {"checkpoint-1", 1600},
        {"checkpoint-2", 1620},
        {"checkpoint-3", 1640},
        {"checkpoint-4", 1660},
        {"finish", 1680},
    };
    auto scroll_previous = run(1740, "course:01", 1610);
    scroll_previous.splits = {
        {"checkpoint-1", 1610},
        {"checkpoint-2", 1630},
        {"checkpoint-3", 1650},
        {"checkpoint-4", 1670},
        {"finish", 1740},
    };
    write_record(scroll_root / "run-0000000000000001-0001.urrun", scroll_pb);
    write_record(
        scroll_root / "run-0000000000000002-0002.urrun",
        scroll_previous);

    CompletedRunRecordsBrowser scroll_browser;
    assert(scroll_browser.refresh(scroll_root.string(), records_scope));
    assert(scroll_browser.open_selected_course());
    assert(scroll_browser.open_selected_run_detail());
    assert(scroll_browser.detail_split_offset() == 0);
    assert(scroll_browser.adjust_detail_split_offset(1));
    assert(scroll_browser.detail_split_offset() == 1);
    assert(!scroll_browser.adjust_detail_split_offset(1));
    assert(scroll_browser.adjust_detail_split_offset(-1));
    assert(scroll_browser.detail_split_offset() == 0);
    assert(!scroll_browser.adjust_detail_split_offset(-1));
    assert(scroll_browser.adjust_detail_split_offset(1));
    assert(scroll_browser.adjust_detail_target(1));
    assert(scroll_browser.detail_target_kind() == RunDataTargetKind::Previous);
    assert(scroll_browser.detail_split_offset() == 0);

    assert(std::string(completed_run_browser_status_name(
               CompletedRunBrowserEntryStatus::Corrupt)) == "CORRUPT");
    assert(std::string(completed_run_browser_status_name(
               CompletedRunBrowserEntryStatus::Incompatible)) == "INCOMPATIBLE");

    return 0;
}
