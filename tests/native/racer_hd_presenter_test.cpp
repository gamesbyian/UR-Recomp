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
        sample_racer_hd_asset(*registration, 123, 90, false, false);
    const std::uint32_t generic_tire =
        sample_racer_hd_contract_candidate(123, 90, false, false);
    assert(authored_tire != 0);
    assert(authored_tire != generic_tire);

    // The immediately preceding exact 0541/0D2D composition has its own
    // authored temporal-neighbor candidate rather than falling through to the
    // generic contract placeholder.
    RacerCompositionState companion_context{
        0x0541, 0x0540, 0x0D2D, 0x0000, 0, 0, 0x0001, 0x0000
    };
    const auto* companion =
        find_racer_registration_for_state(0x0541, companion_context);
    assert(companion != nullptr);
    assert(companion != registration);
    assert(!is_first_authored_remastered_registration(*companion));
    assert(is_authored_0541_p1_companion_0d2d_registration(*companion));
    assert(
        sample_racer_hd_asset(*companion, 130, 10, false, false) !=
        sample_racer_hd_contract_candidate(130, 10, false, false)
    );

    int companion_min_lx = kRacerHdLogicalSize;
    int companion_min_ly = kRacerHdLogicalSize;
    int companion_max_lx = -1;
    int companion_max_ly = -1;
    int companion_bottom_min_lx = kRacerHdLogicalSize;
    int companion_bottom_max_lx = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*companion, sx, sy, false, false) == 0) {
                continue;
            }
            if (lx < companion_min_lx) companion_min_lx = lx;
            if (ly < companion_min_ly) companion_min_ly = ly;
            if (lx > companion_max_lx) companion_max_lx = lx;
            if (ly > companion_max_ly) companion_max_ly = ly;
            if (ly == 38) {
                if (lx < companion_bottom_min_lx) companion_bottom_min_lx = lx;
                if (lx > companion_bottom_max_lx) companion_bottom_max_lx = lx;
            }
        }
    }
    assert(companion_min_lx == 22);
    assert(companion_min_ly == 2);
    assert(companion_max_lx == 39);
    assert(companion_max_ly == 38);
    assert(companion_bottom_min_lx == 29);
    assert(companion_bottom_max_lx == 32);

    // Frame 1218 exact reversed predecessor is independently authored and
    // must match its recovered gameplay envelope/contact rather than reusing
    // the 1219 silhouette.
    RacerCompositionState reversed_context{
        0x0540, 0x0541, 0x0D2C, 0x0000, 0, 0, 0x0001, 0x0000
    };
    const auto* reversed =
        find_racer_registration_for_state(0x0540, reversed_context);
    assert(reversed != nullptr);
    assert(is_authored_0540_p1_predecessor_registration(*reversed));
    assert(
        sample_racer_hd_asset(*reversed, 128, 120, false, false) !=
        sample_racer_hd_contract_candidate(128, 120, false, false)
    );

    int reversed_min_lx = kRacerHdLogicalSize;
    int reversed_min_ly = kRacerHdLogicalSize;
    int reversed_max_lx = -1;
    int reversed_max_ly = -1;
    int reversed_bottom_min_lx = kRacerHdLogicalSize;
    int reversed_bottom_max_lx = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*reversed, sx, sy, false, false) == 0) {
                continue;
            }
            if (lx < reversed_min_lx) reversed_min_lx = lx;
            if (ly < reversed_min_ly) reversed_min_ly = ly;
            if (lx > reversed_max_lx) reversed_max_lx = lx;
            if (ly > reversed_max_ly) reversed_max_ly = ly;
            if (ly == 38) {
                if (lx < reversed_bottom_min_lx) reversed_bottom_min_lx = lx;
                if (lx > reversed_bottom_max_lx) reversed_bottom_max_lx = lx;
            }
        }
    }
    assert(reversed_min_lx == 23);
    assert(reversed_min_ly == 2);
    assert(reversed_max_lx == 40);
    assert(reversed_max_ly == 38);
    assert(reversed_bottom_min_lx == 30);
    assert(reversed_bottom_max_lx == 33);

    // Object-local H/V reflection remains a post-selection presentation
    // transform for authored art.
    const std::uint32_t pedal =
        sample_racer_hd_asset(*registration, 143, 116, false, false);
    assert(pedal != 0);
    assert(
        sample_racer_hd_asset(*registration, 112, 116, true, false) == pedal
    );
    assert(
        sample_racer_hd_asset(*registration, 143, 139, false, true) == pedal
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

    // Art review locks the sampled gameplay envelope to the deterministic
    // stock representation. This prevents a visually smooth 4x asset from
    // silently changing racer scale or contact posture at presentation size.
    int min_lx = kRacerHdLogicalSize;
    int min_ly = kRacerHdLogicalSize;
    int max_lx = -1;
    int max_ly = -1;
    int bottom_min_lx = kRacerHdLogicalSize;
    int bottom_max_lx = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*registration, sx, sy, false, false) == 0) {
                continue;
            }
            if (lx < min_lx) min_lx = lx;
            if (ly < min_ly) min_ly = ly;
            if (lx > max_lx) max_lx = lx;
            if (ly > max_ly) max_ly = ly;
            if (ly == 38) {
                if (lx < bottom_min_lx) bottom_min_lx = lx;
                if (lx > bottom_max_lx) bottom_max_lx = lx;
            }
        }
    }
    assert(min_lx == 22);
    assert(min_ly == 3);
    assert(max_lx == 39);
    assert(max_ly == 38);
    assert(bottom_min_lx == 29);
    assert(bottom_max_lx == 32);

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
