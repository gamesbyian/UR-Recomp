#include "local_tournament_atomic_replace.hpp"

#include <array>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <thread>
#include <vector>

namespace fs = std::filesystem;
using ur::product::write_tournament_replace_staged;

bool simulate_disk_sync_failure(std::FILE*) { return false; }

void check(bool good, const char* message) {
    if (!good) {
        std::fprintf(stderr, "FAIL: %s\n", message);
        std::exit(1);
    }
}
std::string bytes(const fs::path& path) {
    std::ifstream in(path, std::ios::binary);
    return {std::istreambuf_iterator<char>(in),
            std::istreambuf_iterator<char>()};
}

fs::path competing_immutable_target;
void publish_competing_immutable_target() {
    // Deterministic hostile-writer interleaving after our private stage has
    // been flushed, but before its no-replace claim of the canonical name.
    std::ofstream out(competing_immutable_target, std::ios::binary);
    out << "rival-writer";
    out.flush();
    check(out.good(), "competing immutable target created");
}

// An injected exception models process termination without running the
// writer's normal private-stage cleanup. It is never used in production.
struct SimulatedProcessDeath {};
void die_at_publication_cut() { throw SimulatedProcessDeath{}; }

int main() {
    const auto stamp = std::chrono::steady_clock::now()
                           .time_since_epoch().count();
    const fs::path root = fs::temp_directory_path() /
        ("ur-tournament-atomic-replace-" + std::to_string(stamp));
    check(fs::create_directory(root), "test root created");
    check(!write_tournament_replace_staged("", "valid", "urlaunch"),
          "empty target rejected");
    check(!write_tournament_replace_staged(
              (root / "empty").string(), "", "urlaunch"),
          "empty payload rejected");
    check(!write_tournament_replace_staged(
              (root / "absent" / "file").string(), "valid", "urlaunch"),
          "nonexistent parent never created implicitly");

    const fs::path destination = root / "pending.urlaunch";
    // Preserve a Unicode profile directory through the staged native write.
    const fs::path unicode_dir = root / fs::u8path("profile-\xC3\xA9");
    check(fs::create_directory(unicode_dir), "Unicode profile directory created");
    const fs::path unicode_target = unicode_dir / "host-profile.txt";
    check(ur::product::write_host_replace_staged(
              unicode_target, "unicode-state", "urprofile"),
          "Unicode native profile path published");
    check(bytes(unicode_target) == "unicode-state",
          "Unicode native profile bytes round-trip");
    const fs::path native_intent = unicode_dir / "native-intent.pending";
    check(ur::product::write_host_create_staged_native(
              native_intent, "original-intent", "sram-intent"),
          "native Unicode recovery intent published");
    check(!ur::product::write_host_create_staged_native(
              native_intent, "must-not-overwrite", "sram-intent"),
          "native Unicode recovery intent refuses occupied target");
    check(bytes(native_intent) == "original-intent",
          "native Unicode recovery intent retains incumbent bytes");
    // A crash after stage flush but before canonical replacement must leave
    // the old profile authoritative. A later cold writer ignores orphan stage.
    const fs::path preclaim = unicode_dir / "preclaim-profile.txt";
    check(ur::product::write_host_replace_staged(
              preclaim, "last-committed", "urprofile"),
          "preclaim crash fixture establishes committed profile");
    bool preclaim_died = false;
    try {
        (void)ur::product::write_host_replace_staged(
            preclaim, "staged-but-not-committed", "urprofile",
            &die_at_publication_cut);
    } catch (const SimulatedProcessDeath&) {
        preclaim_died = true;
    }
    check(preclaim_died, "preclaim crash cut executed");
    check(bytes(preclaim) == "last-committed",
          "preclaim crash preserves last committed profile");
    fs::path orphaned_stage;
    for (const auto& item : fs::directory_iterator(unicode_dir)) {
        if (item.path().filename().u8string().rfind(
                ".pending-urprofile-", 0) == 0)
            orphaned_stage = item.path();
    }
    check(!orphaned_stage.empty() &&
              bytes(orphaned_stage / "record.tmp") == "staged-but-not-committed",
          "preclaim crash leaves private, non-authoritative staged bytes");
    check(ur::product::write_host_replace_staged(
              preclaim, "cold-restart-commit", "urprofile"),
          "cold writer can publish despite orphaned private stage");
    check(bytes(preclaim) == "cold-restart-commit" &&
              fs::exists(orphaned_stage),
          "cold writer never promotes or deletes unrelated crash debris");

    // A crash after the atomic claim is a committed write even if the
    // writer never reaches private-stage cleanup or returns success.
    const fs::path postclaim = unicode_dir / "postclaim-profile.txt";
    bool postclaim_died = false;
    try {
        (void)ur::product::write_host_replace_staged(
            postclaim, "committed-before-crash", "urprofile",
            nullptr, nullptr, &die_at_publication_cut);
    } catch (const SimulatedProcessDeath&) {
        postclaim_died = true;
    }
    check(postclaim_died && bytes(postclaim) == "committed-before-crash",
          "postclaim crash retains visible committed profile bytes");
    const fs::path raced_intent = unicode_dir / "raced-intent.pending";
    competing_immutable_target = raced_intent;
    check(!ur::product::write_host_create_staged_native(
              raced_intent, "must-not-replace-rival", "sram-intent",
              &publish_competing_immutable_target),
          "immutable intent refuses target created after staging");
    check(bytes(raced_intent) == "rival-writer",
          "competing immutable claim retains exact rival bytes");
    for (const auto& item : fs::directory_iterator(unicode_dir)) {
        check(item.path().filename().u8string().rfind(
                  ".pending-sram-intent-", 0) != 0,
              "failed immutable claim cleans private staging");
    }
    check(write_tournament_replace_staged(
              destination.string(), "original", "urlaunch"),
          "establish a valid incumbent before syncing failure");
    check(!ur::product::write_host_replace_staged(
              destination.string(), "new bytes not safely synced", "urlaunch",
              nullptr, &simulate_disk_sync_failure),
          "injected durable-stage failure aborts canonical publication");
    check(bytes(destination) == "original",
          "stage sync failure preserves exact incumbent bytes");
    for (const auto& item : fs::directory_iterator(root)) {
        check(item.path().filename().string().rfind(
                  ".pending-urlaunch-", 0) != 0,
              "sync failure cleans its own private staging");
    }
    constexpr std::size_t kWriters = 8;
    std::array<std::string, kWriters> candidate{};
    for (std::size_t i = 0; i < kWriters; ++i) {
        candidate[i] = "attempt-" + std::to_string(i) + ":" +
            std::string(800, static_cast<char>('A' + i));
    }
    for (unsigned round = 0; round < 8; ++round) {
        std::atomic<std::size_t> ready{0};
        std::atomic<bool> go{false};
        std::array<bool, kWriters> published{};
        std::vector<std::thread> workers;
        for (std::size_t i = 0; i < kWriters; ++i) {
            workers.emplace_back([&, i] {
                ready.fetch_add(1, std::memory_order_release);
                while (!go.load(std::memory_order_acquire)) {
                    std::this_thread::yield();
                }
                published[i] = write_tournament_replace_staged(
                    destination.string(), candidate[i], "urlaunch");
            });
        }
        while (ready.load(std::memory_order_acquire) != kWriters) {
            std::this_thread::yield();
        }
        go.store(true, std::memory_order_release);
        for (auto& worker : workers) worker.join();

        bool matched = false;
        const auto on_disk = bytes(destination);
        for (std::size_t i = 0; i < kWriters; ++i) {
            check(published[i], "each independent staging writer completes");
            matched = matched || on_disk == candidate[i];
        }
        check(matched, "target is always one WHOLE canonical candidate");
        check(!fs::exists(destination.string() + ".tmp"),
              "legacy shared staging filename never created");
        for (const auto& item : fs::directory_iterator(root)) {
            check(item.path().filename().string().rfind(
                  ".pending-urlaunch-", 0) != 0,
                  "completed writers remove staging reservations");
        }
    }
    const fs::path abandoned = root / ".pending-urlaunch-crashed";
    fs::create_directory(abandoned);
    {
        std::ofstream pending(abandoned / "record.tmp");
        pending << "incomplete pending data";
    }
    check(write_tournament_replace_staged(
              destination.string(), "complete replacement", "urlaunch"),
          "future publication ignores crash debris");
    check(bytes(destination) == "complete replacement",
          "abandoned staging cannot become the authoritative file");
    fs::remove_all(root);
    std::puts("local_tournament_atomic_replace_test: ok");
    return 0;
}
