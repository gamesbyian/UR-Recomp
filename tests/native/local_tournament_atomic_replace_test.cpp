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
