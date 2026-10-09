#include "host_profile_catalog.hpp"
#include "local_tournament_atomic_replace.hpp"
#include "host_product_state.hpp"
#include "host_profile_runtime.hpp"

#include <charconv>
#include <cctype>
#include <cstdio>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <sstream>

namespace ur::product {
namespace {
constexpr std::string_view kHeader = "UR-PROFILE-CATALOG/1";
constexpr std::uintmax_t kMaxCatalogBytes = 1024u * 1024u;

std::string escape_field(std::string_view value) {
    std::string out;
    for (char ch : value) {
        if (ch == '%' || ch == '|' || ch == '\n' || ch == '\r') {
            char buf[4];
            std::snprintf(buf, sizeof(buf), "%%%02X",
                static_cast<unsigned char>(ch));
            out += buf;
        } else {
            out += ch;
        }
    }
    return out;
}

int hex(char ch) {
    if (ch >= '0' && ch <= '9') return ch - '0';
    if (ch >= 'A' && ch <= 'F') return 10 + ch - 'A';
    if (ch >= 'a' && ch <= 'f') return 10 + ch - 'a';
    return -1;
}

std::string canonical_profile_id(std::string_view value) {
    std::string out(value);
    for (char& ch : out) {
        if (ch >= 'A' && ch <= 'Z') {
            ch = static_cast<char>(ch - 'A' + 'a');
        }
    }
    // Windows normalizes trailing dots in ordinary path components. Profile
    // ids do not permit spaces, so dots are the only trailing normalization
    // relevant to this catalog.
    while (!out.empty() && out.back() == '.') out.pop_back();
    return out;
}

bool catalog_safe_profile_id(std::string_view value) {
    return is_safe_profile_storage_id(value);
}

std::optional<std::string> unescape_field(std::string_view value) {
    std::string out;
    for (std::size_t i = 0; i < value.size(); ++i) {
        if (value[i] != '%') { out += value[i]; continue; }
        if (i + 2 >= value.size()) return std::nullopt;
        const int hi = hex(value[i + 1]);
        const int lo = hex(value[i + 2]);
        if (hi < 0 || lo < 0) return std::nullopt;
        out += static_cast<char>((hi << 4) | lo);
        i += 2;
    }
    return out;
}
}  // namespace

std::string encode_host_profile_catalog(
    const std::vector<HostProfileCatalogEntry>& entries) {
    std::ostringstream out;
    out << kHeader << '\n';
    std::vector<std::string> canonical_ids;
    canonical_ids.reserve(entries.size());
    for (const auto& entry : entries) {
        if (!catalog_safe_profile_id(entry.profile_id) ||
            !valid_racer_identity(entry.identity)) return {};
        const std::string canonical_id =
            canonical_profile_id(entry.profile_id);
        for (const auto& prior : canonical_ids) {
            if (prior == canonical_id) return {};
        }
        canonical_ids.push_back(canonical_id);
        out << entry.profile_id << '|'
            << static_cast<unsigned>(entry.identity.rider_index) << '|'
            << escape_field(entry.identity.name) << '\n';
    }
    return out.str();
}

std::optional<std::vector<HostProfileCatalogEntry>> decode_host_profile_catalog(
    std::string_view encoded) {
    std::istringstream in{std::string(encoded)};
    std::string line;
    if (!std::getline(in, line) || line != kHeader) return std::nullopt;
    std::vector<HostProfileCatalogEntry> out;
    while (std::getline(in, line)) {
        if (line.empty()) continue;
        const auto a = line.find('|');
        const auto b = a == std::string::npos ? std::string::npos : line.find('|', a + 1);
        if (a == std::string::npos || b == std::string::npos ||
            line.find('|', b + 1) != std::string::npos) return std::nullopt;
        const std::string id = line.substr(0, a);
        if (!catalog_safe_profile_id(id)) return std::nullopt;
        unsigned rider = 0;
        const std::string_view rider_text =
            std::string_view(line).substr(a + 1, b - a - 1);
        if (rider_text.empty()) return std::nullopt;
        const auto parsed = std::from_chars(
            rider_text.data(),
            rider_text.data() + rider_text.size(),
            rider);
        if (parsed.ec != std::errc{} ||
            parsed.ptr != rider_text.data() + rider_text.size()) {
            return std::nullopt;
        }
        const auto name = unescape_field(std::string_view(line).substr(b + 1));
        if (!name || rider >= 16) return std::nullopt;
        HostProfileCatalogEntry entry{id, {*name, static_cast<std::uint8_t>(rider)}};
        if (!valid_racer_identity(entry.identity)) return std::nullopt;
        const std::string canonical_id = canonical_profile_id(id);
        for (const auto& prior : out) {
            if (canonical_profile_id(prior.profile_id) == canonical_id) {
                return std::nullopt;
            }
        }
        out.push_back(std::move(entry));
    }
    return out;
}

bool save_host_profile_catalog_file(
    const std::string& path,
    const std::vector<HostProfileCatalogEntry>& entries) {
    const std::string encoded = encode_host_profile_catalog(entries);
    if (path.empty() || encoded.empty() ||
        encoded.size() > kMaxCatalogBytes) return false;

    // Malformed persisted metadata is read-only. Never "recover" by
    // overwriting it with an apparently empty in-memory catalog.
    std::error_code exists_ec;
    if (std::filesystem::exists(path, exists_ec)) {
        if (exists_ec) return false;
        // A corrupted or interrupted upgrade can leave an oversized
        // catalog. Validate the byte ceiling BEFORE reading it; the save
        // path must not allocate unbounded memory while checking whether
        // it is safe to overwrite legacy metadata.
        std::error_code size_ec;
        const auto size = std::filesystem::file_size(path, size_ec);
        if (size_ec || size > kMaxCatalogBytes) return false;
        std::ifstream existing(path, std::ios::binary);
        if (!existing) return false;
        // The original code streamed rdbuf() into an unbounded ostringstream.
        // Bounded read remains safe if another process grows the file after
        // the size preflight and before the stream is opened.
        std::string prior(static_cast<std::size_t>(kMaxCatalogBytes) + 1u, '\0');
        existing.read(prior.data(), static_cast<std::streamsize>(prior.size()));
        const auto count = existing.gcount();
        if (count < 0 ||
            static_cast<std::uintmax_t>(count) > kMaxCatalogBytes ||
            (!existing.eof() && existing.fail())) {
            return false;
        }
        prior.resize(static_cast<std::size_t>(count));
        if (!decode_host_profile_catalog(prior)) return false;
    } else if (exists_ec) {
        return false;
    }

    return write_host_replace_staged(path, encoded, "urcatalog");
}

std::optional<std::vector<HostProfileCatalogEntry>> load_host_profile_catalog_file(
    const std::string& path) {
    if (path.empty()) return std::nullopt;
    std::error_code exists_ec;
    const bool exists = std::filesystem::exists(path, exists_ec);
    if (exists_ec) return std::nullopt;
    if (!exists) return std::vector<HostProfileCatalogEntry>{};

    std::ifstream in(path, std::ios::binary);
    if (!in) return std::nullopt;
    std::error_code size_ec;
    const auto size = std::filesystem::file_size(path, size_ec);
    if (size_ec || size > kMaxCatalogBytes) return std::nullopt;
    std::ostringstream data;
    data << in.rdbuf();
    if (!in.good() && !in.eof()) return std::nullopt;
    return decode_host_profile_catalog(data.str());
}

std::string make_profile_id(
    std::string_view racer_name,
    const std::vector<HostProfileCatalogEntry>& existing) {
    std::string base;
    for (unsigned char ch : racer_name) {
        if (std::isalnum(ch)) base += static_cast<char>(std::tolower(ch));
        else if (!base.empty() && base.back() != '-') base += '-';
    }
    while (!base.empty() && base.back() == '-') base.pop_back();
    if (base.empty()) base = "racer";
    if (base.size() > 40) base.resize(40);
    while (!base.empty() && base.back() == '-') base.pop_back();
    if (base.empty()) base = "racer";
    if (!is_safe_profile_storage_id(base)) base = "racer-" + base;
    auto used = [&](std::string_view id) {
        const std::string canonical_id = canonical_profile_id(id);
        for (const auto& e : existing) {
            if (canonical_profile_id(e.profile_id) == canonical_id) return true;
        }
        return false;
    };
    if (!used(base)) return base;
    for (unsigned n = 2; n < 10000; ++n) {
        const std::string candidate = base + "-" + std::to_string(n);
        if (!used(candidate)) return candidate;
    }
    return {};
}

bool catalog_entry_matches_profile_state(
    const HostProfileCatalogEntry& entry,
    const HostProfileState& state) noexcept {
    return entry.profile_id == state.profile_id &&
           state.racer_identity.has_value() &&
           entry.identity == *state.racer_identity;
}

bool profile_catalog_authorizes_state(
    const std::vector<HostProfileCatalogEntry>& entries,
    const HostProfileState& state) noexcept {
    if (!state.racer_identity || !state.stock_sram ||
        !valid_racer_identity(*state.racer_identity)) {
        return false;
    }
    for (const auto& entry : entries) {
        if (catalog_entry_matches_profile_state(entry, state)) {
            return true;
        }
    }
    return false;
}

}  // namespace ur::product
