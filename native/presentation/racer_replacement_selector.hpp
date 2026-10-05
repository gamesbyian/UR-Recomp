#pragma once

#include <cstdint>

namespace ur::presentation {

enum class GraphicsPack : std::uint8_t {
    Original = 0,
    Remastered = 1,
    Reimagined = 2,
};

enum class FallbackReason : std::uint8_t {
    None = 0,
    OriginalRequested,
    UnregisteredSemanticFrame,
    CompositionMismatch,
    PackUnavailable,
};

struct RacerCompositionState {
    std::uint16_t p1_primary;
    std::uint16_t p2_primary;
    std::uint16_t p1_companion;
    std::uint16_t p2_companion;
    std::uint16_t p1_selector;
    std::uint16_t p2_selector;
    std::uint16_t p1_companion_gate_word;
    std::uint16_t p2_companion_gate_word;
};

struct RacerAnchor2 {
    std::int16_t x2;
    std::int16_t y2;
};

constexpr RacerAnchor2 transform_racer_anchor(
    RacerAnchor2 anchor,
    std::uint16_t logical_width,
    std::uint16_t logical_height,
    bool hflip,
    bool vflip
) noexcept {
    if (hflip) {
        anchor.x2 = static_cast<std::int16_t>(
            2 * (static_cast<int>(logical_width) - 1) - anchor.x2
        );
    }
    if (vflip) {
        anchor.y2 = static_cast<std::int16_t>(
            2 * (static_cast<int>(logical_height) - 1) - anchor.y2
        );
    }
    return anchor;
}

struct RacerRegistration {
    std::uint16_t semantic_frame_id;
    std::uint8_t player;
    RacerCompositionState composition;
    std::uint8_t palette_asset_id;
    std::uint16_t logical_width;
    std::uint16_t logical_height;
    std::uint8_t occupancy_tile_x;
    std::uint8_t occupancy_tile_y;
    std::uint8_t remastered_density_scale;
    std::uint8_t anchor_fixed_point_scale;
    RacerAnchor2 semantic_pivot;
    RacerAnchor2 contact_anchor;
    bool has_explicit_pivot;
    bool has_explicit_contact_anchor;
};

struct SelectionResult {
    GraphicsPack requested_pack;
    GraphicsPack selected_pack;
    FallbackReason fallback_reason;
    const RacerRegistration* registration;

    constexpr bool uses_replacement() const noexcept {
        return selected_pack != GraphicsPack::Original && registration != nullptr;
    }
};

constexpr bool composition_equal(
    const RacerCompositionState& a,
    const RacerCompositionState& b
) noexcept {
    return a.p1_primary == b.p1_primary &&
           a.p2_primary == b.p2_primary &&
           a.p1_companion == b.p1_companion &&
           a.p2_companion == b.p2_companion &&
           a.p1_selector == b.p1_selector &&
           a.p2_selector == b.p2_selector &&
           a.p1_companion_gate_word == b.p1_companion_gate_word &&
           a.p2_companion_gate_word == b.p2_companion_gate_word;
}

const RacerRegistration* find_racer_registration(std::uint16_t semantic_frame_id) noexcept;

const RacerRegistration* find_racer_registration_for_state(
    std::uint16_t semantic_frame_id,
    const RacerCompositionState& live_state,
    std::uint8_t player
) noexcept;

SelectionResult select_racer_presentation(
    GraphicsPack requested_pack,
    std::uint16_t semantic_frame_id,
    const RacerCompositionState& live_state,
    std::uint8_t player
) noexcept;

}  // namespace ur::presentation
