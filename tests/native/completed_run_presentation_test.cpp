#include "completed_run_presentation.hpp"

#include <cassert>
#include <cstdint>
#include <limits>
#include <string>

using namespace ur::product;

namespace {

CompletedRunRecord target() {
    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-1p",
    };
    record.elapsed_ticks60 = 1713;
    record.frame_count = 3;
    record.splits = {
        {"checkpoint-1", 850},
        {"finish", 1713},
    };
    record.inputs = {
        {0, 3, 0x100, 0},
    };
    return record;
}

}  // namespace

int main() {
    assert(format_run_ticks60(0) == "0:00.00/60");
    assert(format_run_ticks60(59) == "0:00.59/60");
    assert(format_run_ticks60(60) == "0:01.00/60");
    assert(format_run_ticks60(1713) == "0:28.33/60");
    assert(format_run_ticks60(3661) == "1:01.01/60");

    assert(format_run_delta_ticks60(-6) == "-0:00.06/60");
    assert(format_run_delta_ticks60(0) == "+0:00.00/60");
    assert(format_run_delta_ticks60(12) == "+0:00.12/60");

    const auto record = target();
    const auto pb = present_run_target(record, RunDataTargetKind::PersonalBest);
    assert(pb);
    assert(pb->label == "PB");
    assert(pb->time_text == "0:28.33/60");

    const auto previous = present_run_target(record, RunDataTargetKind::Previous);
    assert(previous && previous->label == "PREVIOUS");

    const auto ahead = present_run_split_delta(record, "checkpoint-1", 844);
    assert(ahead);
    assert(ahead->delta_ticks60 == -6);
    assert(ahead->current_text == "0:14.04/60");
    assert(ahead->target_text == "0:14.10/60");
    assert(ahead->delta_text == "-0:00.06/60");

    const auto behind = present_run_finish_delta(record, 1725);
    assert(behind);
    assert(behind->delta_ticks60 == 12);
    assert(behind->delta_text == "+0:00.12/60");

    const auto live_panel = present_run_timing_panel(
        844, &record, RunTimingPresentationPoint::Live);
    assert(live_panel.clock_label == "TIME");
    assert(live_panel.clock_text == "0:14.04/60");
    assert(live_panel.target_available);
    assert(live_panel.target_text == "0:28.33/60");
    assert(!live_panel.comparison_available);
    assert(live_panel.comparison_text == "--");

    const auto split_panel = present_run_timing_panel(
        844,
        &record,
        RunTimingPresentationPoint::Split,
        "checkpoint-1");
    assert(split_panel.comparison_label == "SPLIT");
    assert(split_panel.comparison_available);
    assert(split_panel.comparison_text == "-0:00.06/60");

    const auto finish_panel = present_run_timing_panel(
        1725, &record, RunTimingPresentationPoint::Finish);
    assert(finish_panel.clock_label == "FINISH");
    assert(finish_panel.comparison_label == "DELTA");
    assert(finish_panel.comparison_available);
    assert(finish_panel.comparison_text == "+0:00.12/60");

    auto current = record;
    current.elapsed_ticks60 = 1725;
    current.splits = {
        {"checkpoint-1", 844},
        {"finish", 1725},
    };
    const auto split_table = present_run_split_table(
        current, record, RunDataTargetKind::PersonalBest);
    assert(split_table);
    assert(split_table->target_label == "PB");
    assert(split_table->rows.size() == 2);
    assert(split_table->rows[0].id == "checkpoint-1");
    assert(split_table->rows[0].current_text == "0:14.04/60");
    assert(split_table->rows[0].target_text == "0:14.10/60");
    assert(split_table->rows[0].delta_text == "-0:00.06/60");
    assert(split_table->rows[1].id == "finish");
    assert(split_table->rows[1].delta_text == "+0:00.12/60");

    auto incompatible_summary_target = previous_target;
    incompatible_summary_target.provenance.course_id = "course:02";
    assert(!present_run_result_summary_against(
        current,
        incompatible_summary_target,
        RunDataTargetKind::Previous));

    auto incompatible_table_target = record;
    incompatible_table_target.provenance.course_id = "course:02";
    assert(!present_run_split_table(
        current,
        incompatible_table_target,
        RunDataTargetKind::PersonalBest));

    auto mismatched_split_target = record;
    mismatched_split_target.splits[0].id = "other";
    assert(!present_run_split_table(
        current,
        mismatched_split_target,
        RunDataTargetKind::PersonalBest));

    auto previous_target = record;
    previous_target.elapsed_ticks60 = 1750;
    previous_target.splits = {
        {"checkpoint-1", 850},
        {"finish", 1750},
    };
    const auto previous_summary = present_run_result_summary_against(
        current, previous_target, RunDataTargetKind::Previous);
    assert(previous_summary);
    assert(previous_summary->finish.target_label == "PREVIOUS");
    assert(previous_summary->finish.target_text == "0:29.10/60");
    assert(previous_summary->finish.comparison_text == "-0:00.25/60");
    assert(previous_summary->splits.size() == 2);
    assert(previous_summary->splits[0].current_text == "0:14.04/60");
    assert(previous_summary->splits[0].target_text == "0:14.10/60");
    assert(previous_summary->splits[0].delta_text == "-0:00.06/60");
    assert(previous_summary->splits[1].target_text == "0:29.10/60");
    assert(previous_summary->splits[1].delta_text == "-0:00.25/60");

    const auto result_summary =
        present_run_result_summary(current, &record);
    assert(result_summary);
    assert(result_summary->finish.clock_label == "FINISH");
    assert(result_summary->finish.clock_text == "0:28.45/60");
    assert(result_summary->finish.target_text == "0:28.33/60");
    assert(result_summary->finish.comparison_text == "+0:00.12/60");
    assert(result_summary->splits.size() == 2);
    assert(result_summary->splits[0].delta_text == "-0:00.06/60");
    assert(result_summary->splits[1].delta_text == "+0:00.12/60");

    const auto result_no_pb =
        present_run_result_summary(current, nullptr);
    assert(result_no_pb);
    assert(result_no_pb->finish.clock_text == "0:28.45/60");
    assert(!result_no_pb->finish.target_available);
    assert(result_no_pb->splits.empty());

    const auto no_pb_panel = present_run_timing_panel(
        844, nullptr, RunTimingPresentationPoint::Live);
    assert(!no_pb_panel.target_available);
    assert(no_pb_panel.target_text == "--");
    assert(!no_pb_panel.comparison_available);

    assert(should_present_run_timing(true, true, true));
    assert(!should_present_run_timing(false, true, true));
    assert(!should_present_run_timing(true, false, true));
    assert(!should_present_run_timing(true, true, false));

    assert(!present_run_split_delta(record, "missing", 100));

    auto malformed = record;
    malformed.inputs[0].duration = 0;
    assert(!present_run_target(malformed, RunDataTargetKind::PersonalBest));
    assert(!present_run_finish_delta(malformed, 1));
    assert(!present_run_result_summary(malformed, &record));
    const auto malformed_panel = present_run_timing_panel(
        1, &malformed, RunTimingPresentationPoint::Finish);
    assert(!malformed_panel.target_available);
    assert(!malformed_panel.comparison_available);

    assert(
        format_run_delta_ticks60(std::numeric_limits<std::int64_t>::min()) ==
        "-2562047788015215:30.08/60");

    return 0;
}
