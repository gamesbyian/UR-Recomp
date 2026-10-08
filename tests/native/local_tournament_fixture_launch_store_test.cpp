#include "local_tournament_fixture_launch_store.hpp"
#include "local_tournament_launch_path_lock.hpp"

#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <thread>

using namespace ur::product;
namespace fs = std::filesystem;
using Status = LocalTournamentLaunchFileStatus;

static void require(bool ok, const char* message) {
    if (!ok) {
        std::fprintf(stderr, "FAIL: %s\n", message);
        std::exit(1);
    }
}

static std::string bytes_of(const fs::path& path) {
    std::ifstream stream(path, std::ios::binary);
    return {std::istreambuf_iterator<char>(stream),
            std::istreambuf_iterator<char>()};
}

static void put_bytes(const fs::path& path, const std::string& text) {
    std::ofstream stream(path, std::ios::binary | std::ios::trunc);
    stream.write(text.data(), static_cast<std::streamsize>(text.size()));
    require(bool(stream), "raw fixture write");
}

int main() {
    const auto model = make_local_round_robin(
        {"alice", "BOB", "carol"},
        {"course:01", "course:04"});
    require(bool(model), "valid 3-player tournament fixture model");
    const std::string instance = "0123456789abcdef0123456789abcdef";
    const std::string other = "abcdef0123456789abcdef0123456789";
    const std::string attempt = "11111111111111111111111111111111";
    LocalTournamentLaunchState issued;
    require(local_tournament_arm_fixture(
            issued, *model, instance, attempt, 0) ==
            LocalTournamentLaunchStatus::Armed,
            "explicit live launch issued");
    const auto pending = *issued.pending;

    const auto unique = std::chrono::steady_clock::now()
        .time_since_epoch().count();
    const fs::path root = fs::temp_directory_path() /
        ("ur-tournament-launch-store-" + std::to_string(unique));
    require(fs::create_directory(root), "temporary store root created");
    const fs::path path = root / "pending.urlaunch";
    const std::string filename = path.string();

    require(load_local_tournament_launch_file(
                filename, *model, instance).status == Status::Missing,
            "nonexistent pending checkpoint is Missing, not a result");
    require(save_local_tournament_launch_file("", pending) == Status::Rejected,
            "empty path cannot be saved");
    require(save_local_tournament_launch_file(
                (root / "absent" / "pending.urlaunch").string(), pending) ==
            Status::IoError,
            "failed parent directory does not silently create data root");
    require(save_local_tournament_launch_file(filename, pending) ==
            Status::Saved,
            "canonical checkpoint saved via same-directory temporary file");
    require(!fs::exists(filename + ".tmp"),
            "successful atomic publication retires temporary file");
    const std::string original_bytes =
        encode_local_tournament_pending_fixture(pending);
    require(bytes_of(path) == original_bytes,
            "persisted checkpoint matches canonical bytes exactly");

    const auto fresh = load_local_tournament_launch_file(
        filename, *model, instance);
    require(fresh.loaded() && fresh.pending->attempt_id == attempt &&
            fresh.pending->immutable_schedule_digest ==
                local_tournament_immutable_schedule_digest(*model),
            "fresh-process reload rebinds exact active session");
    require(load_local_tournament_launch_file(
                filename, *model, other).status == Status::Rejected,
            "wrong tournament instance cannot inherit launch");
    auto changed = *model;
    changed.entrants[2] = "changed-unrelated-participant";
    require(load_local_tournament_launch_file(
                filename, changed, instance).status == Status::Rejected,
            "unrelated changed roster invalidates restored checkpoint");
    changed = *model;
    changed.fixtures[1].course_id = "course:39";
    require(load_local_tournament_launch_file(
                filename, changed, instance).status == Status::Rejected,
            "other fixture drift invalidates restored checkpoint");
    changed = *model;
    changed.results[0] = LocalTournamentRecordedResult{
        "0011223344556677",
        ur::title::OrdinaryTwoPlayerRaceOutcome::Draw, false};
    require(load_local_tournament_launch_file(
                filename, changed, instance).status == Status::Rejected,
            "already-completed selected fixture cannot restore");

    auto corrupt = pending;
    corrupt.tournament_id = "NOT-A-CANONICAL-TOURNAMENT-ID";
    require(save_local_tournament_launch_file(filename, corrupt) ==
            Status::Rejected,
            "invalid pending state cannot overwrite valid checkpoint");
    require(bytes_of(path) == original_bytes,
            "rejected write preserves previously committed bytes");

    put_bytes(path, original_bytes.substr(0, original_bytes.size() - 1u));
    require(load_local_tournament_launch_file(
                filename, *model, instance).status == Status::Rejected,
            "truncated checkpoint rejected");
    put_bytes(path, std::string(kLocalTournamentLaunchMaxBytes + 1u, 'x'));
    require(load_local_tournament_launch_file(
                filename, *model, instance).status == Status::Rejected,
            "oversized file is bounded before allocating");
    put_bytes(path, "");
    require(load_local_tournament_launch_file(
                filename, *model, instance).status == Status::Rejected,
            "empty existing file is Rejected, not Missing");

    require(save_local_tournament_launch_file(filename, pending) ==
            Status::Saved,
            "valid checkpoint can replace corrupted prior payload");
    require(bytes_of(path) == original_bytes,
            "repair atomically republishes canonical bytes");
    auto stale_attempt = pending;
    stale_attempt.attempt_id = "22222222222222222222222222222222";
    require(retire_local_tournament_launch_file(
                filename, stale_attempt) == Status::Rejected,
            "late cancellation with other attempt ID cannot delete checkpoint");
    auto stale_tournament = pending;
    stale_tournament.tournament_id =
        "abcdef0123456789abcdef0123456789";
    require(retire_local_tournament_launch_file(
                filename, stale_tournament) == Status::Rejected,
            "wrong tournament instance cannot delete active checkpoint");
    require(bytes_of(path) == original_bytes,
            "stale retirement leaves latest persisted attempt byte-identical");

    // The fixture may have completed after the capture/receipt transaction.
    // Such a checkpoint is no longer RESTORABLE, but its exact original
    // attempt must still be RETIRABLE without rewriting stored results.
    auto finished = *model;
    finished.results[0] = LocalTournamentRecordedResult{
        "0011223344556677",
        ur::title::OrdinaryTwoPlayerRaceOutcome::Draw, false};
    require(load_local_tournament_launch_file(
                filename, finished, instance).status == Status::Rejected,
            "completed fixture is not eligible to resume");
    require(retire_local_tournament_launch_file(
                filename, pending) == Status::Saved,
            "post-result commit can retire the exact saved launch");
    require(retire_local_tournament_launch_file(
                filename, pending) == Status::Missing,
            "retirement is idempotent for missing checkpoint");
    require(load_local_tournament_launch_file(
                filename, *model, instance).status == Status::Missing,
            "retired launch cannot reappear as a result");

    // Independent processes/threads sharing this file must not allow an
    // obsolete retire to remove another writer's newer checkpoint. Exercise
    // both operation orders, with an actual interleaved start gate and
    // independent OS file-handle locks.
    for (int round = 0; round < 100; ++round) {
        require(save_local_tournament_launch_file(filename, pending) ==
                    Status::Saved, "concurrency seed publishes old launch");
        std::atomic<int> ready{0};
        std::atomic<bool> go{false};
        Status newer_save = Status::IoError;
        Status stale_retire = Status::IoError;
        std::thread replacement([&] {
            ready.fetch_add(1, std::memory_order_release);
            while (!go.load(std::memory_order_acquire)) std::this_thread::yield();
            newer_save = save_local_tournament_launch_file(
                filename, stale_attempt);
        });
        std::thread retirement([&] {
            ready.fetch_add(1, std::memory_order_release);
            while (!go.load(std::memory_order_acquire)) std::this_thread::yield();
            stale_retire = retire_local_tournament_launch_file(
                filename, pending);
        });
        while (ready.load(std::memory_order_acquire) != 2)
            std::this_thread::yield();
        go.store(true, std::memory_order_release);
        replacement.join();
        retirement.join();
        require(newer_save == Status::Saved,
                "competing new checkpoint always reaches storage");
        require(stale_retire == Status::Saved ||
                    stale_retire == Status::Rejected,
                "old retirement either precedes new save or rejects stale bytes");
        const auto current = load_local_tournament_launch_file(
            filename, *model, instance);
        require(current.loaded() &&
                    current.pending->attempt_id == stale_attempt.attempt_id &&
                    bytes_of(path) ==
                        encode_local_tournament_pending_fixture(stale_attempt),
                "stale retirement never removes or corrupts newer attempt");
    }

    // A separate lock holder must block any writer until the scoped OS
    // handle is destroyed, not until a .lock sentinel is manually removed.
    require(save_local_tournament_launch_file(filename, pending) ==
                Status::Saved, "lock blocking test seeded");
    std::atomic<bool> attempting{false};
    std::atomic<bool> finished_write{false};
    std::thread blocked;
    {
        TournamentLaunchPathLock held(filename);
        require(held.acquired(), "OS process-lock handle acquired");
        blocked = std::thread([&] {
            attempting.store(true, std::memory_order_release);
            const auto result = save_local_tournament_launch_file(
                filename, stale_attempt);
            finished_write.store(result == Status::Saved,
                                 std::memory_order_release);
        });
        while (!attempting.load(std::memory_order_acquire))
            std::this_thread::yield();
        // No time-based 'writer must still be blocked' assertion: thread
        // scheduling can delay entering the OS lock. The concurrent-content
        // assertions above are the actual safety discriminator.
    }
    blocked.join();
    require(finished_write.load(std::memory_order_acquire),
            "after releasing scoped lock another writer proceeds");
    require(bytes_of(path) ==
                encode_local_tournament_pending_fixture(stale_attempt),
            "new checkpoint published after OS lock release");

    fs::remove_all(root);
    std::puts("local_tournament_fixture_launch_store_test: ok");
}
