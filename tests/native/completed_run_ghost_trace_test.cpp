#include "completed_run_ghost_trace.hpp"
#include "completed_run_store.hpp"
#include "ghost_trace_equivalence.hpp"

#include <cassert>
#include <string>
#include <filesystem>
#include <fstream>

using namespace ur::product;

namespace {

CompletedRunRecord run_record() {
    CompletedRunRecord record;
    record.provenance = {
        "uniracers-usa",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        "native-sim-v1",
        "course:01",
        "race-1p",
    };
    record.elapsed_ticks60 = 120;
    record.frame_count = 3;
    record.splits = {{"finish", 120}};
    record.inputs = {{0, 3, 0x100, 0}};
    return record;
}

}  // namespace

int main(int argc, char** argv) {
    assert(argc == 2 ||
           (argc == 3 && std::string(argv[2]) == "--verify-persisted-targets"));
    const std::filesystem::path run_path = argv[1];

    if (argc == 3) {
        // A separately launched process can access only serialized artifacts.
        // The writer's in-memory records and selected target state are gone.
        const auto record = run_record();
        const auto directory = run_path.parent_path() / "stored-ghost-targets";
        const RunPlaybackTarget target{
            record.provenance.game_id,
            record.provenance.rom_sha256,
            record.provenance.build_compat_id,
            record.provenance.course_id,
            record.provenance.mode,
        };
        const auto stored = load_compatible_run_records(directory.string(), target);
        assert(stored.size() == 2); // Newer damaged .urrun is not admitted.
        CompletedRunGhostState ghosts;
        ghosts.bind(stored, target);
        const auto* previous = ghosts.stored(CompletedRunGhostKind::Previous);
        const auto* pb = ghosts.stored(CompletedRunGhostKind::PersonalBest);
        assert(previous && pb);
        assert(std::filesystem::path(previous->path).filename() ==
               "run-0000000000000002-0001.urrun");
        assert(std::filesystem::path(pb->path).filename() ==
               "run-0000000000000001-0001.urrun");
        const auto pb_trace = load_selected_completed_run_ghost_trace(
            ghosts, CompletedRunGhostKind::PersonalBest);
        assert(pb_trace.loaded());
        assert(pb_trace.trace->samples[0].world_x == 1200);
        // The Previous sibling was replaced by PB's otherwise-valid data.
        // Cross-process lookup must still refuse the wrong run checksum.
        const auto previous_trace = load_selected_completed_run_ghost_trace(
            ghosts, CompletedRunGhostKind::Previous);
        assert(previous_trace.status ==
               CompletedRunGhostTraceLoadStatus::Incompatible);
        return 0;
    }

    const std::filesystem::path trace_path =
        std::filesystem::path(run_path.string() + ".urghost");
    const auto record = run_record();
    const std::string binding =
        completed_run_record_artifact_checksum(record);
    assert(binding.size() == 16);

    CompletedRunGhostTraceCapture capture;
    assert(!capture.observe({0, 1, 1, 1, 1, 1, 0x40, {}}));
    assert(capture.begin_attempt());
    assert(capture.capturing());
    assert(capture.observe({0, 1088, 859, 0x0007, 0x0541, 1, 0x66, {0x0541, 0x0540, 0x0D0D, 0, 0, 0, 1, 0}}));
    assert(capture.observe({1, 1100, 850, 0x0009, 0x0540, 1, 0x66, {0x0540, 0x0541, 0x0D2C, 0, 0, 0, 1, 0}}));
    assert(!capture.observe({1, 9999, 9999, 0, 0, 0, 0, {}}));
    assert(capture.observe({2, 1115, 840, 0x000B, 0x057D, 0, 0x26, {0x057D, 0x0543, 0x0D48, 0, 0, 0, 1, 0}}));
    assert(capture.sample_count() == 3);

    const auto completed_trace = capture.complete(record);
    assert(completed_trace);
    assert(!capture.capturing());
    assert(capture.sample_count() == 0);

    CompletedRunGhostTrace trace = *completed_trace;
    assert(trace.run_artifact_checksum == binding);
    assert(validate_completed_run_ghost_trace(trace, &record));
    const std::string encoded = encode_completed_run_ghost_trace(trace);
    assert(!encoded.empty());

    // Replay proof requires the complete recorded frame window. An optional
    // sidecar remains readable under its existing schema if truncated, but it
    // cannot attest deterministic trajectory equivalence.
    assert(ur::test::ghost_trace_covers_completed_run(trace, record));
    auto truncated_trace = trace;
    truncated_trace.samples.pop_back();
    assert(!ur::test::ghost_trace_covers_completed_run(
        truncated_trace, record));
    auto longer_record = record;
    ++longer_record.frame_count;
    assert(!ur::test::ghost_trace_covers_completed_run(
        trace, longer_record));

    const auto decoded = decode_completed_run_ghost_trace(encoded, &record);
    assert(decoded.loaded());
    assert(decoded.trace->samples.size() == 3);
    assert(decoded.trace->samples[1].world_x == 1100);
    assert(decoded.trace->samples[2].semantic_frame_id == 0x057D);
    assert(decoded.trace->samples[0].sprite_attr == 0x66);
    assert(decoded.trace->samples[2].sprite_attr == 0x26);
    assert(decoded.trace->samples[0].composition.p1_primary == 0x0541);
    assert(decoded.trace->samples[0].composition.p2_primary == 0x0540);
    assert(decoded.trace->samples[0].composition.p1_companion == 0x0D0D);
    assert(decoded.trace->samples[2].composition.p1_companion == 0x0D48);
    assert(completed_run_ghost_trace_sample_at(*decoded.trace, 0));
    assert(completed_run_ghost_trace_sample_at(*decoded.trace, 1)->world_x == 1100);
    assert(completed_run_ghost_trace_sample_at(*decoded.trace, 2)->semantic_frame_id == 0x057D);
    assert(completed_run_ghost_trace_sample_at(*decoded.trace, 3) == nullptr);

    auto other_record = record;
    other_record.elapsed_ticks60 = 121;
    const auto mismatched =
        decode_completed_run_ghost_trace(encoded, &other_record);
    assert(mismatched.status ==
           CompletedRunGhostTraceLoadStatus::Incompatible);

    std::string corrupt = encoded;
    const auto sample_pos = corrupt.find("1100");
    assert(sample_pos != std::string::npos);
    corrupt[sample_pos] = '9';
    const auto damaged = decode_completed_run_ghost_trace(corrupt, &record);
    assert(damaged.status == CompletedRunGhostTraceLoadStatus::Corrupt);

    std::string detail;
    assert(save_completed_run_ghost_trace_file(
        trace_path.string(), trace, &detail));
    const auto reloaded =
        load_completed_run_ghost_trace_file(trace_path.string(), &record);
    assert(reloaded.loaded());
    assert(reloaded.trace->samples.size() == trace.samples.size());

    // An existing checksum-bound sidecar may be repaired/replaced atomically.
    // Readers must see the old complete trace or the new complete trace,
    // never a truncated intermediate file at the public .urghost path.
    auto replacement_trace = trace;
    replacement_trace.samples[0].world_x = 1203;
    assert(save_completed_run_ghost_trace_file(
        trace_path.string(), replacement_trace, &detail));
    const auto replaced = load_completed_run_ghost_trace_file(
        trace_path.string(), &record);
    assert(replaced.loaded());
    assert(replaced.trace->samples[0].world_x == 1203);
    assert(save_completed_run_ghost_trace_file(
        trace_path.string(), trace, &detail));
    assert(load_completed_run_ghost_trace_file(
        trace_path.string(), &record).trace->samples[0].world_x == 1088);

    // A non-file destination must never be displaced by publication.
    const auto blocked_trace_path =
        run_path.parent_path() / "blocked.urghost";
    assert(std::filesystem::create_directory(blocked_trace_path));
    detail.clear();
    assert(!save_completed_run_ghost_trace_file(
        blocked_trace_path.string(), trace, &detail));
    assert(detail == "ghost trace destination is not a regular file");
    assert(std::filesystem::is_directory(blocked_trace_path));
    assert(std::filesystem::remove(blocked_trace_path));

    // No successful or failed save may leak staging directories. An
    // interrupted writer leaves only an ignored hidden path, never a
    // public partially-written .urghost file.
    for (const auto& entry :
         std::filesystem::directory_iterator(run_path.parent_path())) {
        assert(entry.path().filename().string().find(
            ".pending-urghost-") != 0);
    }

#if defined(__linux__)
    // The stream may buffer a successful write and fail only on close.
    detail.clear();
    assert(!save_completed_run_ghost_trace_file("/dev/full", trace, &detail));
    assert(detail == "ghost trace destination is not a regular file" ||
           detail == "cannot reserve ghost trace staging directory");
#endif

    const auto missing =
        load_completed_run_ghost_trace_file(
            (trace_path.string() + ".missing"), &record);
    assert(missing.status == CompletedRunGhostTraceLoadStatus::IoError);

    CompletedRunGhostState selected_state;
    selected_state.bind(
        {{run_path.string(), record}},
        RunPlaybackTarget{
            record.provenance.game_id,
            record.provenance.rom_sha256,
            record.provenance.build_compat_id,
            record.provenance.course_id,
            record.provenance.mode,
        });
    const auto selected_trace =
        load_selected_completed_run_ghost_trace(
            selected_state, CompletedRunGhostKind::Previous);
    assert(selected_trace.loaded());
    assert(selected_trace.trace->samples.size() == trace.samples.size());

    // Previous and PB must resolve through the exact selected artifact path,
    // not merely whichever compatible sidecar happens to exist.
    auto pb_record = record;
    pb_record.elapsed_ticks60 = 100;
    pb_record.splits = {{"finish", 100}};
    CompletedRunGhostTrace pb_trace = trace;
    pb_trace.run_artifact_checksum =
        completed_run_record_artifact_checksum(pb_record);
    pb_trace.samples[0].world_x = 1200;
    const std::filesystem::path pb_run_path =
        std::filesystem::path(run_path.string() + ".pb.urrun");
    const std::filesystem::path pb_trace_path =
        std::filesystem::path(pb_run_path.string() + ".urghost");
    assert(save_completed_run_ghost_trace_file(
        pb_trace_path.string(), pb_trace, &detail));

    CompletedRunGhostState two_targets;
    two_targets.bind(
        {
            {pb_run_path.string(), pb_record},
            {run_path.string(), record},
        },
        RunPlaybackTarget{
            record.provenance.game_id,
            record.provenance.rom_sha256,
            record.provenance.build_compat_id,
            record.provenance.course_id,
            record.provenance.mode,
        });
    const auto previous_trace = load_selected_completed_run_ghost_trace(
        two_targets, CompletedRunGhostKind::Previous);
    const auto personal_best_trace = load_selected_completed_run_ghost_trace(
        two_targets, CompletedRunGhostKind::PersonalBest);
    assert(previous_trace.loaded());
    assert(personal_best_trace.loaded());
    assert(previous_trace.trace->samples[0].world_x == 1088);
    assert(personal_best_trace.trace->samples[0].world_x == 1200);

    // Rebuild the Previous/PB selectors from *persisted* .urrun files, not
    // caller-injected model records. Verify that each target opens its own
    // checksum-bound sidecar after a filesystem round trip.
    const auto stored_directory = run_path.parent_path() / "stored-ghost-targets";
    std::filesystem::create_directories(stored_directory);
    const auto saved_pb_path =
        stored_directory / "run-0000000000000001-0001.urrun";
    const auto saved_previous_path =
        stored_directory / "run-0000000000000002-0001.urrun";
    assert(save_completed_run_record_file(saved_pb_path.string(), pb_record));
    assert(save_completed_run_record_file(saved_previous_path.string(), record));
    const auto saved_pb_trace_path = saved_pb_path.string() + ".urghost";
    const auto saved_previous_trace_path =
        saved_previous_path.string() + ".urghost";
    assert(save_completed_run_ghost_trace_file(
        saved_pb_trace_path, pb_trace));
    assert(save_completed_run_ghost_trace_file(
        saved_previous_trace_path, trace));

    const RunPlaybackTarget stored_target{
        record.provenance.game_id,
        record.provenance.rom_sha256,
        record.provenance.build_compat_id,
        record.provenance.course_id,
        record.provenance.mode,
    };
    auto loaded_runs = load_compatible_run_records(
        stored_directory.string(), stored_target);
    assert(loaded_runs.size() == 2);
    CompletedRunGhostState disk_targets;
    disk_targets.bind(loaded_runs, stored_target);
    assert(disk_targets.stored(CompletedRunGhostKind::PersonalBest)->path ==
           saved_pb_path.string());
    assert(disk_targets.stored(CompletedRunGhostKind::Previous)->path ==
           saved_previous_path.string());
    assert(load_selected_completed_run_ghost_trace(
        disk_targets, CompletedRunGhostKind::PersonalBest)
               .trace->samples[0].world_x == 1200);
    assert(load_selected_completed_run_ghost_trace(
        disk_targets, CompletedRunGhostKind::Previous)
               .trace->samples[0].world_x == 1088);

    // A missing Previous sidecar must never silently show the PB instead.
    assert(std::filesystem::remove(saved_previous_trace_path));
    assert(load_selected_completed_run_ghost_trace(
        disk_targets, CompletedRunGhostKind::Previous).status ==
           CompletedRunGhostTraceLoadStatus::IoError);
    assert(load_selected_completed_run_ghost_trace(
        disk_targets, CompletedRunGhostKind::PersonalBest).loaded());

    // Likewise, a mismatched sibling trace must not borrow another run's
    // world/pose samples just because both runs share course provenance.
    std::filesystem::copy_file(
        saved_pb_trace_path, saved_previous_trace_path,
        std::filesystem::copy_options::overwrite_existing);
    assert(load_selected_completed_run_ghost_trace(
        disk_targets, CompletedRunGhostKind::Previous).status ==
           CompletedRunGhostTraceLoadStatus::Incompatible);

    // A newer checksum-damaged .urrun must not usurp Previous or PB.
    auto damaged_run = encode_completed_run_record(pb_record);
    const auto damaged_at = damaged_run.rfind("checksum ");
    assert(damaged_at != std::string::npos);
    damaged_run[damaged_at + 9] =
        damaged_run[damaged_at + 9] == '0' ? '1' : '0';
    {
        std::ofstream corrupt_file(
            stored_directory / "run-0000000000000003-0001.urrun",
            std::ios::binary);
        corrupt_file << damaged_run;
        assert(static_cast<bool>(corrupt_file));
    }
    loaded_runs = load_compatible_run_records(
        stored_directory.string(), stored_target);
    assert(loaded_runs.size() == 2);
    disk_targets.bind(loaded_runs, stored_target);
    assert(disk_targets.stored(CompletedRunGhostKind::Previous)->path ==
           saved_previous_path.string());
    assert(disk_targets.stored(CompletedRunGhostKind::PersonalBest)->path ==
           saved_pb_path.string());

    CompletedRunGhostState empty_state;
    const auto no_selection =
        load_selected_completed_run_ghost_trace(
            empty_state, CompletedRunGhostKind::Previous);
    assert(no_selection.status == CompletedRunGhostTraceLoadStatus::Incompatible);

    CompletedRunGhostTraceCapture aborted;
    assert(aborted.begin_attempt());
    assert(aborted.observe({0, 1, 2, 3, 4, 1, 0x40, {}}));
    aborted.abort_attempt();
    assert(!aborted.capturing());
    assert(aborted.sample_count() == 0);
    assert(!aborted.complete(record));

    CompletedRunGhostTraceCapture too_long;
    assert(too_long.begin_attempt());
    assert(too_long.observe({record.frame_count, 1, 2, 3, 4, 1, 0x40, {}}));
    assert(!too_long.complete(record));

    auto unordered = trace;
    unordered.samples[2].race_frame = 1;
    assert(!validate_completed_run_ghost_trace(unordered, &record));

    auto out_of_range = trace;
    out_of_range.samples.back().race_frame = record.frame_count;
    assert(!validate_completed_run_ghost_trace(out_of_range, &record));

    // World trajectory is replay-authoritative; stored presentation pose is
    // historically exact but can include cosmetic state not in the input file.
    std::string mismatch;
    std::size_t common = 0;
    ur::test::GhostTraceReplayComparison comparison;
    assert(ur::test::equivalent_ghost_world_samples(
        trace, *decoded.trace, &mismatch, &common, &comparison));
    assert(common == 3);
    assert(comparison.p1_pose_drift_frames == 0);
    assert(comparison.p2_context_drift_frames == 0);

    auto terminal_short = trace;
    terminal_short.samples.pop_back();
    terminal_short.samples[1].world_x = 65000;
    assert(ur::test::equivalent_ghost_world_samples(
        trace, terminal_short, &mismatch, &common, &comparison));
    assert(common == 2);
    assert(comparison.terminal_observation_drift_frames == 1);
    // Replay cannot pass by comparing only surviving samples when a ghost
    // trace skips frames. The terminal allowance is exactly one guest frame.
    auto sparse_tail = trace;
    sparse_tail.samples.back().race_frame = 100;
    assert(!ur::test::equivalent_ghost_world_samples(
        sparse_tail, terminal_short, &mismatch, &common));
    assert(mismatch.find("noncontiguous") != std::string::npos);
    assert(!ur::test::equivalent_ghost_world_samples(
        sparse_tail, sparse_tail, &mismatch, &common));
    assert(mismatch.find("noncontiguous") != std::string::npos);
    auto late_start = trace;
    for (auto& sample : late_start.samples) ++sample.race_frame;
    assert(!ur::test::equivalent_ghost_world_samples(
        late_start, late_start, &mismatch, &common));
    assert(mismatch.find("noncontiguous") != std::string::npos);

    auto two_short = terminal_short;
    two_short.samples.pop_back();
    assert(!ur::test::equivalent_ghost_world_samples(
        trace, two_short, &mismatch, &common));
    assert(mismatch.find("terminal") != std::string::npos);
    assert(!ur::test::equivalent_ghost_world_samples(
        trace, CompletedRunGhostTrace{}, &mismatch, &common));
    assert(mismatch.find("missing") != std::string::npos);

    auto shifted = trace;
    shifted.samples[1].race_frame = 3;
    assert(!ur::test::equivalent_ghost_world_samples(
        trace, shifted, &mismatch, &common));
    assert(mismatch.find("noncontiguous") != std::string::npos);
    auto divergent = trace;
    divergent.samples[1].world_x++;
    assert(!ur::test::equivalent_ghost_world_samples(
        trace, divergent, &mismatch, &common));
    assert(mismatch.find("world_x") != std::string::npos);
    divergent = trace;
    divergent.samples[1].world_y++;
    assert(!ur::test::equivalent_ghost_world_samples(
        trace, divergent, &mismatch, &common));
    assert(mismatch.find("world_y") != std::string::npos);
    divergent = trace;
    divergent.samples[1].pitch_angle++;
    assert(!ur::test::equivalent_ghost_world_samples(
        trace, divergent, &mismatch, &common));
    assert(mismatch.find("pitch_angle") != std::string::npos);
    divergent = trace;
    divergent.samples[1].semantic_frame_id++;
    divergent.samples[1].sprite_attr++;
    divergent.samples[1].composition.p1_companion++;
    divergent.samples[2].composition.p2_primary++;
    assert(ur::test::equivalent_ghost_world_samples(
        trace, divergent, &mismatch, &common, &comparison));
    assert(comparison.p1_pose_drift_frames == 1);
    assert(comparison.first_p1_pose_drift_frame == 1);
    assert(comparison.p2_context_drift_frames == 1);
    assert(comparison.first_p2_context_drift_frame == 2);

    // A terminal lifecycle difference must not excuse another frame's
    // physical divergence.
    divergent = terminal_short;
    divergent.samples[0].world_y++;
    assert(!ur::test::equivalent_ghost_world_samples(
        trace, divergent, &mismatch, &common));
    assert(mismatch.find("world_y") != std::string::npos);

    return 0;
}
