// ROM-free Win32 profile-level CAS acceptance: two actual processes, one winner.
// The lower-level atomic writer's last-writer-wins race is a different contract.
// This test exercises the production typed-profile codec, OS lock, exact-state
// comparison and publication, then verifies the winner in a fresh process.
// It does not establish raw+typed cross-file atomicity or physical power loss.
#if !defined(_WIN32)
#error This process fixture is intentionally Win32-only.
#endif

#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

#include "host_profile_store.hpp"
#include "local_tournament_atomic_replace.hpp"
#include "local_tournament_utf8_path.hpp"

#include <array>
#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <thread>

namespace fs = std::filesystem;
using namespace ur::product;

namespace {

void require(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "WIN32_PROFILE_CAS_FAILED " << message << "\n";
        std::exit(2);
    }
}

std::array<std::uint8_t, kStockSramBytes> payload(char marker) {
    std::array<std::uint8_t, kStockSramBytes> result{};
    result.fill(static_cast<std::uint8_t>(marker));
    return result;
}

std::string utf8_path(const fs::path& file) {
    // The runner supplies an ASCII-only temporary path; use the same UTF-8
    // storage API as the real host rather than a second test-only file writer.
    return file.u8string();
}

int writer(const fs::path& file, char marker) {
    const auto path = utf8_path(file);
    const auto loaded = load_host_profile_state_file(
        ExecutionMode::Modern, path, "profile.alpha");
    if (!loaded.loaded()) return 40;
    HostProfileState next = *loaded.state;
    const auto bytes = payload(marker);
    if (capture_stock_sram_for_profile(
            ExecutionMode::Modern, next, bytes.data(), bytes.size()) !=
        HostProfileTransferStatus::Applied) return 41;

    const auto ready = file.parent_path() /
        (std::string("cas-ready-") + marker);
    {
        std::ofstream signal(ready, std::ios::binary);
        signal << "ready";
        signal.flush();
        if (!signal.good()) return 42;
    }
    const auto deadline = std::chrono::steady_clock::now() +
        std::chrono::seconds(15);
    while (!fs::exists(file.parent_path() / "cas-go")) {
        if (std::chrono::steady_clock::now() >= deadline) return 43;
        std::this_thread::sleep_for(std::chrono::milliseconds(2));
    }

    const auto result = save_host_profile_state_file_if_current(
        ExecutionMode::Modern, path, loaded.state, next);
    if (result == HostProfileSaveStatus::Saved) return 0;
    if (result == HostProfileSaveStatus::Conflict) return 31;
    return 44;
}

int verify_cold(const fs::path& file, char marker) {
    const auto loaded = load_host_profile_state_file(
        ExecutionMode::Modern, utf8_path(file), "profile.alpha");
    if (!loaded.loaded() || loaded.state->autosave_generation !=
        (marker == 'C' ? 4u : marker == 'R' ? 3u : 2u)) return 50;
    std::array<std::uint8_t, kStockSramBytes> actual{};
    if (restore_stock_sram_from_profile(
            ExecutionMode::Modern, *loaded.state,
            actual.data(), actual.size()) != HostProfileTransferStatus::Applied)
        return 51;
    return actual == payload(marker) ? 0 : 52;
}

fs::path self_executable() {
    std::wstring buffer(32768, L'\0');
    const DWORD size = GetModuleFileNameW(
        nullptr, buffer.data(), static_cast<DWORD>(buffer.size()));
    require(size > 0 && size < buffer.size(), "self executable path");
    buffer.resize(size);
    return fs::path(buffer);
}

PROCESS_INFORMATION start_child(
    const fs::path& exe, const fs::path& file, const std::wstring& mode) {
    std::wstring command = L"\"" + exe.wstring() +
        L"\" " + mode + L" \"" + file.wstring() + L"\"";
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION process{};
    require(CreateProcessW(
                exe.c_str(), command.data(), nullptr, nullptr, FALSE,
                CREATE_NO_WINDOW, nullptr, nullptr, &startup, &process) != 0,
            "CreateProcessW independent profile reader/writer");
    return process;
}

