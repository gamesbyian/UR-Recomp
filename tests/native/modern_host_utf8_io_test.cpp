#include "local_tournament_utf8_path.hpp"

#include <cassert>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <system_error>

int main() {
    namespace fs = std::filesystem;

    using ur::product::host_trim_user_data_root;
    // Absolute roots must stay absolute, including Windows drive roots.
    assert(host_trim_user_data_root("") == "");
    assert(host_trim_user_data_root("/") == "/");
    assert(host_trim_user_data_root("///") == "//");
    assert(host_trim_user_data_root("\\") == "\\");
    assert(host_trim_user_data_root("\\\\") == "\\\\");
    assert(host_trim_user_data_root("C:\\") == "C:\\");
    assert(host_trim_user_data_root("c:\\\\\\") == "c:\\");
    assert(host_trim_user_data_root("D://") == "D:/");
    assert(host_trim_user_data_root("\\\\?\\C:\\\\\\") == "\\\\?\\C:\\");
    assert(host_trim_user_data_root("\\\\server\\share\\") == "\\\\server\\share");
    assert(host_trim_user_data_root("C:\\Profiles\\Racer\\") == "C:\\Profiles\\Racer");
    assert(host_trim_user_data_root("/home/racer///") == "/home/racer");
    assert(host_trim_user_data_root(std::string(u8"/home/路径/🌈///")) ==
           std::string(u8"/home/路径/🌈"));
    const auto nonce = std::to_string(
        std::chrono::steady_clock::now().time_since_epoch().count());
    const fs::path root = fs::temp_directory_path() /
        fs::u8path(std::string(u8"ur-host-io-路径-🌈-") + nonce);
    std::error_code ec;
    fs::create_directories(root, ec);
    assert(!ec);
    const std::string utf8_root = root.u8string();
    assert(fs::exists(ur::product::host_native_path_from_utf8(utf8_root)));

    for (const char* leaf : {
             "onboarding-v1.seen", "host-state-v1.txt",
             "tour-continue-input.txt", "record-override.input"}) {
        const std::string path = (root / leaf).u8string();
        const std::string payload = std::string("0:2:80\n\0payload", 15);
        {
            std::ofstream out(ur::product::host_native_path_from_utf8(path),
                              std::ios::binary | std::ios::trunc);
            assert(out);
            out.write(payload.data(), static_cast<std::streamsize>(payload.size()));
            out.flush();
            assert(out);
        }
        std::ifstream in(ur::product::host_native_path_from_utf8(path),
                         std::ios::binary);
        assert(in);
        const std::string actual((std::istreambuf_iterator<char>(in)),
                                 std::istreambuf_iterator<char>());
        assert(actual == payload);
    }
    fs::remove_all(root, ec);
    assert(!ec);
}
