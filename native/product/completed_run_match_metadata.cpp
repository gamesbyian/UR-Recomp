#include "completed_run_match_metadata.hpp"

#include "host_product_state.hpp"

#include <charconv>
#include <cctype>
#include <cstdio>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string_view>

namespace ur::product {
namespace {

void set_detail(std::string* detail, const std::string& value) {
    if (detail) *detail = value;
}

std::uint64_t fnv1a64(const std::string& text) noexcept {
    std::uint64_t hash = 1469598103934665603ull;
    for (unsigned char ch : text) {
        hash ^= ch;
        hash *= 1099511628211ull;
    }
    return hash;
}

std::string checksum_hex(const std::string& payload) {
    std::ostringstream out;
    out << std::hex << std::setw(16) << std::setfill('0') << fnv1a64(payload);
    return out.str();
}

bool hex16_ok(std::string_view value) noexcept {
    if (value.size() != 16) return false;
    for (unsigned char ch : value) {
        if (!std::isxdigit(ch)) return false;
    }
    return true;
}

std::string escape_field(std::string_view value) {
    std::string out;
    for (unsigned char ch : value) {
        if (ch == '%' || ch == '|' || ch == '\n' || ch == '\r') {
            char encoded[4];
            std::snprintf(encoded, sizeof(encoded), "%%%02X", ch);
            out += encoded;
        } else {
            out += static_cast<char>(ch);
        }
    }
    return out;
}

int hex_value(char ch) noexcept {
    if (ch >= '0' && ch <= '9') return ch - '0';
    if (ch >= 'A' && ch <= 'F') return 10 + ch - 'A';
    if (ch >= 'a' && ch <= 'f') return 10 + ch - 'a';
    return -1;
}

std::optional<std::string> unescape_field(std::string_view value) {
    std::string out;
    for (std::size_t i = 0; i < value.size(); ++i) {
        if (value[i] != '%') {
            out += value[i];
            continue;
        }
        if (i + 2 >= value.size()) return std::nullopt;
        const int hi = hex_value(value[i + 1]);
        const int lo = hex_value(value[i + 2]);
        if (hi < 0 || lo < 0) return std::nullopt;
        out += static_cast<char>((hi << 4) | lo);
        i += 2;
    }
    return out;
}

template <typename T>
bool parse_unsigned(std::string_view value, T& out) noexcept {
    if (value.empty()) return false;
    unsigned long long parsed_value = 0;
    const auto parsed = std::from_chars(
        value.data(), value.data() + value.size(), parsed_value);
    if (parsed.ec != std::errc{} ||
        parsed.ptr != value.data() + value.size() ||
        parsed_value > static_cast<unsigned long long>(
            std::numeric_limits<T>::max())) {
        return false;
    }
    out = static_cast<T>(parsed_value);
    return true;
}

const char* outcome_name(
    ur::title::OrdinaryTwoPlayerRaceOutcome outcome) noexcept {
    switch (outcome) {
    case ur::title::OrdinaryTwoPlayerRaceOutcome::Draw:
        return "draw";
    case ur::title::OrdinaryTwoPlayerRaceOutcome::Player1Win:
        return "p1-win";
    case ur::title::OrdinaryTwoPlayerRaceOutcome::Player2Win:
        return "p2-win";
    }
    return "";
}

std::optional<ur::title::OrdinaryTwoPlayerRaceOutcome> parse_outcome(
    std::string_view value) noexcept {
    if (value == "draw") {
        return ur::title::OrdinaryTwoPlayerRaceOutcome::Draw;
    }
    if (value == "p1-win") {
        return ur::title::OrdinaryTwoPlayerRaceOutcome::Player1Win;
    }
    if (value == "p2-win") {
        return ur::title::OrdinaryTwoPlayerRaceOutcome::Player2Win;
    }
    return std::nullopt;
}

ur::title::OrdinaryTwoPlayerRaceOutcome expected_outcome(
    std::uint16_t player1_hundredths,
    std::uint16_t player2_hundredths) noexcept {
    constexpr auto no_time = ur::title::kOrdinaryTwoPlayerNoTimeHundredths;
    if (player1_hundredths == player2_hundredths) {
        return ur::title::OrdinaryTwoPlayerRaceOutcome::Draw;
    }
    if (player1_hundredths == no_time) {
        return ur::title::OrdinaryTwoPlayerRaceOutcome::Player2Win;
    }
    if (player2_hundredths == no_time ||
        player1_hundredths < player2_hundredths) {
        return ur::title::OrdinaryTwoPlayerRaceOutcome::Player1Win;
    }
    return ur::title::OrdinaryTwoPlayerRaceOutcome::Player2Win;
}

bool parse_player(
    std::string_view value,
    HostProfileCatalogEntry& player) noexcept {
    const auto a = value.find('|');
    const auto b = a == std::string_view::npos
        ? std::string_view::npos
        : value.find('|', a + 1);
    if (a == std::string_view::npos || b == std::string_view::npos ||
        value.find('|', b + 1) != std::string_view::npos) {
        return false;
    }

    const auto profile = unescape_field(value.substr(0, a));
    const auto name = unescape_field(value.substr(b + 1));
    std::uint8_t rider = 0;
    if (!profile || !name ||
        !parse_unsigned(value.substr(a + 1, b - a - 1), rider)) {
        return false;
    }
    player = {*profile, HostRacerIdentity{*name, rider}};
    return is_valid_profile_id(player.profile_id) &&
           valid_racer_identity(player.identity);
}

std::string encode_player(const HostProfileCatalogEntry& player) {
    return escape_field(player.profile_id) + "|" +
           std::to_string(static_cast<unsigned>(player.identity.rider_index)) +
           "|" + escape_field(player.identity.name);
}

}  // namespace

std::optional<CompletedRunMatchMetadata> make_completed_run_match_metadata(
    const BoundOrdinaryTwoPlayerMatchContext& context,
    const CompletedRunRecord& run) noexcept {
    const std::string run_checksum =
        completed_run_record_artifact_checksum(run);
    if (run_checksum.empty() ||
        context.course_id != run.provenance.course_id) {
        return std::nullopt;
    }

    CompletedRunMatchMetadata metadata;
    metadata.run_artifact_checksum = run_checksum;
    metadata.course_id = context.course_id;
    metadata.player1 = context.match.player1;
    metadata.player2 = context.match.player2;
    metadata.player1_hundredths =
        context.match.result.player1_hundredths;
    metadata.player2_hundredths =
        context.match.result.player2_hundredths;
    metadata.outcome = context.match.result.outcome;

    std::string detail;
    if (!validate_completed_run_match_metadata(metadata, &run, &detail)) {
        return std::nullopt;
    }
    return metadata;
}

bool validate_completed_run_match_metadata(
    const CompletedRunMatchMetadata& metadata,
    const CompletedRunRecord* bound_run,
    std::string* detail) noexcept {
    if (metadata.schema_version != kCompletedRunMatchMetadataSchemaVersion) {
        set_detail(detail, "unsupported schema version");
        return false;
    }
    if (!hex16_ok(metadata.run_artifact_checksum)) {
        set_detail(detail, "invalid run artifact checksum");
        return false;
    }
    if (metadata.course_id.empty() ||
        metadata.course_id.size() != 9 ||
        metadata.course_id.compare(0, 7, "course:") != 0 ||
        !std::isdigit(static_cast<unsigned char>(metadata.course_id[7])) ||
        !std::isdigit(static_cast<unsigned char>(metadata.course_id[8]))) {
        set_detail(detail, "invalid course identity");
        return false;
    }
    const int course =
        (metadata.course_id[7] - '0') * 10 + (metadata.course_id[8] - '0');
    if (course < 1 || course > 45) {
        set_detail(detail, "invalid course identity");
        return false;
    }
    if (!is_valid_profile_id(metadata.player1.profile_id) ||
        !is_valid_profile_id(metadata.player2.profile_id) ||
        metadata.player1.profile_id == metadata.player2.profile_id) {
        set_detail(detail, "invalid participant profile identity");
        return false;
    }
    if (!valid_racer_identity(metadata.player1.identity) ||
        !valid_racer_identity(metadata.player2.identity)) {
        set_detail(detail, "invalid participant racer identity");
        return false;
    }
    constexpr auto no_time = ur::title::kOrdinaryTwoPlayerNoTimeHundredths;
    if (metadata.player1_hundredths > no_time ||
        metadata.player2_hundredths > no_time ||
        metadata.outcome != expected_outcome(
            metadata.player1_hundredths, metadata.player2_hundredths)) {
        set_detail(detail, "invalid authoritative result");
        return false;
    }

    if (bound_run) {
        const std::string expected =
            completed_run_record_artifact_checksum(*bound_run);
        if (expected.empty() ||
            expected != metadata.run_artifact_checksum ||
            bound_run->provenance.course_id != metadata.course_id) {
            set_detail(detail, "bound completed-run artifact mismatch");
            return false;
        }
    }
    return true;
}

std::string encode_completed_run_match_metadata(
    const CompletedRunMatchMetadata& metadata) {
    std::string detail;
    if (!validate_completed_run_match_metadata(metadata, nullptr, &detail)) {
        return {};
    }

    std::ostringstream payload;
    payload << "URRUN_MATCH " << metadata.schema_version << "\n";
    payload << "run_checksum " << metadata.run_artifact_checksum << "\n";
    payload << "course " << metadata.course_id << "\n";
    payload << "player1 " << encode_player(metadata.player1) << "\n";
    payload << "player2 " << encode_player(metadata.player2) << "\n";
    payload << "result "
            << metadata.player1_hundredths << " "
            << metadata.player2_hundredths << " "
            << outcome_name(metadata.outcome) << "\n";
    payload << "END\n";

    const std::string body = payload.str();
    return body + "checksum " + checksum_hex(body) + "\n";
}

CompletedRunMatchMetadataLoadResult decode_completed_run_match_metadata(
    const std::string& text,
    const CompletedRunRecord* bound_run) {
    CompletedRunMatchMetadataLoadResult result;
    const auto checksum_pos = text.rfind("checksum ");
    if (checksum_pos == std::string::npos) {
        result.detail = "missing checksum";
        return result;
    }
    const std::string body = text.substr(0, checksum_pos);
    std::istringstream checksum_row(text.substr(checksum_pos));
    std::string checksum_key, checksum_value, extra;
    if (!(checksum_row >> checksum_key >> checksum_value) ||
        checksum_key != "checksum" || !hex16_ok(checksum_value) ||
        (checksum_row >> extra)) {
        result.detail = "malformed checksum";
        return result;
    }
    if (checksum_hex(body) != checksum_value) {
        result.status = CompletedRunMatchMetadataLoadStatus::Corrupt;
        result.detail = "checksum mismatch";
        return result;
    }

    CompletedRunMatchMetadata metadata;
    std::istringstream input(body);
    std::string line;
    bool header = false;
    bool run_checksum = false;
    bool course = false;
    bool player1 = false;
    bool player2 = false;
    bool match_result = false;
    bool end = false;

    while (std::getline(input, line)) {
        if (line.empty()) continue;
        if (end) {
            result.detail = "content after END";
            return result;
        }

        if (!header) {
            std::istringstream row(line);
            std::string key, version_text;
            std::uint32_t version = 0;
            if (!(row >> key >> version_text) || (row >> extra) ||
                key != "URRUN_MATCH" ||
                !parse_unsigned(version_text, version)) {
                result.detail = "invalid header";
                return result;
            }
            if (version != kCompletedRunMatchMetadataSchemaVersion) {
                result.status =
                    CompletedRunMatchMetadataLoadStatus::UnsupportedVersion;
                result.detail = "unsupported schema version";
                return result;
            }
            metadata.schema_version = version;
            header = true;
            continue;
        }

        if (line == "END") {
            end = true;
            continue;
        }
        const auto split = line.find(' ');
        if (split == std::string::npos || split == 0) {
            result.detail = "malformed field";
            return result;
        }
        const std::string key = line.substr(0, split);
        const std::string_view value(line.data() + split + 1, line.size() - split - 1);

        if (key == "run_checksum") {
            if (run_checksum || !hex16_ok(value)) {
                result.detail = "malformed run checksum";
                return result;
            }
            metadata.run_artifact_checksum = std::string(value);
            run_checksum = true;
        } else if (key == "course") {
            if (course) {
                result.detail = "duplicate course";
                return result;
            }
            metadata.course_id = std::string(value);
            course = true;
        } else if (key == "player1" || key == "player2") {
            bool& seen = key == "player1" ? player1 : player2;
            auto& player = key == "player1" ? metadata.player1 : metadata.player2;
            if (seen || !parse_player(value, player)) {
                result.detail = "malformed participant";
                return result;
            }
            seen = true;
        } else if (key == "result") {
            if (match_result) {
                result.detail = "duplicate result";
                return result;
            }
            std::istringstream row{std::string(value)};
            std::string p1, p2, outcome_text;
            if (!(row >> p1 >> p2 >> outcome_text) || (row >> extra) ||
                !parse_unsigned(p1, metadata.player1_hundredths) ||
                !parse_unsigned(p2, metadata.player2_hundredths)) {
                result.detail = "malformed result";
                return result;
            }
            const auto outcome = parse_outcome(outcome_text);
            if (!outcome) {
                result.detail = "malformed result";
                return result;
            }
            metadata.outcome = *outcome;
            match_result = true;
        } else {
            result.detail = "unknown field";
            return result;
        }
    }

    if (!header || !run_checksum || !course || !player1 || !player2 ||
        !match_result || !end) {
        result.detail = "missing required field";
        return result;
    }

    std::string detail;
    if (!validate_completed_run_match_metadata(metadata, bound_run, &detail)) {
        result.status =
            bound_run && detail == "bound completed-run artifact mismatch"
                ? CompletedRunMatchMetadataLoadStatus::Incompatible
                : CompletedRunMatchMetadataLoadStatus::Malformed;
        result.detail = detail;
        return result;
    }

    result.status = CompletedRunMatchMetadataLoadStatus::Loaded;
    result.metadata = std::move(metadata);
    return result;
}

bool save_completed_run_match_metadata_file(
    const std::string& path,
    const CompletedRunMatchMetadata& metadata,
    std::string* detail) {
    const std::string encoded = encode_completed_run_match_metadata(metadata);
    if (encoded.empty()) {
        set_detail(detail, "match metadata validation failed");
        return false;
    }
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) {
        set_detail(detail, "cannot open match metadata");
        return false;
    }
    out.write(encoded.data(), static_cast<std::streamsize>(encoded.size()));
    if (!out) {
        set_detail(detail, "cannot write match metadata");
        return false;
    }
    return true;
}

CompletedRunMatchMetadataLoadResult load_completed_run_match_metadata_file(
    const std::string& path,
    const CompletedRunRecord* bound_run) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        return {
            CompletedRunMatchMetadataLoadStatus::IoError,
            std::nullopt,
            "cannot open match metadata",
        };
    }
    std::ostringstream buffer;
    buffer << in.rdbuf();
    if (!in.good() && !in.eof()) {
        return {
            CompletedRunMatchMetadataLoadStatus::IoError,
            std::nullopt,
            "cannot read match metadata",
        };
    }
    return decode_completed_run_match_metadata(buffer.str(), bound_run);
}

}  // namespace ur::product
