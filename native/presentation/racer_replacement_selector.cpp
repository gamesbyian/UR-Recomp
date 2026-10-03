#include "racer_replacement_selector.hpp"

#include <array>

namespace ur::presentation {
namespace {

constexpr RacerRegistration kRegistrations[] = {
    {
        0x0541,
        1,
        {
            0x0541,
            0x0540,
            0x0D0D,
            0x0000,
            0,
            0,
            0x0001,
            0x0000,
        },
        0x06,
        64,
        64,
        1,
        0,
        4,
        2,
        {63, 63},
        {61, 76},
        true,
        true,
    },
};

}  // namespace

const RacerRegistration* find_racer_registration(std::uint16_t semantic_frame_id) noexcept {
    for (const auto& registration : kRegistrations) {
        if (registration.semantic_frame_id == semantic_frame_id) {
            return &registration;
        }
    }
    return nullptr;
}

SelectionResult select_racer_presentation(
    GraphicsPack requested_pack,
    std::uint16_t semantic_frame_id,
    const RacerCompositionState& live_state
) noexcept {
    if (requested_pack == GraphicsPack::Original) {
        return {
            requested_pack,
            GraphicsPack::Original,
            FallbackReason::OriginalRequested,
            nullptr,
        };
    }

    const RacerRegistration* registration = find_racer_registration(semantic_frame_id);
    if (registration == nullptr) {
        return {
            requested_pack,
            GraphicsPack::Original,
            FallbackReason::UnregisteredSemanticFrame,
            nullptr,
        };
    }

    if (!composition_equal(registration->composition, live_state)) {
        return {
            requested_pack,
            GraphicsPack::Original,
            FallbackReason::CompositionMismatch,
            registration,
        };
    }

    if (requested_pack != GraphicsPack::Remastered) {
        return {
            requested_pack,
            GraphicsPack::Original,
            FallbackReason::PackUnavailable,
            registration,
        };
    }

    return {
        requested_pack,
        GraphicsPack::Remastered,
        FallbackReason::None,
        registration,
    };
}

}  // namespace ur::presentation
