#include "racer_hd_presenter.hpp"
#include "racer_replacement_selector.hpp"

#include <cassert>
#include <cstdint>

int main() {
    using namespace ur::presentation;

    const auto* registration = find_racer_registration(0x0541);
    assert(registration != nullptr);
    assert(is_first_authored_remastered_registration(*registration));

    // The authored baseline registration uses the real candidate, not the
    // generic contract placeholder.
    const std::uint32_t authored_tire =
        sample_racer_hd_asset(*registration, 124, 78, false, false);
    const std::uint32_t generic_tire =
        sample_racer_hd_contract_candidate(124, 78, false, false);
    assert(authored_tire != 0);
    assert(authored_tire != generic_tire);

    // A different exact composition sharing semantic 0541 stays on the
    // contract candidate until separately authored.
    RacerCompositionState companion_context{
        0x0541, 0x0540, 0x0D2D, 0x0000, 0, 0, 0x0001, 0x0000
    };
    const auto* companion =
        find_racer_registration_for_state(0x0541, companion_context);
    assert(companion != nullptr);
    assert(companion != registration);
    assert(!is_first_authored_remastered_registration(*companion));
    assert(
        sample_racer_hd_asset(*companion, 144, 58, false, false) ==
        sample_racer_hd_contract_candidate(144, 58, false, false)
    );

    // Object-local H/V reflection remains a post-selection presentation
    // transform for authored art.
    const std::uint32_t pedal =
        sample_racer_hd_asset(*registration, 143, 108, false, false);
    assert(pedal != 0);
    assert(
        sample_racer_hd_asset(*registration, 112, 108, true, false) == pedal
    );
    assert(
        sample_racer_hd_asset(*registration, 143, 147, false, true) == pedal
    );

    // The candidate preserves the recovered logical contact row. Sampling the
    // 4x asset at logical pixel centres yields occupied pixels at y=38 but none
    // below the 64x registration target.
    bool contact_row_occupied = false;
    for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
        const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        const int sy = 38 * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        if (sample_racer_hd_asset(*registration, sx, sy, false, false) != 0) {
            contact_row_occupied = true;
        }
    }
    assert(contact_row_occupied);

    // Position remains an independent live presentation coordinate.
    const auto selected = select_racer_presentation(
        GraphicsPack::Remastered,
        0x0541,
        registration->composition
    );
    assert(selected.uses_replacement());
    assert(selected.registration == registration);

    RacerOamPlacement a{};
    a.x_signed = 10;
    a.y_raw_8bit = 20;
    RacerOamPlacement b = a;
    b.x_signed = 30;
    b.y_raw_8bit = 35;

    const auto pa = sample_racer_hd_presented_pixel(*registration, a, 40, 58);
    const auto pb = sample_racer_hd_presented_pixel(*registration, b, 60, 73);
    assert(pa == pb);

    assert(racer_hd_asset_available(0x0541));
    assert(racer_hd_asset_available(0x0540));
    assert(racer_hd_asset_available(0x057D));
    assert(racer_hd_asset_available(0x0542));
    assert(racer_hd_asset_available(0x0543));
    assert(racer_hd_asset_available(0x057E));
    assert(racer_hd_asset_available(0x057F));
    assert(racer_hd_asset_available(0x0544));
    assert(!racer_hd_asset_available(0x0999));

    assert(sample_racer_hd_asset(*registration, -1, 0, false, false) == 0);
    assert(
        sample_racer_hd_asset(
            *registration, kRacerHdAssetSize, 0, false, false
        ) == 0
    );
    return 0;
}
