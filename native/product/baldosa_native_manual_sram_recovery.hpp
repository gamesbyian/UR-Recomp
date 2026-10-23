#pragma once

// Explicit post-crash choice for historical saves WITHOUT a trustworthy
// native pre-write intent, or with an untrusted malformed pending intent.
// This is never invoked by automatic guest boot. An untrusted intent may be
// archived then retired only after the player explicitly restores the still-
// authenticated committed typed SRAM; never promote its claimed newer raw.
// Archive exact committed typed bytes and original raw bytes BEFORE changing
// either canonical authority. User must choose the source of truth. This
// archive is evidence only and will NEVER be loaded as a second save store.
#include "baldosa_native_sram_recovery.hpp"
#include "clean_stock_sram.hpp"

#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <string_view>
#include <utility>

namespace ur::product {

enum class BaldosaManualSramChoice {
    TrustGuestRaw,       // explicit user decision: promote real-format raw
    RestoreCommitted,    // explicit user decision: restore last typed SRAM
};

enum class BaldosaManualSramRecoveryStatus {
    RestoredRaw,
    RestoredCommitted,
    AlreadyConsistent,
    Rejected,
    BusyOrIoError,
};

inline std::string baldosa_manual_sram_hex64(std::uint64_t n) {
    constexpr char digits[] = "0123456789abcdef";
    std::string s(16, '0');
    for (int i = 15; i >= 0; --i) {
        s[static_cast<std::size_t>(i)] = digits[n & 15u];
        n >>= 4u;
    }
    return s;
}

inline bool archive_baldosa_manual_sram_choice(
    const std::filesystem::path& root,
    const HostProfileState& committed,
    std::string_view exact_typed_bytes,
    bool raw_present,
    std::string_view raw_bytes) {
    namespace fs = std::filesystem;
    // The typed loader legitimately accepts some text-equivalent forms,
    // including empty lines and reordered fields. Never silently archive a
    // freshly ENCODED substitute for the player's exact original file.
    const auto decoded = decode_host_profile_state(exact_typed_bytes);
    if (!decoded || !(*decoded.state == committed) ||
        exact_typed_bytes.empty() ||
        exact_typed_bytes.size() > kStockSramBytes * 2 + 1024 ||
        raw_bytes.size() > kStockSramBytes)
        return false;
    // Framed raw bytes are binary; no line ending, UTF conversion or text
    // parsing must alter an opaque guest image.
    const std::string bytes =
        "UR-BALDOSA-MANUAL-SRAM-RECOVERY/1\n" +
        std::to_string(exact_typed_bytes.size()) + "\n" +
        std::to_string(raw_present ? 1 : 0) + "\n" +
        std::to_string(raw_bytes.size()) + "\n" +
        std::string(exact_typed_bytes) + std::string(raw_bytes);
    std::uint64_t fnv = 14695981039346656037ull;
    for (unsigned char ch : bytes) {
        fnv ^= ch;
        fnv *= 1099511628211ull;
    }
    const auto archive = root /
        ("native-sram-manual-archive-" +
         std::to_string(committed.autosave_generation) + "-" +
         baldosa_manual_sram_hex64(fnv) + ".bin");
    if (!baldosa_sram_entry_missing(archive)) {
        std::error_code ec;
        if (fs::is_symlink(archive, ec) || ec ||
            !fs::is_regular_file(archive, ec) || ec ||
            fs::file_size(archive, ec) != bytes.size() || ec)
            return false;
        std::ifstream in(archive, std::ios::binary);
        return in &&
            std::string(std::istreambuf_iterator<char>(in),
                        std::istreambuf_iterator<char>()) == bytes &&
            !in.bad();
    }
    return write_host_create_staged_native(archive, bytes, "manual-archive");
}

// A malformed pending transaction has NO replay authority. An explicit
// RestoreCommitted decision may preserve its exact bytes as an immutable
// forensic receipt before restoring validated typed SRAM and retiring it.
// Empty and non-UTF8 inputs are framed as opaque bytes, never interpreted.
inline bool archive_baldosa_untrusted_sram_intent(
    const std::filesystem::path& root,
    const HostProfileState& committed,
    std::string_view untrusted_bytes) {
    namespace fs = std::filesystem;
    if (untrusted_bytes.size() > 100000) return false;
    const std::string framed =
        "UR-BALDOSA-UNTRUSTED-SRAM-INTENT/1\n" +
        std::to_string(untrusted_bytes.size()) + "\n" +
        std::string(untrusted_bytes);
    std::uint64_t fnv = 14695981039346656037ull;
    for (unsigned char ch : framed) {
        fnv ^= ch;
        fnv *= 1099511628211ull;
    }
    const auto archive = root /
        ("native-sram-untrusted-intent-" +
         std::to_string(committed.autosave_generation) + "-" +
         baldosa_manual_sram_hex64(fnv) + ".bin");
    if (!baldosa_sram_entry_missing(archive)) {
        std::error_code ec;
        if (fs::is_symlink(archive, ec) || ec ||
            !fs::is_regular_file(archive, ec) || ec ||
            fs::file_size(archive, ec) != framed.size() || ec)
            return false;
        std::ifstream in(archive, std::ios::binary);
        return in &&
            std::string(std::istreambuf_iterator<char>(in),
                        std::istreambuf_iterator<char>()) == framed &&
            !in.bad();
    }
    return write_host_create_staged_native(
        archive, framed, "untrusted-sram-intent");
}

inline BaldosaManualSramRecoveryStatus recover_baldosa_legacy_sram_explicit(
    const std::filesystem::path& user_root,
    std::string_view expected_active,
    BaldosaManualSramChoice choice) {
    namespace fs = std::filesystem;
    using Status = BaldosaManualSramRecoveryStatus;
    if (!user_root.is_absolute() ||
        !baldosa_native_real_directory(user_root) ||
        !is_safe_profile_storage_id(expected_active))
        return Status::Rejected;
    const auto location = resolve_host_profile_save_root(
        ExecutionMode::Modern, std::string(expected_active));
    if (!location.isolated() ||
        !baldosa_native_real_directory(user_root / "saves") ||
        !baldosa_native_real_directory(user_root / location.save_root))
        return Status::Rejected;
    const auto root = user_root / location.save_root;
    const auto selector = user_root / "host-state-v1.txt";
    const auto catalog = user_root / "profiles-v1.txt";
    const auto typed = root / "host-profile.txt";
    const auto raw = root / "save.srm";
    const auto pending = baldosa_sram_intent_path(root);
    if (!baldosa_native_real_file(selector) ||
        !baldosa_native_real_file(catalog) ||
        !baldosa_native_real_file(typed))
        return Status::Rejected;
    TournamentLaunchPathLock selector_lock(selector, true);
    if (!selector_lock.acquired()) return Status::BusyOrIoError;
    TournamentLaunchPathLock catalog_lock(catalog, true);
    if (!catalog_lock.acquired()) return Status::BusyOrIoError;
    TournamentLaunchPathLock typed_lock(typed, true);
    if (!typed_lock.acquired()) return Status::BusyOrIoError;

    const bool has_pending = !baldosa_sram_entry_missing(pending);
    const auto global = load_host_product_state_file(selector.u8string());
    const auto roster = load_host_profile_catalog_file(catalog.u8string());
    const auto profile = load_host_profile_state_file(
        ExecutionMode::Modern, typed.u8string(), expected_active);
    if (!global.loaded() || !global.state->active_profile_id ||
        *global.state->active_profile_id != expected_active ||
        !roster || !profile.loaded() ||
        !profile_catalog_authorizes_state(*roster, *profile.state) ||
        !profile.state->stock_sram ||
        !stock_sram_format_signature_present(
            profile.state->stock_sram->data(), kStockSramBytes))
        return Status::Rejected;

    // A partial original native write is unknowable; an explicit rollback
    // to the still-committed typed SRAM is safe ONLY when a canonical
    // validated pending intent names that exact previous profile. Preserve
    // the intent and interrupted raw independently before any replacement.
    std::optional<BaldosaSramIntent> interrupted;
    std::optional<std::string> untrusted_pending;
    if (has_pending) {
        if (choice != BaldosaManualSramChoice::RestoreCommitted)
            return Status::Rejected;
        interrupted = read_baldosa_sram_intent(pending, expected_active);
        if (interrupted) {
            // A valid intent that names a DIFFERENT typed generation is a
            // live authority conflict, not a malformed framing to discard.
            if (!(interrupted->previous == *profile.state) ||
                !profile_catalog_authorizes_state(*roster, interrupted->next))
                return Status::Rejected;
        } else {
            // No symlinks, directories, or oversized paths. Preserve exact
            // opaque bytes even for empty, truncated or damaged framing.
            std::error_code pending_ec;
            const auto pending_st = fs::symlink_status(pending, pending_ec);
            if (pending_ec || !fs::is_regular_file(pending_st) ||
                fs::is_symlink(pending_st))
                return Status::Rejected;
            const auto size = fs::file_size(pending, pending_ec);
            if (pending_ec || size > 100000) return Status::Rejected;
            std::ifstream input(pending, std::ios::binary);
            if (!input) return Status::BusyOrIoError;
            std::string data{std::istreambuf_iterator<char>(input),
                             std::istreambuf_iterator<char>()};
            if (input.bad() || data.size() != size)
                return Status::BusyOrIoError;
            untrusted_pending = std::move(data);
        }
    }

    // Absent raw may be recreated only by an explicit RestoreCommitted
    // decision. Short/opaque raw is still archived byte-for-byte. A symlink,
    // redirect or oversized file is never followed or overwritten.
    std::error_code ec;
    const auto st = fs::symlink_status(raw, ec);
    const bool absent = st.type() == fs::file_type::not_found &&
        (!ec || ec == std::errc::no_such_file_or_directory);
    if (!absent && (ec || !fs::is_regular_file(st) ||
                    fs::is_symlink(st)))
        return Status::Rejected;
    std::string raw_bytes;
    if (!absent) {
        const auto size = fs::file_size(raw, ec);
        if (ec || size > kStockSramBytes) return Status::Rejected;
        std::ifstream in(raw, std::ios::binary);
        if (!in) return Status::BusyOrIoError;
        raw_bytes.assign(std::istreambuf_iterator<char>(in),
                         std::istreambuf_iterator<char>());
        if (in.bad() || raw_bytes.size() != size)
            return Status::BusyOrIoError;
    }
    if (!has_pending && !absent && raw_bytes.size() == kStockSramBytes &&
        baldosa_sram_file_matches_exact(
            raw, profile.state->stock_sram->data(), kStockSramBytes))
        return Status::AlreadyConsistent;
    if (choice == BaldosaManualSramChoice::TrustGuestRaw &&
        (absent || raw_bytes.size() != kStockSramBytes ||
         !stock_sram_format_signature_present(
             reinterpret_cast<const std::uint8_t*>(raw_bytes.data()),
             raw_bytes.size())))
        return Status::Rejected;

    // Do not turn unknown raw into a supposedly earned medal or record.
    // Archive the ORIGINAL committed typed FILE bytes, not their decoded
    // re-encoding: even valid legacy/whitespace variants must be restorable
    // from the exact forensic receipt. Reject a changed/unreadable file.
    std::error_code typed_error;
    const auto typed_size = fs::file_size(typed, typed_error);
    if (typed_error || typed_size == 0 ||
        typed_size > kStockSramBytes * 2 + 1024)
        return Status::BusyOrIoError;
    std::string exact_typed_bytes;
    {
        // On Windows the ordinary ifstream handle does not share DELETE.
        // It MUST close before the typed CAS below atomically replaces this
        // same file. Keep no original typed file handle across publication.
        std::ifstream typed_in(typed, std::ios::binary);
        if (!typed_in) return Status::BusyOrIoError;
        exact_typed_bytes.assign(std::istreambuf_iterator<char>(typed_in),
                                 std::istreambuf_iterator<char>());
        if (typed_in.bad() || exact_typed_bytes.size() != typed_size)
            return Status::BusyOrIoError;
    }
    if (!archive_baldosa_manual_sram_choice(
            root, *profile.state, exact_typed_bytes, !absent, raw_bytes))
        return Status::BusyOrIoError;
    if (interrupted && !archive_baldosa_recovered_intent(
                           root, *interrupted))
        return Status::BusyOrIoError;
    if (untrusted_pending && !archive_baldosa_untrusted_sram_intent(
                                 root, *profile.state, *untrusted_pending))
        return Status::BusyOrIoError;

    if (choice == BaldosaManualSramChoice::RestoreCommitted) {
        const auto& known = *profile.state->stock_sram;
        const std::string bytes(
            reinterpret_cast<const char*>(known.data()), known.size());
        if (!write_host_replace_staged(raw, bytes, "restore-sram") ||
            !baldosa_sram_file_matches_exact(raw, known.data(), known.size()))
            return Status::BusyOrIoError;
        if (has_pending) {
            // Original raw and any valid OR untrusted pending bytes were
            // archived before the canonical committed pair was restored.
            // Retire only this selected profile's pending path under locks.
            std::error_code remove_error;
            if (!fs::remove(pending, remove_error) || remove_error)
                return Status::BusyOrIoError;
        }
        return Status::RestoredCommitted;
    }

    auto next = *profile.state;
    if (capture_stock_sram_for_profile(
            ExecutionMode::Modern, next,
            reinterpret_cast<const std::uint8_t*>(raw_bytes.data()),
            raw_bytes.size()) != HostProfileTransferStatus::Applied)
        return Status::Rejected;
    if (save_host_profile_state_file_if_current_under_lock(
            ExecutionMode::Modern, typed.u8string(), *profile.state, next) !=
        HostProfileSaveStatus::Saved)
        return Status::BusyOrIoError;
    return Status::RestoredRaw;
}

} // namespace ur::product
