// Host-layer containment for malformed Modern-profile stock-SRAM mirrors.
//
// Classes mirror tools/probe_malformed_sram_containment.py (guest boot
// evidence: analysis/generated/malformed-sram-containment.json):
//   1 wrong size / truncated mirror   -> codec rejects, file preserved, read-only
//   2 medal-checksum mismatch         -> opaque: round-trips and installs exactly
//   3 records-checksum mismatch       -> opaque: round-trips and installs exactly
//   4 out-of-range medal/record bytes -> opaque, but tour resume refuses medal>3
//   5 out-of-range tour flag/play mode-> opaque, tour resume refuses them
//   6 damaged stock format signature  -> install predicate refuses it, because
//                                        the stock boot (80:8C4E) reformats it
#include "clean_stock_sram.hpp"
#include "host_profile_ghost_target.hpp"
#include "host_profile_state.hpp"
#include "host_profile_store.hpp"
#include "uniracers_tour_resume.hpp"

#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <sstream>
#include <string>

using namespace ur::product;

namespace {

#define CHECK(cond)                                                       \
    do {                                                                  \
        if (!(cond)) {                                                    \
            std::fprintf(stderr, "%s:%d: CHECK failed: %s\n", __FILE__,  \
                         __LINE__, #cond);                                \
            std::abort();                                                 \
        }                                                                 \
    } while (0)

using Sram = std::array<std::uint8_t, kStockSramBytes>;

constexpr std::size_t kRecords = 0x0422;
constexpr std::size_t kRecordWords = 150;
constexpr std::size_t kRecordChecksum = 0x054E;
constexpr std::size_t kRecordHolders = 0x0550;
constexpr std::size_t kMedalBlock = 0x05E8;
constexpr std::size_t kMedalWords = 170;
constexpr std::size_t kMedalChecksum = 0x073C;
constexpr std::size_t kMedalMikeCrawler = 0x069C;
constexpr std::size_t kRiderIndex = 0x0748;
constexpr std::size_t kTourFlags = 0x1075;
constexpr std::size_t kPlayMode = 0x10AD;

std::uint16_t word(const Sram& s, std::size_t at) {
    return static_cast<std::uint16_t>(s[at] | (s[at + 1] << 8));
}

void put_word(Sram& s, std::size_t at, std::uint16_t value) {
    s[at] = static_cast<std::uint8_t>(value & 0xffu);
    s[at + 1] = static_cast<std::uint8_t>((value >> 8) & 0xffu);
}

std::uint16_t sum_words(const Sram& s, std::size_t at, std::size_t count) {
    std::uint32_t sum = 0;
    for (std::size_t i = 0; i < count; ++i) sum += word(s, at + 2 * i);
    return static_cast<std::uint16_t>(sum & 0xffffu);
}

void fix_checksums(Sram& s) {
    put_word(s, kMedalChecksum, sum_words(s, kMedalBlock, kMedalWords));
    put_word(s, kRecordChecksum, sum_words(s, kRecords, kRecordWords));
}

bool checksums_valid(const Sram& s) {
    return word(s, kMedalChecksum) == sum_words(s, kMedalBlock, kMedalWords) &&
           word(s, kRecordChecksum) == sum_words(s, kRecords, kRecordWords);
}

Sram progressed_base() {
    Sram s = clean_stock_sram();
    s[kMedalMikeCrawler] = 2;
    put_word(s, kRecords, 3000);
    s[kRecordHolders] = 0;
    fix_checksums(s);
    return s;
}

std::string hex(const std::uint8_t* data, std::size_t size) {
    static constexpr char digits[] = "0123456789abcdef";
    std::string out;
    out.reserve(size * 2);
    for (std::size_t i = 0; i < size; ++i) {
        out.push_back(digits[data[i] >> 4]);
        out.push_back(digits[data[i] & 0x0f]);
    }
    return out;
}

std::string profile_text(const std::string& sram_hex) {
    return "UR-HOST-PROFILE/5\n"
           "profile=malformed.alpha\n"
           "generation=3\n"
           "stock_sram=" + sram_hex + "\n"
           "tour_resume=\n"
           "ghost_target=off\n"
           "racer_name=MIKE\n"
           "racer_index=0\n"
           "recent_track=\n";
}

std::string read_file(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    return std::string(std::istreambuf_iterator<char>(in), {});
}

void write_file(const std::string& path, const std::string& text) {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    out << text;
    CHECK(out.good());
}

// A mirror the codec admits must install byte-for-byte: the generic profile
// layer never repairs or reinterprets guest-owned bytes.
void check_opaque_round_trip(const Sram& image) {
    const auto decoded =
        decode_host_profile_state(profile_text(hex(image.data(), image.size())));
    CHECK(decoded);
    CHECK(decoded.state->stock_sram);
    CHECK(*decoded.state->stock_sram == image);
    const std::string reencoded = encode_host_profile_state(*decoded.state);
    CHECK(reencoded == profile_text(hex(image.data(), image.size())));

    Sram live{};
    live.fill(0x5a);
    CHECK(restore_stock_sram_from_profile(
              ExecutionMode::Modern, *decoded.state, live.data(), live.size()) ==
          HostProfileTransferStatus::Applied);
    CHECK(live == image);
}

void class1_wrong_size(const std::string& dir) {
    const Sram base = progressed_base();
    // Truncated, oversized, odd-length and non-hex mirrors are all rejected.
    CHECK(!decode_host_profile_state(profile_text(hex(base.data(), 4096))));
    std::string over = hex(base.data(), base.size()) + "a5";
    CHECK(!decode_host_profile_state(profile_text(over)));
    std::string odd = hex(base.data(), base.size());
    odd.pop_back();
    CHECK(!decode_host_profile_state(profile_text(odd)));
    std::string bad = hex(base.data(), base.size());
    bad[100] = 'g';
    CHECK(!decode_host_profile_state(profile_text(bad)));

    // A malformed file on disk resolves to a read-only default and is never
    // rewritten by the store or by a profile-owned preference update.
    const std::string path = dir + "/malformed-host-profile.txt";
    const std::string original = profile_text(hex(base.data(), 4096));
    write_file(path, original);
    const auto loaded =
        load_host_profile_state_file(ExecutionMode::Modern, path, "malformed.alpha");
    CHECK(loaded.status == HostProfileLoadStatus::Malformed);
    CHECK(loaded.error == "invalid stock SRAM snapshot");
    auto resolved = resolve_host_profile_state_file(
        ExecutionMode::Modern, path, "malformed.alpha");
    CHECK(resolved.status == HostProfileResolveStatus::DefaultedMalformed);
    CHECK(!host_profile_resolve_writable(resolved.status));
    CHECK(resolved.state && !resolved.state->stock_sram);
    Sram live = clean_stock_sram();
    CHECK(restore_stock_sram_from_profile(
              ExecutionMode::Modern, *resolved.state, live.data(), live.size()) ==
          HostProfileTransferStatus::MissingSnapshot);
    CHECK(live == clean_stock_sram());
    CHECK(update_host_profile_ghost_target(
              ExecutionMode::Modern, path, false, *resolved.state,
              CompletedRunGhostTarget::Previous) ==
          HostProfileGhostTargetUpdateStatus::ReadOnly);
    CHECK(read_file(path) == original);

    // An oversized file is rejected by the bounded reader before decoding.
    const std::string huge_path = dir + "/huge-host-profile.txt";
    const std::string huge =
        profile_text(hex(base.data(), base.size())) + std::string(2048, '\n');
    write_file(huge_path, huge);
    const auto huge_loaded = load_host_profile_state_file(
        ExecutionMode::Modern, huge_path, "malformed.alpha");
    CHECK(huge_loaded.status == HostProfileLoadStatus::Malformed);
    CHECK(read_file(huge_path) == huge);

    // The install predicate itself refuses anything that is not exact 8 KiB.
    CHECK(!stock_sram_format_signature_present(nullptr, kStockSramBytes));
    CHECK(!stock_sram_format_signature_present(base.data(), 4096));
    CHECK(!stock_sram_format_signature_present(base.data(), kStockSramBytes + 1));
    std::puts("MALFORMED_SRAM_HOST class=wrong_size outcome=rejected_read_only_preserved");
}

void class2_3_checksum_mismatch() {
    Sram medal = progressed_base();
    put_word(medal, kMedalChecksum,
             static_cast<std::uint16_t>(word(medal, kMedalChecksum) ^ 1u));
    CHECK(!checksums_valid(medal));
    check_opaque_round_trip(medal);
    CHECK(stock_sram_format_signature_present(medal.data(), medal.size()));

    Sram records = progressed_base();
    put_word(records, kRecordChecksum,
             static_cast<std::uint16_t>(word(records, kRecordChecksum) ^ 1u));
    CHECK(!checksums_valid(records));
    check_opaque_round_trip(records);
    CHECK(stock_sram_format_signature_present(records.data(), records.size()));
    std::puts("MALFORMED_SRAM_HOST class=checksum_mismatch outcome=opaque_installable");
}

void class4_out_of_range_values() {
    Sram s = progressed_base();
    s[kMedalMikeCrawler] = 7;
    put_word(s, kRecords, 0xffff);
    s[kRecordHolders] = 0xff;
    fix_checksums(s);
    CHECK(checksums_valid(s));
    check_opaque_round_trip(s);
    CHECK(stock_sram_format_signature_present(s.data(), s.size()));

    // The title tour-resume layer never projects an out-of-range medal.
    std::array<std::uint8_t, 0x20000> wram{};
    s[kPlayMode] = 1;
    s[kRiderIndex] = 0;
    s[kTourFlags] = 1;
    CHECK(!ur::title::observe_tour_progress(wram.data(), wram.size(), s.data(), s.size()));
    ur::title::TourProgress out_of_range{0, 0, 7, {1, 0, 0, 0, 0}};
    CHECK(!ur::title::valid_unfinished_tour_progress(out_of_range));
    const ur::title::TourProgress resume{0, 0, 2, {1, 0, 0, 0, 0}};
    CHECK(!ur::title::tour_resume_frontend_source_matches_sram(resume, s.data(), s.size()));
    std::puts("MALFORMED_SRAM_HOST class=out_of_range_values outcome=opaque_installable_resume_refused");
}

void class5_tour_flags_and_play_mode() {
    std::array<std::uint8_t, 0x20000> wram{};
    const ur::title::TourProgress resume{0, 0, 2, {1, 1, 0, 0, 0}};

    Sram flags = progressed_base();
    flags[kRiderIndex] = 0;
    flags[kPlayMode] = 1;
    flags[kTourFlags] = 0xff;
    flags[kTourFlags + 1] = 1;
    check_opaque_round_trip(flags);
    CHECK(!ur::title::observe_tour_progress(
        wram.data(), wram.size(), flags.data(), flags.size()));
    CHECK(!ur::title::tour_resume_source_matches_sram(resume, flags.data(), flags.size()));
    const Sram flags_before = flags;
    CHECK(ur::title::apply_tour_resume(resume, wram.data(), wram.size(),
                                       flags.data(), flags.size()) ==
          ur::title::TourResumeApplyStatus::InvalidState);
    CHECK(flags == flags_before);

    Sram mode = progressed_base();
    mode[kRiderIndex] = 0;
    mode[kTourFlags] = 1;
    mode[kTourFlags + 1] = 1;
    mode[kPlayMode] = 0x7f;
    check_opaque_round_trip(mode);
    CHECK(!ur::title::observe_tour_progress(
        wram.data(), wram.size(), mode.data(), mode.size()));
    CHECK(!ur::title::tour_resume_source_matches_sram(resume, mode.data(), mode.size()));
    CHECK(!ur::title::tour_resume_frontend_source_matches_sram(resume, mode.data(), mode.size()));
    // Control: the same bytes with a stock play mode are accepted.
    mode[kPlayMode] = 1;
    CHECK(ur::title::tour_resume_source_matches_sram(resume, mode.data(), mode.size()));
    std::puts("MALFORMED_SRAM_HOST class=tour_flag_play_mode outcome=opaque_installable_resume_refused");
}

void class6_damaged_signature() {
    const Sram clean = clean_stock_sram();
    CHECK(stock_sram_format_signature_present(clean.data(), clean.size()));
    const std::string signature(reinterpret_cast<const char*>(clean.data()),
                                kStockSramFormatSignatureBytes);
    CHECK(signature == std::string("ASJIver3.30\xff", 12));

    for (std::size_t i = 0; i < kStockSramFormatSignatureBytes; ++i) {
        Sram damaged = progressed_base();
        damaged[i] ^= 0x01;
        CHECK(checksums_valid(damaged));
        CHECK(!stock_sram_format_signature_present(damaged.data(), damaged.size()));
        // The codec still preserves it exactly; only the install boundary,
        // which bypasses the guest boot check, refuses it.
        check_opaque_round_trip(damaged);
    }
    // Bytes after the compared prefix are not part of the stock check.
    Sram tail = progressed_base();
    tail[kStockSramFormatSignatureBytes] ^= 0x01;
    CHECK(stock_sram_format_signature_present(tail.data(), tail.size()));
    std::puts("MALFORMED_SRAM_HOST class=damaged_signature outcome=install_refused");
}

}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::fprintf(stderr, "usage: %s <scratch-dir>\n", argv[0]);
        return 2;
    }
    class1_wrong_size(argv[1]);
    class2_3_checksum_mismatch();
    class4_out_of_range_values();
    class5_tour_flags_and_play_mode();
    class6_damaged_signature();
    return 0;
}
