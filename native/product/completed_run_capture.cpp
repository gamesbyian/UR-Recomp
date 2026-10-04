#include "completed_run_capture.hpp"

namespace ur::product {

bool CompletedRunCapture::begin_attempt(const RunRecordProvenance& provenance) {
    CompletedRunRecord probe;
    probe.provenance = provenance;
    probe.elapsed_ticks60 = 0;
    std::string detail;
    if (!validate_completed_run_record(probe, &detail)) {
        return false;
    }

    provenance_ = provenance;
    recorder_.reset();
    splits_.clear();
    captured_frames_ = 0;
    capturing_ = true;
    return true;
}

bool CompletedRunCapture::observe_guest_frame(std::uint32_t controller_word) {
    if (!capturing_) return false;

    const std::uint16_t p1 =
        static_cast<std::uint16_t>(controller_word & 0x0fffu);
    const std::uint16_t p2 =
        static_cast<std::uint16_t>((controller_word >> 12) & 0x0fffu);
    recorder_.observe_input_frame(captured_frames_, p1, p2);
    ++captured_frames_;
    return true;
}

bool CompletedRunCapture::observe_split(
    const std::string& id,
    std::uint64_t ticks60) {
    if (!capturing_ || id.empty()) return false;
    if (!splits_.empty() && ticks60 < splits_.back().ticks60) return false;
    splits_.push_back({id, ticks60});
    return true;
}

std::optional<CompletedRunRecord> CompletedRunCapture::complete(
    std::uint64_t elapsed_ticks60,
    const std::string& terminal_simulation_digest) {
    if (!capturing_) return std::nullopt;

    CompletedRunRecord record;
    record.provenance = provenance_;
    record.elapsed_ticks60 = elapsed_ticks60;
    record.frame_count = captured_frames_;
    record.terminal_simulation_digest = terminal_simulation_digest;
    record.splits = splits_;
    record.inputs = recorder_.inputs();

    std::string detail;
    if (!validate_completed_run_record(record, &detail)) {
        abort_attempt();
        return std::nullopt;
    }

    abort_attempt();
    return record;
}

void CompletedRunCapture::abort_attempt() {
    capturing_ = false;
    captured_frames_ = 0;
    provenance_ = {};
    recorder_.reset();
    splits_.clear();
}

std::optional<std::size_t> select_fastest_compatible_run(
    const std::vector<CompletedRunRecord>& records,
    const RunPlaybackTarget& target) {
    std::optional<std::size_t> best;
    std::uint64_t best_ticks = 0;
    for (std::size_t i = 0; i < records.size(); ++i) {
        std::string detail;
        if (!validate_completed_run_record(records[i], &detail) ||
            !compatible_for_playback(records[i], target, &detail)) {
            continue;
        }
        if (!best || records[i].elapsed_ticks60 <= best_ticks) {
            best = i;
            best_ticks = records[i].elapsed_ticks60;
        }
    }
    return best;
}

}  // namespace ur::product
