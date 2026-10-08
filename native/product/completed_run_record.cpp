#include "completed_run_record.hpp"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <iomanip>
#include <limits>
#include <sstream>

namespace ur::product {
namespace {

bool token_ok(const std::string& s) {
    if (s.empty() || s.size() > 160) return false;
    return std::all_of(s.begin(), s.end(), [](unsigned char c) {
        return std::isalnum(c) || c == '.' || c == '_' || c == '-' || c == ':';
    });
}

bool hex64_ok(const std::string& s) {
    if (s.size() != 64) return false;
    return std::all_of(s.begin(), s.end(), [](unsigned char c) {
        return std::isxdigit(c) != 0;
    });
}

std::uint64_t fnv1a64(const std::string& text) {
    std::uint64_t hash = 14695981039346656037ull;
    for (unsigned char c : text) {
        hash ^= c;
        hash *= 1099511628211ull;
    }
    return hash;
}

std::string checksum_hex(const std::string& payload) {
    std::ostringstream out;
    out << std::hex << std::setw(16) << std::setfill('0') << fnv1a64(payload);
    return out.str();
}

void fail_detail(std::string* detail, const std::string& value) {
    if (detail) *detail = value;
}

bool parse_u64(const std::string& token, std::uint64_t& out, int base = 10) {
    // stoull accepts leading signs (including "-1" -> UINT64_MAX).
    // Canonical v1 artifact fields are unsigned digit strings only.
    if (token.empty() || (base != 10 && base != 16)) return false;
    for (unsigned char c : token) {
        if (base == 10 ? !std::isdigit(c) : !std::isxdigit(c))
            return false;
    }
    try {
        std::size_t used = 0;
        const auto value = std::stoull(token, &used, base);
        if (used != token.size()) return false;
        out = value;
        return true;
    } catch (...) {
        return false;
    }
}

}  // namespace

void CompletedRunRecorder::observe_input_frame(
    std::uint64_t frame,
    std::uint16_t p1_mask,
    std::uint16_t p2_mask) {
    p1_mask &= 0x0fffu;
    p2_mask &= 0x0fffu;
    if (p1_mask == 0 && p2_mask == 0) return;

    if (!inputs_.empty()) {
        auto& last = inputs_.back();
        if (last.end_frame() == frame &&
            last.p1_mask == p1_mask &&
            last.p2_mask == p2_mask) {
            ++last.duration;
            return;
        }
    }
    inputs_.push_back({frame, 1, p1_mask, p2_mask});
}

void CompletedRunRecorder::reset() {
    inputs_.clear();
}

bool validate_completed_run_record(const CompletedRunRecord& record, std::string* detail) {
    if (record.schema_version != kCompletedRunRecordSchemaVersion) {
        fail_detail(detail, "unsupported schema version");
        return false;
    }
    const auto& p = record.provenance;
    if (!token_ok(p.game_id) || !hex64_ok(p.rom_sha256) ||
        !token_ok(p.build_compat_id) || !token_ok(p.course_id) ||
        !token_ok(p.mode)) {
        fail_detail(detail, "invalid provenance");
        return false;
    }
    if (!record.terminal_simulation_digest.empty() &&
        !hex64_ok(record.terminal_simulation_digest)) {
        fail_detail(detail, "invalid terminal simulation digest");
        return false;
    }

    std::uint64_t previous_split = 0;
    for (std::size_t i = 0; i < record.splits.size(); ++i) {
        const auto& split = record.splits[i];
        if (!token_ok(split.id) || split.ticks60 > record.elapsed_ticks60 ||
            (i && split.ticks60 < previous_split)) {
            fail_detail(detail, "invalid split sequence");
            return false;
        }
        previous_split = split.ticks60;
    }

    std::uint64_t previous_end = 0;
    bool first = true;
    for (const auto& input : record.inputs) {
        if (!input.duration ||
            (input.p1_mask & ~0x0fffu) ||
            (input.p2_mask & ~0x0fffu) ||
            (!input.p1_mask && !input.p2_mask) ||
            input.start_frame > std::numeric_limits<std::uint64_t>::max() - input.duration ||
            (!first && input.start_frame < previous_end) ||
            input.end_frame() > record.frame_count) {
            fail_detail(detail, "invalid or overlapping input run");
            return false;
        }
        previous_end = input.end_frame();
        first = false;
    }
    return true;
}

bool compatible_for_playback(
    const CompletedRunRecord& record,
    const RunPlaybackTarget& target,
    std::string* detail) {
    const auto& p = record.provenance;
    if (p.game_id != target.game_id ||
        p.rom_sha256 != target.rom_sha256 ||
        p.build_compat_id != target.build_compat_id ||
        p.course_id != target.course_id ||
        p.mode != target.mode) {
        fail_detail(detail, "run provenance does not match playback target");
        return false;
    }
    return true;
}

std::string encode_completed_run_record(const CompletedRunRecord& record) {
    std::string detail;
    if (!validate_completed_run_record(record, &detail)) return {};

    std::ostringstream payload;
    payload << "URRUN " << record.schema_version << "\n";
    payload << "game " << record.provenance.game_id << "\n";
    payload << "rom_sha256 " << record.provenance.rom_sha256 << "\n";
    payload << "build_compat " << record.provenance.build_compat_id << "\n";
    payload << "course " << record.provenance.course_id << "\n";
    payload << "mode " << record.provenance.mode << "\n";
    payload << "elapsed_ticks60 " << record.elapsed_ticks60 << "\n";
    payload << "frame_count " << record.frame_count << "\n";
    payload << "terminal_digest "
            << (record.terminal_simulation_digest.empty() ? "-" : record.terminal_simulation_digest)
            << "\n";
    for (const auto& split : record.splits) {
        payload << "split " << split.id << " " << split.ticks60 << "\n";
    }
    for (const auto& input : record.inputs) {
        payload << "input " << input.start_frame << " " << input.duration << " "
                << std::hex << std::uppercase << input.p1_mask << " " << input.p2_mask
                << std::dec << "\n";
    }
    payload << "END\n";

    const std::string body = payload.str();
    const std::string trailer = "checksum " + checksum_hex(body) + "\n";
    if (body.size() > kCompletedRunRecordMaxBytes - trailer.size())
        return {};
    return body + trailer;
}

std::string completed_run_record_artifact_checksum(
    const CompletedRunRecord& record) {
    const std::string encoded = encode_completed_run_record(record);
    if (encoded.empty()) return {};
    const auto pos = encoded.rfind("checksum ");
    if (pos == std::string::npos || pos + 25 > encoded.size()) return {};
    return encoded.substr(pos + 9, 16);
}

std::string encode_completed_run_input_file(
    const CompletedRunRecord& record,
    std::uint64_t frame_offset) {
    std::string detail;
    if (!validate_completed_run_record(record, &detail)) return {};
    std::ostringstream out;
    for (const auto& input : record.inputs) {
        if (input.start_frame >
            std::numeric_limits<std::uint64_t>::max() - frame_offset) {
            return {};
        }
        out << (input.start_frame + frame_offset) << ":" << input.duration << ":"
            << std::hex << std::uppercase << input.p1_mask << ":"
            << input.p2_mask << std::dec << "\n";
    }
    return out.str();
}

RunRecordLoadResult decode_completed_run_record(const std::string& text) {
    RunRecordLoadResult result;
    if (text.size() > kCompletedRunRecordMaxBytes) {
        result.status = RunRecordLoadStatus::Malformed;
        result.detail = "run record byte limit exceeded";
        return result;
    }
    const auto checksum_pos = text.rfind("checksum ");
    if (checksum_pos == std::string::npos) {
        result.status = RunRecordLoadStatus::Malformed;
        result.detail = "missing checksum";
        return result;
    }
    const std::string body = text.substr(0, checksum_pos);
    const std::string checksum_line = text.substr(checksum_pos);
    std::istringstream checksum_stream(checksum_line);
    std::string checksum_key, checksum_value, checksum_extra;
    if (!(checksum_stream >> checksum_key >> checksum_value) ||
        checksum_key != "checksum" || checksum_value.size() != 16 ||
        (checksum_stream >> checksum_extra)) {
        result.status = RunRecordLoadStatus::Malformed;
        result.detail = "malformed checksum";
        return result;
    }
    if (checksum_hex(body) != checksum_value) {
        result.status = RunRecordLoadStatus::Corrupt;
        result.detail = "checksum mismatch";
        return result;
    }

    CompletedRunRecord record;
    std::istringstream in(body);
    std::string line;
    bool saw_header = false, saw_end = false;
    bool game = false, rom = false, build = false, course = false, mode = false;
    bool elapsed = false, frame_count = false, terminal = false;
    while (std::getline(in, line)) {
        if (line.empty()) continue;
        std::istringstream row(line);
        std::string key;
        row >> key;
        if (!saw_header) {
            std::uint64_t version = 0;
            std::string version_token, extra;
            if (key != "URRUN" || !(row >> version_token) || (row >> extra) ||
                !parse_u64(version_token, version)) {
                result.status = RunRecordLoadStatus::Malformed;
                result.detail = "invalid header";
                return result;
            }
            if (version != kCompletedRunRecordSchemaVersion) {
                result.status = RunRecordLoadStatus::UnsupportedVersion;
                result.detail = "unsupported schema version";
                return result;
            }
            record.schema_version = static_cast<std::uint32_t>(version);
            saw_header = true;
            continue;
        }
        if (key == "END") {
            std::string extra;
            if ((row >> extra)) {
                result.status = RunRecordLoadStatus::Malformed;
                result.detail = "malformed END";
                return result;
            }
            saw_end = true;
            continue;
        }
        if (saw_end) {
            result.status = RunRecordLoadStatus::Malformed;
            result.detail = "data after END";
            return result;
        }

        std::string a, b, c, d, extra;
        if (key == "game" || key == "rom_sha256" || key == "build_compat" ||
            key == "course" || key == "mode" || key == "elapsed_ticks60" ||
            key == "frame_count" || key == "terminal_digest") {
            if (!(row >> a) || (row >> extra)) {
                result.status = RunRecordLoadStatus::Malformed;
                result.detail = "malformed scalar";
                return result;
            }
            if (key == "game") { if (game) goto duplicate; record.provenance.game_id = a; game = true; }
            else if (key == "rom_sha256") { if (rom) goto duplicate; record.provenance.rom_sha256 = a; rom = true; }
            else if (key == "build_compat") { if (build) goto duplicate; record.provenance.build_compat_id = a; build = true; }
            else if (key == "course") { if (course) goto duplicate; record.provenance.course_id = a; course = true; }
            else if (key == "mode") { if (mode) goto duplicate; record.provenance.mode = a; mode = true; }
            else if (key == "elapsed_ticks60") {
                if (elapsed || !parse_u64(a, record.elapsed_ticks60)) goto malformed;
                elapsed = true;
            } else if (key == "frame_count") {
                if (frame_count || !parse_u64(a, record.frame_count)) goto malformed;
                frame_count = true;
            } else {
                if (terminal) goto duplicate;
                record.terminal_simulation_digest = a == "-" ? "" : a;
                terminal = true;
            }
            continue;
        }
        if (key == "split") {
            std::uint64_t ticks = 0;
            if (!(row >> a >> b) || (row >> extra) || !parse_u64(b, ticks)) goto malformed;
            record.splits.push_back({a, ticks});
            continue;
        }
        if (key == "input") {
            std::uint64_t start = 0, duration = 0, p1 = 0, p2 = 0;
            if (!(row >> a >> b >> c >> d) || (row >> extra) ||
                !parse_u64(a, start) || !parse_u64(b, duration) ||
                !parse_u64(c, p1, 16) || !parse_u64(d, p2, 16) ||
                p1 > 0xffffu || p2 > 0xffffu) goto malformed;
            record.inputs.push_back({
                start, duration,
                static_cast<std::uint16_t>(p1),
                static_cast<std::uint16_t>(p2)});
            continue;
        }
        result.status = RunRecordLoadStatus::Malformed;
        result.detail = "unknown field";
        return result;

duplicate:
        result.status = RunRecordLoadStatus::Malformed;
        result.detail = "duplicate field";
        return result;
malformed:
        result.status = RunRecordLoadStatus::Malformed;
        result.detail = "malformed field";
        return result;
    }

    if (!saw_header || !saw_end || !game || !rom || !build || !course ||
        !mode || !elapsed || !frame_count || !terminal) {
        result.status = RunRecordLoadStatus::Malformed;
        result.detail = "missing required field";
        return result;
    }
    std::string detail;
    if (!validate_completed_run_record(record, &detail)) {
        result.status = RunRecordLoadStatus::Malformed;
        result.detail = detail;
        return result;
    }
    result.status = RunRecordLoadStatus::Loaded;
    result.record = std::move(record);
    return result;
}

bool save_completed_run_record_file(
    const std::string& path,
    const CompletedRunRecord& record,
    std::string* detail) {
    const std::string encoded = encode_completed_run_record(record);
    if (encoded.empty()) {
        fail_detail(detail, "record validation failed");
        return false;
    }
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) {
        fail_detail(detail, "cannot open run record");
        return false;
    }
    out.write(encoded.data(), static_cast<std::streamsize>(encoded.size()));
    if (!out) {
        fail_detail(detail, "cannot write run record");
        return false;
    }
    return true;
}

