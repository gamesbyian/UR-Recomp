#include "host_product_store.hpp"
#include "local_tournament_atomic_replace.hpp"

#include <cerrno>
#include <cstdio>
#include <string>

namespace ur::product {
namespace {

constexpr long kMaxHostStateBytes = 4096;

}  // namespace

HostProductLoadResult load_host_product_state_file(const std::string& path) {
    if (path.empty()) {
        return {HostProductLoadStatus::Rejected, std::nullopt, "empty host-state path"};
    }

    errno = 0;
    std::FILE* file = std::fopen(path.c_str(), "rb");
    if (!file) {
        if (errno == ENOENT) {
            return {HostProductLoadStatus::Missing, std::nullopt, {}};
        }
        return {HostProductLoadStatus::IoError, std::nullopt, "unable to open host-state file"};
    }

    if (std::fseek(file, 0, SEEK_END) != 0) {
        std::fclose(file);
        return {HostProductLoadStatus::IoError, std::nullopt, "unable to size host-state file"};
    }
    const long size = std::ftell(file);
    if (size < 0 || size > kMaxHostStateBytes) {
        std::fclose(file);
        return {HostProductLoadStatus::Rejected, std::nullopt, "host-state file size is invalid"};
    }
    if (std::fseek(file, 0, SEEK_SET) != 0) {
        std::fclose(file);
        return {HostProductLoadStatus::IoError, std::nullopt, "unable to rewind host-state file"};
    }

    std::string encoded(static_cast<std::size_t>(size), '\0');
    if (size > 0) {
        const std::size_t read = std::fread(
            encoded.data(), 1, static_cast<std::size_t>(size), file);
        if (read != static_cast<std::size_t>(size)) {
            std::fclose(file);
            return {HostProductLoadStatus::IoError, std::nullopt, "short host-state read"};
        }
    }
    if (std::fclose(file) != 0) {
        return {HostProductLoadStatus::IoError, std::nullopt, "unable to close host-state file"};
    }

    const DecodeResult decoded = decode_host_product_state(encoded);
    if (!decoded) {
        return {HostProductLoadStatus::Rejected, std::nullopt, decoded.error};
    }
    return {HostProductLoadStatus::Loaded, decoded.state, {}};
}

HostProductSaveStatus save_host_product_state_file(
    const std::string& path,
    const HostProductState& state) {
    if (path.empty()) {
        return HostProductSaveStatus::Rejected;
    }
    const std::string encoded = encode_host_product_state(state);
    if (encoded.empty()) {
        return HostProductSaveStatus::Rejected;
    }

    if (!write_host_replace_staged(path, encoded, "urhost")) {
        return HostProductSaveStatus::IoError;
    }
    return HostProductSaveStatus::Saved;
}

}  // namespace ur::product
