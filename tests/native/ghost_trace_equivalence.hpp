#pragma once

#include "completed_run_ghost_trace.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <string>

namespace ur::test {

// Comparison of independently decoded, checksum-validated presentation traces.
// Frame count on the two completed-run artifacts may differ by one observation
// at retirement; that metadata has no replay authority. The common race-frame
// prefix must still have exactly equal world and full pose/composition samples.
// At most one *terminal* sample may be absent, never an interior sample.
inline bool equivalent_ghost_world_samples(
    const product::CompletedRunGhostTrace& original,
    const product::CompletedRunGhostTrace& replayed,
    std::string* detail = nullptr,
    std::size_t* compared_samples = nullptr) {
    if (compared_samples) *compared_samples = 0;
    const auto& a = original.samples;
    const auto& b = replayed.samples;
    const auto fail = [&](const std::string& why) {
        if (detail) *detail = why;
        return false;
    };

    if (a.empty() || b.empty()) return fail("missing authoritative world samples");
    const auto common = std::min(a.size(), b.size());
    const auto extra = std::max(a.size(), b.size()) - common;
    if (extra > 1) return fail("more than one terminal sample differs");

    for (std::size_t i = 0; i < common; ++i) {
        const auto& x = a[i];
        const auto& y = b[i];
        const auto field = [&](const char* name, std::uint64_t lhs,
                               std::uint64_t rhs) {
            if (lhs == rhs) return true;
            return fail("sample=" + std::to_string(i) +
                        " race_frame=" + std::to_string(x.race_frame) +
                        " field=" + name +
                        " original=" + std::to_string(lhs) +
                        " replayed=" + std::to_string(rhs));
        };
        if (!field("race_frame", x.race_frame, y.race_frame) ||
            !field("world_x", x.world_x, y.world_x) ||
            !field("world_y", x.world_y, y.world_y) ||
            !field("pitch_angle", x.pitch_angle, y.pitch_angle) ||
            !field("semantic_frame_id", x.semantic_frame_id, y.semantic_frame_id) ||
            !field("facing", x.facing, y.facing) ||
            !field("sprite_attr", x.sprite_attr, y.sprite_attr) ||
            !field("p1_primary", x.composition.p1_primary, y.composition.p1_primary) ||
            !field("p2_primary", x.composition.p2_primary, y.composition.p2_primary) ||
            !field("p1_companion", x.composition.p1_companion, y.composition.p1_companion) ||
            !field("p2_companion", x.composition.p2_companion, y.composition.p2_companion) ||
            !field("p1_selector", x.composition.p1_selector, y.composition.p1_selector) ||
            !field("p2_selector", x.composition.p2_selector, y.composition.p2_selector) ||
            !field("p1_companion_gate_word", x.composition.p1_companion_gate_word, y.composition.p1_companion_gate_word) ||
            !field("p2_companion_gate_word", x.composition.p2_companion_gate_word, y.composition.p2_companion_gate_word)) {
            return false;
        }
    }
    // A one-frame difference is admissible only at the very end. Both traces
    // were individually validated as strictly increasing before this function.
    if (extra) {
        const auto& longer = a.size() > b.size() ? a : b;
        if (longer.back().race_frame <= longer[common - 1].race_frame)
            return fail("non-terminal extra sample");
    }
    if (compared_samples) *compared_samples = common;
    if (detail) *detail = "matching authoritative ghost samples";
    return true;
}

}  // namespace ur::test
