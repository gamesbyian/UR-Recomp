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
#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <csignal>
#include <sys/resource.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#endif

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


// A genuine separate executable invocation, terminated with _Exit(86), is
// distinct from the exception-only crash-cut fixtures below. The child must
// not run C++ destructors or the writer's staging cleanup after the cut.
void terminate_at_real_process_cut() { std::_Exit(86); }

fs::path process_cut_root() {
#if defined(_WIN32)
    const DWORD needed = GetEnvironmentVariableW(
        L"UR_ATOMIC_TEST_CUT_ROOT", nullptr, 0);
    if (needed < 2) return {};
    std::wstring value(needed, L'\0');
    const DWORD length = GetEnvironmentVariableW(
        L"UR_ATOMIC_TEST_CUT_ROOT", value.data(), needed);
    if (!length || length >= needed) return {};
    value.resize(length);
    return fs::path(value);
#else
    const char* value = std::getenv("UR_ATOMIC_TEST_CUT_ROOT");
    return value ? fs::path(value) : fs::path{};
#endif
}

int run_real_process_cut_child(const std::string& mode) {
    const fs::path root = process_cut_root();
    if (root.empty() || !fs::is_directory(root)) return 87;
    if (mode == "--real-preclaim") {
        (void)ur::product::write_host_replace_staged(
            root / "real-preclaim.txt", "uncommitted-child", "urprofile",
            &terminate_at_real_process_cut);
    } else if (mode == "--real-postclaim") {
        (void)ur::product::write_host_replace_staged(
            root / "real-postclaim.txt", "committed-child", "urprofile",
            nullptr, nullptr, &terminate_at_real_process_cut);
    } else if (mode == "--real-race-A" || mode == "--real-race-B") {
        // An actual second Windows process, not another thread in this one.
        // Wait until both children are alive before racing the same target.
        const char writer = mode.back();
        const fs::path ready = root / (std::string("race-ready-") + writer);
        {
            std::ofstream signal(ready, std::ios::binary);
            signal << "ready";
            signal.flush();
            if (!signal.good()) return 95;
        }
        const auto deadline = std::chrono::steady_clock::now() +
                              std::chrono::seconds(15);
        while (!fs::exists(root / "race-go")) {
            if (std::chrono::steady_clock::now() >= deadline) return 96;
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        const bool published = ur::product::write_host_replace_staged(
            root / "race-target.txt", std::string(8192, writer), "urprofile");
        return published ? 0 : 94;
    } else {
        return 88;
    }
    // The only successful child outcome is an abrupt exit at the requested
    // production-writer callback. A returned writer is a failed witness.
    return 89;
}

void run_real_process_cut(const fs::path& root, const char* self,
                          const char* mode) {
#if defined(_WIN32)
    check(SetEnvironmentVariableW(L"UR_ATOMIC_TEST_CUT_ROOT", root.c_str()) != 0,
          "Windows child test root configured");
    std::wstring executable(32768, L'\0');
    const DWORD length = GetModuleFileNameW(
        nullptr, executable.data(), static_cast<DWORD>(executable.size()));
    check(length > 0 && length < executable.size(),
          "Windows test executable path obtained");
    executable.resize(length);
    const std::wstring option =
        std::string(mode) == "--real-preclaim"
            ? L"--real-preclaim" : L"--real-postclaim";
    std::wstring command = L"\"" + executable + L"\" " + option;
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION child{};
    check(CreateProcessW(executable.c_str(), command.data(), nullptr, nullptr,
                         FALSE, CREATE_NO_WINDOW, nullptr, nullptr,
                         &startup, &child) != 0,
          "real Windows child process started");
    const DWORD waited = WaitForSingleObject(child.hProcess, 30000);
    DWORD exit_code = 0;
    const bool exited = waited == WAIT_OBJECT_0 &&
        GetExitCodeProcess(child.hProcess, &exit_code) != 0;
    CloseHandle(child.hThread);
    CloseHandle(child.hProcess);
    check(exited && exit_code == 86, "real Windows child died at crash cut");
#else
    check(setenv("UR_ATOMIC_TEST_CUT_ROOT", root.c_str(), 1) == 0,
          "POSIX child test root configured");
    const pid_t pid = fork();
    check(pid >= 0, "real POSIX child forked");
    if (pid == 0) {
        execl(self, self, mode, static_cast<char*>(nullptr));
        std::_Exit(127);
    }
    int status = 0;
    check(waitpid(pid, &status, 0) == pid &&
              WIFEXITED(status) && WEXITSTATUS(status) == 86,
          "real POSIX child died at crash cut");
#endif
}


void run_real_two_process_writer_race(const fs::path& root) {
#if defined(_WIN32)
    // Unlike the existing eight-thread fixture, these are separate Win32
    // processes with independent CRT buffers and private stage reservations.
    const fs::path race_root = root / "real-two-process";
    check(fs::create_directory(race_root), "two-process root created");
    check(SetEnvironmentVariableW(
              L"UR_ATOMIC_TEST_CUT_ROOT", race_root.c_str()) != 0,
          "two-process root inherited by children");
    std::wstring executable(32768, L'\0');
    const DWORD length = GetModuleFileNameW(
        nullptr, executable.data(), static_cast<DWORD>(executable.size()));
    check(length > 0 && length < executable.size(),
          "two-process executable path obtained");
    executable.resize(length);
    PROCESS_INFORMATION children[2]{};
    for (unsigned i = 0; i < 2; ++i) {
        const wchar_t label = i == 0 ? L'A' : L'B';
        std::wstring command = L"\"" + executable +
                               L"\" --real-race-" + label;
        STARTUPINFOW startup{};
        startup.cb = sizeof(startup);
        check(CreateProcessW(executable.c_str(), command.data(),
                             nullptr, nullptr, FALSE, CREATE_NO_WINDOW,
                             nullptr, nullptr, &startup, &children[i]) != 0,
              "independent Windows writer process started");
    }
    const auto deadline = std::chrono::steady_clock::now() +
                          std::chrono::seconds(15);
    while ((!fs::exists(race_root / "race-ready-A") ||
            !fs::exists(race_root / "race-ready-B")) &&
           std::chrono::steady_clock::now() < deadline) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    check(fs::exists(race_root / "race-ready-A") &&
          fs::exists(race_root / "race-ready-B"),
          "both independent writers reached publication barrier");
    {
        std::ofstream go(race_root / "race-go", std::ios::binary);
        go << "go";
        go.flush();
        check(go.good(), "two-process publication barrier released");
    }
    bool at_least_one_committed = false;
    for (auto& child : children) {
        const DWORD waited = WaitForSingleObject(child.hProcess, 30000);
        DWORD exit_code = 0;
        const bool exited = waited == WAIT_OBJECT_0 &&
            GetExitCodeProcess(child.hProcess, &exit_code) != 0;
        CloseHandle(child.hThread);
        CloseHandle(child.hProcess);
        check(exited && (exit_code == 0 || exit_code == 94),
              "independent writer completed or reported publication conflict");
        at_least_one_committed |= exit_code == 0;
    }
    check(at_least_one_committed, "at least one Windows writer committed");
    const std::string final_bytes = bytes(race_root / "race-target.txt");
    check(final_bytes == std::string(8192, 'A') ||
          final_bytes == std::string(8192, 'B'),
          "two-process target contains exactly one complete writer payload");
    for (const auto& entry : fs::directory_iterator(race_root)) {
        check(entry.path().filename().wstring().rfind(
                  L".pending-urprofile-", 0) != 0,
              "both independent writers cleaned their private stages");
    }
#else
    (void)root;
#endif
}

int main(int argc, char** argv) {
    if (argc == 2) return run_real_process_cut_child(argv[1]);
    check(argc == 1, "unexpected test executable arguments");
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
    // Fresh executable process, actual _Exit, then parent-side cold read.
    // This proves the callback cuts survive real OS process teardown rather
    // than only C++ exception unwinding in a single address space.
    const fs::path real_preclaim = unicode_dir / "real-preclaim.txt";
    check(ur::product::write_host_replace_staged(
              real_preclaim, "last-committed-child", "urprofile"),
          "real preclaim fixture committed before child");
    run_real_process_cut(unicode_dir, argv[0], "--real-preclaim");
    check(bytes(real_preclaim) == "last-committed-child",
          "real process death before claim retains committed bytes");
    fs::path real_orphan;
    for (const auto& item : fs::directory_iterator(unicode_dir)) {
        if (item.path().filename().u8string().rfind(
                ".pending-urprofile-", 0) == 0 &&
            fs::exists(item.path() / "record.tmp") &&
            bytes(item.path() / "record.tmp") == "uncommitted-child")
            real_orphan = item.path();
    }
    check(!real_orphan.empty(),
          "real process death preserves non-authoritative private stage");
    check(ur::product::write_host_replace_staged(
              real_preclaim, "committed-after-child", "urprofile"),
          "fresh parent writer publishes after real child death");
    check(bytes(real_preclaim) == "committed-after-child" &&
              fs::exists(real_orphan),
          "cold writer neither promotes nor deletes dead child's stage");

    const fs::path real_postclaim = unicode_dir / "real-postclaim.txt";
    run_real_process_cut(unicode_dir, argv[0], "--real-postclaim");
    check(bytes(real_postclaim) == "committed-child",
          "real process death after claim retains committed bytes");
    run_real_two_process_writer_race(unicode_dir);
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
#if !defined(_WIN32)
    // A real kernel-enforced write ceiling, not a mocked sync callback:
    // stdio may report the failure at fwrite, fflush or fclose. Regardless
    // of that timing, the previously committed profile must remain intact.
    const fs::path limited = root / "kernel-limit-profile.txt";
    check(ur::product::write_host_replace_staged(
              limited, "last-committed", "urprofile"),
          "kernel write-limit test establishes committed profile");
    const pid_t limited_pid = ::fork();
    check(limited_pid >= 0, "fork kernel-limited writer");
    if (limited_pid == 0) {
        struct rlimit limit{};
        limit.rlim_cur = 1024;
        limit.rlim_max = 1024;
        if (::setrlimit(RLIMIT_FSIZE, &limit) != 0) std::_Exit(91);
        if (std::signal(SIGXFSZ, SIG_IGN) == SIG_ERR) std::_Exit(92);
        const bool published = ur::product::write_host_replace_staged(
            limited, std::string(8192, 'N'), "urprofile");
        std::_Exit(published ? 93 : 0);
    }
    int limited_status = 0;
    check(::waitpid(limited_pid, &limited_status, 0) == limited_pid &&
              WIFEXITED(limited_status) && WEXITSTATUS(limited_status) == 0,
          "kernel-limited staged write fails without publishing");
    check(bytes(limited) == "last-committed",
          "kernel-limited write retains exact committed profile bytes");
    for (const auto& item : fs::directory_iterator(root)) {
        check(item.path().filename().string().rfind(
                  ".pending-urprofile-", 0) != 0,
              "kernel-limited write cleans its private staging");
    }
    check(ur::product::write_host_replace_staged(
              limited, std::string(8192, 'N'), "urprofile"),
          "unlimited cold retry publishes the previously refused payload");
    check(bytes(limited) == std::string(8192, 'N'),
          "unlimited retry publishes complete bytes, never partial data");
#endif

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