DWORD finish_child(PROCESS_INFORMATION& process) {
    const DWORD waited = WaitForSingleObject(process.hProcess, 30000);
    if (waited != WAIT_OBJECT_0) {
        (void)TerminateProcess(process.hProcess, 99);
        (void)WaitForSingleObject(process.hProcess, 5000);
    }
    DWORD exit_code = 99;
    const bool got_exit = GetExitCodeProcess(process.hProcess, &exit_code) != 0;
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    require(waited == WAIT_OBJECT_0 && got_exit, "child completed on time");
    return exit_code;
}

// A real Win32 sharing denial must not discard an earned typed profile.
// Antivirus, indexers and another process can hold a handle without
// FILE_SHARE_DELETE while permitting reads. The canonical replacement must
// fail closed; after the handle is released a fresh save and cold boot work.
void verify_sharing_denial_recovery(const fs::path& file, char winner) {
    const std::string path = utf8_path(file);
    const auto incumbent = load_host_profile_state_file(
        ExecutionMode::Modern, path, "profile.alpha");
    require(incumbent.loaded() && incumbent.state->autosave_generation == 2,
            "sharing-denial case starts from committed CAS winner");
    std::ifstream before_stream(file, std::ios::binary);
    require(before_stream.good(), "read exact incumbent encoded bytes");
    const std::string before{
        std::istreambuf_iterator<char>{before_stream},
        std::istreambuf_iterator<char>{}};
    before_stream.close();
    require(!before.empty(), "incumbent encoded bytes are nonempty");

    HostProfileState next = *incumbent.state;
    const auto replacement = payload('R');
    require(capture_stock_sram_for_profile(
                ExecutionMode::Modern, next,
                replacement.data(), replacement.size()) ==
            HostProfileTransferStatus::Applied,
            "prepare generation-three replacement");

    HANDLE blocker = CreateFileW(
        file.c_str(), GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE,
        nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    require(blocker != INVALID_HANDLE_VALUE,
            "hold real Win32 handle denying canonical rename/delete");
    const auto refused = save_host_profile_state_file_if_current(
        ExecutionMode::Modern, path, incumbent.state, next);
    require(refused == HostProfileSaveStatus::IoError,
            "OS sharing denial rejects typed-profile replacement");
    std::ifstream after_stream(file, std::ios::binary);
    require(after_stream.good(), "read incumbent after refused replacement");
    const std::string after{
        std::istreambuf_iterator<char>{after_stream},
        std::istreambuf_iterator<char>{}};
    after_stream.close();
    require(after == before, "sharing denial retains exact incumbent bytes");
    require(CloseHandle(blocker) != 0, "release Win32 sharing-denial handle");

    const auto still_current = load_host_profile_state_file(
        ExecutionMode::Modern, path, "profile.alpha");
    require(still_current.loaded() && *still_current.state == *incumbent.state,
            "refused save leaves original typed CAS baseline valid");
    require(save_host_profile_state_file_if_current(
                ExecutionMode::Modern, path, incumbent.state, next) ==
            HostProfileSaveStatus::Saved,
            "explicit retry commits after sharing denial is released");
    auto cold = start_child(self_executable(), file, L"--verify-R");
    require(finish_child(cold) == 0,
            "independent cold process recovers retry's generation-three SRAM");
    for (const auto& entry : fs::directory_iterator(file.parent_path())) {
        require(entry.path().filename().wstring().rfind(
                    L".pending-urprofile-", 0) != 0,
                "sharing-denial and retry leave no private stages");
    }
    std::cout << "WIN32_PROFILE_SHARING_DENIAL_OK winner=" << winner
              << " refused=io-error incumbent=unchanged cold_retry=pass\n";
}

// Actual child-process death after flushing a complete typed profile into
// private staging, but before the canonical rename. This is a deterministic
// process-cut witness, NOT a real power cut or NTFS short write.
int crash_before_profile_claim(const fs::path& file) {
    const auto loaded = load_host_profile_state_file(
        ExecutionMode::Modern, utf8_path(file), "profile.alpha");
    if (!loaded.loaded() || loaded.state->autosave_generation != 3) return 60;
    HostProfileState next = *loaded.state;
    const auto replacement = payload('C');
    if (capture_stock_sram_for_profile(
            ExecutionMode::Modern, next,
            replacement.data(), replacement.size()) !=
        HostProfileTransferStatus::Applied) return 61;
    const auto encoded = encode_host_profile_state(next);
    if (encoded.empty()) return 62;
    // The public CAS API intentionally has no crash hook. Use its exact
    // production staged-writer primitive with a test-only process cut.
    // There is no concurrent writer during this controlled boundary.
    (void)write_host_replace_staged(
        host_native_path_from_utf8(utf8_path(file)), encoded, "urprofile",
        [] { std::_Exit(86); });
    return 63; // Reaching here means the cut never fired.
}

void verify_preclaim_cold_recovery(const fs::path& file) {
    const auto path = utf8_path(file);
    const auto incumbent = load_host_profile_state_file(
        ExecutionMode::Modern, path, "profile.alpha");
    require(incumbent.loaded() && incumbent.state->autosave_generation == 3,
            "preclaim cut begins with committed generation three");
    std::ifstream before_stream(file, std::ios::binary);
    require(before_stream.good(), "read committed profile before process cut");
    const std::string before{
        std::istreambuf_iterator<char>{before_stream},
        std::istreambuf_iterator<char>{}};
    before_stream.close();

    HostProfileState next = *incumbent.state;
    const auto replacement = payload('C');
    require(capture_stock_sram_for_profile(
                ExecutionMode::Modern, next,
                replacement.data(), replacement.size()) ==
            HostProfileTransferStatus::Applied,
            "prepare genuine encoded generation-four candidate");
    const std::string staged_expected = encode_host_profile_state(next);
    require(!staged_expected.empty(), "generation-four codec succeeded");

    auto dying = start_child(
        self_executable(), file, L"--crash-before-profile-claim");
    require(finish_child(dying) == 86,
            "independent process died at flushed preclaim boundary");
    std::ifstream after_stream(file, std::ios::binary);
    require(after_stream.good(), "read canonical profile after process death");
    const std::string after{
        std::istreambuf_iterator<char>{after_stream},
        std::istreambuf_iterator<char>{}};
    after_stream.close();
    require(after == before, "preclaim death preserves incumbent exact bytes");

    fs::path orphan;
    for (const auto& entry : fs::directory_iterator(file.parent_path())) {
        if (entry.path().filename().wstring().rfind(
                L".pending-urprofile-", 0) != 0) continue;
        const auto staged = entry.path() / "record.tmp";
        if (!fs::is_regular_file(staged)) continue;
        std::ifstream staged_stream(staged, std::ios::binary);
        const std::string bytes{
            std::istreambuf_iterator<char>{staged_stream},
            std::istreambuf_iterator<char>{}};
        if (bytes == staged_expected) orphan = entry.path();
    }
    require(!orphan.empty(),
            "actual dead child left complete but non-authoritative typed stage");
    auto cold = start_child(self_executable(), file, L"--verify-R");
    require(finish_child(cold) == 0,
            "independent cold boot ignores uncommitted stage");

    require(save_host_profile_state_file_if_current(
                ExecutionMode::Modern, path, incumbent.state, next) ==
            HostProfileSaveStatus::Saved,
            "explicit CAS retry commits after crashed process");
    auto recovered = start_child(self_executable(), file, L"--verify-C");
    require(finish_child(recovered) == 0,
            "second cold process recovers exact generation-four SRAM");
    require(fs::is_directory(orphan),
            "successful retry does not promote or delete dead child's stage");
    std::cout << "WIN32_PROFILE_PRECLAIM_COLD_OK death=86"
              << " incumbent=unchanged orphan=non-authoritative"
              << " explicit_retry=pass cold=pass\\n";
}

void parent(const fs::path& file) {
    const fs::path root = file.parent_path();
    require(fs::create_directories(root) || fs::is_directory(root),
            "isolated profile root exists");
    require(!fs::exists(file), "new isolated profile target");

    HostProfileState initial;
    initial.profile_id = "profile.alpha";
    const auto seed = payload('S');
    require(capture_stock_sram_for_profile(
                ExecutionMode::Modern, initial,
                seed.data(), seed.size()) == HostProfileTransferStatus::Applied,
            "seed captured with generation one");
    require(save_host_profile_state_file(
                ExecutionMode::Modern, utf8_path(file), initial) ==
                HostProfileSaveStatus::Saved,
            "seed profile durably published");

    const fs::path exe = self_executable();
    auto a = start_child(exe, file, L"--writer-A");
    auto b = start_child(exe, file, L"--writer-B");
    const auto deadline = std::chrono::steady_clock::now() +
        std::chrono::seconds(15);
    while ((!fs::exists(root / "cas-ready-A") ||
            !fs::exists(root / "cas-ready-B")) &&
           std::chrono::steady_clock::now() < deadline) {
        std::this_thread::sleep_for(std::chrono::milliseconds(2));
    }
    require(fs::exists(root / "cas-ready-A") &&
            fs::exists(root / "cas-ready-B"),
            "both independent processes read the same committed profile");
    {
        std::ofstream go(root / "cas-go", std::ios::binary);
        go << "go";
        go.flush();
        require(go.good(), "release two-process CAS barrier");
    }
    const DWORD result_a = finish_child(a);
    const DWORD result_b = finish_child(b);
    require((result_a == 0 && result_b == 31) ||
            (result_a == 31 && result_b == 0),
            "exactly one CAS commit and one stale-state conflict");

    const char winner = result_a == 0 ? 'A' : 'B';
    const auto loaded = load_host_profile_state_file(
        ExecutionMode::Modern, utf8_path(file), "profile.alpha");
    require(loaded.loaded() && loaded.state->autosave_generation == 2,
            "complete generation-two profile survives conflict");
    std::array<std::uint8_t, kStockSramBytes> actual{};
    require(restore_stock_sram_from_profile(
                ExecutionMode::Modern, *loaded.state,
                actual.data(), actual.size()) == HostProfileTransferStatus::Applied &&
            actual == payload(winner),
            "loser never overwrites winner's complete SRAM mirror");
    auto cold = start_child(
        exe, file, winner == 'A' ? L"--verify-A" : L"--verify-B");
    require(finish_child(cold) == 0,
            "third fresh process recovers winning exact SRAM bytes");
    for (const auto& entry : fs::directory_iterator(root)) {
        require(entry.path().filename().wstring().rfind(
                    L".pending-urprofile-", 0) != 0,
                "both writers cleaned private stages");
    }
    std::cout << "WIN32_PROFILE_CAS_OK winner=" << winner
              << " loser=conflict cold_process=pass\n";
    verify_sharing_denial_recovery(file, winner);
    verify_preclaim_cold_recovery(file);
}

} // namespace

int main(int argc, char** argv) {
    if (argc == 2) {
        parent(fs::path(argv[1]));
        return 0;
    }
    if (argc != 3) return 3;
    const std::string mode = argv[1];
    const fs::path file(argv[2]);
    if (mode == "--writer-A") return writer(file, 'A');
    if (mode == "--writer-B") return writer(file, 'B');
    if (mode == "--verify-A") return verify_cold(file, 'A');
    if (mode == "--verify-B") return verify_cold(file, 'B');
    if (mode == "--verify-R") return verify_cold(file, 'R');
    if (mode == "--verify-C") return verify_cold(file, 'C');
    if (mode == "--crash-before-profile-claim")
        return crash_before_profile_claim(file);
    return 4;
}
