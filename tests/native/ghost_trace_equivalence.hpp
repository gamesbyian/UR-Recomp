#pragma once

#include "completed_run_ghost_trace.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <string>

namespace ur::test {

// A deterministic controller stream must reproduce P1 world trajectory.
// Stock post-finish presentation IDs can depend on state outside the input
// stream, however. Those IDs belong to the saved, checksum-bound ghost trace:
// playback must use the ORIGINAL samples, not regenerate them from the current
// simulation. Report pose/context drift separately, rather than manufacturing
// replay-simulation authority for them.
struct GhostTraceReplayComparison {
    std::size_t compared_frames = 0;
    std::size_t p1_pose_drift_frames = 0;
    std::size_t p2_context_drift_frames = 0;
    std::size_t terminal_observation_drift_frames = 0;
    std::uint64_t first_p1_pose_drift_frame = 0;
    std::uint64_t first_p2_context_drift_frame = 0;
};

inline bool equivalent_ghost_world_samples(
    const product::CompletedRunGhostTrace& original,
    const product::CompletedRunGhostTrace& replayed,
    std::string* detail = nullptr,
    std::size_t* compared_samples = nullptr,
    GhostTraceReplayComparison* report = nullptr) {
    if (compared_samples) *compared_samples = 0;
    if (report) *report = {};
    const auto& a = original.samples;
    const auto& b = replayed.samples;
    const auto fail = [&](const std::string& why) {
        if (detail) *detail = why;
        return false;
    };

    if (a.empty() || b.empty()) return fail("missing authoritative world samples");
    // Production capture samples every race-relative guest frame, starting at
    // zero. Two equally sparse or truncated traces must not accidentally pass
    // just because their surviving world positions agree. In particular, an
    // extra sample is a one-frame retirement allowance, not arbitrary tail.
    const auto contiguous_from_zero = [](const auto& samples) {
        if (samples.front().race_frame != 0) return false;
        for (std::size_t i = 1; i < samples.size(); ++i) {
            if (samples[i].race_frame - samples[i - 1].race_frame != 1u)
                return false;
        }
        return true;
    };
    if (!contiguous_from_zero(a) || !contiguous_from_zero(b))
        return fail("noncontiguous authoritative world samples");
    const auto common = std::min(a.size(), b.size());
    const auto extra = std::max(a.size(), b.size()) - common;
    if (extra > 1) return fail("more than one terminal sample differs");

    GhostTraceReplayComparison result;
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

        if (!field("race_frame", x.race_frame, y.race_frame)) return false;
        const bool trajectory_drift = x.world_x != y.world_x ||
                                      x.world_y != y.world_y ||
                                      x.pitch_angle != y.pitch_angle;
        if (trajectory_drift) {
            // The known one-frame retirement phase can expose transient WRAM
            // in the shorter trace's last sample, while its longer counterpart
            // captured one more completed frame. Never allow an interior
            // physical divergence or a terminal difference with equal lengths.
            if (extra != 1 || i != common - 1) {
                if (!field("world_x", x.world_x, y.world_x) ||
                    !field("world_y", x.world_y, y.world_y) ||
                    !field("pitch_angle", x.pitch_angle, y.pitch_angle))
                    return false;
            }
            ++result.terminal_observation_drift_frames;
        }
        const bool pose_drift =
            x.semantic_frame_id != y.semantic_frame_id ||
            x.facing != y.facing ||
            x.sprite_attr != y.sprite_attr ||
            x.composition.p1_primary != y.composition.p1_primary ||
            x.composition.p1_companion != y.composition.p1_companion ||
            x.composition.p1_selector != y.composition.p1_selector ||
            x.composition.p1_companion_gate_word !=
                y.composition.p1_companion_gate_word;
        const bool context_drift =
            x.composition.p2_primary != y.composition.p2_primary ||
            x.composition.p2_companion != y.composition.p2_companion ||
            x.composition.p2_selector != y.composition.p2_selector ||
            x.composition.p2_companion_gate_word !=
                y.composition.p2_companion_gate_word;
        if (pose_drift) {
            if (!result.p1_pose_drift_frames)
                result.first_p1_pose_drift_frame = x.race_frame;
            ++result.p1_pose_drift_frames;
        }
        if (context_drift) {
            if (!result.p2_context_drift_frames)
                result.first_p2_context_drift_frame = x.race_frame;
            ++result.p2_context_drift_frames;
        }
    }
    if (extra) {
        const auto& longer = a.size() > b.size() ? a : b;
        if (longer.back().race_frame <= longer[common - 1].race_frame)
            return fail("non-terminal extra sample");
    }
    result.compared_frames = common;
    if (report) *report = result;
    if (compared_samples) *compared_samples = common;
    if (detail) *detail = "matching authoritative P1 world trajectory";
    return true;
}

}  // namespace ur::test
