#include "multiplayer_match_record.hpp"

#include <array>
#include <charconv>
#include <cctype>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace ur::product {
namespace {

constexpr std::string_view kMagic = "UR-MULTIPLAYER-MATCH/1";
constexpr std::size_t kChecksumHexSize = 16;
constexpr std::size_t kMaxRecordBytes = 4096;

bool fail(std::string* detail, const char* message) noexcept {
    if (detail) *detail = message;
    return false;
}

bool valid_hex16(std::string_view value) noexcept {
    if (value.size() != kChecksumHexSize) return false;
    for (char ch : value) {
        if (!std::isxdigit(static_cast<unsigned char>(ch))) return false;
    }
    return true;
}

bool parse_course_id(std::string_view value, int* course_index) noexcept {
    if (value.size() != 9u || value.substr(0, 7) != "course:") return false;
    int parsed = 0;
    const auto result =
        std::from_chars(value.data() + 7, value.data() + value.size(), parsed);
    if (result.ec != std::errc{} ||
        result.ptr != value.data() + value.size() ||
        parsed < 1 || parsed > 45) {
        return false;
    }
    *course_index = parsed;
    return true;
}

std::string hex_encode(std::string_view value) {
    static constexpr char digits[] = "0123456789abcdef";
    std::string out;
    out.reserve(value.size() * 2u);
    for (unsigned char ch : value) {
        out.push_back(digits[ch >> 4u]);
        out.push_back(digits[ch & 0x0fu]);
    }
    return out;
}

std::optional<std::string> hex_decode(std::string_view value) {
    if (value.size() % 2u) return std::nullopt;
    auto nibble = [](char ch) -> int {
        if (ch >= '0' && ch <= '9') return ch - '0';
        if (ch >= 'a' && ch <= 'f') return 10 + ch - 'a';
        if (ch >= 'A' && ch <= 'F') return 10 + ch - 'A';
        return -1;
    };
    std::string out;
    out.reserve(value.size() / 2u);
    for (std::size_t i = 0; i < value.size(); i += 2u) {
        const int hi = nibble(value[i]);
        const int lo = nibble(value[i + 1u]);
        if (hi < 0 || lo < 0) return std::nullopt;
        out.push_back(static_cast<char>((hi << 4) | lo));
    }
    return out;
}

template <typename T>
bool parse_unsigned(std::string_view text, T* out) {
    T value{};
    const auto parsed =
        std::from_chars(text.data(), text.data() + text.size(), value);
    if (parsed.ec != std::errc{} ||
        parsed.ptr != text.data() + text.size()) {
        return false;
    }
    *out = value;
    return true;
}

std::uint64_t fnv1a64(std::string_view value) noexcept {
    std::uint64_t hash = 14695981039346656037ull;
    for (unsigned char ch : value) {
        hash ^= ch;
        hash *= 1099511628211ull;
    }
    return hash;
}

std::string hex64(std::uint64_t value) {
    static constexpr char digits[] = "0123456789abcdef";
    std::string out(16, '0');
    for (int i = 15; i >= 0; --i) {
        out[static_cast<std::size_t>(i)] = digits[value & 0x0fu];
        value >>= 4u;
    }
    return out;
}

const char* outcome_name(
    ur::title::OrdinaryTwoPlayerRaceOutcome outcome) noexcept {
    switch (outcome) {
    case ur::title::OrdinaryTwoPlayerRaceOutcome::Draw: return "draw";
    case ur::title::OrdinaryTwoPlayerRaceOutcome::Player1Win: return "p1";
    case ur::title::OrdinaryTwoPlayerRaceOutcome::Player2Win: return "p2";
    }
    return "";
}

std::optional<ur::title::OrdinaryTwoPlayerRaceOutcome> parse_outcome(
    std::string_view value) noexcept {
    if (value == "draw") return ur::title::OrdinaryTwoPlayerRaceOutcome::Draw;
    if (value == "p1") {
        return ur::title::OrdinaryTwoPlayerRaceOutcome::Player1Win;
    }
    if (value == "p2") {
        return ur::title::OrdinaryTwoPlayerRaceOutcome::Player2Win;
    }
    return std::nullopt;
}

ur::title::OrdinaryTwoPlayerRaceOutcome expected_outcome(
    std::uint16_t p1,
    std::uint16_t p2) noexcept {
    const auto no_time = ur::title::kOrdinaryTwoPlayerNoTimeHundredths;
    if (p1 == p2) return ur::title::OrdinaryTwoPlayerRaceOutcome::Draw;
    if (p1 == no_time) {
        return ur::title::OrdinaryTwoPlayerRaceOutcome::Player2Win;
    }
    if (p2 == no_time || p1 < p2) {
        return ur::title::OrdinaryTwoPlayerRaceOutcome::Player1Win;
    }
    return ur::title::OrdinaryTwoPlayerRaceOutcome::Player2Win;
}

void append_profile(
    std::ostringstream& out,
    const char* prefix,
    const HostProfileCatalogEntry& profile) {
    out << prefix << "_profile " << hex_encode(profile.profile_id) << "\n";
    out << prefix << "_name " << hex_encode(profile.identity.name) << "\n";
    out << prefix << "_rider "
        << static_cast<unsigned>(profile.identity.rider_index) << "\n";
}

std::optional<HostProfileCatalogEntry> parse_profile(
    const std::array<std::string, 3>& values) {
    const auto id = hex_decode(values[0]);
    const auto name = hex_decode(values[1]);
    unsigned rider = 0;
    if (!id || id->empty() || !name ||
        !parse_unsigned(values[2], &rider) || rider > 255u) {
        return std::nullopt;
    }
    HostProfileCatalogEntry entry{
        *id,
        HostRacerIdentity{*name, static_cast<std::uint8_t>(rider)},
    };
    if (!valid_racer_identity(entry.identity)) return std::nullopt;
    return entry;
}

}  // namespace

