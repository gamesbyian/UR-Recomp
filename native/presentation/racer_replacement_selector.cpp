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
    {
        0x0540,
        2,
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
        0x07,
        64,
        64,
        1,
        0,
        4,
        2,
        {63, 63},
        {63, 76},
        true,
        true,
    },
    {
        0x057D,
        1,
        {
            0x057D,
            0x0543,
            0x0D48,
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
        {69, 76},
        true,
        true,
    },
    {
        0x0543,
        2,
        {
            0x057D,
            0x0543,
            0x0D48,
            0x0000,
            0,
            0,
            0x0001,
            0x0000,
        },
        0x07,
        64,
        64,
        1,
        0,
        4,
        2,
        {63, 63},
        {57, 76},
        true,
        true,
    },
    {
        0x057E,
        1,
        {
            0x057E,
            0x0544,
            0x0D49,
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
        {67, 76},
        true,
        true,
    },
    {
        0x0544,
        2,
        {
            0x057E,
            0x0544,
            0x0D49,
            0x0000,
            0,
            0,
            0x0001,
            0x0000,
        },
        0x07,
        64,
        64,
        1,
        0,
        4,
        2,
        {63, 63},
        {55, 76},
        true,
        true,
    },
    {
        0x057E,
        1,
        {
            0x057E,
            0x0543,
            0x0D49,
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
        {67, 76},
        true,
        true,
    },
    {
        0x0543,
        2,
        {
            0x057E,
            0x0543,
            0x0D49,
            0x0000,
            0,
            0,
            0x0001,
            0x0000,
        },
        0x07,
        64,
        64,
        1,
        0,
        4,
        2,
        {63, 63},
        {57, 76},
        true,
        true,
    },
    {
        0x057E,
        1,
        {
            0x057E,
            0x0544,
            0x0D69,
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
        {67, 76},
        true,
        true,
    },
    {
        0x0544,
        2,
        {
            0x057E,
            0x0544,
            0x0D69,
            0x0000,
            0,
            0,
            0x0001,
            0x0000,
        },
        0x07,
        64,
        64,
        1,
        0,
        4,
        2,
        {63, 63},
        {55, 76},
        true,
        true,
    },
    {
        0x057D,
        1,
        {
            0x057D,
            0x0542,
            0x0D48,
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
        {69, 76},
        true,
        true,
    },
    {
        0x0542,
        2,
        {
            0x057D,
            0x0542,
            0x0D48,
            0x0000,
            0,
            0,
            0x0001,
            0x0000,
        },
        0x07,
        64,
        64,
        1,
        0,
        4,
        2,
        {63, 63},
        {59, 76},
        true,
        true,
    },
    {
        0x057F,
        1,
        {
            0x057F,
            0x0543,
            0x0D6A,
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
        {65, 76},
        true,
        true,
    },
    {
        0x0543,
        2,
        {
            0x057F,
            0x0543,
            0x0D6A,
            0x0000,
            0,
            0,
            0x0001,
            0x0000,
        },
        0x07,
        64,
        64,
        1,
        0,
        4,
        2,
        {63, 63},
        {57, 76},
        true,
        true,
    },
    {
        0x0541,
        1,
        {
            0x0541,
            0x0540,
            0x0D2D,
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
    {
        0x0540,
        2,
        {
            0x0541,
            0x0540,
            0x0D2D,
            0x0000,
            0,
            0,
            0x0001,
            0x0000,
        },
        0x07,
        64,
        64,
        1,
        0,
        4,
        2,
        {63, 63},
        {63, 76},
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

const RacerRegistration* find_racer_registration_for_state(
    std::uint16_t semantic_frame_id,
    const RacerCompositionState& live_state
) noexcept {
    for (const auto& registration : kRegistrations) {
        if (registration.semantic_frame_id == semantic_frame_id &&
            composition_equal(registration.composition, live_state)) {
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

    const RacerRegistration* first_registration =
        find_racer_registration(semantic_frame_id);
    if (first_registration == nullptr) {
        return {
            requested_pack,
            GraphicsPack::Original,
            FallbackReason::UnregisteredSemanticFrame,
            nullptr,
        };
    }

    const RacerRegistration* registration =
        find_racer_registration_for_state(semantic_frame_id, live_state);
    if (registration == nullptr) {
        return {
            requested_pack,
            GraphicsPack::Original,
            FallbackReason::CompositionMismatch,
            first_registration,
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
