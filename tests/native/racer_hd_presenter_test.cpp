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


    static_assert(valid_racer_hd_internal_render_scale(1));
    static_assert(valid_racer_hd_internal_render_scale(4));
    static_assert(!valid_racer_hd_internal_render_scale(0));
    static_assert(!valid_racer_hd_internal_render_scale(5));
    for (int x = 0; x < kRacerHdAssetSize; x += 17) {
        assert(racer_hd_scaled_sample_coordinate(x, 4) == x);
        assert(
            sample_racer_hd_scaled_asset(
                *registration, x, 0, 4, false, false
            ) ==
            sample_racer_hd_asset(*registration, x, 0, false, false)
        );
    }
    for (int logical = 0; logical < kRacerHdLogicalSize; logical += 7) {
        assert(
            racer_hd_scaled_sample_coordinate(logical, 1) ==
            logical * kRacerHdDensityScale + kRacerHdDensityScale / 2
        );
    }
    for (int scale = 1; scale <= kRacerHdDensityScale; ++scale) {
        const int last = kRacerHdLogicalSize * scale - 1;
        const int sample = racer_hd_scaled_sample_coordinate(last, scale);
        assert(sample >= 0);
        assert(sample < kRacerHdAssetSize);
    }
    // True-density refinement pass 1 restores internal structure that was
    // visibly absent in the first shipping review while staying inside the
    // accepted logical envelope/contact.
    assert(sample_racer_hd_asset(*registration, 116, 88, false, false) != 0);
    assert(sample_racer_hd_asset(*registration, 110, 122, false, false) != 0);

    // The immediately preceding exact 0541/0D2D composition has its own
    // authored temporal-neighbor candidate rather than falling through to the
    // generic contract placeholder.
    RacerCompositionState companion_context{
        0x0541, 0x0540, 0x0D2D, 0x0000, 0, 0, 0x0001, 0x0000
    };
    const auto* companion =
        find_racer_registration_for_state(0x0541, companion_context, 1);
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
        find_racer_registration_for_state(0x0540, reversed_context, 1);
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
        find_racer_registration_for_state(0x0540, reused_context, 1);
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
        find_racer_registration_for_state(0x057F, repeated_057f_context, 1);
    assert(repeated_057f != nullptr);
    assert(is_authored_057f_p1_companion_0d4a_registration(*repeated_057f));
    assert(sample_racer_hd_asset(*repeated_057f, 156, 22, false, false) == 0);
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
        find_racer_registration_for_state(0x057E, repeated_057e_context, 1);
    assert(repeated_057e != nullptr);
    assert(is_authored_057e_p1_with_p2_0543_registration(*repeated_057e));
    assert(sample_racer_hd_asset(*repeated_057e, 150, 22, false, false) == 0);

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
        find_racer_registration_for_state(0x057D, repeated_057d_context, 1);
    assert(repeated_057d != nullptr);
    assert(is_authored_057d_p1_with_p2_0543_registration(*repeated_057d));
    assert(sample_racer_hd_asset(*repeated_057d, 146, 26, false, false) == 0);

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
        find_racer_registration_for_state(0x0540, p2_baseline_context, 2);
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
        find_racer_registration_for_state(0x0540, p2_reuse_context, 2);
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
        find_racer_registration_for_state(0x0541, p2_predecessor_context, 2);
    assert(p2_predecessor != nullptr);
    assert(is_authored_0541_p2_predecessor_registration(*p2_predecessor));
    assert(sample_racer_hd_asset(*p2_predecessor, 94, 22, false, false) == 0);

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

    // Frame 1217 P2 0542 is the next genuine visual change. The same stock
    // raster recurs under the 057F/0D4A context at frames 1215-1216, so both
    // exact registrations must resolve to one shared authored pose.
    RacerCompositionState p2_0542_context{
        0x0540, 0x0542, 0x0D2C, 0x0000, 0, 0, 0x0001, 0x0000
    };
    const auto* p2_0542 =
        find_racer_registration_for_state(0x0542, p2_0542_context, 2);
    assert(p2_0542 != nullptr);
    assert(is_authored_0542_p2_companion_0d2c_registration(*p2_0542));
    assert(sample_racer_hd_asset(*p2_0542, 132, 84, false, false) != 0);
    assert(sample_racer_hd_asset(*p2_0542, 126, 110, false, false) != 0);

    RacerCompositionState p2_0542_reuse_context{
        0x057F, 0x0542, 0x0D4A, 0x0000, 0, 0, 0x0001, 0x0000
    };
    const auto* p2_0542_reuse =
        find_racer_registration_for_state(0x0542, p2_0542_reuse_context, 2);
    assert(p2_0542_reuse != nullptr);
    assert(is_authored_0542_p2_companion_0d4a_registration(*p2_0542_reuse));

    int p2_0542_min_lx = kRacerHdLogicalSize;
    int p2_0542_min_ly = kRacerHdLogicalSize;
    int p2_0542_max_lx = -1;
    int p2_0542_max_ly = -1;
    int p2_0542_bottom_min_lx = kRacerHdLogicalSize;
    int p2_0542_bottom_max_lx = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const auto primary = sample_racer_hd_asset(*p2_0542, sx, sy, false, false);
            const auto reused = sample_racer_hd_asset(*p2_0542_reuse, sx, sy, false, false);
            assert(primary == reused);
            if (primary == 0) continue;
            if (lx < p2_0542_min_lx) p2_0542_min_lx = lx;
            if (ly < p2_0542_min_ly) p2_0542_min_ly = ly;
            if (lx > p2_0542_max_lx) p2_0542_max_lx = lx;
            if (ly > p2_0542_max_ly) p2_0542_max_ly = ly;
            if (ly == 38) {
                if (lx < p2_0542_bottom_min_lx) p2_0542_bottom_min_lx = lx;
                if (lx > p2_0542_bottom_max_lx) p2_0542_bottom_max_lx = lx;
            }
        }
    }
    assert(p2_0542_min_lx == 21);
    assert(p2_0542_min_ly == 4);
    assert(p2_0542_max_lx == 40);
    assert(p2_0542_max_ly == 38);
    assert(p2_0542_bottom_min_lx == 28);
    assert(p2_0542_bottom_max_lx == 31);
    assert(p2_0542_bottom_min_lx + p2_0542_bottom_max_lx == 59);

    // The retained 0543 P2 contexts share byte-identical stock art, so one
    // authored pose must serve both exact synchronized guards.
    RacerCompositionState p2_0543_context{
        0x057D, 0x0543, 0x0D48, 0x0000, 0, 0, 0x0001, 0x0000
    };
    const auto* p2_0543 =
        find_racer_registration_for_state(0x0543, p2_0543_context, 2);
    assert(p2_0543 != nullptr);
    assert(is_authored_0543_p2_057d_registration(*p2_0543));
    assert(sample_racer_hd_asset(*p2_0543, 130, 88, false, false) != 0);
    assert(sample_racer_hd_asset(*p2_0543, 122, 110, false, false) != 0);

    RacerCompositionState p2_0543_reuse_context{
        0x057E, 0x0543, 0x0D49, 0x0000, 0, 0, 0x0001, 0x0000
    };
    const auto* p2_0543_reuse =
        find_racer_registration_for_state(0x0543, p2_0543_reuse_context, 2);
    assert(p2_0543_reuse != nullptr);
    assert(is_authored_0543_p2_057e_registration(*p2_0543_reuse));

    int p2_0543_min_lx = kRacerHdLogicalSize;
    int p2_0543_min_ly = kRacerHdLogicalSize;
    int p2_0543_max_lx = -1;
    int p2_0543_max_ly = -1;
    int p2_0543_bottom_min_lx = kRacerHdLogicalSize;
    int p2_0543_bottom_max_lx = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const auto primary = sample_racer_hd_asset(*p2_0543, sx, sy, false, false);
            const auto reused = sample_racer_hd_asset(*p2_0543_reuse, sx, sy, false, false);
            assert(primary == reused);
            if (primary == 0) continue;
            if (lx < p2_0543_min_lx) p2_0543_min_lx = lx;
            if (ly < p2_0543_min_ly) p2_0543_min_ly = ly;
            if (lx > p2_0543_max_lx) p2_0543_max_lx = lx;
            if (ly > p2_0543_max_ly) p2_0543_max_ly = ly;
            if (ly == 38) {
                if (lx < p2_0543_bottom_min_lx) p2_0543_bottom_min_lx = lx;
                if (lx > p2_0543_bottom_max_lx) p2_0543_bottom_max_lx = lx;
            }
        }
    }
    assert(p2_0543_min_lx == 20);
    assert(p2_0543_min_ly == 4);
    assert(p2_0543_max_lx == 40);
    assert(p2_0543_max_ly == 38);
    assert(p2_0543_bottom_min_lx == 26);
    assert(p2_0543_bottom_max_lx == 31);
    assert(p2_0543_bottom_min_lx + p2_0543_bottom_max_lx == 57);

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
        registration->composition,
        1
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
    RacerCompositionState frequency_0544_0578_context{
        0x0544, 0x0578, 0x0000, 0x0D63, 0, 0, 0x0000, 0x0001
    };
    const auto* frequency_p1 =
        find_racer_registration_for_state(0x0544, frequency_0544_0578_context, 1);
    const auto* frequency_p2 =
        find_racer_registration_for_state(0x0578, frequency_0544_0578_context, 2);
    assert(frequency_p1 != nullptr);
    assert(frequency_p2 != nullptr);
    assert(is_authored_frequency_0544_p1_0578_registration(*frequency_p1));
    assert(is_authored_frequency_0578_p2_0544_registration(*frequency_p2));

    for (const auto* target : {frequency_p1, frequency_p2}) {
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
                if (sample_racer_hd_asset(*target, sx, sy, false, false) == 0) continue;
                if (lx < min_lx) min_lx = lx;
                if (ly < min_ly) min_ly = ly;
                if (lx > max_lx) max_lx = lx;
                if (ly > max_ly) max_ly = ly;
            }
        }
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = max_ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*target, sx, sy, false, false) == 0) continue;
            if (lx < bottom_min_lx) bottom_min_lx = lx;
            if (lx > bottom_max_lx) bottom_max_lx = lx;
        }
        if (target == frequency_p1) {
            assert(min_lx == 19 && min_ly == 5 && max_lx == 41 && max_ly == 38);
            assert(bottom_min_lx + bottom_max_lx == 55);
        } else {
            assert(min_lx == 17 && min_ly == 5 && max_lx == 47 && max_ly == 36);
            assert(bottom_min_lx + bottom_max_lx == 77);
        }
    }

    RacerCompositionState broader_04b9_context{
        0x04B9, 0x0578, 0x0000, 0x0EC3, 0, 0, 0x0000, 0x0001
    };
    const auto* broader_04b9 =
        find_racer_registration_for_state(0x04B9, broader_04b9_context, 1);
    assert(broader_04b9 != nullptr);
    assert(is_authored_broader_04b9_p1_registration(*broader_04b9));

    int broader_min_lx = kRacerHdLogicalSize;
    int broader_min_ly = kRacerHdLogicalSize;
    int broader_max_lx = -1;
    int broader_max_ly = -1;
    int broader_bottom_min_lx = kRacerHdLogicalSize;
    int broader_bottom_max_lx = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*broader_04b9, sx, sy, false, false) == 0) continue;
            if (lx < broader_min_lx) broader_min_lx = lx;
            if (ly < broader_min_ly) broader_min_ly = ly;
            if (lx > broader_max_lx) broader_max_lx = lx;
            if (ly > broader_max_ly) broader_max_ly = ly;
        }
    }
    for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
        const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        const int sy = broader_max_ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        if (sample_racer_hd_asset(*broader_04b9, sx, sy, false, false) == 0) continue;
        if (lx < broader_bottom_min_lx) broader_bottom_min_lx = lx;
        if (lx > broader_bottom_max_lx) broader_bottom_max_lx = lx;
    }
    assert(broader_min_lx == 18);
    assert(broader_min_ly == 5);
    assert(broader_max_lx == 47);
    assert(broader_max_ly == 36);
    assert(broader_bottom_min_lx + broader_bottom_max_lx == 77);

    RacerCompositionState broader_0239_context{
        0x0239, 0x057A, 0x0000, 0x0EC5, 0, 0, 0x0000, 0x0001
    };
    const auto* broader_0239 =
        find_racer_registration_for_state(0x0239, broader_0239_context, 1);
    assert(broader_0239 != nullptr);
    assert(is_authored_broader_0239_p1_registration(*broader_0239));

    int b0239_min_x = kRacerHdLogicalSize, b0239_min_y = kRacerHdLogicalSize;
    int b0239_max_x = -1, b0239_max_y = -1;
    int b0239_bottom_min_x = kRacerHdLogicalSize, b0239_bottom_max_x = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*broader_0239, sx, sy, false, false) == 0) continue;
            if (lx < b0239_min_x) b0239_min_x = lx;
            if (ly < b0239_min_y) b0239_min_y = ly;
            if (lx > b0239_max_x) b0239_max_x = lx;
            if (ly > b0239_max_y) b0239_max_y = ly;
        }
    }
    for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
        const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        const int sy = b0239_max_y * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        if (sample_racer_hd_asset(*broader_0239, sx, sy, false, false) == 0) continue;
        if (lx < b0239_bottom_min_x) b0239_bottom_min_x = lx;
        if (lx > b0239_bottom_max_x) b0239_bottom_max_x = lx;
    }
    assert(b0239_min_x == 18);
    assert(b0239_min_y == 5);
    assert(b0239_max_x == 47);
    assert(b0239_max_y == 36);
    assert(b0239_bottom_min_x + b0239_bottom_max_x == 77);

    assert(racer_hd_asset_available(0x0239));
    assert(racer_hd_asset_available(0x0439));

    RacerCompositionState broader_0439_context{
        0x0439, 0x0578, 0x0000, 0x0EC3, 0, 0, 0x0000, 0x0001
    };
    const auto* broader_0439 =
        find_racer_registration_for_state(0x0439, broader_0439_context, 1);
    assert(broader_0439 != nullptr);
    assert(is_authored_broader_0439_p1_registration(*broader_0439));

    int b0439_min_x = kRacerHdLogicalSize, b0439_min_y = kRacerHdLogicalSize;
    int b0439_max_x = -1, b0439_max_y = -1;
    int b0439_bottom_min_x = kRacerHdLogicalSize, b0439_bottom_max_x = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*broader_0439, sx, sy, false, false) == 0) continue;
            if (lx < b0439_min_x) b0439_min_x = lx;
            if (ly < b0439_min_y) b0439_min_y = ly;
            if (lx > b0439_max_x) b0439_max_x = lx;
            if (ly > b0439_max_y) b0439_max_y = ly;
        }
    }
    for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
        const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        const int sy = b0439_max_y * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        if (sample_racer_hd_asset(*broader_0439, sx, sy, false, false) == 0) continue;
        if (lx < b0439_bottom_min_x) b0439_bottom_min_x = lx;
        if (lx > b0439_bottom_max_x) b0439_bottom_max_x = lx;
    }
    assert(b0439_min_x == 18);
    assert(b0439_min_y == 5);
    assert(b0439_max_x == 47);
    assert(b0439_max_y == 36);
    assert(b0439_bottom_min_x + b0439_bottom_max_x == 77);

    assert(racer_hd_asset_available(0x0039));

    RacerCompositionState broader_0039_context{
        0x0039, 0x0577, 0x0000, 0x0EC2, 0, 0, 0x0000, 0x0001
    };
    const auto* broader_0039 =
        find_racer_registration_for_state(0x0039, broader_0039_context, 1);
    assert(broader_0039 != nullptr);
    assert(is_authored_broader_0039_p1_registration(*broader_0039));

    int b0039_min_x = kRacerHdLogicalSize, b0039_min_y = kRacerHdLogicalSize;
    int b0039_max_x = -1, b0039_max_y = -1;
    int b0039_bottom_min_x = kRacerHdLogicalSize, b0039_bottom_max_x = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*broader_0039, sx, sy, false, false) == 0) continue;
            if (lx < b0039_min_x) b0039_min_x = lx;
            if (ly < b0039_min_y) b0039_min_y = ly;
            if (lx > b0039_max_x) b0039_max_x = lx;
            if (ly > b0039_max_y) b0039_max_y = ly;
        }
    }
    for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
        const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        const int sy = b0039_max_y * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        if (sample_racer_hd_asset(*broader_0039, sx, sy, false, false) == 0) continue;
        if (lx < b0039_bottom_min_x) b0039_bottom_min_x = lx;
        if (lx > b0039_bottom_max_x) b0039_bottom_max_x = lx;
    }
    assert(b0039_min_x == 18);
    assert(b0039_min_y == 5);
    assert(b0039_max_x == 47);
    assert(b0039_max_y == 36);
    assert(b0039_bottom_min_x + b0039_bottom_max_x == 77);

    assert(racer_hd_asset_available(0x00B9));

    RacerCompositionState broader_00b9_context{
        0x00B9, 0x0578, 0x0000, 0x0EC3, 0, 0, 0x0000, 0x0001
    };
    const auto* broader_00b9 =
        find_racer_registration_for_state(0x00B9, broader_00b9_context, 1);
    assert(broader_00b9 != nullptr);
    assert(is_authored_broader_00b9_p1_registration(*broader_00b9));

    int b00b9_min_x = kRacerHdLogicalSize, b00b9_min_y = kRacerHdLogicalSize;
    int b00b9_max_x = -1, b00b9_max_y = -1;
    int b00b9_bottom_min_x = kRacerHdLogicalSize, b00b9_bottom_max_x = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*broader_00b9, sx, sy, false, false) == 0) continue;
            if (lx < b00b9_min_x) b00b9_min_x = lx;
            if (ly < b00b9_min_y) b00b9_min_y = ly;
            if (lx > b00b9_max_x) b00b9_max_x = lx;
            if (ly > b00b9_max_y) b00b9_max_y = ly;
        }
    }
    for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
        const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        const int sy = b00b9_max_y * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        if (sample_racer_hd_asset(*broader_00b9, sx, sy, false, false) == 0) continue;
        if (lx < b00b9_bottom_min_x) b00b9_bottom_min_x = lx;
        if (lx > b00b9_bottom_max_x) b00b9_bottom_max_x = lx;
    }
    assert(b00b9_min_x == 18);
    assert(b00b9_min_y == 5);
    assert(b00b9_max_x == 47);
    assert(b00b9_max_y == 36);
    assert(b00b9_bottom_min_x + b00b9_bottom_max_x == 77);

    assert(racer_hd_asset_available(0x02B9));

    RacerCompositionState broader_02b9_context{
        0x02B9, 0x057E, 0x0000, 0x0C29, 0, 0, 0x0000, 0x0001
    };
    const auto* broader_02b9 =
        find_racer_registration_for_state(0x02B9, broader_02b9_context, 1);
    assert(broader_02b9 != nullptr);
    assert(is_authored_broader_02b9_p1_registration(*broader_02b9));

    int b02b9_min_x = kRacerHdLogicalSize, b02b9_min_y = kRacerHdLogicalSize;
    int b02b9_max_x = -1, b02b9_max_y = -1;
    int b02b9_bottom_min_x = kRacerHdLogicalSize, b02b9_bottom_max_x = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*broader_02b9, sx, sy, false, false) == 0) continue;
            if (lx < b02b9_min_x) b02b9_min_x = lx;
            if (ly < b02b9_min_y) b02b9_min_y = ly;
            if (lx > b02b9_max_x) b02b9_max_x = lx;
            if (ly > b02b9_max_y) b02b9_max_y = ly;
        }
    }
    for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
        const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        const int sy = b02b9_max_y * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        if (sample_racer_hd_asset(*broader_02b9, sx, sy, false, false) == 0) continue;
        if (lx < b02b9_bottom_min_x) b02b9_bottom_min_x = lx;
        if (lx > b02b9_bottom_max_x) b02b9_bottom_max_x = lx;
    }
    assert(b02b9_min_x == 18);
    assert(b02b9_min_y == 5);
    assert(b02b9_max_x == 47);
    assert(b02b9_max_y == 36);
    assert(b02b9_bottom_min_x + b02b9_bottom_max_x == 77);

    assert(racer_hd_asset_available(0x01B9));

    RacerCompositionState broader_01b9_context{
        0x01B9, 0x057C, 0x0000, 0x0C27, 0, 0, 0x0000, 0x0001
    };
    const auto* broader_01b9 =
        find_racer_registration_for_state(0x01B9, broader_01b9_context, 1);
    assert(broader_01b9 != nullptr);
    assert(is_authored_broader_01b9_p1_registration(*broader_01b9));

    int b01b9_min_x = kRacerHdLogicalSize, b01b9_min_y = kRacerHdLogicalSize;
    int b01b9_max_x = -1, b01b9_max_y = -1;
    int b01b9_bottom_min_x = kRacerHdLogicalSize, b01b9_bottom_max_x = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*broader_01b9, sx, sy, false, false) == 0) continue;
            if (lx < b01b9_min_x) b01b9_min_x = lx;
            if (ly < b01b9_min_y) b01b9_min_y = ly;
            if (lx > b01b9_max_x) b01b9_max_x = lx;
            if (ly > b01b9_max_y) b01b9_max_y = ly;
        }
    }
    for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
        const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        const int sy = b01b9_max_y * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        if (sample_racer_hd_asset(*broader_01b9, sx, sy, false, false) == 0) continue;
        if (lx < b01b9_bottom_min_x) b01b9_bottom_min_x = lx;
        if (lx > b01b9_bottom_max_x) b01b9_bottom_max_x = lx;
    }
    assert(b01b9_min_x == 18);
    assert(b01b9_min_y == 5);
    assert(b01b9_max_x == 47);
    assert(b01b9_max_y == 36);
    assert(b01b9_bottom_min_x + b01b9_bottom_max_x == 77);

    assert(racer_hd_asset_available(0x0139));

    RacerCompositionState broader_0139_context{
        0x0139, 0x057C, 0x0000, 0x0C27, 0, 0, 0x0000, 0x0001
    };
    const auto* broader_0139 =
        find_racer_registration_for_state(0x0139, broader_0139_context, 1);
    assert(broader_0139 != nullptr);
    assert(is_authored_broader_0139_p1_registration(*broader_0139));

    int b0139_min_x = kRacerHdLogicalSize, b0139_min_y = kRacerHdLogicalSize;
    int b0139_max_x = -1, b0139_max_y = -1;
    int b0139_bottom_min_x = kRacerHdLogicalSize, b0139_bottom_max_x = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*broader_0139, sx, sy, false, false) == 0) continue;
            if (lx < b0139_min_x) b0139_min_x = lx;
            if (ly < b0139_min_y) b0139_min_y = ly;
            if (lx > b0139_max_x) b0139_max_x = lx;
            if (ly > b0139_max_y) b0139_max_y = ly;
        }
    }
    for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
        const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        const int sy = b0139_max_y * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        if (sample_racer_hd_asset(*broader_0139, sx, sy, false, false) == 0) continue;
        if (lx < b0139_bottom_min_x) b0139_bottom_min_x = lx;
        if (lx > b0139_bottom_max_x) b0139_bottom_max_x = lx;
    }
    assert(b0139_min_x == 18);
    assert(b0139_min_y == 5);
    assert(b0139_max_x == 47);
    assert(b0139_max_y == 36);
    assert(b0139_bottom_min_x + b0139_bottom_max_x == 77);

    assert(racer_hd_asset_available(0x0539));

    RacerCompositionState broader_0539_context{
        0x0539, 0x0578, 0x0000, 0x0EC3, 0, 0, 0x0000, 0x0001
    };
    const auto* broader_0539 =
        find_racer_registration_for_state(0x0539, broader_0539_context, 1);
    assert(broader_0539 != nullptr);
    assert(is_authored_broader_0539_p1_registration(*broader_0539));

    int b0539_min_x = kRacerHdLogicalSize, b0539_min_y = kRacerHdLogicalSize;
    int b0539_max_x = -1, b0539_max_y = -1;
    int b0539_bottom_min_x = kRacerHdLogicalSize, b0539_bottom_max_x = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*broader_0539, sx, sy, false, false) == 0) continue;
            if (lx < b0539_min_x) b0539_min_x = lx;
            if (ly < b0539_min_y) b0539_min_y = ly;
            if (lx > b0539_max_x) b0539_max_x = lx;
            if (ly > b0539_max_y) b0539_max_y = ly;
        }
    }
    for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
        const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        const int sy = b0539_max_y * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        if (sample_racer_hd_asset(*broader_0539, sx, sy, false, false) == 0) continue;
        if (lx < b0539_bottom_min_x) b0539_bottom_min_x = lx;
        if (lx > b0539_bottom_max_x) b0539_bottom_max_x = lx;
    }
    assert(b0539_min_x == 18);
    assert(b0539_min_y == 5);
    assert(b0539_max_x == 47);
    assert(b0539_max_y == 36);
    assert(b0539_bottom_min_x + b0539_bottom_max_x == 77);

    assert(racer_hd_asset_available(0x05B9));

    RacerCompositionState broader_05b9_context{
        0x05B9, 0x0544, 0x0000, 0x0000, 0, 0, 0x0000, 0x0000
    };
    const auto* broader_05b9 =
        find_racer_registration_for_state(0x05B9, broader_05b9_context, 1);
    assert(broader_05b9 != nullptr);
    assert(is_authored_broader_05b9_p1_registration(*broader_05b9));

    int b05b9_min_x = kRacerHdLogicalSize, b05b9_min_y = kRacerHdLogicalSize;
    int b05b9_max_x = -1, b05b9_max_y = -1;
    int b05b9_bottom_min_x = kRacerHdLogicalSize, b05b9_bottom_max_x = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*broader_05b9, sx, sy, false, false) == 0) continue;
            if (lx < b05b9_min_x) b05b9_min_x = lx;
            if (ly < b05b9_min_y) b05b9_min_y = ly;
            if (lx > b05b9_max_x) b05b9_max_x = lx;
            if (ly > b05b9_max_y) b05b9_max_y = ly;
        }
    }
    for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
        const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        const int sy = b05b9_max_y * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        if (sample_racer_hd_asset(*broader_05b9, sx, sy, false, false) == 0) continue;
        if (lx < b05b9_bottom_min_x) b05b9_bottom_min_x = lx;
        if (lx > b05b9_bottom_max_x) b05b9_bottom_max_x = lx;
    }
    assert(b05b9_min_x == 18);
    assert(b05b9_min_y == 5);
    assert(b05b9_max_x == 47);
    assert(b05b9_max_y == 36);
    assert(b05b9_bottom_min_x + b05b9_bottom_max_x == 77);

    assert(racer_hd_asset_available(0x03B9));

    RacerCompositionState broader_03b9_context{
        0x03B9, 0x0541, 0x0000, 0x0C0D, 0, 0, 0x0000, 0x0001
    };
    const auto* broader_03b9 =
        find_racer_registration_for_state(0x03B9, broader_03b9_context, 1);
    assert(broader_03b9 != nullptr);
    assert(is_authored_broader_03b9_p1_registration(*broader_03b9));

    int b03b9_min_x = kRacerHdLogicalSize, b03b9_min_y = kRacerHdLogicalSize;
    int b03b9_max_x = -1, b03b9_max_y = -1;
    int b03b9_bottom_min_x = kRacerHdLogicalSize, b03b9_bottom_max_x = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*broader_03b9, sx, sy, false, false) == 0) continue;
            if (lx < b03b9_min_x) b03b9_min_x = lx;
            if (ly < b03b9_min_y) b03b9_min_y = ly;
            if (lx > b03b9_max_x) b03b9_max_x = lx;
            if (ly > b03b9_max_y) b03b9_max_y = ly;
        }
    }
    for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
        const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        const int sy = b03b9_max_y * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        if (sample_racer_hd_asset(*broader_03b9, sx, sy, false, false) == 0) continue;
        if (lx < b03b9_bottom_min_x) b03b9_bottom_min_x = lx;
        if (lx > b03b9_bottom_max_x) b03b9_bottom_max_x = lx;
    }
    assert(b03b9_min_x == 18);
    assert(b03b9_min_y == 5);
    assert(b03b9_max_x == 47);
    assert(b03b9_max_y == 36);
    assert(b03b9_bottom_min_x + b03b9_bottom_max_x == 77);

    assert(racer_hd_asset_available(0x0339));

    RacerCompositionState broader_0339_context{
        0x0339, 0x0540, 0x0000, 0x0C0C, 0, 0, 0x0000, 0x0001
    };
    const auto* broader_0339 =
        find_racer_registration_for_state(0x0339, broader_0339_context, 1);
    assert(broader_0339 != nullptr);
    assert(is_authored_broader_0339_p1_registration(*broader_0339));

    int b0339_min_x = kRacerHdLogicalSize, b0339_min_y = kRacerHdLogicalSize;
    int b0339_max_x = -1, b0339_max_y = -1;
    int b0339_bottom_min_x = kRacerHdLogicalSize, b0339_bottom_max_x = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*broader_0339, sx, sy, false, false) == 0) continue;
            if (lx < b0339_min_x) b0339_min_x = lx;
            if (ly < b0339_min_y) b0339_min_y = ly;
            if (lx > b0339_max_x) b0339_max_x = lx;
            if (ly > b0339_max_y) b0339_max_y = ly;
        }
    }
    for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
        const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        const int sy = b0339_max_y * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        if (sample_racer_hd_asset(*broader_0339, sx, sy, false, false) == 0) continue;
        if (lx < b0339_bottom_min_x) b0339_bottom_min_x = lx;
        if (lx > b0339_bottom_max_x) b0339_bottom_max_x = lx;
    }
    assert(b0339_min_x == 18);
    assert(b0339_min_y == 5);
    assert(b0339_max_x == 47);
    assert(b0339_max_y == 36);
    assert(b0339_bottom_min_x + b0339_bottom_max_x == 77);

    assert(racer_hd_asset_available(0x0379));

    RacerCompositionState broader_0379_context{
        0x0379, 0x0543, 0x0000, 0x0000, 0, 0, 0x0000, 0x0000
    };
    const auto* broader_0379 =
        find_racer_registration_for_state(0x0379, broader_0379_context, 1);
    assert(broader_0379 != nullptr);
    assert(is_authored_broader_0379_p1_registration(*broader_0379));

    int b0379_min_x = kRacerHdLogicalSize, b0379_min_y = kRacerHdLogicalSize;
    int b0379_max_x = -1, b0379_max_y = -1;
    int b0379_bottom_min_x = kRacerHdLogicalSize, b0379_bottom_max_x = -1;
    for (int ly = 0; ly < kRacerHdLogicalSize; ++ly) {
        for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
            const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            const int sy = ly * kRacerHdDensityScale + kRacerHdDensityScale / 2;
            if (sample_racer_hd_asset(*broader_0379, sx, sy, false, false) == 0) continue;
            if (lx < b0379_min_x) b0379_min_x = lx;
            if (ly < b0379_min_y) b0379_min_y = ly;
            if (lx > b0379_max_x) b0379_max_x = lx;
            if (ly > b0379_max_y) b0379_max_y = ly;
        }
    }
    for (int lx = 0; lx < kRacerHdLogicalSize; ++lx) {
        const int sx = lx * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        const int sy = b0379_max_y * kRacerHdDensityScale + kRacerHdDensityScale / 2;
        if (sample_racer_hd_asset(*broader_0379, sx, sy, false, false) == 0) continue;
        if (lx < b0379_bottom_min_x) b0379_bottom_min_x = lx;
        if (lx > b0379_bottom_max_x) b0379_bottom_max_x = lx;
    }
    assert(b0379_min_x == 18);
    assert(b0379_min_y == 5);
    assert(b0379_max_x == 47);
    assert(b0379_max_y == 36);
    assert(b0379_bottom_min_x + b0379_bottom_max_x == 77);

    return 0;
}
