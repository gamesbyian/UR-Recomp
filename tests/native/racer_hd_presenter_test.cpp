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

    // Frame 1217 has a distinct synchronized context but a byte-identical
    // P1 stock raster, so it must resolve to the exact same reviewed authored
    // sampler as frame 1218 rather than inventing another visual pose.
    RacerCompositionState reused_context{
        0x0540, 0x0542, 0x0D2C, 0x0000, 0, 0, 0x0001, 0x0000
    };
    const auto* reused =
        find_racer_registration_for_state(0x0540, reused_context);
    assert(reused != nullptr);
    assert(
        is_authored_0540_p1_companion_0d2c_with_p2_0542_registration(
            *reused
        )
    );
    for (int y = 0; y < kRacerHdAssetSize; y += 7) {
        for (int x = 0; x < kRacerHdAssetSize; x += 7) {
            assert(
                sample_racer_hd_asset(*reused, x, y, false, false) ==
                sample_racer_hd_asset(*reversed, x, y, false, false)
            );
        }
    }

    // Frames 1215-1216 are one repeated exact state and therefore share one
    // newly authored pose. The sampled gameplay silhouette must match the
    // recovered envelope and contact before any enlarged-art judgement.
    RacerCompositionState repeated_057f_context{
        0x057F, 0x0542, 0x0D4A, 0x0000, 0, 0, 0x0001, 0x0000
    };
    const auto* repeated_057f =
        find_racer_registration_for_state(0x057F, repeated_057f_context);
    assert(repeated_057f != nullptr);
    assert(is_authored_057f_p1_companion_0d4a_registration(*repeated_057f));
    assert(
        sample_racer_hd_asset(*repeated_057f, 132, 120, false, false) !=
        sample_racer_hd_contract_candidate(132, 120, false, false)
    );

    int repeated_min_lx = kRacerHdLogicalSize;
    int repeated_min_ly = kRacerHdLogicalSize;
    int repeated_max_lx = -1;
    int repeated_max_ly = -1;
    int repeated_bottom_min_lx = kRacerHdLogicalSize;
    int repeated_bottom_max_lx = -1;
    int repeated_opaque = 0;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*repeated_057f, sx, sy, false, false) == 0) {
                continue;
            }
            ++repeated_opaque;
            if (lx < repeated_min_lx) repeated_min_lx = lx;
            if (ly < repeated_min_ly) repeated_min_ly = ly;
            if (lx > repeated_max_lx) repeated_max_lx = lx;
            if (ly > repeated_max_ly) repeated_max_ly = ly;
            if (ly == 38) {
                if (lx < repeated_bottom_min_lx) repeated_bottom_min_lx = lx;
                if (lx > repeated_bottom_max_lx) repeated_bottom_max_lx = lx;
            }
        }
    }
    assert(repeated_min_lx == 22);
    assert(repeated_min_ly == 2);
    assert(repeated_max_lx == 41);
    assert(repeated_max_ly == 38);
    assert(repeated_bottom_min_lx == 31);
    assert(repeated_bottom_max_lx == 34);
    assert(repeated_bottom_min_lx + repeated_bottom_max_lx == 65);
    assert(repeated_opaque == 321);

    // Frames 1213-1214 and 1205-1206 share the exact 057E/0543 state and
    // therefore one authored pose. Lock the recovered gameplay envelope and
    // contact before judging the enlarged asset.
    RacerCompositionState repeated_057e_context{
        0x057E, 0x0543, 0x0D49, 0x0000, 0, 0, 0x0001, 0x0000
    };
    const auto* repeated_057e =
        find_racer_registration_for_state(0x057E, repeated_057e_context);
    assert(repeated_057e != nullptr);
    assert(is_authored_057e_p1_with_p2_0543_registration(*repeated_057e));

    int repeated_057e_min_lx = kRacerHdLogicalSize;
    int repeated_057e_min_ly = kRacerHdLogicalSize;
    int repeated_057e_max_lx = -1;
    int repeated_057e_max_ly = -1;
    int repeated_057e_bottom_min_lx = kRacerHdLogicalSize;
    int repeated_057e_bottom_max_lx = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*repeated_057e, sx, sy, false, false) == 0) {
                continue;
            }
            if (lx < repeated_057e_min_lx) repeated_057e_min_lx = lx;
            if (ly < repeated_057e_min_ly) repeated_057e_min_ly = ly;
            if (lx > repeated_057e_max_lx) repeated_057e_max_lx = lx;
            if (ly > repeated_057e_max_ly) repeated_057e_max_ly = ly;
            if (ly == 38) {
                if (lx < repeated_057e_bottom_min_lx) repeated_057e_bottom_min_lx = lx;
                if (lx > repeated_057e_bottom_max_lx) repeated_057e_bottom_max_lx = lx;
            }
        }
    }
    assert(repeated_057e_min_lx == 21);
    assert(repeated_057e_min_ly == 2);
    assert(repeated_057e_max_lx == 42);
    assert(repeated_057e_max_ly == 38);
    assert(repeated_057e_bottom_min_lx == 32);
    assert(repeated_057e_bottom_max_lx == 35);
    assert(repeated_057e_bottom_min_lx + repeated_057e_bottom_max_lx == 67);

    // Frames 1207-1212 share the exact 057D/0543 state and one authored pose.
    // Lock the recovered gameplay envelope/contact before enlarged-art review.
    RacerCompositionState repeated_057d_context{
        0x057D, 0x0543, 0x0D48, 0x0000, 0, 0, 0x0001, 0x0000
    };
    const auto* repeated_057d =
        find_racer_registration_for_state(0x057D, repeated_057d_context);
    assert(repeated_057d != nullptr);
    assert(is_authored_057d_p1_with_p2_0543_registration(*repeated_057d));

    int repeated_057d_min_lx = kRacerHdLogicalSize;
    int repeated_057d_min_ly = kRacerHdLogicalSize;
    int repeated_057d_max_lx = -1;
    int repeated_057d_max_ly = -1;
    int repeated_057d_bottom_min_lx = kRacerHdLogicalSize;
    int repeated_057d_bottom_max_lx = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*repeated_057d, sx, sy, false, false) == 0) {
                continue;
            }
            if (lx < repeated_057d_min_lx) repeated_057d_min_lx = lx;
            if (ly < repeated_057d_min_ly) repeated_057d_min_ly = ly;
            if (lx > repeated_057d_max_lx) repeated_057d_max_lx = lx;
            if (ly > repeated_057d_max_ly) repeated_057d_max_ly = ly;
            if (ly == 38) {
                if (lx < repeated_057d_bottom_min_lx) repeated_057d_bottom_min_lx = lx;
                if (lx > repeated_057d_bottom_max_lx) repeated_057d_bottom_max_lx = lx;
            }
        }
    }
    assert(repeated_057d_min_lx == 21);
    assert(repeated_057d_min_ly == 3);
    assert(repeated_057d_max_lx == 43);
    assert(repeated_057d_max_ly == 38);
    assert(repeated_057d_bottom_min_lx == 33);
    assert(repeated_057d_bottom_max_lx == 36);
    assert(repeated_057d_bottom_min_lx + repeated_057d_bottom_max_lx == 69);

    // P2 baseline now has its own authored Remastered asset rather than the
    // generic contract placeholder. Lock its exact stock envelope/contact.
    RacerCompositionState p2_baseline_context{
        0x0541, 0x0540, 0x0D0D, 0x0000, 0, 0, 0x0001, 0x0000
    };
    const auto* p2_baseline =
        find_racer_registration_for_state(0x0540, p2_baseline_context);
    assert(p2_baseline != nullptr);
    assert(is_authored_0540_p2_baseline_registration(*p2_baseline));

    int p2_baseline_min_lx = kRacerHdLogicalSize;
    int p2_baseline_min_ly = kRacerHdLogicalSize;
    int p2_baseline_max_lx = -1;
    int p2_baseline_max_ly = -1;
    int p2_baseline_bottom_min_lx = kRacerHdLogicalSize;
    int p2_baseline_bottom_max_lx = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*p2_baseline, sx, sy, false, false) == 0) {
                continue;
            }
            if (lx < p2_baseline_min_lx) p2_baseline_min_lx = lx;
            if (ly < p2_baseline_min_ly) p2_baseline_min_ly = ly;
            if (lx > p2_baseline_max_lx) p2_baseline_max_lx = lx;
            if (ly > p2_baseline_max_ly) p2_baseline_max_ly = ly;
            if (ly == 38) {
                if (lx < p2_baseline_bottom_min_lx) p2_baseline_bottom_min_lx = lx;
                if (lx > p2_baseline_bottom_max_lx) p2_baseline_bottom_max_lx = lx;
            }
        }
    }
    assert(p2_baseline_min_lx == 23);
    assert(p2_baseline_min_ly == 3);
    assert(p2_baseline_max_lx == 40);
    assert(p2_baseline_max_ly == 38);
    assert(p2_baseline_bottom_min_lx == 30);
    assert(p2_baseline_bottom_max_lx == 33);
    assert(p2_baseline_bottom_min_lx + p2_baseline_bottom_max_lx == 63);

    // Frame 1219 P2 has a distinct synchronized guard but byte-identical
    // stock art to frame 1220, so it must reuse the exact same authored asset.
    RacerCompositionState p2_reuse_context{
        0x0541, 0x0540, 0x0D2D, 0x0000, 0, 0, 0x0001, 0x0000
    };
    const auto* p2_reuse =
        find_racer_registration_for_state(0x0540, p2_reuse_context);
    assert(p2_reuse != nullptr);
    assert(is_authored_0540_p2_companion_0d2d_registration(*p2_reuse));
    for (int y = 0; y < kRacerHdAssetSize; y += 7) {
        for (int x = 0; x < kRacerHdAssetSize; x += 7) {
            assert(
                sample_racer_hd_asset(*p2_reuse, x, y, false, false) ==
                sample_racer_hd_asset(*p2_baseline, x, y, false, false)
            );
        }
    }

    // Frame 1218 P2 is the first distinct authored P2 pose after the 0540
    // baseline/reuse pair. Its stock contact advances one logical pixel left.
    RacerCompositionState p2_predecessor_context{
        0x0540, 0x0541, 0x0D2C, 0x0000, 0, 0, 0x0001, 0x0000
    };
    const auto* p2_predecessor =
        find_racer_registration_for_state(0x0541, p2_predecessor_context);
    assert(p2_predecessor != nullptr);
    assert(is_authored_0541_p2_predecessor_registration(*p2_predecessor));

    int p2_predecessor_min_lx = kRacerHdLogicalSize;
    int p2_predecessor_min_ly = kRacerHdLogicalSize;
    int p2_predecessor_max_lx = -1;
    int p2_predecessor_max_ly = -1;
    int p2_predecessor_bottom_min_lx = kRacerHdLogicalSize;
    int p2_predecessor_bottom_max_lx = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*p2_predecessor, sx, sy, false, false) == 0) continue;
            if (lx < p2_predecessor_min_lx) p2_predecessor_min_lx = lx;
            if (ly < p2_predecessor_min_ly) p2_predecessor_min_ly = ly;
            if (lx > p2_predecessor_max_lx) p2_predecessor_max_lx = lx;
            if (ly > p2_predecessor_max_ly) p2_predecessor_max_ly = ly;
            if (ly == 38) {
                if (lx < p2_predecessor_bottom_min_lx) p2_predecessor_bottom_min_lx = lx;
                if (lx > p2_predecessor_bottom_max_lx) p2_predecessor_bottom_max_lx = lx;
            }
        }
    }
    assert(p2_predecessor_min_lx == 22);
    assert(p2_predecessor_min_ly == 3);
    assert(p2_predecessor_max_lx == 39);
    assert(p2_predecessor_max_ly == 38);
    assert(p2_predecessor_bottom_min_lx == 29);
    assert(p2_predecessor_bottom_max_lx == 32);
    assert(p2_predecessor_bottom_min_lx + p2_predecessor_bottom_max_lx == 61);

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