RunRecordLoadResult load_completed_run_record_file(
    const std::string& path,
    const RunPlaybackTarget* target) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        return {RunRecordLoadStatus::IoError, std::nullopt, "cannot open run record"};
    }
    // Bound the entire read, even if a regular file grows after open.
    // A damaged local-run artifact must not exhaust memory merely by being
    // enumerated in Local Runs or the profile Records browser.
    std::string encoded;
    char chunk[8192];
    for (;;) {
        in.read(chunk, sizeof(chunk));
        const std::streamsize read_bytes = in.gcount();
        if (read_bytes > 0) {
            const auto count = static_cast<std::size_t>(read_bytes);
            if (count > kCompletedRunRecordMaxBytes - encoded.size()) {
                return {
                    RunRecordLoadStatus::Malformed,
                    std::nullopt,
                    "run record byte limit exceeded"};
            }
            encoded.append(chunk, count);
        }
        if (in.eof()) break;
        if (!in) {
            return {
                RunRecordLoadStatus::IoError,
                std::nullopt,
                "cannot read run record"};
        }
    }
    auto result = decode_completed_run_record(encoded);
    if (result.loaded() && target) {
        std::string detail;
        if (!compatible_for_playback(*result.record, *target, &detail)) {
            result.status = RunRecordLoadStatus::Incompatible;
            result.record.reset();
            result.detail = detail;
        }
    }
    return result;
}

std::pair<std::uint16_t, std::uint16_t> run_record_input_at(
    const CompletedRunRecord& record,
    std::uint64_t frame) {
    for (const auto& input : record.inputs) {
        if (input.start_frame > frame) break;
        if (frame < input.end_frame()) return {input.p1_mask, input.p2_mask};
    }
    return {0, 0};
}

}  // namespace ur::product
