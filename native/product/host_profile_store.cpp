#include "host_profile_store.hpp"

#include <cerrno>
#include <cstdio>
#include <string>

#if defined(_WIN32)
#include <windows.h>
#endif

namespace ur::product {
namespace {

constexpr long kMaxProfileStateBytes =
    static_cast<long>(kStockSramBytes * 2 + 1024);

bool replace_file_atomically(
    const std::string& temporary_path,
    const std::string& final_path) noexcept {
#if defined(_WIN32)
    return MoveFileExA(
        temporary_path.c_str(),
        final_path.c_str(),
        MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH) != 0;
#else
    return std::rename(temporary_path.c_str(), final_path.c_str()) == 0;
#endif
}

}  // namespace

HostProfileLoadResult load_host_profile_state_file(
    ExecutionMode mode,
    const std::string& path,
    std::string_view expected_profile_id) {
    if (!policy_for(mode).host_profiles) {
        return {
            HostProfileLoadStatus::Rejected,
            std::nullopt,
            false,
            "profile persistence disabled by execution policy"};
    }
    if (path.empty() || !is_valid_profile_id(expected_profile_id)) {
        return {
            HostProfileLoadStatus::Rejected,
            std::nullopt,
            false,
            "invalid profile load request"};
    }

    errno = 0;
    std::FILE* file = std::fopen(path.c_str(), "rb");
    if (!file) {
        if (errno == ENOENT) {
            return {HostProfileLoadStatus::Missing, std::nullopt, false, {}};
        }
        return {
            HostProfileLoadStatus::IoError,
            std::nullopt,
            false,
            "unable to open profile-state file"};
    }

    if (std::fseek(file, 0, SEEK_END) != 0) {
        std::fclose(file);
        return {
            HostProfileLoadStatus::IoError,
            std::nullopt,
            false,
            "unable to size profile-state file"};
    }
    const long size = std::ftell(file);
    if (size < 0 || size > kMaxProfileStateBytes) {
        std::fclose(file);
        return {
            HostProfileLoadStatus::Rejected,
            std::nullopt,
            false,
            "profile-state file size is invalid"};
    }
    if (std::fseek(file, 0, SEEK_SET) != 0) {
        std::fclose(file);
        return {
            HostProfileLoadStatus::IoError,
            std::nullopt,
            false,
            "unable to rewind profile-state file"};
    }

    std::string encoded(static_cast<std::size_t>(size), '\0');
    if (size > 0) {
        const std::size_t read = std::fread(
            encoded.data(), 1, static_cast<std::size_t>(size), file);
        if (read != static_cast<std::size_t>(size)) {
            std::fclose(file);
            return {
                HostProfileLoadStatus::IoError,
                std::nullopt,
                false,
                "short profile-state read"};
        }
    }
    if (std::fclose(file) != 0) {
        return {
            HostProfileLoadStatus::IoError,
            std::nullopt,
            false,
            "unable to close profile-state file"};
    }

    const auto decoded = decode_host_profile_state(encoded);
    if (!decoded) {
        return {
            HostProfileLoadStatus::Rejected,
            std::nullopt,
            false,
            decoded.error};
    }
    if (decoded.state->profile_id != expected_profile_id) {
        return {
            HostProfileLoadStatus::Rejected,
            std::nullopt,
            decoded.migrated,
            "profile-state identifier mismatch"};
    }

    return {
        HostProfileLoadStatus::Loaded,
        decoded.state,
        decoded.migrated,
        {}};
}

HostProfileSaveStatus save_host_profile_state_file(
    ExecutionMode mode,
    const std::string& path,
    const HostProfileState& state) {
    if (!policy_for(mode).host_profiles || path.empty()) {
        return HostProfileSaveStatus::Rejected;
    }

    const std::string encoded = encode_host_profile_state(state);
    if (encoded.empty() ||
        encoded.size() > static_cast<std::size_t>(kMaxProfileStateBytes)) {
        return HostProfileSaveStatus::Rejected;
    }

    const std::string temporary_path = path + ".tmp";
    std::FILE* file = std::fopen(temporary_path.c_str(), "wb");
    if (!file) {
        return HostProfileSaveStatus::IoError;
    }

    const std::size_t written =
        std::fwrite(encoded.data(), 1, encoded.size(), file);
    const bool flushed = std::fflush(file) == 0;
    const bool closed = std::fclose(file) == 0;
    if (written != encoded.size() || !flushed || !closed) {
        std::remove(temporary_path.c_str());
        return HostProfileSaveStatus::IoError;
    }

    if (!replace_file_atomically(temporary_path, path)) {
        std::remove(temporary_path.c_str());
        return HostProfileSaveStatus::IoError;
    }

    return HostProfileSaveStatus::Saved;
}

}  // namespace ur::product
