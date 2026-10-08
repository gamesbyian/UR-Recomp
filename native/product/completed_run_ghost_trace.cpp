#include "completed_run_ghost_trace.hpp"

#include <cctype>
#include <fstream>
#include <iomanip>
#include <limits>
#include <sstream>

namespace ur::product {
namespace {

void set_detail(std::string* detail, const std::string& value) {
    if (detail) *detail = value;
}

std::uint64_t fnv1a64(const std::string& text) {
    std::uint64_t hash = 1469598103934665603ull;
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

bool hex16_ok(const std::string& value) {
    if (value.size() != 16) return false;
    for (unsigned char c : value) {
        if (!std::isxdigit(c)) return false;
    }
    return true;
}

bool parse_u64(
    const std::string& token,
    std::uint64_t& out,
    int base = 10) {
    try {
        std::size_t used = 0;
        const auto parsed = std::stoull(token, &used, base);
        if (used != token.size()) return false;
        out = parsed;
        return true;
    } catch (...) {
        return false;
    }
}

}  // namespace

bool CompletedRunGhostTraceCapture::begin_attempt() {
    samples_.clear();
    capturing_ = true;
    return true;
}

bool CompletedRunGhostTraceCapture::observe(
    const CompletedRunGhostWorldSample& sample) {
    if (!capturing_ ||
        samples_.size() >= kCompletedRunGhostTraceMaxSamples) return false;
    if (!samples_.empty() &&
        sample.race_frame <= samples_.back().race_frame) {
        return false;
    }
    samples_.push_back(sample);
    return true;
}

std::optional<CompletedRunGhostTrace> CompletedRunGhostTraceCapture::complete(
    const CompletedRunRecord& completed_run) {
    if (!capturing_) return std::nullopt;

    CompletedRunGhostTrace trace;
    trace.run_artifact_checksum =
        completed_run_record_artifact_checksum(completed_run);
    trace.samples = samples_;

    std::string detail;
    if (!validate_completed_run_ghost_trace(
            trace, &completed_run, &detail)) {
        abort_attempt();
        return std::nullopt;
    }

    capturing_ = false;
    samples_.clear();
    return trace;
}

void CompletedRunGhostTraceCapture::abort_attempt() {
    capturing_ = false;
    samples_.clear();
}

bool validate_completed_run_ghost_trace(
    const CompletedRunGhostTrace& trace,
    const CompletedRunRecord* bound_record,
    std::string* detail) {
    if (trace.schema_version != kCompletedRunGhostTraceSchemaVersion) {
        set_detail(detail, "unsupported schema version");
        return false;
    }
    if (!hex16_ok(trace.run_artifact_checksum)) {
        set_detail(detail, "invalid run artifact checksum");
        return false;
    }
    if (trace.samples.size() > kCompletedRunGhostTraceMaxSamples) {
        set_detail(detail, "ghost trace sample limit exceeded");
        return false;
    }

    if (bound_record) {
        const std::string expected =
            completed_run_record_artifact_checksum(*bound_record);
        if (expected.empty() || expected != trace.run_artifact_checksum) {
            set_detail(detail, "bound completed-run artifact mismatch");
            return false;
        }
    }

    std::uint64_t previous_frame = 0;
    bool first = true;
    for (const auto& sample : trace.samples) {
        if ((!first && sample.race_frame <= previous_frame) ||
            (bound_record && sample.race_frame >= bound_record->frame_count)) {
            set_detail(detail, "invalid ghost trace sample sequence");
            return false;
        }
        previous_frame = sample.race_frame;
        first = false;
    }

    return true;
}

std::string encode_completed_run_ghost_trace(
    const CompletedRunGhostTrace& trace) {
    std::string detail;
    if (!validate_completed_run_ghost_trace(trace, nullptr, &detail)) return {};

    std::ostringstream payload;
    payload << "URRUN_GHOST_TRACE " << trace.schema_version << "\n";
    payload << "run_checksum " << trace.run_artifact_checksum << "\n";
    for (const auto& sample : trace.samples) {
        payload << "sample "
                << sample.race_frame << " "
                << sample.world_x << " "
                << sample.world_y << " "
                << sample.pitch_angle << " "
                << sample.semantic_frame_id << " "
                << static_cast<unsigned>(sample.facing) << " "
                << static_cast<unsigned>(sample.sprite_attr) << " "
                << sample.composition.p1_primary << " "
                << sample.composition.p2_primary << " "
                << sample.composition.p1_companion << " "
                << sample.composition.p2_companion << " "
                << sample.composition.p1_selector << " "
                << sample.composition.p2_selector << " "
                << sample.composition.p1_companion_gate_word << " "
                << sample.composition.p2_companion_gate_word << "\n";
    }
    payload << "END\n";
    const std::string body = payload.str();
    const std::string trailer = "checksum " + checksum_hex(body) + "\n";
    if (body.size() > kCompletedRunGhostTraceMaxBytes - trailer.size())
        return {};
    return body + trailer;
}

CompletedRunGhostTraceLoadResult decode_completed_run_ghost_trace(
    const std::string& text,
    const CompletedRunRecord* bound_record) {
    CompletedRunGhostTraceLoadResult result;
    if (text.size() > kCompletedRunGhostTraceMaxBytes) {
        result.detail = "ghost trace byte limit exceeded";
        return result;
    }

    const auto checksum_pos = text.rfind("checksum ");
    if (checksum_pos == std::string::npos) {
        result.detail = "missing checksum";
        return result;
    }

    const std::string body = text.substr(0, checksum_pos);
    const std::string checksum_line = text.substr(checksum_pos);
    std::istringstream checksum_stream(checksum_line);
    std::string key;
    std::string checksum;
    std::string extra;
    if (!(checksum_stream >> key >> checksum) ||
        key != "checksum" || !hex16_ok(checksum) ||
        (checksum_stream >> extra)) {
        result.detail = "malformed checksum";
        return result;
    }
    if (checksum_hex(body) != checksum) {
        result.status = CompletedRunGhostTraceLoadStatus::Corrupt;
        result.detail = "checksum mismatch";
        return result;
    }

    CompletedRunGhostTrace trace;
    std::istringstream input(body);
    std::string line;
    bool saw_header = false;
    bool saw_run_checksum = false;
    bool saw_end = false;

    while (std::getline(input, line)) {
        if (line.empty()) continue;
        if (saw_end) {
            result.detail = "content after END";
            return result;
        }

        std::istringstream row(line);
        std::string row_key;
        row >> row_key;

        if (!saw_header) {
            std::string version_token;
            std::uint64_t version = 0;
            if (row_key != "URRUN_GHOST_TRACE" ||
                !(row >> version_token) || (row >> extra) ||
                !parse_u64(version_token, version)) {
                result.detail = "invalid header";
                return result;
            }
            if (version != kCompletedRunGhostTraceSchemaVersion) {
                result.status =
                    CompletedRunGhostTraceLoadStatus::UnsupportedVersion;
                result.detail = "unsupported schema version";
                return result;
            }
            trace.schema_version = static_cast<std::uint32_t>(version);
            saw_header = true;
            continue;
        }

        if (row_key == "END") {
            if (row >> extra) {
                result.detail = "malformed END";
                return result;
            }
            saw_end = true;
            continue;
        }

        if (row_key == "run_checksum") {
            if (saw_run_checksum || !(row >> trace.run_artifact_checksum) ||
                (row >> extra)) {
                result.detail = saw_run_checksum
                    ? "duplicate run checksum"
                    : "malformed run checksum";
                return result;
            }
            saw_run_checksum = true;
            continue;
        }

        if (row_key == "sample") {
            if (trace.samples.size() >= kCompletedRunGhostTraceMaxSamples) {
                result.detail = "ghost trace sample limit exceeded";
                return result;
            }
            std::string frame_token, x_token, y_token, pitch_token;
            std::string semantic_token, facing_token, attr_token;
            std::string p1_primary_token, p2_primary_token;
            std::string p1_companion_token, p2_companion_token;
            std::string p1_selector_token, p2_selector_token;
            std::string p1_gate_token, p2_gate_token;
            std::uint64_t frame = 0, x = 0, y = 0, pitch = 0;
            std::uint64_t semantic = 0, facing = 0, attr = 0;
            std::uint64_t p1_primary = 0, p2_primary = 0;
            std::uint64_t p1_companion = 0, p2_companion = 0;
            std::uint64_t p1_selector = 0, p2_selector = 0;
            std::uint64_t p1_gate = 0, p2_gate = 0;
            if (!(row >> frame_token >> x_token >> y_token >> pitch_token >>
                  semantic_token >> facing_token >> attr_token >>
                  p1_primary_token >> p2_primary_token >>
                  p1_companion_token >> p2_companion_token >>
                  p1_selector_token >> p2_selector_token >>
                  p1_gate_token >> p2_gate_token) ||
                (row >> extra) ||
                !parse_u64(frame_token, frame) ||
                !parse_u64(x_token, x) ||
                !parse_u64(y_token, y) ||
                !parse_u64(pitch_token, pitch) ||
                !parse_u64(semantic_token, semantic) ||
                !parse_u64(facing_token, facing) ||
                !parse_u64(attr_token, attr) ||
                !parse_u64(p1_primary_token, p1_primary) ||
                !parse_u64(p2_primary_token, p2_primary) ||
                !parse_u64(p1_companion_token, p1_companion) ||
                !parse_u64(p2_companion_token, p2_companion) ||
                !parse_u64(p1_selector_token, p1_selector) ||
                !parse_u64(p2_selector_token, p2_selector) ||
                !parse_u64(p1_gate_token, p1_gate) ||
                !parse_u64(p2_gate_token, p2_gate) ||
                x > 0xffffu || y > 0xffffu ||
                pitch > 0xffffu || semantic > 0xffffu ||
                facing > 0xffu || attr > 0xffu ||
                p1_primary > 0xffffu || p2_primary > 0xffffu ||
                p1_companion > 0xffffu || p2_companion > 0xffffu ||
                p1_selector > 0xffffu || p2_selector > 0xffffu ||
                p1_gate > 0xffffu || p2_gate > 0xffffu) {
                result.detail = "malformed sample";
                return result;
            }
            trace.samples.push_back({
                frame,
                static_cast<std::uint16_t>(x),
                static_cast<std::uint16_t>(y),
                static_cast<std::uint16_t>(pitch),
                static_cast<std::uint16_t>(semantic),
                static_cast<std::uint8_t>(facing),
                static_cast<std::uint8_t>(attr),
                {
                    static_cast<std::uint16_t>(p1_primary),
                    static_cast<std::uint16_t>(p2_primary),
                    static_cast<std::uint16_t>(p1_companion),
                    static_cast<std::uint16_t>(p2_companion),
                    static_cast<std::uint16_t>(p1_selector),
                    static_cast<std::uint16_t>(p2_selector),
                    static_cast<std::uint16_t>(p1_gate),
                    static_cast<std::uint16_t>(p2_gate),
                },
            });
            continue;
        }

        result.detail = "unknown field";
        return result;
    }

    if (!saw_header || !saw_run_checksum || !saw_end) {
        result.detail = "missing required field";
        return result;
    }

    std::string detail;
    if (!validate_completed_run_ghost_trace(trace, bound_record, &detail)) {
        result.status = bound_record &&
                        detail == "bound completed-run artifact mismatch"
            ? CompletedRunGhostTraceLoadStatus::Incompatible
            : CompletedRunGhostTraceLoadStatus::Malformed;
        result.detail = detail;
        return result;
    }

    result.status = CompletedRunGhostTraceLoadStatus::Loaded;
    result.trace = std::move(trace);
    return result;
}

bool save_completed_run_ghost_trace_file(
    const std::string& path,
    const CompletedRunGhostTrace& trace,
    std::string* detail) {
    const std::string encoded = encode_completed_run_ghost_trace(trace);
    if (encoded.empty()) {
        set_detail(detail, "ghost trace validation failed");
        return false;
    }

    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) {
        set_detail(detail, "cannot open ghost trace");
        return false;
    }
    out.write(encoded.data(), static_cast<std::streamsize>(encoded.size()));
    if (!out) {
        set_detail(detail, "cannot write ghost trace");
        return false;
    }
    return true;
}

CompletedRunGhostTraceLoadResult load_completed_run_ghost_trace_file(
    const std::string& path,
    const CompletedRunRecord* bound_record) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        return {
            CompletedRunGhostTraceLoadStatus::IoError,
            std::nullopt,
            "cannot open ghost trace"};
    }

    // Stream in bounded chunks instead of constructing an unbounded
    // ostringstream before validation. Keep the ceiling even if the file
    // changes after opening: ghost failure never invalidates the .urrun.
    std::string encoded;
    char chunk[8192];
    for (;;) {
        in.read(chunk, sizeof(chunk));
        const std::streamsize read_bytes = in.gcount();
        if (read_bytes > 0) {
            const auto count = static_cast<std::size_t>(read_bytes);
            if (count > kCompletedRunGhostTraceMaxBytes - encoded.size()) {
                return {
                    CompletedRunGhostTraceLoadStatus::Malformed,
                    std::nullopt,
                    "ghost trace byte limit exceeded"};
            }
            encoded.append(chunk, count);
        }
        if (in.eof()) break;
        if (!in) {
            return {
                CompletedRunGhostTraceLoadStatus::IoError,
                std::nullopt,
                "cannot read ghost trace"};
        }
    }
    return decode_completed_run_ghost_trace(encoded, bound_record);
}


CompletedRunGhostTraceLoadResult load_selected_completed_run_ghost_trace(
    const CompletedRunGhostState& state,
    CompletedRunGhostKind kind) {
    const StoredRunRecord* selected = state.stored(kind);
    if (!selected) {
        return {
            CompletedRunGhostTraceLoadStatus::Incompatible,
            std::nullopt,
            "selected completed-run artifact unavailable"};
    }
    return load_completed_run_ghost_trace_file(
        selected->path + ".urghost", &selected->record);
}

const CompletedRunGhostWorldSample* completed_run_ghost_trace_sample_at(
    const CompletedRunGhostTrace& trace,
    std::uint64_t race_frame) {
    std::size_t lo = 0;
    std::size_t hi = trace.samples.size();
    while (lo < hi) {
        const std::size_t mid = lo + (hi - lo) / 2;
        const auto frame = trace.samples[mid].race_frame;
        if (frame < race_frame) {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    if (lo >= trace.samples.size() ||
        trace.samples[lo].race_frame != race_frame) {
        return nullptr;
    }
    return &trace.samples[lo];
}

}  // namespace ur::product
