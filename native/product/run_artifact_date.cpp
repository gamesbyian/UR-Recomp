#include "run_artifact_date.hpp"

#include <algorithm>
#include <chrono>
#include <cctype>
#include <ctime>
#include <filesystem>

namespace ur::product {

std::string run_artifact_date_text(const std::string& path) {
    const std::string name =
        std::filesystem::path(path).filename().string();
    constexpr std::size_t kPrefixSize = 4;
    constexpr std::size_t kTimestampSize = 16;
    if (name.size() < kPrefixSize + kTimestampSize + 1 ||
        name.compare(0, kPrefixSize, "run-") != 0 ||
        name[kPrefixSize + kTimestampSize] != '-') {
        return "--";
    }

    const std::string digits =
        name.substr(kPrefixSize, kTimestampSize);
    if (!std::all_of(
            digits.begin(), digits.end(),
            [](unsigned char ch) { return std::isdigit(ch) != 0; })) {
        return "--";
    }

    std::uint64_t milliseconds = 0;
    for (char ch : digits) {
        milliseconds =
            milliseconds * 10u + static_cast<unsigned>(ch - '0');
    }

    const auto point = std::chrono::system_clock::time_point(
        std::chrono::milliseconds(milliseconds));
    const std::time_t seconds =
        std::chrono::system_clock::to_time_t(point);
    std::tm local{};
#ifdef _WIN32
    if (localtime_s(&local, &seconds) != 0) return "--";
#else
    if (!localtime_r(&seconds, &local)) return "--";
#endif

    char text[16];
    if (std::strftime(text, sizeof(text), "%Y-%m-%d", &local) == 0) {
        return "--";
    }
    return text;
}

}  // namespace ur::product
