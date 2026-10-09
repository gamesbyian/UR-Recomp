#include "host_profile_store.hpp"
#include "local_tournament_atomic_replace.hpp"
#include "local_tournament_launch_path_lock.hpp"

#include <cerrno>
#include <cstdio>
#include <string>

namespace ur::product {
namespace {

constexpr long kMaxProfileStateBytes =
    static_cast<long>(kStockSramBytes * 2 + 1024);

}  // namespace

HostProfileLoadResult load_host_profile_state_file(
    ExecutionMode mode,
    const std::string& path,
    std::string_view expected_profile_id) {
    if (!policy_for(mode).host_profiles) {
        return {
            HostProfileLoadStatus::RejectedByPolicy,
            std::nullopt,
            "profile persistence disabled by execution policy"};
    }
    if (path.empty() || !is_valid_profile_id(expected_profile_id)) {
        return {
            HostProfileLoadStatus::Malformed,
            std::nullopt,
            "invalid profile load request"};
    }

    errno = 0;
    std::FILE* file = std::fopen(path.c_str(), "rb");
    if (!file) {
        if (errno == ENOENT) {
            return {HostProfileLoadStatus::Missing, std::nullopt, {}};
        }
        return {
            HostProfileLoadStatus::IoError,
            std::nullopt,
            "unable to open profile-state file"};
    }

    if (std::fseek(file, 0, SEEK_END) != 0) {
        std::fclose(file);
        return {
            HostProfileLoadStatus::IoError,
            std::nullopt,
            "unable to size profile-state file"};
    }
    const long size = std::ftell(file);
    if (size < 0 || size > kMaxProfileStateBytes) {
        std::fclose(file);
        return {
            HostProfileLoadStatus::Malformed,
            std::nullopt,
            "profile-state file size is invalid"};
    }
    if (std::fseek(file, 0, SEEK_SET) != 0) {
        std::fclose(file);
        return {
            HostProfileLoadStatus::IoError,
            std::nullopt,
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
                "short profile-state read"};
        }
    }
    if (std::fclose(file) != 0) {
        return {
            HostProfileLoadStatus::IoError,
            std::nullopt,
            "unable to close profile-state file"};
    }

    const auto decoded = decode_host_profile_state(encoded);
    if (!decoded) {
        return {
            HostProfileLoadStatus::Malformed,
            std::nullopt,
            decoded.error};
    }
    if (decoded.state->profile_id != expected_profile_id) {
        return {
            HostProfileLoadStatus::Malformed,
            std::nullopt,
            "profile-state identifier mismatch"};
    }

    return {HostProfileLoadStatus::Loaded, decoded.state, {}};
}

HostProfileResolveResult resolve_host_profile_state_file(
    ExecutionMode mode,
    const std::string& path,
    std::string_view expected_profile_id) {
    const auto loaded =
        load_host_profile_state_file(mode, path, expected_profile_id);
    if (loaded.loaded()) {
        return {HostProfileResolveStatus::Loaded, loaded.state, {}};
    }
    if (loaded.status == HostProfileLoadStatus::RejectedByPolicy) {
        return {
            HostProfileResolveStatus::RejectedByPolicy,
            std::nullopt,
            loaded.error};
    }
    if (loaded.status == HostProfileLoadStatus::IoError) {
        return {HostProfileResolveStatus::IoError, std::nullopt, loaded.error};
    }

    auto fallback = make_default_host_profile_state(expected_profile_id);
    if (!fallback) {
        return {
            HostProfileResolveStatus::IoError,
            std::nullopt,
            "unable to construct default profile state"};
    }

    if (loaded.status == HostProfileLoadStatus::Missing) {
        return {
            HostProfileResolveStatus::DefaultedMissing,
            fallback,
            {}};
    }
    return {
        HostProfileResolveStatus::DefaultedMalformed,
        fallback,
        loaded.error};
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

    if (!write_host_replace_staged(path, encoded, "urprofile")) {
        return HostProfileSaveStatus::IoError;
    }
    return HostProfileSaveStatus::Saved;
}

HostProfileSaveStatus save_host_profile_state_file_if_current(
    ExecutionMode mode,
    const std::string& path,
    const std::optional<HostProfileState>& expected_current,
    const HostProfileState& next) {
    if (!policy_for(mode).host_profiles || path.empty() ||
        encode_host_profile_state(next).empty() ||
        (expected_current &&
         expected_current->profile_id != next.profile_id)) {
        return HostProfileSaveStatus::Rejected;
    }

    // The lock must cover both the comparison and the publication. A read
    // followed by a separate unlocked write is vulnerable to the same
    // two-process lost-update race as the previous .tmp implementation.
    TournamentLaunchPathLock lock(path);
    if (!lock.acquired()) return HostProfileSaveStatus::IoError;
    const auto current =
        load_host_profile_state_file(mode, path, next.profile_id);
    if (expected_current) {
        if (current.status == HostProfileLoadStatus::IoError)
            return HostProfileSaveStatus::IoError;
        if (!current.loaded() || *current.state != *expected_current)
            return HostProfileSaveStatus::Conflict;
    } else {
        if (current.status == HostProfileLoadStatus::IoError)
            return HostProfileSaveStatus::IoError;
        if (current.status != HostProfileLoadStatus::Missing)
            return HostProfileSaveStatus::Conflict;
    }
    return save_host_profile_state_file(mode, path, next);
}

}  // namespace ur::product