bool validate_multiplayer_match_record(
    const MultiplayerMatchRecord& record,
    std::string* detail) noexcept {
    if (record.schema_version != kMultiplayerMatchRecordSchemaVersion) {
        return fail(detail, "unsupported schema version");
    }
    if (!valid_hex16(record.run_artifact_checksum)) {
        return fail(detail, "invalid run artifact checksum");
    }

    int course_index = 0;
    if (!parse_course_id(record.context.course_id, &course_index)) {
        return fail(detail, "invalid course id");
    }

    const auto rebound = bind_local_multiplayer_match_context(
        record.context.match.result,
        record.context.match.player1,
        record.context.match.player2,
        UrUniracersCourseIdentity{1, course_index});
    if (!rebound.bound() ||
        rebound.context->course_id != record.context.course_id) {
        return fail(detail, "invalid bound match context");
    }

    const auto no_time = ur::title::kOrdinaryTwoPlayerNoTimeHundredths;
    if (record.context.match.result.player1_hundredths > no_time ||
        record.context.match.result.player2_hundredths > no_time) {
        return fail(detail, "invalid race result value");
    }
    if (record.context.match.result.outcome != expected_outcome(
            record.context.match.result.player1_hundredths,
            record.context.match.result.player2_hundredths)) {
        return fail(detail, "outcome does not match result values");
    }
    return true;
}

std::string encode_multiplayer_match_record(
    const MultiplayerMatchRecord& record) {
    std::string detail;
    if (!validate_multiplayer_match_record(record, &detail)) return {};

    std::ostringstream body;
    body << kMagic << "\n";
    body << "run_checksum " << record.run_artifact_checksum << "\n";
    body << "course " << record.context.course_id << "\n";
    body << "outcome "
         << outcome_name(record.context.match.result.outcome) << "\n";
    body << "p1_result "
         << record.context.match.result.player1_hundredths << "\n";
    body << "p2_result "
         << record.context.match.result.player2_hundredths << "\n";
    append_profile(body, "p1", record.context.match.player1);
    append_profile(body, "p2", record.context.match.player2);

    const std::string canonical = body.str();
    return canonical + "checksum " + hex64(fnv1a64(canonical)) + "\n";
}

MultiplayerMatchDecodeResult decode_multiplayer_match_record(
    std::string_view encoded) {
    MultiplayerMatchDecodeResult result;
    std::istringstream input{std::string(encoded)};
    std::vector<std::string> lines;
    for (std::string line; std::getline(input, line);) lines.push_back(line);
    if (lines.size() != 13u || lines[0] != kMagic) {
        result.error = "unexpected multiplayer match shape";
        return result;
    }

    const std::array<std::string_view, 12> keys = {
        "run_checksum ", "course ", "outcome ", "p1_result ", "p2_result ",
        "p1_profile ", "p1_name ", "p1_rider ",
        "p2_profile ", "p2_name ", "p2_rider ", "checksum ",
    };
    std::array<std::string, 12> values{};
    for (std::size_t i = 0; i < keys.size(); ++i) {
        const auto& line = lines[i + 1u];
        if (line.rfind(std::string(keys[i]), 0) != 0) {
            result.error = "unexpected multiplayer match field";
            return result;
        }
        values[i] = line.substr(keys[i].size());
    }

    const auto checksum_line = std::string(encoded).rfind("\nchecksum ");
    if (checksum_line == std::string::npos || !valid_hex16(values[11])) {
        result.error = "invalid metadata checksum";
        return result;
    }
    const std::string_view canonical =
        encoded.substr(0, checksum_line + 1u);
    if (hex64(fnv1a64(canonical)) != values[11]) {
        result.error = "metadata checksum mismatch";
        return result;
    }

    const auto outcome = parse_outcome(values[2]);
    const auto p1 = parse_profile({values[5], values[6], values[7]});
    const auto p2 = parse_profile({values[8], values[9], values[10]});
    unsigned p1_result = 0;
    unsigned p2_result = 0;
    int course_index = 0;
    if (!outcome || !p1 || !p2 ||
        !parse_unsigned(values[3], &p1_result) ||
        !parse_unsigned(values[4], &p2_result) ||
        p1_result > 65535u || p2_result > 65535u ||
        !parse_course_id(values[1], &course_index)) {
        result.error = "invalid match fields";
        return result;
    }

    ur::title::OrdinaryTwoPlayerRaceResult observed;
    observed.player1_rider = p1->identity.rider_index;
    observed.player2_rider = p2->identity.rider_index;
    observed.player1_hundredths = static_cast<std::uint16_t>(p1_result);
    observed.player2_hundredths = static_cast<std::uint16_t>(p2_result);
    observed.outcome = *outcome;

    const auto context = bind_local_multiplayer_match_context(
        observed,
        *p1,
        *p2,
        UrUniracersCourseIdentity{1, course_index});
    if (!context.bound()) {
        result.error = "match context rejected";
        return result;
    }

    MultiplayerMatchRecord record;
    record.run_artifact_checksum = values[0];
    record.context = *context.context;

    std::string detail;
    if (!validate_multiplayer_match_record(record, &detail)) {
        result.error = detail;
        return result;
    }
    result.record = std::move(record);
    return result;
}

