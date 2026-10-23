#pragma once

// Crash-only intent around the ORIGINAL native RtlWriteSram -> Modern typed
// checkpoint boundary. Not a second authoritative save store. The journal
// contains the exact old/new canonical typed snapshots authorized under
// selector -> roster -> profile locks BEFORE the real guest SRAM write.
// Replay admits only old/old, new/old or new/new exact-byte states. Anything
// else (including a missing/corrupt typed sidecar) remains untouched and is
// explicitly recoverable only through a separate user decision.
#include "baldosa_native_profile_sram_checkpoint.hpp"
#include "baldosa_native_profile_path_guard.hpp"
#include "local_tournament_atomic_replace.hpp"

#include <charconv>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <limits>
#include <string>
#include <string_view>

namespace ur::product {

enum class BaldosaSramIntentStatus {
    NoIntent,       // no changed guest SRAM, or no pending transaction
    Prepared,       // durable pre-write intent, native write may begin
    Cleared,        // raw/typed old: archive exact uncommitted guest intent before retirement
    Reconciled,     // raw/typed new: typed publication complete or replayed
    Rejected,       // uncertain or corrupt state: preserve EVERYTHING
    IoError,
};

inline std::filesystem::path baldosa_sram_intent_path(
    const std::filesystem::path& profile_root) {
    return profile_root / "native-sram-checkpoint.pending";
}

inline bool baldosa_sram_entry_missing(const std::filesystem::path& path) {
    std::error_code ec;
    const auto st = std::filesystem::symlink_status(path, ec);
    return st.type() == std::filesystem::file_type::not_found &&
           (!ec || ec == std::errc::no_such_file_or_directory);
}

struct BaldosaSramIntent {
    HostProfileState previous;
    HostProfileState next;
    std::string exact_bytes;
};

inline std::string encode_baldosa_sram_intent(
    const HostProfileState& previous, const HostProfileState& next) {
    const std::string a = encode_host_profile_state(previous);
    const std::string b = encode_host_profile_state(next);
    if (a.empty() || b.empty()) return {};
    return "UR-BALDOSA-NATIVE-SRAM-INTENT/1\n" +
           std::to_string(a.size()) + "\n" +
           std::to_string(b.size()) + "\n" + a + b;
}

inline std::optional<BaldosaSramIntent> decode_baldosa_sram_intent(
    const std::string& encoded, std::string_view required_id) {
    constexpr std::string_view marker = "UR-BALDOSA-NATIVE-SRAM-INTENT/1\n";
    if (encoded.size() > 100000 ||
        encoded.compare(0, marker.size(), marker) != 0) return std::nullopt;
    std::size_t pos = marker.size();
    const auto length = [&](std::size_t& out) -> bool {
        const auto end = encoded.find('\n', pos);
        if (end == std::string::npos || end == pos || end - pos > 8)
            return false;
        const char* first = encoded.data() + pos;
        const char* last = encoded.data() + end;
        const auto parsed = std::from_chars(first, last, out);
        if (parsed.ec != std::errc{} || parsed.ptr != last ||
            out == 0 || out > 45000) return false;
        pos = end + 1;
        return true;
    };
    std::size_t old_size = 0, next_size = 0;
    if (!length(old_size) || !length(next_size) ||
        pos > encoded.size() || old_size > encoded.size() - pos ||
        next_size != encoded.size() - pos - old_size)
        return std::nullopt;
    const auto old_text = encoded.substr(pos, old_size);
    const auto next_text = encoded.substr(pos + old_size, next_size);
    const auto old = decode_host_profile_state(old_text);
    const auto next = decode_host_profile_state(next_text);
    if (!old || !next ||
        old.state->profile_id != required_id ||
        next.state->profile_id != required_id ||
        !old.state->stock_sram || !next.state->stock_sram ||
        !old.state->racer_identity || !next.state->racer_identity ||
        encode_host_profile_state(*old.state) != old_text ||
        encode_host_profile_state(*next.state) != next_text)
        return std::nullopt;
    auto expected_next = *old.state;
    if (capture_stock_sram_for_profile(
            ExecutionMode::Modern, expected_next,
            next.state->stock_sram->data(), kStockSramBytes) !=
            HostProfileTransferStatus::Applied ||
        !(expected_next == *next.state) ||
        *old.state->stock_sram == *next.state->stock_sram)
        return std::nullopt;
    return BaldosaSramIntent{*old.state, *next.state, encoded};
}

inline std::optional<BaldosaSramIntent> read_baldosa_sram_intent(
    const std::filesystem::path& path, std::string_view id) {
    namespace fs = std::filesystem;
    std::error_code ec;
    const auto st = fs::symlink_status(path, ec);
    if (ec || !fs::is_regular_file(st) || fs::is_symlink(st) ||
        fs::file_size(path, ec) > 100000 || ec)
        return std::nullopt;
    std::ifstream in(path, std::ios::binary);
    if (!in) return std::nullopt;
    std::string content{std::istreambuf_iterator<char>(in),
                        std::istreambuf_iterator<char>()};
    if (in.bad()) return std::nullopt;
    return decode_baldosa_sram_intent(content, id);
}

// Caller holds all canonical locks and has already performed preflight and
// raw == previous exact-byte comparison. Refuse a leftover journal even if
// nominally redundant; only the cold restart reconciler may retire it.
inline BaldosaSramIntentStatus prepare_baldosa_sram_intent_under_lock(
    const BaldosaSramCheckpoint& request) {
    if (baldosa_sram_checkpoint_preflight_under_lock(request))
        return BaldosaSramIntentStatus::Rejected;
    const auto location = resolve_host_profile_save_root(
        ExecutionMode::Modern, request.expected_profile.profile_id);
    if (!location.isolated() ||
        !baldosa_native_selected_profile_paths_are_real(
            request.user_root, location.save_root) ||
        !baldosa_sram_file_matches_exact(
            request.user_root / location.save_root / "save.srm",
            request.expected_profile.stock_sram->data(), kStockSramBytes))
        return BaldosaSramIntentStatus::Rejected;
    const auto path = baldosa_sram_intent_path(
        request.user_root / location.save_root);
    if (!baldosa_sram_entry_missing(path))
        return BaldosaSramIntentStatus::Rejected;
    if (std::equal(request.expected_profile.stock_sram->begin(),
                   request.expected_profile.stock_sram->end(),
                   request.guest_sram))
        return BaldosaSramIntentStatus::NoIntent;
    auto next = request.expected_profile;
    if (capture_stock_sram_for_profile(
            ExecutionMode::Modern, next, request.guest_sram,
            request.guest_sram_size) != HostProfileTransferStatus::Applied)
        return BaldosaSramIntentStatus::Rejected;
    const std::string intent =
        encode_baldosa_sram_intent(request.expected_profile, next);
    if (!decode_baldosa_sram_intent(
            intent, request.expected_profile.profile_id) ||
        !write_host_create_staged_native(path, intent, "sram-intent"))
        return BaldosaSramIntentStatus::IoError;
    return BaldosaSramIntentStatus::Prepared;
}

// After a successful native write and typed checkpoint, discard only OUR
// exact intent. A failed remove leaves a harmless new/new intent which the
// restart reconciler can archive and retire. No rollback after typed commit.
inline bool finish_baldosa_sram_intent_under_lock(
    const BaldosaSramCheckpoint& request) {
    const auto location = resolve_host_profile_save_root(
        ExecutionMode::Modern, request.expected_profile.profile_id);
    if (!location.isolated()) return false;
    const auto path = baldosa_sram_intent_path(
        request.user_root / location.save_root);
    if (baldosa_sram_entry_missing(path)) {
        return std::equal(request.expected_profile.stock_sram->begin(),
                          request.expected_profile.stock_sram->end(),
                          request.guest_sram);
    }
    const auto intent = read_baldosa_sram_intent(
        path, request.expected_profile.profile_id);
    if (!intent || !(intent->previous == request.expected_profile) ||
        !std::equal(intent->next.stock_sram->begin(),
                    intent->next.stock_sram->end(), request.guest_sram))
        return false;
    std::error_code ec;
    return std::filesystem::remove(path, ec) && !ec;
}

// Archive exact old/new snapshots BEFORE repair; never silently discard a
// newer raw image or the last committed typed state. This read-only receipt
// has NO load authority. Stable generation-based name makes retries idempotent.
inline bool archive_baldosa_recovered_intent(
    const std::filesystem::path& profile_root,
    const BaldosaSramIntent& intent,
    bool uncommitted_prewrite_only = false) {
    // Distinguish repeated attempts after an explicit rollback: both may
    // target the same generation but legitimately contain different guest
    // SRAM. Never overwrite an earlier archive or block a second good save.
    std::uint64_t hash = 14695981039346656037ull;
    for (unsigned char byte : intent.exact_bytes) {
        hash ^= byte;
        hash *= 1099511628211ull;
    }
    constexpr char hex[] = "0123456789abcdef";
    std::string digest(16, '0');
    for (int i = 15; i >= 0; --i) {
        digest[static_cast<std::size_t>(i)] = hex[hash & 15u];
        hash >>= 4u;
    }
    const auto path = profile_root /
        ((uncommitted_prewrite_only
              ? "native-sram-uncommitted-"
              : "native-sram-recovered-") +
         std::to_string(intent.previous.autosave_generation) + "-to-" +
         std::to_string(intent.next.autosave_generation) + "-" +
         digest + ".txt");
    if (!baldosa_sram_entry_missing(path)) {
        std::error_code ec;
        if (!std::filesystem::is_regular_file(path, ec) || ec ||
            std::filesystem::is_symlink(path, ec) || ec ||
            std::filesystem::file_size(path, ec) != intent.exact_bytes.size() ||
            ec) return false;
        std::ifstream in(path, std::ios::binary);
        return in && std::string(std::istreambuf_iterator<char>(in),
                                 std::istreambuf_iterator<char>()) ==
                         intent.exact_bytes && !in.bad();
    }
    return write_host_create_staged_native(
        path, intent.exact_bytes, "sram-recovered");
}

// Called BEFORE first guest frame, on selected named profile, with exactly
// selector -> catalog -> profile locks. Mismatched bytes without a valid
// intent are never promoted. No Records publishing, fake medals or guest IO.
inline BaldosaSramIntentStatus recover_baldosa_sram_intent_on_cold_boot(
    const std::filesystem::path& user_root, std::string_view profile_id) {
    namespace fs = std::filesystem;
    if (!user_root.is_absolute() ||
        !baldosa_native_real_directory(user_root) ||
        !is_safe_profile_storage_id(profile_id))
        return BaldosaSramIntentStatus::Rejected;
    const auto location = resolve_host_profile_save_root(
        ExecutionMode::Modern, std::string(profile_id));
    if (!location.isolated() ||
        !baldosa_native_selected_profile_paths_are_real(
            user_root, location.save_root))
        return BaldosaSramIntentStatus::Rejected;
    const fs::path root = user_root / location.save_root;
    const fs::path pending = baldosa_sram_intent_path(root);
    if (baldosa_sram_entry_missing(pending))
        return BaldosaSramIntentStatus::NoIntent;
    const fs::path selector = user_root / "host-state-v1.txt";
    const fs::path catalog = user_root / "profiles-v1.txt";
    const fs::path typed = root / "host-profile.txt";
    TournamentLaunchPathLock selector_lock(selector, true);
    if (!selector_lock.acquired()) return BaldosaSramIntentStatus::IoError;
    TournamentLaunchPathLock catalog_lock(catalog, true);
    if (!catalog_lock.acquired()) return BaldosaSramIntentStatus::IoError;
    TournamentLaunchPathLock profile_lock(typed, true);
    if (!profile_lock.acquired()) return BaldosaSramIntentStatus::IoError;

    const auto current_global = load_host_product_state_file(selector.u8string());
    const auto roster = load_host_profile_catalog_file(catalog.u8string());
    const auto current = load_host_profile_state_file(
        ExecutionMode::Modern, typed.u8string(), profile_id);
    const auto intent = read_baldosa_sram_intent(pending, profile_id);
    if (!baldosa_native_selected_profile_paths_are_real(
            user_root, location.save_root) ||
        !current_global.loaded() || !current_global.state->active_profile_id ||
        *current_global.state->active_profile_id != profile_id ||
        !roster || !current.loaded() || !intent ||
        !profile_catalog_authorizes_state(*roster, intent->previous) ||
        !profile_catalog_authorizes_state(*roster, intent->next) ||
        (!( *current.state == intent->previous) &&
         !( *current.state == intent->next)))
        return BaldosaSramIntentStatus::Rejected;

    const bool raw_old = baldosa_sram_file_matches_exact(
        root / "save.srm", intent->previous.stock_sram->data(), kStockSramBytes);
    const bool raw_new = baldosa_sram_file_matches_exact(
        root / "save.srm", intent->next.stock_sram->data(), kStockSramBytes);
    const bool typed_old = *current.state == intent->previous;
    const bool typed_new = *current.state == intent->next;
    if (!((raw_old && typed_old) || (raw_new && (typed_old || typed_new))))
        return BaldosaSramIntentStatus::Rejected;

    // Crash after durable intent but before RtlWriteSram: canonical raw and
    // typed are both OLD, but the exact journal is the *only durable copy*
    // of guest-authored NEW SRAM. Do not promote it as a completed save.
    // Equally, do not discard it merely because native raw was never written.
    // The immutable forensic archive has NO replay authority and is marked
    // uncommitted to distinguish this cut from authenticated new/raw replay.
    // If archive creation, validation or final unlink fails, preserve the
    // pending intent and refuse the cold guest instead of losing evidence.
    if (raw_old && typed_old) {
        if (!archive_baldosa_recovered_intent(root, *intent, true))
            return BaldosaSramIntentStatus::IoError;
        std::error_code ec;
        return fs::remove(pending, ec) && !ec
            ? BaldosaSramIntentStatus::Cleared
            : BaldosaSramIntentStatus::IoError;
    }

    // Persist an exact, inspectable copy of both typed snapshots before
    // any cross-file reconciliation. Archive failures must leave data intact.
    if (!archive_baldosa_recovered_intent(root, *intent))
        return BaldosaSramIntentStatus::IoError;
    if (typed_old &&
        save_host_profile_state_file_if_current_under_lock(
            ExecutionMode::Modern, typed.u8string(),
            intent->previous, intent->next) != HostProfileSaveStatus::Saved)
        return BaldosaSramIntentStatus::IoError;
    std::error_code ec;
    return fs::remove(pending, ec) && !ec
        ? BaldosaSramIntentStatus::Reconciled
        : BaldosaSramIntentStatus::IoError;
}

} // namespace ur::product
