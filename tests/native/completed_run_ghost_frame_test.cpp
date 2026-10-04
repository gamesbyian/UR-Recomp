#include "completed_run_ghost_frame.hpp"

#include <cassert>

using namespace ur::product;

int main() {
    CompletedRunGhostTrace trace;
    trace.run_artifact_checksum = "0123456789abcdef";
    trace.samples = {
        {0, 1088, 859, 0x0007, 0x0541, 1, 0x66, {0x0541, 0x0540, 0x0D0D, 0, 0, 0, 1, 0}},
        {1, 1100, 850, 0x0009, 0x0540, 1, 0xE6, {0x0540, 0x0541, 0x0D2C, 0, 0, 0, 1, 0}},
    };

    CompletedRunGhostProjectionContext live;
    live.camera_x = 1000;
    live.camera_y = 800;
    live.horizontal_scale_shifts = 0;
    live.horizontal_lower_bound = 0xFFD7;
    live.horizontal_upper_bound = 0x00E1;
    live.horizontal_wrap_mask = 0x00FF;

    const auto frame0 =
        resolve_completed_run_ghost_presentation_frame(trace, 0, live);
    assert(frame0);
    assert(frame0->race_frame == 0);
    assert(frame0->semantic_frame_id == 0x0541);
    assert(frame0->pitch_angle == 0x0007);
    assert(frame0->facing == 1);
    assert(frame0->sprite_attr == 0x66);
    assert(frame0->composition.p1_primary == 0x0541);
    assert(frame0->composition.p2_primary == 0x0540);
    assert(frame0->composition.p1_companion == 0x0D0D);
    assert(frame0->screen_x == 88);
    assert(frame0->screen_y == 59);
    assert(frame0->hflip);
    assert(!frame0->vflip);
    assert(!frame0->oam_x_high);

    const auto frame1 =
        resolve_completed_run_ghost_presentation_frame(trace, 1, live);
    assert(frame1);
    assert(frame1->semantic_frame_id == 0x0540);
    assert(frame1->hflip);
    assert(frame1->vflip);

    assert(!resolve_completed_run_ghost_presentation_frame(
        trace, 2, live));

    auto culled = live;
    culled.camera_y = 1000;
    assert(!resolve_completed_run_ghost_presentation_frame(
        trace, 0, culled));

    return 0;
}