std::optional<MultiplayerMatchRecord> make_multiplayer_match_record(
    const CompletedRunRecord& run,
    const BoundOrdinaryTwoPlayerMatchContext& context) noexcept {
    std::string detail;
    if (!validate_completed_run_record(run, &detail) ||
        run.provenance.mode != "race-2p" ||
        context.course_id != run.provenance.course_id) {
        return std::nullopt;
    }

    MultiplayerMatchRecord record;
    record.run_artifact_checksum =
        completed_run_record_artifact_checksum(run);
    record.context = context;
    if (record.run_artifact_checksum.empty() ||
        !validate_multiplayer_match_record(record, &detail)) {
        return std::nullopt;
    }
    return record;
}

bool multiplayer_match_record_matches_run(
    const MultiplayerMatchRecord& record,
    const CompletedRunRecord& run) noexcept {
    std::string detail;
    if (!validate_multiplayer_match_record(record, &detail) ||
        !validate_completed_run_record(run, &detail) ||
        run.provenance.mode != "race-2p") {
        return false;
    }
    return record.run_artifact_checksum ==
               completed_run_record_artifact_checksum(run) &&
           record.context.course_id == run.provenance.course_id;
}

bool save_multiplayer_match_record_file(
    const std::string& path,
    const MultiplayerMatchRecord& record,
    std::string* detail) {
    const std::string encoded = encode_multiplayer_match_record(record);
    if (encoded.empty()) return fail(detail, "match validation failed");
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) return fail(detail, "cannot open match record");
    out.write(encoded.data(), static_cast<std::streamsize>(encoded.size()));
    if (!out) return fail(detail, "cannot write match record");
    return true;
}

MultiplayerMatchDecodeResult load_multiplayer_match_record_file(
    const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return {std::nullopt, "cannot open match record"};

    std::string encoded(kMaxRecordBytes + 1u, '\0');
    in.read(encoded.data(), static_cast<std::streamsize>(encoded.size()));
    const auto count = in.gcount();
    if (count < 0) return {std::nullopt, "cannot read match record"};
    if (static_cast<std::size_t>(count) > kMaxRecordBytes) {
        return {std::nullopt, "match record too large"};
    }
    encoded.resize(static_cast<std::size_t>(count));
    if (!in.eof() && in.fail()) {
        return {std::nullopt, "cannot read match record"};
    }
    return decode_multiplayer_match_record(encoded);
}

std::string multiplayer_match_record_path_for_run(
    std::string_view run_path) {
    if (run_path.empty()) return {};
    return std::string(run_path) + ".urmatch";
}

bool save_multiplayer_match_record_for_run(
    const std::string& run_path,
    const CompletedRunRecord& run,
    const MultiplayerMatchRecord& record,
    std::string* detail) {
    const std::string sidecar =
        multiplayer_match_record_path_for_run(run_path);
    if (sidecar.empty()) return fail(detail, "missing completed-run path");
    if (!multiplayer_match_record_matches_run(record, run)) {
        return fail(detail, "match record does not bind completed run");
    }
    return save_multiplayer_match_record_file(sidecar, record, detail);
}

MultiplayerMatchDecodeResult load_multiplayer_match_record_for_run(
    const std::string& run_path,
    const CompletedRunRecord& run) {
    const std::string sidecar =
        multiplayer_match_record_path_for_run(run_path);
    if (sidecar.empty()) {
        return {std::nullopt, "missing completed-run path"};
    }
    auto loaded = load_multiplayer_match_record_file(sidecar);
    if (!loaded) return loaded;
    if (!multiplayer_match_record_matches_run(*loaded.record, run)) {
        return {std::nullopt, "match record does not bind completed run"};
    }
    return loaded;
}

}  // namespace ur::product
