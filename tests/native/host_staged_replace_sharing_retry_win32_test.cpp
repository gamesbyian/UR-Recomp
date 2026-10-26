// ROM-free Win32 acceptance: transient sharing denial at the actual
// post-flush/pre-rename boundary, and persistent denial without data loss.
#if !defined(_WIN32)
#error This fixture is Win32-only.
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include "local_tournament_atomic_replace.hpp"
#include <atomic>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <thread>

namespace fs = std::filesystem;
namespace {
std::atomic<bool> staged{false};
void after_stage() { staged.store(true, std::memory_order_release); }
void require(bool good, const char* message) {
    if (!good) {
        std::cerr << "WIN32_REPLACE_SHARING_RETRY_FAILED " << message << "\n";
        std::exit(2);
    }
}
std::string read_bytes(const fs::path& path) {
    std::ifstream in(path, std::ios::binary);
    require(in.good(), "read canonical file");
    return {std::istreambuf_iterator<char>{in}, std::istreambuf_iterator<char>{}};
}
void no_stages(const fs::path& root) {
    for (const auto& item : fs::directory_iterator(root))
        require(item.path().filename().wstring().rfind(L".pending-urprofile-", 0) != 0,
                "private stage cleaned");
}
HANDLE hold_without_delete(const fs::path& path) {
    HANDLE handle = CreateFileW(path.c_str(), GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr, OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL, nullptr);
    require(handle != INVALID_HANDLE_VALUE,
            "open canonical handle without FILE_SHARE_DELETE");
    return handle;
}
} // namespace

int main(int argc, char** argv) {
    require(argc == 2, "isolated root argument");
    const fs::path root(argv[1]);
    require(fs::is_directory(root), "isolated root exists");
    const fs::path path = root / "host-profile.txt";
    require(ur::product::write_host_replace_staged(path, "generation-one", "urprofile"),
            "establish canonical incumbent");
    HANDLE blocker = hold_without_delete(path);
    // The release timer begins only after the staged writer has synced and
    // closed its own file. Its first rename must encounter a genuine blocker.
    std::thread release([&] {
        while (!staged.load(std::memory_order_acquire)) Sleep(1);
        Sleep(35);
        require(CloseHandle(blocker) != 0, "release transient blocker");
    });
    const bool committed = ur::product::write_host_replace_staged(
        path, "generation-two", "urprofile", &after_stage);
    release.join();
    require(committed, "transient sharing refusal retried to completion");
    require(read_bytes(path) == "generation-two", "exact replacement after transient denial");
    no_stages(root);

    blocker = hold_without_delete(path);
    const bool refused = ur::product::write_host_replace_staged(
        path, "generation-three", "urprofile");
    require(!refused, "persistent sharing refusal remains an I/O failure");
    require(read_bytes(path) == "generation-two", "persistent refusal retains exact incumbent");
    require(CloseHandle(blocker) != 0, "release persistent blocker");
    no_stages(root);
    std::cout << "WIN32_REPLACE_SHARING_RETRY_OK transient=committed"
              << " persistent=refused incumbent=unchanged\n";
    return 0;
}
