#pragma once

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

struct SnesDesktopHostFrameStats;
struct SnesDisplayViewport;

void ur_uniracers_modern_after_config(void);
void ur_uniracers_modern_after_run_frame(
    const struct SnesDesktopHostFrameStats* stats);
int ur_uniracers_modern_system_key_down(int key, int mod, int repeat);
int ur_uniracers_modern_system_gamepad_button(int button, int pressed);
int ur_uniracers_modern_controls_active(void);
int ur_uniracers_modern_system_gamepad_control(int control, int pressed);
void ur_uniracers_modern_system_overlay(
    uint8_t* dst,
    size_t pitch,
    int width,
    int height);
/* 0 keeps presentation locked to authoritative guest cadence; positive
 * values request only host-side re-presentation of captured frames. */
double ur_uniracers_modern_presentation_hz(double display_refresh);

/* Widescreen presentation callbacks. They are inert unless the accepted
 * authentic-16x9 selector is active; scene ownership stays title-side. */
int ur_uniracers_modern_native_widescreen_enabled(void);
void ur_uniracers_modern_prepare_frame(
    int drawable_width,
    int drawable_height,
    int* frame_width,
    int* frame_height);
void ur_uniracers_modern_begin_sim_frame(unsigned frame_number);
int ur_uniracers_modern_presentation_scale(void);
int ur_uniracers_modern_draw_frame(
    uint8_t* dst, size_t pitch, const uint8_t* field,
    int frame_width, int frame_height, double alpha);
void ur_uniracers_modern_compute_viewport(
    int frame_width,
    int frame_height,
    int drawable_width,
    int drawable_height,
    struct SnesDisplayViewport* viewport);

#ifdef __cplusplus
}
#endif
