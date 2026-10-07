#include "multiplayer_match_record.hpp"

#include <array>
#include <charconv>
#include <cctype>
#include <cstdint>
#include <fstream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace ur::product {
namespace {

constexpr std::string_view kMagic = "UR-MULTIPLAYER-MATCH/1";
constexpr std::size_t kChecksumHexSize = 16;
constexpr std::size_t kMaxMatchRecordBytes = 4096;

bool set_error(std::string* detail, const char* message) noexcept {
    if (detail) *detail = message;
    return false;
}

bool valid_run_checksum(std::string_view value) noexcept {
    if (value.size() != kChecksumHexSize) return false;
    for (char ch : value) {
        if (!std::isxdigit(static_cast<unsigned char>(ch))) return false;
    }
    return true;
}

bool valid_course_id(std::string_view value) noexcept {
    if (value.empty() || value.size() > 64) return false;
    for (char ch : value) {
        const auto uch = static_cast<unsigned char>(ch);
        if (!(std::isalnum(uch) || ch == ':' || ch == '-' || ch == '_')) {
            return false;
        }
    }
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
    if ((value.size() & 1u) != 0u) return std::nullopt;
    std::string out;
    out.reserve(value.size() / 2u);
    auto nibble = [](char ch) -> int {
        if (ch >= '0' && ch <= '9') return ch - '0';
        if (ch >= 'a' && ch <= 'f') return 10 + ch - 'a';
        if (ch >= 'A' && ch <= 'F') return 10 + ch - 'A';
        return -1;
    };
    for (std::size_t i = 0; i < value.size(); i += 2u) {
        const int hi = nibble(value[i]);
        const int lo = nibble(value[i + 1u]);
        if (hi < 0 || lo < 0) return std::nullopt;
        out.push_back(static_cast<char>((hi << 4) | lo));
    }
    return out;
}

std::string outcome_name(ur::title::OrdinaryTwoPlayerRaceOutcome outcome) {
    switch (outcome) {
    case ur::title::OrdinaryTwoPlayerRaceOutcome::Draw:
        return "draw";
    case ur::title::OrdinaryTwoPlayerRaceOutcome::Player1Win:
        return "p1";
    case ur::title::OrdinaryTwoPlayerRaceOutcome::Player2Win:
        return "p2";
    }
    return {};
}

std::optional<ur::title::OrdinaryTwoPlayerRaceOutcome> parse_outcome(
    std::string_view value) {
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

template <typename T>
bool parse_unsigned(std::string_view text, T* out) {
    T value{};
    const char* first = text.data();
    const char* last = first + text.size();
    const auto parsed = std::from_chars(first, last, value);
    if (parsed.ec != std::errc{} || parsed.ptr != last) return false;
    *out = value;
    return true;
}

void append_participant(
    std::ostringstream& out,
    const char* prefix,
    const MultiplayerMatchParticipant& participant) {
    out << prefix << "_profile "
        << (participant.profile_id ? hex_encode(*participant.profile_id) : "-")
        << "\n";
    out << prefix << "_name " << hex_encode(participant.racer.name) << "\n";
    out << prefix << "_rider "
        << static_cast<unsigned>(participant.racer.rider_index) << "\n";
}

std::optional<MultiplayerMatchParticipant> parse_participant(
    const std::array<std::string, 3>& values) {
    std::optional<std::string> profile;
    if (values[0] != "-") {
        auto decoded = hex_decode(values[0]);
        if (!decoded || decoded->empty()) return std::nullopt;
        profile = *decoded;
    }
    auto name = hex_decode(values[1]);
    if (!name) return std::nullopt;
    unsigned rider = 0;
    if (!parse_unsigned(values[2], &rider) || rider > 255u) {
        return std::nullopt;
    }
    MultiplayerMatchParticipant participant{
        profile,
        HostRacerIdentity{*name, static_cast<std::uint8_t>(rider)},
    };
    if (!valid_racer_identity(participant.racer)) return std::nullopt;
    return participant;
}

}  // namespace

bool validate_multiplayer_match_record(
    const MultiplayerMatchRecord& record,
    std::string* detail) noexcept {
    if (record.schema_version != kMultiplayerMatchRecordSchemaVersion) {
        return set_error(detail, "unsupported schema version");
    }
    if (!valid_run_checksum(record.run_artifact_checksum)) {
        return set_error(detail, "invalid run artifact checksum");
    }
    if (!valid_course_id(record.match.course_id)) {
        return set_error(detail, "invalid course id");
    }
    if (!valid_racer_identity(record.match.player1.racer) ||
        !valid_racer_identity(record.match.player2.racer)) {
        return set_error(detail, "invalid racer identity");
    }
    if (record.match.player1.racer.rider_index !=
            record.match.result.player1_rider ||
        record.match.player2.racer.rider_index !=
            record.match.result.player2_rider) {
        return set_error(detail, "participant rider mismatch");
    }
    if (record.match.player1.profile_id &&
        record.match.player1.profile_id->empty()) {
        return set_error(detail, "empty player1 profile id");
    }
    if (record.match.player2.profile_id &&
        record.match.player2.profile_id->empty()) {
        return set_error(detail, "empty player2 profile id");
    }
    if (record.match.player1.profile_id &&
        record.match.player2.profile_id &&
        *record.match.player1.profile_id == *record.match.player2.profile_id) {
        return set_error(detail, "duplicate participant profile");
    }
    const auto no_time = ur::title::kOrdinaryTwoPlayerNoTimeHundredths;
    if (record.match.result.player1_hundredths > no_time ||
        record.match.result.player2_hundredths > no_time) {
        return set_error(detail, "invalid race result value");
    }
    if (record.match.result.outcome != expected_outcome(
            record.match.result.player1_hundredths,
            record.match.result.player2_hundredths)) {
        return set_error(detail, "outcome does not match result values");
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
    body << "course " << record.match.course_id << "\n";
    body << "outcome " << outcome_name(record.match.result.outcome) << "\n";
    body << "p1_result " << record.match.result.player1_hundredths << "\n";
    body << "p2_result " << record.match.result.player2_hundredths << "\n";
    append_participant(body, "p1", record.match.player1);
    append_participant(body, "p2", record.match.player2);

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

    const std::size_t checksum_line =
        std::string(encoded).rfind("checksum ");
    if (checksum_line == std::string::npos ||
        !valid_run_checksum(values[11])) {
        result.error = "invalid metadata checksum";
        return result;
    }
    const std::string_view canonical = encoded.substr(0, checksum_line);
    if (hex64(fnv1a64(canonical)) != values[11]) {
        result.error = "metadata checksum mismatch";
        return result;
    }

    auto outcome = parse_outcome(values[2]);
    unsigned p1_result = 0;
    unsigned p2_result = 0;
    if (!outcome ||
        !parse_unsigned(values[3], &p1_result) ||
        !parse_unsigned(values[4], &p2_result) ||
        p1_result > 65535u || p2_result > 65535u) {
        result.error = "invalid result fields";
        return result;
    }

    const auto p1 = parse_participant({values[5], values[6], values[7]});
    const auto p2 = parse_participant({values[8], values[9], values[10]});
    if (!p1 || !p2) {
        result.error = "invalid participant fields";
        return result;
    }

    MultiplayerMatchRecord record;
    record.run_artifact_checksum = values[0];
    record.match.course_id = values[1];
    record.match.result.player1_rider = p1->racer.rider_index;
    record.match.result.player2_rider = p2->racer.rider_index;
    record.match.result.player1_hundredths =
        static_cast<std::uint16_t>(p1_result);
    record.match.result.player2_hundredths =
        static_cast<std::uint16_t>(p2_result);
    record.match.result.outcome = *outcome;
    record.match.player1 = *p1;
    record.match.player2 = *p2;

    std::string detail;
    if (!validate_multiplayer_match_record(record, &detail)) {
        result.error = detail;
        return result;
    }
    result.record = std::move(record);
    return result;
}

bool multiplayer_match_record_matches_run(
    const MultiplayerMatchRecord& record,
    const CompletedRunRecord& run) noexcept {
    std::string detail;
    if (!validate_multiplayer_match_record(record, &detail) ||
        !validate_completed_run_record(run, &detail)) {
        return false;
    }
    return record.run_artifact_checksum ==
               completed_run_record_artifact_checksum(run) &&
           record.match.course_id == run.provenance.course_id;
}

bool save_multiplayer_match_record_file(
    const std::string& path,
    const MultiplayerMatchRecord& record,
    std::string* detail) {
    const std::string encoded = encode_multiplayer_match_record(record);
    if (encoded.empty()) {
        return set_error(detail, "match record validation failed");
    }
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) return set_error(detail, "cannot open match record");
    out.write(encoded.data(), static_cast<std::streamsize>(encoded.size()));
    if (!out) return set_error(detail, "cannot write match record");
    return true;
}

MultiplayerMatchDecodeResult load_multiplayer_match_record_file(
    const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return {std::nullopt, "cannot open match record"};

    std::string encoded;
    encoded.resize(kMaxMatchRecordBytes + 1u);
    in.read(encoded.data(), static_cast<std::streamsize>(encoded.size()));
    const std::streamsize count = in.gcount();
    if (count < 0) return {std::nullopt, "cannot read match record"};
    if (static_cast<std::size_t>(count) > kMaxMatchRecordBytes) {
        return {std::nullopt, "match record too large"};
    }
    encoded.resize(static_cast<std::size_t>(count));
    if (!in.eof() && in.fail()) {
        return {std::nullopt, "cannot read match record"};
    }
    return decode_multiplayer_match_record(encoded);
}

}  // namespace ur::product
